import pandas as pd


def transform_dim_novedad(data):
    """
    Construye la dimensión Novedad.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Novedad lista para cargar.
    """

    tipo_novedad = data["mensajeria_tiponovedad"].copy()

    # Renombrar columnas
    dim_novedad = tipo_novedad.rename(
        columns={
            "id": "tipo_novedad_id",
            "nombre": "nombre_novedad",
        }
    )

    # Eliminar duplicados
    dim_novedad = (
        dim_novedad
        .drop_duplicates(subset="tipo_novedad_id")
        .sort_values("tipo_novedad_id")
        .reset_index(drop=True)
    )

    # Llave sustituta
    dim_novedad.insert(0, "novedad_key", dim_novedad.index + 1)

    # Tratamiento de nulos
    dim_novedad["nombre_novedad"] = (
        dim_novedad["nombre_novedad"]
        .fillna("Sin especificar")
    )

    fila_desconocido = pd.DataFrame(
        [
            {
                "novedad_key": -1,
                "tipo_novedad_id": -1,
                "nombre_novedad": "Sin novedad",
            }
        ]
    )

    dim_novedad = pd.concat(
        [fila_desconocido, dim_novedad],
        ignore_index=True,
    )
    return dim_novedad