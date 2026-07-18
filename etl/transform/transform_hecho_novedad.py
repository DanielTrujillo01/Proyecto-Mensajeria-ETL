import pandas as pd


def transform_hecho_novedad(data, dim_fechahora, dim_novedad, dim_mensajero):
    """
    Construye la tabla de hechos Novedad.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().
    dim_fechahora : pandas.DataFrame
        Dimensión FechaHora ya construida (y extendida con fechas de novedad).
    dim_novedad : pandas.DataFrame
        Dimensión Novedad ya construida.
    dim_mensajero : pandas.DataFrame
        Dimensión Mensajero ya construida.

    Returns
    -------
    pandas.DataFrame
        Hecho Novedad listo para cargar.
    """

    novedad = data["mensajeria_novedadesservicio"].copy()

    # Filtrar registros de prueba
    novedad = novedad[novedad["es_prueba"] == False]

    # Quitar zona horaria para que coincida con dim_fechahora
    novedad["fecha_novedad"] = novedad["fecha_novedad"].dt.tz_localize(None)

    # Lookup fecha
    novedad = novedad.merge(
        dim_fechahora[["fecha_hora_key", "fecha_hora"]],
        left_on="fecha_novedad",
        right_on="fecha_hora",
        how="left",
    )

    # Lookup tipo de novedad
    novedad = novedad.merge(
        dim_novedad[["novedad_key", "tipo_novedad_id"]],
        on="tipo_novedad_id",
        how="left",
    )

    # Lookup mensajero
    novedad = novedad.merge(
        dim_mensajero[["mensajero_key", "mensajero_id"]],
        on="mensajero_id",
        how="left",
    )

    # Nulos -> desconocido
    novedad["fecha_hora_key"] = novedad["fecha_hora_key"].fillna(-1).astype(int)
    novedad["novedad_key"] = novedad["novedad_key"].fillna(-1).astype(int)
    novedad["mensajero_key"] = novedad["mensajero_key"].fillna(-1).astype(int)

    # Construcción del hecho
    fact_novedad = novedad.rename(
        columns={
            "fecha_hora_key": "fk_fecha",
            "novedad_key": "fk_tipo_novedad",
            "mensajero_key": "fk_mensajero",
        }
    )

    fact_novedad = fact_novedad[
        [
            "id",
            "servicio_id",
            "fk_fecha",
            "fk_tipo_novedad",
            "fk_mensajero",
            "descripcion",
        ]
    ].rename(columns={"id": "novedad_id"})

    fact_novedad["cantidad"] = 1

    return fact_novedad