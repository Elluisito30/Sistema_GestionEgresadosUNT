import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables de entorno desde .env

# Configuración de la Base de Datos
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "bd_egresadosUNT"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "port": os.getenv("DB_PORT", "5432")
}

# Otras configuraciones
SECRET_KEY = os.getenv("SECRET_KEY", "una-clave-secreta-muy-segura-cambiar-en-produccion")

# Configuración SMTP (Email)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")