
import os
import psycopg2
from src.utils.database import DB_CONFIG

def reset_database():
    print("Iniciando reinicio de base de datos...")
    # Usar valores de .env directamente para evitar errores de importación/config
    db_params = {
        "host": "localhost",
        "database": "bd_egresadosUNT",
        "user": "postgres",
        "password": "contrasena_que_probablemente_esta_en_el_sistema",
        "port": "5432"
    }
    # Intentar leer del .env manualmente si fallamos
    try:
        # Conectar a la base de datos
        print("Intentando conectar con DB_CONFIG de src.config...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Leer create_bd.sql
        print("Ejecutando create_bd.sql...")
        with open('database/create_bd.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            cur.execute(sql)
        
        # Leer seed_bd.sql
        print("Ejecutando seed_bd.sql...")
        with open('database/seed_bd.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            cur.execute(sql)

        print("Base de datos reiniciada exitosamente con 3 usuarios.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error al reiniciar la base de datos: {e}")

if __name__ == "__main__":
    reset_database()
