import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

conn_str = "postgres://postgres:300805@127.0.0.1:5432/bd_egresadosUNT"
try:
    # SQL_ASCII allows reading raw bytes without decoding
    conn = psycopg2.connect(conn_str, client_encoding='SQL_ASCII')
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, email, password_hash, rol, activo FROM usuarios")
    rows = cur.fetchall()
    
    def decode_val(val):
        if isinstance(val, memoryview):
            return val.tobytes().decode('utf-8', errors='replace')
        elif isinstance(val, bytes):
            return val.decode('utf-8', errors='replace')
        return str(val)

    with open("users_info.json", "w", encoding="utf-8") as f:
        json.dump([{k: decode_val(v) for k, v in row.items()} for row in rows], f, indent=4)
    print("Exported to users_info.json")
except Exception as e:
    print("Error:", e)
