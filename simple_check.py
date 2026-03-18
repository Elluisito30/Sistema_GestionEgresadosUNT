
import psycopg2

def check():
    conn_params = {
        "host": "localhost",
        "database": "bd_egresadosUNT",
        "user": "postgres",
        "password": "300805",
        "port": "5432"
    }
    try:
        conn = psycopg2.connect(**conn_params)
        with conn.cursor() as cur:
            cur.execute("SELECT id, activa, fecha_inicio, fecha_fin, dirigida_a FROM encuestas")
            rows = cur.fetchall()
            print(f"Total encuestas: {len(rows)}")
            for r in rows:
                print(f"ID: {r[0]}, Activa: {r[1]}, Inicio: {r[2]}, Fin: {r[3]}, Dirigida: {r[4]}")
            
            cur.execute("SELECT id, nombres FROM egresados")
            egs = cur.fetchall()
            print(f"Total egresados: {len(egs)}")
            for e in egs:
                print(f"ID: {e[0]}, Nombre: {e[1]}")
                
            cur.execute("SELECT encuesta_id, egresado_id FROM asignaciones_encuesta")
            asigs = cur.fetchall()
            print(f"Total asignaciones: {len(asigs)}")
            for a in asigs:
                print(f"Enc: {a[0]}, Egr: {a[1]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()
