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
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20, **DB_CONFIG
                )
                print("Pool de conexiones creado exitosamente.")
            except Exception as e:
                print(f"Error al crear el pool: {e}")
                self._pool = None

    def get_connection(self):
        if self._pool:
            try:
                return self._pool.getconn()
            except Exception as e:
                print(f"Error al obtener conexión del pool: {e}. Intentando reconectar...")
                self._init_pool()
                if self._pool:
                    return self._pool.getconn()
        
        # Fallback a conexión directa si el pool falla
        return psycopg2.connect(**DB_CONFIG)

    def return_connection(self, conn):
        if self._pool and hasattr(conn, 'cursor'): # Verificar que sea una conexión válida
            try:
                self._pool.putconn(conn)
            except Exception:
                conn.close()
        elif conn:
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