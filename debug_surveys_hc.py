
import psycopg2
from datetime import date

def debug_surveys():
    # Hardcoded values from the .env output to bypass encoding issues
    conn_params = {
        "host": "localhost",
        "database": "bd_egresadosUNT",
        "user": "postgres",
        "password": "300805",
        "port": "5432"
    }
    
    print("--- DEPURACIÓN DE ENCUESTAS (LATIN1) ---")
    try:
        # Try connecting with a specific encoding
        conn = psycopg2.connect(**conn_params)
        conn.set_client_encoding('UTF8') 
        with conn.cursor() as cur:
            # Fix NULL values in dirigida_a
            print("Corrigiendo posibles valores NULL en dirigida_a...")
            cur.execute("UPDATE encuestas SET dirigida_a = 'todos' WHERE dirigida_a IS NULL")
            conn.commit()

            # 1. Ver egresados
            cur.execute("SELECT id, nombres, apellido_paterno FROM egresados")
            egresados = cur.fetchall()
            print("\nEgresados registrados:")
            for eg in egresados:
                print(f"ID: {eg[0]} | Nombre: {eg[1]} {eg[2]}")

            # 2. Ver encuestas
            cur.execute("SELECT id, titulo, activa, fecha_inicio, fecha_fin, dirigida_a FROM encuestas")
            encuestas = cur.fetchall()
            print("\nEncuestas en BD:")
            today = date.today()
            for en in encuestas:
                print(f"ID: {en[0]} | Título: {en[1]} | Activa: {en[2]} | Inicio: {en[3]} | Fin: {en[4]} | Dirigida: {en[5]}")

            # 3. Ver asignaciones
            cur.execute("SELECT encuesta_id, egresado_id FROM asignaciones_encuesta")
            asignaciones = cur.fetchall()
            print("\nAsignaciones específicas:")
            for asig in asignaciones:
                print(f"Encuesta ID: {asig[0]} -> Egresado ID: {asig[1]}")

        conn.close()
    except Exception as e:
        print(f"Error en depuración: {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_surveys()
