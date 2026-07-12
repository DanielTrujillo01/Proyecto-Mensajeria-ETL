from database import mensajeria, warehouse
from extract import extract_tables
from load import load_table

from transform.transform_dim_cliente import transform_dim_cliente
from transform.transform_dim_mensajero import transform_dim_mensajero
from transform.transform_dim_fecha import transform_dim_fechahora


PIPELINE = [
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
        "destination": "dim_fecha_hora",
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
    for job in PIPELINE:
        data = extract_tables(
            mensajeria,
            *job["tables"]      # Desempaqueta la lista como argumentos
        )

        df = job["transform"](data)

        load_table(
            df,
            job["destination"],
            warehouse,
        )


if __name__ == "__main__":
    run()