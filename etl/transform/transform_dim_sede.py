import pandas as pd

def transform_dim_sede(data):
    """
    Construye la dimensión Sede cruzando con la dimensión Cliente.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames. Ahora incluye tanto la tabla del OLTP
        como las dimensiones previamente calculadas en el caché.

    Returns
    -------
    pandas.DataFrame
        Dimensión Sede lista para cargar.
    """

    # 1. Extraer los dataframes del diccionario
    sede = data["sede"].copy()
    dim_cliente = data["dim_cliente"].copy()

    # 2. Eliminar columnas que no irán a la bodega
    columnas_a_eliminar = ['nombre_contacto', 'direccion', 'telefono', 'ciudad_id']
    dim_sede = sede.drop(columns=columnas_a_eliminar, errors='ignore')

    # 3. Relacionar con dim_cliente para obtener la surrogate key
    dim_sede = dim_sede.merge(
        dim_cliente[["cliente_id", "cliente_key"]],
        on="cliente_id",
        how="left",
    )

    # 4. Eliminar el ID del OLTP y renombrar la llave foránea
    dim_sede = (
        dim_sede
        .drop(columns=["cliente_id"])
        .rename(columns={"cliente_key": "fk_cliente"})
    )

    # Asegurar que no queden nulos y forzar tipo entero
    dim_sede["fk_cliente"] = dim_sede["fk_cliente"].fillna(-1).astype("Int64")

    # 5. Eliminar duplicados y resetear índice
    dim_sede = (
        dim_sede
        .drop_duplicates()
        .sort_values("sede_id")
        .reset_index(drop=True)
    )

    # 6. Crear llave sustituta 
    dim_sede.insert(0, "sede_key", dim_sede.index + 1)

    # 7. Agregar fila "No aplica"
    fila_no_aplica = pd.DataFrame([
        {
            "sede_key": -1,
            "sede_id": -1,
            "nombre": "No aplica - dirección puntual",
            "fk_cliente": -1,
        }
    ])

    dim_sede = pd.concat([fila_no_aplica, dim_sede], ignore_index=True)

    # 8. Ordenar columnas finales (opcional pero buena práctica)
    dim_sede = dim_sede[["sede_key", "sede_id", "nombre", "fk_cliente"]]

    return dim_sede