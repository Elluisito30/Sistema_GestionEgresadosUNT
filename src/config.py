import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables de entorno desde .env


def get_env(*keys, default=None):
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default

# Configuración de la Base de Datos
DB_CONFIG = {
    "host": str(get_env("DB_HOST", default="localhost")),
    "database": str(get_env("DB_NAME", "POSTGRES_DB", default="egresados_unt_db")),
    "user": str(get_env("DB_USER", "POSTGRES_USER", default="postgres")),
    "password": str(get_env("DB_PASSWORD", "POSTGRES_PASSWORD", default="postgres")),
    "port": str(get_env("DB_PORT", default="5432"))
}

# Otras configuraciones
SECRET_KEY = os.getenv("SECRET_KEY", "una-clave-secreta-muy-segura-cambiar-en-produccion")

# Configuración SMTP (Email)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")