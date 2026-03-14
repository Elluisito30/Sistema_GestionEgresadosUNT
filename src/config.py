import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables de entorno desde .env

# Configuración de la Base de Datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "egresados_unt_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

# Otras configuraciones
SECRET_KEY = os.getenv("SECRET_KEY", "una-clave-secreta-muy-segura-cambiar-en-produccion")