def transform_dim_cliente(data):
    """
    Construye la dimensión Cliente a partir de las tablas extraídas.

    Parameters
    ----------
    data : dict
        Diccionario de DataFrames obtenido con extract_tables().

    Returns
    -------
    pandas.DataFrame
        Dimensión Cliente lista para cargar.
    """

    cliente = data["cliente"]
    tipo_cliente = data["tipo_cliente"][["tipo_cliente_id", "nombre"]]
    ciudad = data["ciudad"][["ciudad_id", "nombre"]]

    # Cliente + Tipo de Cliente
    dim_cliente = (
        cliente
        .merge(tipo_cliente, on="tipo_cliente_id", how="left")
        .rename(
            columns={
                "nombre_x": "nombre_cliente",
                "nombre_y": "tipo_cliente",
            }
        )
    )

    # Cliente + Ciudad
    dim_cliente = (
        dim_cliente
        .merge(ciudad, on="ciudad_id", how="left")
        .rename(
            columns={
                "nombre": "ciudad_principal",
                "activo": "estado_activo",
            }
        )
    )

    # Seleccionar columnas
    dim_cliente = dim_cliente[
        [
            "cliente_id",
            "nit_cliente",
            "nombre_cliente",
            "sector",
            "tipo_cliente",
            "ciudad_principal",
            "estado_activo",
        ]
    ]

    # Eliminar duplicados
    dim_cliente = (
        dim_cliente
        .drop_duplicates(subset="cliente_id")
        .sort_values("cliente_id")
        .reset_index(drop=True)
    )

    # Llave sustituta
    dim_cliente.insert(0, "cliente_key", dim_cliente.index + 1)

    # Tratamiento de nulos
    dim_cliente["sector"] = dim_cliente["sector"].fillna("No especificado")
    dim_cliente["ciudad_principal"] = dim_cliente["ciudad_principal"].fillna("Sin ciudad")

    return dim_cliente