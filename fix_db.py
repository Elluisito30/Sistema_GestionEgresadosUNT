import psycopg2
import sys

conn_str = "postgres://postgres:300805@127.0.0.1:5432/postgres"

try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database;")
    dbs = [row[0] for row in cur.fetchall()]
    print("Databases:", dbs)
    
    target_db = None
    for db in dbs:
        if "bd_egresadosUNT" in db:
            target_db = db
            break
            
    if target_db and target_db != "bd_egresadosUNT":
        print(f"Renaming '{target_db}' to 'bd_egresadosUNT'")
        cur.execute(f'ALTER DATABASE "{target_db}" RENAME TO bd_egresadosUNT;')
        print("Success!")
    elif target_db == "bd_egresadosUNT":
        print("Database is already named correctly.")
    else:
        print("Database not found. Creating it!")
        cur.execute("CREATE DATABASE bd_egresadosUNT;")
        print("Created!")
        
    cur.close()
    conn.close()
except Exception as e:
    import traceback
    traceback.print_exc()
