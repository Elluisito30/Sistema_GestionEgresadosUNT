import psycopg2
from src.config import DB_CONFIG

try:
    psycopg2.connect(**DB_CONFIG)
except Exception as e:
    with open('error_log.txt', 'wb') as f:
        f.write(str(e).encode('utf-8', errors='ignore'))
        import traceback
        f.write(traceback.format_exc().encode('utf-8', errors='ignore'))
