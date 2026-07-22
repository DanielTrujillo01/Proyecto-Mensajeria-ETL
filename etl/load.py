import sqlalchemy as db


def load_table(
    df,
    table_name,
    engine,
    truncate=True,
    if_exists="append",
):
    """
    Carga un DataFrame en una tabla de la base de datos.

    Parameters
    ----------
    df : pandas.DataFrame

    table_name : str

    engine : sqlalchemy.Engine

    truncate : bool
        Si es True limpia la tabla antes de insertar.

    if_exists : str
        Comportamiento de pandas.to_sql().
    """

    if truncate:
        with engine.begin() as conn:
            conn.execute(
                db.text(
                    f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"
                )
            )

    df.to_sql(
        table_name,
        engine,
        if_exists=if_exists,
        index=False,
    )