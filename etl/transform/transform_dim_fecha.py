import pandas as pd

def transform_dim_fechahora(data):
    """
    Construye la dimensión FechaHora.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión FechaHora lista para cargar.
    """

    fechas = data["mensajeria_estadosservicio"].copy()
    estados = data["mensajeria_estado"].copy()
    servicio = data["mensajeria_servicio"].copy()

    # Eliminar columnas innecesarias
    fechas = fechas.drop(
        columns=[
            "foto",
            "observaciones",
            "es_prueba",
            "foto_binary",
        ]
    )

    # Variables de fecha
    fechas["day_of_week"] = fechas["fecha"].dt.weekday
    fechas["year"] = fechas["fecha"].dt.year
    fechas["month"] = fechas["fecha"].dt.month

    # Corrección de nombres de estados
    estados.loc[0, "nombre"] = "Recogido en origen"
    estados.loc[3, "nombre"] = "Cerrado"

    # Agregar nombre del estado
    fechas = (
        fechas.merge(
            estados[["id", "nombre"]],
            left_on="estado_id",
            right_on="id",
            how="left",
        )
        .rename(columns={"nombre": "estado"})
        .drop(columns=["id_y"])
    )

    # Eliminar columnas innecesarias de servicio
    columnas_eliminar = [
        "descripcion",
        "nombre_solicitante",
        "fecha_solicitud",
        "hora_solicitud",
        "fecha_deseada",
        "hora_deseada",
        "nombre_recibe",
        "telefono_recibe",
        "descripcion_pago",
        "ida_y_regreso",
        "activo",
        "novedades",
        "cliente_id",
        "destino_id",
        "mensajero_id",
        "origen_id",
        "tipo_pago_id",
        "tipo_servicio_id",
        "tipo_vehiculo_id",
        "usuario_id",
        "prioridad",
        "ciudad_destino_id",
        "ciudad_origen_id",
        "hora_visto_por_mensajero",
        "visto_por_mensajero",
        "descripcion_multiples_origenes",
        "mensajero2_id",
        "mensajero3_id",
        "multiples_origenes",
        "asignar_mensajero",
        "es_prueba",
        "descripcion_cancelado",
    ]

    servicio = servicio.drop(columns=columnas_eliminar)

    # Unir servicio con estados del servicio
    servicio = (
        servicio.merge(
            fechas,
            left_on="id",
            right_on="servicio_id",
            how="left",
        )
        .drop(columns=["estado_id"])
    )

    # Construcción del timestamp
    servicio["fecha_hora"] = pd.to_datetime(
        servicio["fecha"].dt.date.astype(str)
        + " "
        + servicio["hora"].astype(str),
        errors="coerce",
    )

    # Construcción de la dimensión
    dim_fechahora = (
        servicio[["fecha_hora"]]
        .drop_duplicates()
        .sort_values("fecha_hora")
        .reset_index(drop=True)
    )

    # Llave sustituta
    dim_fechahora.insert(
        0,
        "fecha_hora_key",
        dim_fechahora.index + 1,
    )

    # Atributos temporales
    dim_fechahora["año"] = dim_fechahora["fecha_hora"].dt.year
    dim_fechahora["mes"] = dim_fechahora["fecha_hora"].dt.month
    dim_fechahora["dia"] = dim_fechahora["fecha_hora"].dt.day
    dim_fechahora["hora"] = dim_fechahora["fecha_hora"].dt.hour
    dim_fechahora["minuto"] = dim_fechahora["fecha_hora"].dt.minute
    dim_fechahora["dia_de_la_semana"] = dim_fechahora["fecha_hora"].dt.day_name()

    fila_desconocido = pd.DataFrame(
    [
        {
            "fecha_hora_key": -1,
            "fecha_hora": pd.NaT,
            "año": None,
            "mes": None,
            "dia": None,
            "hora": None,
            "minuto": None,
            "dia_de_la_semana": "No aplica",
        }
    ]
    )

    dim_fechahora = pd.concat(
        [fila_desconocido, dim_fechahora],
        ignore_index=True,
    )
    
    return dim_fechahora