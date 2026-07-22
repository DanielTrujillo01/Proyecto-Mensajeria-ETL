from etl.database import mensajeria, warehouse

from etl.extract import extract_tables
from etl.transform.transform_hecho_servicio import transform_fact_servicio
from etl.load import load_table


def run():

    oltp = extract_tables(
        mensajeria,
        "mensajeria_estadosservicio",
        "mensajeria_estado",
        "mensajeria_servicio",
        "clientes_usuarioaquitoy",
    )

    dw = extract_tables(
        warehouse,
        "dim_cliente",
        "dim_mensajero",
        "dim_sede",
        "dim_fechahora",
    )

    data = {
        **oltp,
        **dw,
    }

    fact_servicio = transform_fact_servicio(data)

    load_table(
        fact_servicio,
        "fact_servicio",
        warehouse,
    )