import pandas as pd

def transform_hecho_servicio(data):
    """
    Construye la tabla de hechos de Servicio calculando duraciones
    y cruzando con las dimensiones.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames. Debe contener tablas del OLTP y las
        dimensiones previamente cargadas en el warehouse.

    Returns
    -------
    pandas.DataFrame
        Tabla de hechos fact_servicio lista para cargar.
    """

    # 1. Extraer tablas de origen (OLTP)
    estadosservicio = data["mensajeria_estadosservicio"].copy()
    servicio = data["mensajeria_servicio"].copy()
    clientes_usuario = data["clientes_usuarioaquitoy"].copy()

    # 2. Extraer dimensiones (Warehouse ETL)
    dim_fechahora = data["dim_fechahora"].copy()
    dim_cliente = data["dim_cliente"].copy()
    dim_mensajero = data["dim_mensajero"].copy()
    dim_sede = data["dim_sede"].copy()

    # ==========================================
    # A. PIVOTEAR ESTADOS Y CALCULAR DURACIONES
    # ==========================================
    
    # Crear datetime limpio
    estadosservicio["fecha_hora"] = pd.to_datetime(
        (estadosservicio["fecha"].astype(str) + " " + estadosservicio["hora"].astype(str)).str[:19],
        errors="coerce"
    )

    mapa_estados = {1: "iniciado", 2: "asignado", 4: "recogido", 5: "entregado", 6: "cerrado"}

    # Agrupar y pivotear
    agg = (
        estadosservicio[estadosservicio["estado_id"].isin(mapa_estados.keys())]
        .groupby(["servicio_id", "estado_id"])["fecha_hora"]
        .min()
        .reset_index()
    )
    agg["estado"] = agg["estado_id"].map(mapa_estados)

    estados_wide = agg.pivot(
        index="servicio_id", columns="estado", values="fecha_hora"
    ).reset_index()

    # Base de hechos
    hecho_servicio = servicio[["id"]].rename(columns={"id": "servicio_id"})
    hecho_servicio = hecho_servicio.merge(estados_wide, on="servicio_id", how="left")

    # Asegurar que existan las columnas por si falta data
    for estado in mapa_estados.values():
        if estado not in hecho_servicio.columns:
            hecho_servicio[estado] = pd.NaT

    # Calcular duraciones en minutos
    hecho_servicio["duracion_iniciado_asignado_min"] = (
        (hecho_servicio["asignado"] - hecho_servicio["iniciado"]).dt.total_seconds() / 60
    )
    hecho_servicio["duracion_asignado_recogido_min"] = (
        (hecho_servicio["recogido"] - hecho_servicio["asignado"]).dt.total_seconds() / 60
    )
    hecho_servicio["duracion_recogido_entregado_min"] = (
        (hecho_servicio["entregado"] - hecho_servicio["recogido"]).dt.total_seconds() / 60
    )
    hecho_servicio["duracion_entregado_cerrado_min"] = (
        (hecho_servicio["cerrado"] - hecho_servicio["entregado"]).dt.total_seconds() / 60
    )
    hecho_servicio["duracion_total_min"] = (
        (hecho_servicio["cerrado"] - hecho_servicio["iniciado"]).dt.total_seconds() / 60
    )

    # ==========================================
    # B. CRUCE CON DIMENSIONES (LLAVES FORÁNEAS)
    # ==========================================

    # 1. Dimensión Fecha/Hora
    KEY_FECHA_DESCONOCIDA = -1

    dim_fechahora["fecha_hora"] = pd.to_datetime(dim_fechahora["fecha_hora"], errors="coerce")
    
    # El nombre de la key dependera de cómo quedó al final en tu script de transform_dim_fechahora
    # Acá uso key_dim_fechahora basándome en el notebook
    if "fecha_hora_key" in dim_fechahora.columns:
        col_llave_fecha = "fecha_hora_key"
    else:
        col_llave_fecha = "key_dim_fechahora"
        
    dim_fh_lookup = dim_fechahora.loc[
        dim_fechahora["fecha_hora"].notna(), [col_llave_fecha, "fecha_hora"]
    ]

    for col in ["iniciado", "asignado", "recogido", "entregado", "cerrado"]:
        hecho_servicio[col] = pd.to_datetime(hecho_servicio[col], errors="coerce")

        hecho_servicio = hecho_servicio.merge(
            dim_fh_lookup, left_on=col, right_on="fecha_hora", how="left"
        )
        hecho_servicio = hecho_servicio.rename(
            columns={col_llave_fecha: f"fk_fecha_{col}"}
        )
        hecho_servicio = hecho_servicio.drop(columns=["fecha_hora", col])

        hecho_servicio[f"fk_fecha_{col}"] = (
            hecho_servicio[f"fk_fecha_{col}"].fillna(KEY_FECHA_DESCONOCIDA).astype("Int64")
        )

    # 2. Dimensión Cliente
    hecho_servicio = hecho_servicio.merge(
        servicio[["id", "cliente_id"]].rename(columns={"id": "servicio_id"}),
        on="servicio_id",
        how="left",
    )
    hecho_servicio = hecho_servicio.merge(
        dim_cliente[["cliente_key", "cliente_id"]], on="cliente_id", how="left"
    )
    hecho_servicio = hecho_servicio.rename(columns={"cliente_key": "fk_cliente"})
    hecho_servicio = hecho_servicio.drop(columns=["cliente_id"])
    hecho_servicio["fk_cliente"] = hecho_servicio["fk_cliente"].fillna(-1).astype("Int64")

    # 3. Dimensión Mensajero
    mensajero_servicio = servicio[["id", "mensajero_id"]].rename(columns={"id": "servicio_id"})
    mensajero_servicio["mensajero_id"] = (
        mensajero_servicio["mensajero_id"].fillna(-1).astype("int64")
    )
    
    hecho_servicio = hecho_servicio.merge(
        mensajero_servicio, on="servicio_id", how="left"
    )
    hecho_servicio = hecho_servicio.merge(
        dim_mensajero[["mensajero_key", "mensajero_id"]], on="mensajero_id", how="left"
    )
    hecho_servicio = hecho_servicio.rename(columns={"mensajero_key": "fk_mensajero"})
    hecho_servicio = hecho_servicio.drop(columns=["mensajero_id"])
    hecho_servicio["fk_mensajero"] = hecho_servicio["fk_mensajero"].fillna(-1).astype("Int64")

    # 4. Dimensión Sede
    usuario_servicio = servicio[["id", "usuario_id"]].rename(columns={"id": "servicio_id"})
    usuario_servicio = usuario_servicio.merge(
        clientes_usuario[["id", "sede_id"]].rename(columns={"id": "usuario_id"}),
        on="usuario_id",
        how="left",
    )
    hecho_servicio = hecho_servicio.merge(
        usuario_servicio[["servicio_id", "sede_id"]], on="servicio_id", how="left"
    )
    hecho_servicio = hecho_servicio.merge(
        dim_sede[["key_dim_sede", "sede_id"]].rename(columns={"key_dim_sede": "fk_sede"}),
        on="sede_id",
        how="left",
    ).drop(columns=["sede_id"])
    hecho_servicio["fk_sede"] = hecho_servicio["fk_sede"].fillna(-1).astype("Int64")

    # Eliminar posibles columnas extra que hayan quedado en el dataframe
    if "usuario_id" in hecho_servicio.columns:
        hecho_servicio = hecho_servicio.drop(columns=["usuario_id"])

    return hecho_servicio