import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from src.config import DB_CONFIG
import streamlit as st

# Pool de conexiones para eficiencia
class DatabasePool:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            try:
                cls._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20, **DB_CONFIG
                )
                print("Pool de conexiones creado exitosamente.")
            except Exception as e:
                print(f"Error al crear el pool: {e}")
                cls._pool = None
        return cls._instance

    def get_connection(self):
        if self._pool:
            return self._pool.getconn()
        else:
            # Fallback a conexión directa si el pool falla
            return psycopg2.connect(**DB_CONFIG)

    def return_connection(self, conn):
        if self._pool:
            self._pool.putconn(conn)
        else:
            conn.close()

db_pool = DatabasePool()

@contextmanager
def get_db_connection():
    """Context manager para obtener y liberar una conexión."""
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        db_pool.return_connection(conn)

@contextmanager
def get_db_cursor(commit=False):
    """Context manager para obtener un cursor. Realiza commit si se especifica."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()