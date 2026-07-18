from etl.database import mensajeria, warehouse

from etl.extract import extract_tables
from etl.load import load_table

from etl.transform.transform_dim_cliente import transform_dim_cliente
from etl.transform.transform_dim_mensajero import transform_dim_mensajero
from etl.transform.transform_dim_fecha import transform_dim_fechahora



PIPELINES = [
    {
        "tables": [
            "cliente",
            "tipo_cliente",
            "ciudad",
        ],
        "transform": transform_dim_cliente,
        "destination": "dim_cliente",
    },
    {
        "tables": [
            "mensajeria_estadosservicio",
            "mensajeria_estado",
            "mensajeria_servicio",
        ],
        "transform": transform_dim_fechahora,
        "destination": "dim_fechahora",
    },
    {
        "tables": [
            "clientes_mensajeroaquitoy",
            "auth_user",
        ],
        "transform": transform_dim_mensajero,
        "destination": "dim_mensajero",
    },
]


def run():

    for pipeline in PIPELINES:

        data = extract_tables(
            mensajeria,
            *pipeline["tables"],
        )

        dataframe = pipeline["transform"](data)

        load_table(
            dataframe,
            pipeline["destination"],
            warehouse,
        )