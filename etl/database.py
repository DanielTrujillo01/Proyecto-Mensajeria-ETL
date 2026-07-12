import yaml
from sqlalchemy import create_engine
from pathlib import Path

# 1. Obtiene la ruta de la carpeta donde vive este archivo ('etl')
# 2. Con el segundo '.parent' subimos a la carpeta raíz ('Proyecto-Mensajeria-ETL')
ROOT_DIR = Path(__file__).resolve().parent.parent

# 3. Ahora apuntamos al archivo config.yml que está en la raíz
CONFIG_PATH = ROOT_DIR / "config.yml"

# 4. Abrimos el archivo usando la ruta absoluta calculada
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

config_mensajeria = config["MENSAJERIA_OLTP"]
config_etl = config["ETL_PROCESS"]

url_mensajeria = (
    f"{config_mensajeria['drivername']}://{config_mensajeria['user']}:"
    f"{config_mensajeria['password']}@{config_mensajeria['host']}:"
    f"{config_mensajeria['port']}/{config_mensajeria['dbname']}"
)

url_etl = (
    f"{config_etl['drivername']}://{config_etl['user']}:"
    f"{config_etl['password']}@{config_etl['host']}:"
    f"{config_etl['port']}/{config_etl['dbname']}"
)

mensajeria = create_engine(url_mensajeria)
warehouse = create_engine(url_etl)