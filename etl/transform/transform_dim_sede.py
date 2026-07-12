import pandas as pd


def transform_dim_sede(data):
    """
    Construye la dimensión Sede.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Sede lista para cargar.
    """

    dim_sede = data["sede"].copy()
    dim_cliente = data["dim_cliente"].copy()

    # Eliminar columnas que no se utilizarán
    dim_sede = dim_sede.drop(
        columns=[
            "nombre_contacto",
            "direccion",
            "telefono",
            "ciudad_id",
        ]
    )

    # Relacionar con la dimensión Cliente para obtener la surrogate key
    dim_sede = dim_sede.merge(
        dim_cliente[
            [
                "cliente_id",
                "cliente_key",
            ]
        ],
        on="cliente_id",
        how="left",
    )

    # Ya no necesitamos el id del OLTP
    dim_sede = (
        dim_sede
        .drop(columns=["cliente_id"])
        .rename(columns={"cliente_key": "fk_cliente"})
    )

    # Eliminar registros duplicados
    dim_sede = (
        dim_sede
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Crear llave sustituta
    dim_sede.insert(
        0,
        "sede_key",
        dim_sede.index + 1,
    )

    # Agregar registro "No aplica"
    fila_no_aplica = pd.DataFrame(
        [
            {
                "sede_key": -1,
                "sede_id": -1,
                "nombre": "No aplica - dirección puntual",
                "fk_cliente": -1,
            }
        ]
    )

    dim_sede = pd.concat(
        [fila_no_aplica, dim_sede],
        ignore_index=True,
    )

    # Ordenar columnas
    dim_sede = dim_sede[
        [
            "sede_key",
            "sede_id",
            "nombre",
            "fk_cliente",
        ]
    ]

    return dim_sede