import pandas as pd

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

    # 1. Extraer los dataframes del diccionario
    cliente = data["cliente"]
    tipo_cliente = data["tipo_cliente"][["tipo_cliente_id", "nombre"]]
    ciudad = data["ciudad"][["ciudad_id", "nombre"]]

    # 2. Primer merge: Cliente + Tipo de Cliente
    dim_cliente = (
        cliente
        .merge(tipo_cliente, on="tipo_cliente_id", how="left")
        .rename(columns={
            "nombre_x": "nombre_cliente", 
            "nombre_y": "tipo_cliente"
        })
    )

    # 3. Segundo merge: Cliente + Ciudad
    dim_cliente = (
        dim_cliente
        .merge(ciudad, on="ciudad_id", how="left")
        .rename(columns={
            "nombre": "ciudad_principal", 
            "activo": "estado_activo"
        })
    )

    # 4. Seleccionar columnas deseadas
    columnas_deseadas = [
        "cliente_id", "nit_cliente", "nombre_cliente", 
        "sector", "tipo_cliente", "ciudad_principal", "estado_activo"
    ]
    dim_cliente = dim_cliente[columnas_deseadas]

    # 5. Eliminar duplicados y ordenar
    dim_cliente = (
        dim_cliente
        .drop_duplicates(subset=["cliente_id"])
        .sort_values("cliente_id")
        .reset_index(drop=True)
    )

    # 6. Crear llave sustituta (Surrogate Key)
    dim_cliente["cliente_key"] = dim_cliente.index + 1

    # 7. Reordenar dejando la llave sustituta de primera
    dim_cliente = dim_cliente[[
        "cliente_key", "cliente_id", "nit_cliente", "nombre_cliente", 
        "sector", "tipo_cliente", "ciudad_principal", "estado_activo"
    ]]

    # 8. Eliminar las columnas que ya no van para el warehouse
    dim_cliente.drop(
        columns=[
            "nit_cliente",
            "sector",
            "tipo_cliente",
            "ciudad_principal",
            "estado_activo",
        ], 
        inplace=True
    )

    # 9. Fila de cliente desconocido (Manejo de integridad referencial)
    # Adaptada para tener solo las columnas finales que dejaste en el dataframe
    fila_desconocido = pd.DataFrame([
        {
            "cliente_key": -1,
            "cliente_id": -1,
            "nombre_cliente": "Cliente desconocido",
        }
    ])

    dim_cliente = pd.concat(
        [fila_desconocido, dim_cliente],
        ignore_index=True,
    )
    
    return dim_cliente