import pandas as pd


def extract_tables(engine, *table_names):
    """
    Extrae una o varias tablas de una base de datos.

    Parameters
    ----------
    engine : sqlalchemy.Engine
        Conexión a la base de datos.

    *table_names : str
        Nombres de las tablas a extraer.

    Returns
    -------
    dict
        Diccionario donde la llave es el nombre de la tabla y el valor
        es un DataFrame.
    """

    return {
        table_name: pd.read_sql_table(table_name, engine)
        for table_name in table_names
    }