from etl.database import mensajeria, warehouse

from etl.extract import extract_tables
from etl.transform.transform_dim_sede import transform_dim_sede
from etl.load import load_table


def run():

    oltp = extract_tables(
        mensajeria,
        "sede",
    )

    dw = extract_tables(
        warehouse,
        "dim_cliente",
    )

    data = {
        **oltp,
        **dw,
    }

    dim_sede = transform_dim_sede(data)

    load_table(
        dim_sede,
        "dim_sede",
        warehouse,
    )