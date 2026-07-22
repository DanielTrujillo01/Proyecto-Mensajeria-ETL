from .dimensions import run as run_dimensions
from .dim_sede import run as run_dim_sede
from .fact_servicio import run as run_fact_servicio
from .fact_novedad import run as run_fact_novedad

def run():
    run_dimensions()
    ##run_dim_sede()
    run_fact_servicio()
    run_fact_novedad()


if __name__ == "__main__":
    run()