import pandas as pd

def agregar_medidas_tiempo(fact_servicio):
    """
    Calcula las medidas de tiempo entre las distintas fases del servicio.
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

    return fact_servicio

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

    KEY_FECHA_DESCONOCIDA = (
        dim_fechahora.loc[
            dim_fechahora["fecha_hora"].isna(),
            "fecha_hora_key",
        ]
        .iloc[0]
    )

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
            .fillna(KEY_FECHA_DESCONOCIDA)
            .astype("Int64")
        )

    return fact_servicio


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

    fact_servicio["fk_cliente"] = (
        fact_servicio["fk_cliente"]
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

    fact_servicio["fk_sede"] = (
        fact_servicio["fk_sede"]
        .astype("Int64")
    )

    return fact_servicio