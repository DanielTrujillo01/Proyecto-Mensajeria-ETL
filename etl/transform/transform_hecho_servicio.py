import pandas as pd
from .utils import *


def transform_fact_servicio(data):
    """
    Construye la tabla de hechos de servicios.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Tabla de hechos lista para cargar.
    """

    # ============================
    # Tablas OLTP
    # ============================

    estados_servicio = data["mensajeria_estadosservicio"].copy()
    estado = data["mensajeria_estado"].copy()
    servicio = data["mensajeria_servicio"].copy()
    clientes_usuario = data["clientes_usuarioaquitoy"].copy()

    # ============================
    # Dimensiones
    # ============================

    dim_fechahora = data["dim_fechahora"].copy()
    dim_cliente = data["dim_cliente"].copy()
    dim_mensajero = data["dim_mensajero"].copy()
    dim_sede = data["dim_sede"].copy()

    # ==================================================
    # Construcción del timestamp de cada cambio de estado
    # ==================================================

    estados_servicio["fecha_hora"] = pd.to_datetime(
        (
            estados_servicio["fecha"].astype(str)
            + " "
            + estados_servicio["hora"].astype(str)
        ).str[:19],
        errors="coerce",
    )

    # ==================================================
    # Obtener el primer momento en que ocurre cada estado
    # ==================================================

    mapa_estados = {
        1: "iniciado",
        2: "asignado",
        4: "recogido",
        5: "entregado",
        6: "cerrado",
    }

    agg = (
        estados_servicio[
            estados_servicio["estado_id"].isin(mapa_estados)
        ]
        .groupby(
            ["servicio_id", "estado_id"]
        )["fecha_hora"]
        .min()
        .reset_index()
    )

    agg["estado"] = agg["estado_id"].map(mapa_estados)

    estados_wide = (
        agg.pivot(
            index="servicio_id",
            columns="estado",
            values="fecha_hora",
        )
        .reset_index()
    )

    # ==================================================
    # Base de la tabla de hechos
    # ==================================================

    fact_servicio = (
        servicio[["id"]]
        .rename(columns={"id": "servicio_id"})
        .merge(
            estados_wide,
            on="servicio_id",
            how="left",
        )
    )

    fact_servicio = agregar_medidas_tiempo(
        fact_servicio
    )

    fact_servicio = agregar_fk_fecha(
        fact_servicio,
        dim_fechahora,
    )

    fact_servicio = agregar_fk_cliente(
        fact_servicio,
        servicio,
        dim_cliente,
    )

    fact_servicio = agregar_fk_mensajero(
        fact_servicio,
        servicio,
        dim_mensajero,
    )

    fact_servicio = agregar_fk_sede(
        fact_servicio,
        servicio,
        clientes_usuario,
        dim_sede,
    )

    return fact_servicio