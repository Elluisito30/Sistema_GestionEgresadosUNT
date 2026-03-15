import psycopg2

conn_str = "postgres://postgres:300805@127.0.0.1:5432/postgres"

try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('ALTER DATABASE "bd_egresadosUNT " RENAME TO bd_egresadosUNT;')
    print("Database renamed successfully!")
    cur.close()
    conn.close()
except psycopg2.Error as e:
    print(f"PostgreSQL Error: {e}")
except Exception as e:
    print(f"Error: {e}")
