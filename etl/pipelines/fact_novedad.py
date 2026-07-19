from etl.database import mensajeria, warehouse

from etl.extract import extract_tables
from etl.transform.transform_hecho_novedad import transform_hecho_novedad
from etl.load import load_table


def run():
    # 1. Extraer la tabla transaccional (OLTP)
    oltp = extract_tables(
        mensajeria,
        "mensajeria_novedadesservicio",
    )

    # 2. Extraer las dimensiones necesarias (Warehouse ETL)
    dw = extract_tables(
        warehouse,
        "dim_fechahora",
        "dim_novedad",
        "dim_mensajero",
    )

    # 3. Transformar los datos
    # Le pasamos el dict oltp como 'data', y extraemos los df de las dimensiones de 'dw'
    fact_novedad = transform_hecho_novedad(
        data=oltp,
        dim_fechahora=dw["dim_fechahora"],
        dim_novedad=dw["dim_novedad"],
        dim_mensajero=dw["dim_mensajero"],
    )

    # 4. Cargar los hechos en la bodega
    load_table(
        fact_novedad,
        "fact_novedad",
        warehouse,
    )

if __name__ == "__main__":
    run()