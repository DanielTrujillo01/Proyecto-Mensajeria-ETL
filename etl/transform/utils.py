import pandas as pd


# ======================================================================
# Medidas de tiempo: cálculo + limpieza de negativos/outliers
# ======================================================================

def limpiar_metricas_tiempo(df, columnas, factor_iqr=1.5, grupo_col=None, min_muestra_outlier=30):
    """
    Invalida (deja en NaN) valores negativos y outliers estadísticos en
    columnas de duración, sin descartar la fila completa.

    - Negativos: se consideran dato sucio del sistema origen (fechas
      invertidas), no un error de cálculo, y se excluyen siempre.
    - Outliers: definidos por IQR (Q3 + factor_iqr * IQR). Si se pasa
      grupo_col, el IQR se calcula POR GRUPO (p. ej. por año) en vez de
      globalmente -- necesario porque un IQR global calculado sobre una
      mezcla de periodos con volúmenes/distribuciones muy distintas
      termina tratando al grupo minoritario casi entero como "outlier"
      frente a la distribución del grupo dominante.
    - Si un grupo tiene menos de min_muestra_outlier valores válidos, no
      se le aplica corte de outliers (solo se excluyen negativos): con
      muestras tan chicas, el propio IQR es estadísticamente inestable y
      puede descartar datos legítimos.

    Returns
    -------
    (pandas.DataFrame, pandas.DataFrame)
        DataFrame limpio y resumen (por columna y por grupo si aplica) de
        cuántos valores se excluyeron y por qué motivo.
    """
    df = df.copy()
    resumen = []

    grupos_valores = df[grupo_col].dropna().unique() if grupo_col is not None else [None]

    for col in columnas:
        negativos_total = df[col] < 0
        outliers_total = pd.Series(False, index=df.index)

        for grupo_val in grupos_valores:
            mask_grupo = (df[grupo_col] == grupo_val) if grupo_col is not None else pd.Series(True, index=df.index)

            serie_grupo = df.loc[mask_grupo, col]
            negativos_grupo = serie_grupo < 0
            validos_grupo = serie_grupo[~negativos_grupo & serie_grupo.notna()]
            n_validos = len(validos_grupo)

            if n_validos < min_muestra_outlier:
                limite_superior = None
                outliers_grupo = pd.Series(False, index=serie_grupo.index)
                print(f"[AVISO] {col} - grupo {grupo_val}: muestra pequeña (n={n_validos} < "
                      f"{min_muestra_outlier}), no se aplica corte de outliers, solo negativos.")
            else:
                q1 = validos_grupo.quantile(0.25)
                q3 = validos_grupo.quantile(0.75)
                iqr = q3 - q1
                limite_superior = q3 + factor_iqr * iqr
                outliers_grupo = serie_grupo > limite_superior

            outliers_total.loc[outliers_grupo.index] |= outliers_grupo

            resumen.append({
                "columna": col,
                "grupo": grupo_val if grupo_col is not None else "TODOS",
                "n_valido_original": int(serie_grupo.notna().sum()),
                "n_negativos_excluidos": int(negativos_grupo.sum()),
                "limite_superior_outlier_min": round(float(limite_superior), 2) if limite_superior is not None else None,
                "n_outliers_excluidos": int(outliers_grupo.sum()),
            })

        df.loc[negativos_total | outliers_total, col] = pd.NA

    return df, pd.DataFrame(resumen)


def agregar_medidas_tiempo(fact_servicio):
    """
    Calcula las medidas de tiempo entre las distintas fases del servicio,
    excluye negativos/outliers (ver limpiar_metricas_tiempo) y redondea a
    2 decimales para coincidir con NUMERIC(10,2) del DDL.
    """

    fact_servicio["duracion_iniciado_asignado_min"] = (
        fact_servicio["asignado"]
        - fact_servicio["iniciado"]
    ).dt.total_seconds() / 60

    fact_servicio["duracion_asignado_recogido_min"] = (
        fact_servicio["recogido"]
        - fact_servicio["asignado"]
    ).dt.total_seconds() / 60

    fact_servicio["duracion_recogido_entregado_min"] = (
        fact_servicio["entregado"]
        - fact_servicio["recogido"]
    ).dt.total_seconds() / 60

    fact_servicio["duracion_entregado_cerrado_min"] = (
        fact_servicio["cerrado"]
        - fact_servicio["entregado"]
    ).dt.total_seconds() / 60

    fact_servicio["duracion_total_min"] = (
        fact_servicio["cerrado"]
        - fact_servicio["iniciado"]
    ).dt.total_seconds() / 60

    columnas_duracion = [
        "duracion_iniciado_asignado_min",
        "duracion_asignado_recogido_min",
        "duracion_recogido_entregado_min",
        "duracion_entregado_cerrado_min",
        "duracion_total_min",
    ]

    # Limpieza GLOBAL (sin agrupar por año): se probó agrupar por año, pero
    # 2023 combina poca muestra con datos genuinamente atípicos (período
    # piloto del sistema), y la salvaguarda de muestra mínima terminaba
    # dejando pasar esos valores extremos sin ningún corte. Para un
    # promedio operativo general, un único IQR sobre todos los servicios es
    # el criterio correcto.
    fact_servicio, resumen_limpieza = limpiar_metricas_tiempo(fact_servicio, columnas_duracion)
    print("Resumen de limpieza de duraciones (negativos + outliers excluidos):")
    print(resumen_limpieza.to_string(index=False))

    for col in columnas_duracion:
        fact_servicio[col] = fact_servicio[col].round(2)

    return fact_servicio


# ======================================================================
# FK de fecha + validación de integridad
# ======================================================================

def obtener_key_fecha_desconocida(dim_fechahora):
    """
    Devuelve la fecha_hora_key de la fila 'Desconocido' de dim_fechahora
    (aquella cuyo fecha_hora es NaT). Se calcula dinámicamente en vez de
    asumir que siempre es -1, por si esa convención cambia en el futuro.
    """
    return (
        dim_fechahora
        .loc[dim_fechahora["fecha_hora"].isna(), "fecha_hora_key"]
        .iloc[0]
    )


def agregar_fk_fecha(fact_servicio, dim_fechahora):

    dim_fechahora = dim_fechahora.copy()

    dim_fechahora["fecha_hora"] = pd.to_datetime(
        dim_fechahora["fecha_hora"],
        errors="coerce",
    )

    dim_fh_lookup = dim_fechahora.loc[
        dim_fechahora["fecha_hora"].notna(),
        ["fecha_hora_key", "fecha_hora"],
    ]

    key_fecha_desconocida = obtener_key_fecha_desconocida(dim_fechahora)

    hitos = [
        "iniciado",
        "asignado",
        "recogido",
        "entregado",
        "cerrado",
    ]

    for hito in hitos:

        fact_servicio[hito] = pd.to_datetime(
            fact_servicio[hito],
            errors="coerce",
        )

        fact_servicio = (
            fact_servicio
            .merge(
                dim_fh_lookup,
                left_on=hito,
                right_on="fecha_hora",
                how="left",
            )
            .rename(
                columns={
                    "fecha_hora_key": f"fk_fecha_{hito}"
                }
            )
            .drop(
                columns=[
                    "fecha_hora",
                    hito,
                ]
            )
        )

        fact_servicio[f"fk_fecha_{hito}"] = (
            fact_servicio[f"fk_fecha_{hito}"]
            .fillna(key_fecha_desconocida)
            .astype("Int64")
        )

    return fact_servicio


def validar_fk_fecha(fact_servicio, fechas_originales, dim_fechahora, key_fecha_desconocida):
    """
    Verifica que cada fk_fecha_{hito} apunte, en dim_fechahora, al mismo
    timestamp que realmente se calculó para ese hito y ese servicio.

    Debe llamarse DESPUÉS de agregar_fk_fecha, usando una copia de las
    columnas de fecha originales capturada ANTES de llamar a esa función
    (agregar_fk_fecha las reemplaza/elimina).
    """
    hitos = ["iniciado", "asignado", "recogido", "entregado", "cerrado"]
    dim_lookup = dim_fechahora.set_index("fecha_hora_key")["fecha_hora"]

    comparacion = fact_servicio[
        ["servicio_id"] + [f"fk_fecha_{hito}" for hito in hitos]
    ].merge(fechas_originales, on="servicio_id", how="left")

    for hito in hitos:
        fk_col = f"fk_fecha_{hito}"
        fecha_original = comparacion[hito]
        fecha_en_dim = comparacion[fk_col].map(dim_lookup)

        # Solo se compara donde había una fecha real y la FK no cayó en
        # 'Desconocido' (válido cuando la fecha no existía o fue invalidada
        # por la limpieza de outliers de las duraciones).
        comparable = fecha_original.notna() & (comparacion[fk_col] != key_fecha_desconocida)
        coincide = fecha_en_dim[comparable] == fecha_original[comparable]

        malos = comparacion.loc[comparable][~coincide]
        assert malos.empty, (
            f"{fk_col} tiene {len(malos)} servicio(s) cuya fecha en dim_fechahora no "
            f"coincide con la fecha real de ese estado (ejemplo servicio_id: "
            f"{malos['servicio_id'].iloc[0]})"
        )

    print("[OK] Todas las FK de fecha del hecho corresponden a la fecha real de cada estado.")


# ======================================================================
# FK de cliente / mensajero / sede
# ======================================================================

def agregar_fk_cliente(fact_servicio, servicio, dim_cliente):

    fact_servicio = fact_servicio.merge(
        servicio[
            [
                "id",
                "cliente_id",
            ]
        ].rename(
            columns={
                "id": "servicio_id"
            }
        ),
        on="servicio_id",
        how="left",
    )

    fact_servicio = fact_servicio.merge(
        dim_cliente[
            [
                "cliente_key",
                "cliente_id",
            ]
        ],
        on="cliente_id",
        how="left",
    )

    fact_servicio = (
        fact_servicio
        .rename(
            columns={
                "cliente_key": "fk_cliente"
            }
        )
        .drop(columns="cliente_id")
    )

    # fk_cliente es NOT NULL en el DDL. Sin este fillna, un cliente_id que no
    # matcheara en dim_cliente (o viniera nulo desde el OLTP) dejaría NA en
    # fk_cliente y la carga fallaría contra la restricción NOT NULL.
    n_sin_match = int(fact_servicio["fk_cliente"].isna().sum())
    if n_sin_match:
        print(f"[AVISO] {n_sin_match} servicio(s) sin cliente_id coincidente en dim_cliente; "
              f"se asigna fk_cliente = -1.")

    fact_servicio["fk_cliente"] = (
        fact_servicio["fk_cliente"]
        .fillna(-1)
        .astype("Int64")
    )

    return fact_servicio


def agregar_fk_mensajero(
    fact_servicio,
    servicio,
    dim_mensajero,
):

    mensajero_servicio = (
        servicio[
            [
                "id",
                "mensajero_id",
            ]
        ]
        .rename(
            columns={
                "id": "servicio_id"
            }
        )
    )

    mensajero_servicio["mensajero_id"] = (
        mensajero_servicio["mensajero_id"]
        .fillna(-1)
        .astype("int64")
    )

    fact_servicio = fact_servicio.merge(
        mensajero_servicio,
        on="servicio_id",
        how="left",
    )

    fact_servicio = fact_servicio.merge(
        dim_mensajero[
            [
                "mensajero_key",
                "mensajero_id",
            ]
        ],
        on="mensajero_id",
        how="left",
    )

    fact_servicio = (
        fact_servicio
        .rename(
            columns={
                "mensajero_key": "fk_mensajero"
            }
        )
        .drop(columns="mensajero_id")
    )

    # fk_mensajero es nullable en el DDL, así que a diferencia de fk_cliente
    # aquí sí se deja NULL real cuando no hay mensajero asignado o no matchea
    # (no se fuerza -1) -- es una FK opcional legítima.
    fact_servicio["fk_mensajero"] = (
        fact_servicio["fk_mensajero"]
        .astype("Int64")
    )

    return fact_servicio


def agregar_fk_sede(
    fact_servicio,
    servicio,
    clientes_usuario,
    dim_sede,
):

    usuario_servicio = (
        servicio[
            [
                "id",
                "usuario_id",
            ]
        ]
        .rename(
            columns={
                "id": "servicio_id"
            }
        )
    )

    usuario_servicio = usuario_servicio.merge(
        clientes_usuario[
            [
                "id",
                "sede_id",
            ]
        ].rename(
            columns={
                "id": "usuario_id"
            }
        ),
        on="usuario_id",
        how="left",
    )

    fact_servicio = fact_servicio.merge(
        usuario_servicio[
            [
                "servicio_id",
                "sede_id",
            ]
        ],
        on="servicio_id",
        how="left",
    )

    fact_servicio = fact_servicio.merge(
        dim_sede[
            [
                "sede_key",
                "sede_id",
            ]
        ],
        on="sede_id",
        how="left",
    )

    fact_servicio = (
        fact_servicio
        .rename(
            columns={
                "sede_key": "fk_sede"
            }
        )
        .drop(columns="sede_id")
    )

    # fk_sede también es nullable en el DDL: se deja NULL real si el
    # servicio no tiene sede asociada, igual que fk_mensajero.
    fact_servicio["fk_sede"] = (
        fact_servicio["fk_sede"]
        .astype("Int64")
    )

    return fact_servicio