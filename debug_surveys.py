
import psycopg2
import sys
import os
from datetime import date

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.utils.database import get_db_cursor

def debug_surveys():
    print("--- DEPURACIÓN DE ENCUESTAS ---")
    try:
        with get_db_cursor() as cur:
            # 1. Ver egresados
            cur.execute("SELECT id, nombres, apellido_paterno, usuario_id FROM egresados")
            egresados = cur.fetchall()
            print("\nEgresados registrados:")
            for eg in egresados:
                print(f"ID: {eg[0]} | Nombre: {eg[1]} {eg[2]} | UsuarioID: {eg[3]}")

            # 2. Ver encuestas
            cur.execute("SELECT id, titulo, activa, fecha_inicio, fecha_fin, dirigida_a FROM encuestas")
            encuestas = cur.fetchall()
            print("\nEncuestas en BD:")
            today = date.today()
            for en in encuestas:
                print(f"ID: {en[0]} | Título: {en[1]} | Activa: {en[2]} | Inicio: {en[3]} | Fin: {en[4]} | Dirigida: {en[5]}")
                if not en[2]: print(f"  -> MOTIVO: No está activa")
                if en[3] > today: print(f"  -> MOTIVO: No ha iniciado (Inicio: {en[3]}, Hoy: {today})")
                if en[4] < today: print(f"  -> MOTIVO: Ya venció (Fin: {en[4]}, Hoy: {today})")

            # 3. Ver asignaciones
            cur.execute("SELECT encuesta_id, egresado_id FROM asignaciones_encuesta")
            asignaciones = cur.fetchall()
            print("\nAsignaciones específicas:")
            for asig in asignaciones:
                print(f"Encuesta ID: {asig[0]} -> Egresado ID: {asig[1]}")

    except Exception as e:
        print(f"Error en depuración: {e}")

if __name__ == "__main__":
    debug_surveys()
