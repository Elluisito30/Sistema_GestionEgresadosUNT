
import psycopg2
from datetime import date, timedelta

def update_surveys():
    conn_params = {
        "host": "localhost",
        "database": "bd_egresadosUNT",
        "user": "postgres",
        "password": "300805",
        "port": "5432"
    }
    try:
        conn = psycopg2.connect(**conn_params)
        conn.set_client_encoding('UTF8')
        conn.autocommit = True
        with conn.cursor() as cur:
            today = date.today()
            start_date = today - timedelta(days=1)
            end_date = today + timedelta(days=30)
            
            print(f"Actualizando encuestas...")
            
            # Update all active surveys to be visible today
            cur.execute("""
                UPDATE encuestas 
                SET fecha_inicio = %s, 
                    fecha_fin = %s,
                    activa = true,
                    dirigida_a = 'todos'
            """, (start_date, end_date))
            
            print(f"Se actualizaron {cur.rowcount} encuestas.")
            
        conn.close()
        print("Hecho.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_surveys()
