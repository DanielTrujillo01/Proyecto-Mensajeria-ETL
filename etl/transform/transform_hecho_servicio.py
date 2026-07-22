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

    # Se usa .dt.date en vez de .astype(str) directo sobre 'fecha': si esa
    # columna ya trae un componente de hora (p. ej. medianoche), concatenar
    # el string completo con 'hora' y cortar a 19 caracteres puede producir
    # una fecha mal formada que pd.to_datetime no interpreta bien.
    estados_servicio["fecha_hora"] = pd.to_datetime(
        estados_servicio["fecha"].dt.date.astype(str)
        + " "
        + estados_servicio["hora"].astype(str),
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

    # Si en este lote ningún servicio llegó a algún hito (columna ausente
    # del todo tras el pivot), se crea vacía para que el resto del pipeline
    # no falle por un KeyError.
    for hito in mapa_estados.values():
        if hito not in fact_servicio.columns:
            fact_servicio[hito] = pd.NaT

    fact_servicio = agregar_medidas_tiempo(
        fact_servicio
    )

    # Copia de las fechas reales por hito ANTES de que agregar_fk_fecha las
    # reemplace/elimine, para poder validar integridad después. No participa
    # en la carga final.
    fechas_originales = fact_servicio[
        ["servicio_id"] + list(mapa_estados.values())
    ].copy()

    fact_servicio = agregar_fk_fecha(
        fact_servicio,
        dim_fechahora,
    )

    # Verifica que cada fk_fecha_{hito} apunte, en dim_fechahora, al mismo
    # timestamp real calculado arriba para ese hito. Detectaría, por
    # ejemplo, un mapa_estados mal armado (un estado apuntando al fk de
    # otro) antes de que llegue a cargarse a la bodega.
    validar_fk_fecha(
        fact_servicio,
        fechas_originales,
        dim_fechahora,
        obtener_key_fecha_desconocida(dim_fechahora),
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