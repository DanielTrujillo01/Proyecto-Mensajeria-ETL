import pandas as pd

def transform_dim_fechahora(data):
    """
    Construye la dimensión Fecha/Hora extrayendo todos los timestamps
    de los estados de servicio y de las novedades.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Fecha/Hora lista para cargar.
    """
    
    # 1. Obtener los dataframes de fechas (usamos .get por si falta alguna tabla en la config)
    estados_servicio = data.get("mensajeria_estadosservicio")
    novedades = data.get("mensajeria_novedadesservicio")
    
    if estados_servicio is None:
        raise ValueError("Falta la tabla 'mensajeria_estadosservicio' en los datos extraídos.")

    # 2. Construir la columna datetime a partir de fecha y hora de estados_servicio
    fechas_estados = pd.to_datetime(
        estados_servicio["fecha"].dt.date.astype(str) + " " + estados_servicio["hora"].astype(str),
        errors="coerce"
    ).dropna().to_frame(name="fecha_hora")

    # 3. Extraer las fechas de las novedades (quitando la zona horaria para estandarizar)
    if novedades is not None and not novedades.empty:
        fechas_nov = novedades[["fecha_novedad"]].rename(columns={"fecha_novedad": "fecha_hora"})
        fechas_nov["fecha_hora"] = fechas_nov["fecha_hora"].dt.tz_localize(None)
    else:
        # Por si la tabla viene vacía
        fechas_nov = pd.DataFrame(columns=["fecha_hora"])

    # 4. Unir ambos universos de fechas y dejar solo los valores únicos
    dim_fechahora = pd.concat([fechas_estados, fechas_nov], ignore_index=True)
    
    dim_fechahora = (
        dim_fechahora
        .drop_duplicates()
        .sort_values("fecha_hora")
        .reset_index(drop=True)
    )

    # 5. Generar los atributos de la dimensión de tiempo
    dim_fechahora["año"] = dim_fechahora["fecha_hora"].dt.year
    dim_fechahora["mes"] = dim_fechahora["fecha_hora"].dt.month
    dim_fechahora["dia"] = dim_fechahora["fecha_hora"].dt.day
    dim_fechahora["hora"] = dim_fechahora["fecha_hora"].dt.hour
    dim_fechahora["minuto"] = dim_fechahora["fecha_hora"].dt.minute
    dim_fechahora["dia_de_la_semana"] = dim_fechahora["fecha_hora"].dt.day_name()

    # 6. Crear la llave sustituta (Surrogate Key)
    dim_fechahora.insert(0, "fecha_hora_key", dim_fechahora.index + 1)

    # 7. Agregar fila para fechas desconocidas (Manejo de integridad referencial)
    fila_desconocido = pd.DataFrame([
        {
            "fecha_hora_key": -1,
            "fecha_hora": pd.NaT,
            "año": -1,
            "mes": -1,
            "dia": -1,
            "hora": -1,
            "minuto": -1,
            "dia_de_la_semana": "Desconocido"
        }
    ])

    dim_fechahora = pd.concat([fila_desconocido, dim_fechahora], ignore_index=True)

    return dim_fechahora