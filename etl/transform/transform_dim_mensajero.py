import pandas as pd

def transform_dim_mensajero(data):
    """
    Construye la dimensión Mensajero a partir de las tablas extraídas.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Mensajero lista para cargar.
    """

    # 1. Extraer los dataframes del diccionario
    mensajeroAquiToy = data["clientes_mensajeroaquitoy"]
    auth_user = data["auth_user"][["id", "username"]]

    # 2. Merge para traer el nombre de usuario (username) del mensajero
    dim_mensajero = mensajeroAquiToy.merge(
        auth_user,
        left_on="user_id",
        right_on="id",
        how="left"
    )

    # 3. Renombrar columnas para el warehouse y seleccionar las necesarias
    dim_mensajero = dim_mensajero.rename(columns={
        "id_x": "mensajero_id", 
        "username": "nombre_completo"
    })
    
    dim_mensajero = dim_mensajero[["mensajero_id", "nombre_completo"]]

    # 4. Eliminar duplicados, ordenar y resetear índice
    dim_mensajero = (
        dim_mensajero
        .drop_duplicates(subset=["mensajero_id"])
        .sort_values("mensajero_id")
        .reset_index(drop=True)
    )

    # 5. Crear llave sustituta (Surrogate Key)
    dim_mensajero["mensajero_key"] = dim_mensajero.index + 1

    # 6. Manejo de nulos
    dim_mensajero["nombre_completo"] = dim_mensajero["nombre_completo"].fillna("Sin nombre")

    # 7. Reordenar dejando la llave de primera
    dim_mensajero = dim_mensajero[["mensajero_key", "mensajero_id", "nombre_completo"]]

    # 8. Agregar fila por defecto (Manejo de integridad referencial)
    fila_no_aplica = pd.DataFrame([
        {
            "mensajero_key": -1, 
            "mensajero_id": -1, 
            "nombre_completo": "No aplica"
        }
    ])

    dim_mensajero = pd.concat([fila_no_aplica, dim_mensajero], ignore_index=True)

    return dim_mensajero