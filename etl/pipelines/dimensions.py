from etl.database import mensajeria, warehouse

from etl.extract import extract_tables
from etl.load import load_table

from etl.transform.transform_dim_cliente import transform_dim_cliente
from etl.transform.transform_dim_mensajero import transform_dim_mensajero
from etl.transform.transform_dim_fecha import transform_dim_fechahora
from etl.transform.transform_dim_sede import transform_dim_sede
from etl.transform.transform_dim_novedad import transform_dim_novedad

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
            "mensajeria_novedadesservicio",  # Agregada para los timestamps de novedades
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
    {
        "tables": [
            "sede",
        ],
        "transform": transform_dim_sede,
        "destination": "dim_sede",
    },
    {
        "tables": [
            "mensajeria_tiponovedad",
        ],
        "transform": transform_dim_novedad,
        "destination": "dim_novedad",
    },
]

def run():
    """
    Ejecuta el pipeline de extracción, transformación y carga para todas las dimensiones.
    """
    # Caché para almacenar las dimensiones ya procesadas en memoria
    dw_cache = {}

    for pipeline in PIPELINES:
        # 1. Extraer los datos del OLTP
        data = extract_tables(
            mensajeria,
            *pipeline["tables"],
        )

        # 2. Inyectar las dimensiones previamente creadas (Ej: dim_cliente para dim_sede)
        data.update(dw_cache)

        # 3. Transformar los datos
        dataframe = pipeline["transform"](data)

        # Guardar el resultado en el caché por si la siguiente dimensión lo necesita
        dw_cache[pipeline["destination"]] = dataframe

        # 4. Cargar los datos en la bodega
        load_table(
            dataframe,
            pipeline["destination"],
            warehouse,
        )

if __name__ == "__main__":
    run()