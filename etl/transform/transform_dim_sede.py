import pandas as pd

def transform_dim_sede(data):
    """
    Construye la dimensión Sede a partir de las tablas extraídas.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Sede lista para cargar.
    """

    # 1. Extraer el dataframe del diccionario
    sede = data["sede"].copy()

    # 2. Eliminar las columnas que no irán a la bodega de datos
    columnas_a_eliminar = ['nombre_contacto', 'direccion', 'telefono', 'ciudad_id']
    dim_sede = sede.drop(columns=columnas_a_eliminar, errors='ignore')

    # 3. Eliminar duplicados y resetear índice
    dim_sede = (
        dim_sede
        .drop_duplicates()
        .sort_values("sede_id")
        .reset_index(drop=True)
    )

    # 4. Crear llave sustituta (manteniendo el nombre del notebook: key_dim_sede)
    dim_sede.insert(0, "key_dim_sede", dim_sede.index + 1)

    # 5. Agregar fila por defecto (Manejo de integridad referencial para direcciones puntuales)
    fila_no_aplica = pd.DataFrame([
        {
            "key_dim_sede": -1,
            "sede_id": -1,
            "nombre": "No aplica - dirección puntual",
            "cliente_id": -1,
        }
    ])

    dim_sede = pd.concat([fila_no_aplica, dim_sede], ignore_index=True)

    return dim_sede