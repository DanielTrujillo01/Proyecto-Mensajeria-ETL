from .dimensions import run as run_dimensions
from .dim_sede import run as run_dim_sede
from .fact_servicio import run as run_fact_servicio


def run():
    run_dimensions()
    run_dim_sede()
    run_fact_servicio()


if __name__ == "__main__":
    run()