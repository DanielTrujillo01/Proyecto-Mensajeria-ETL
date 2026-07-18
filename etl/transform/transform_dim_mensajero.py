import pandas as pd

def transform_dim_mensajero(data):
    """
    Construye la dimensión Mensajero.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Mensajero lista para cargar.
    """

    mensajero = data["clientes_mensajeroaquitoy"].copy()
    auth_user = data["auth_user"].copy()

    # Seleccionar únicamente las columnas necesarias
    auth_user = auth_user[["id", "username"]]

    # Unir con la tabla de usuarios
    dim_mensajero = (
        mensajero
        .merge(
            auth_user,
            left_on="user_id",
            right_on="id",
            how="left",
        )
        .rename(
            columns={
                "id_x": "mensajero_id",
                "username": "nombre_completo",
            }
        )
    )

    # Seleccionar columnas finales
    dim_mensajero = dim_mensajero[
        [
            "mensajero_id",
            "nombre_completo",
        ]
    ]

    # Eliminar duplicados
    dim_mensajero = (
        dim_mensajero
        .drop_duplicates(subset="mensajero_id")
        .sort_values("mensajero_id")
        .reset_index(drop=True)
    )

    # Llave sustituta
    dim_mensajero.insert(
        0,
        "mensajero_key",
        dim_mensajero.index + 1,
    )

    # Tratamiento de nulos
    dim_mensajero["nombre_completo"] = (
        dim_mensajero["nombre_completo"]
        .fillna("Sin nombre")
    )

    fila_desconocido = pd.DataFrame(
    [
        {
            "mensajero_key": -1,
            "mensajero_id": -1,
            "nombre_completo": "Sin mensajero",
        }
    ]
    )

    dim_mensajero = pd.concat(
        [fila_desconocido, dim_mensajero],
        ignore_index=True,
    )
    return dim_mensajero