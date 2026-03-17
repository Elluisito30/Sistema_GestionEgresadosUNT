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
                conn = self._pool.getconn()
                # Verificar si la conexión es válida
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                    return conn
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

def init_critical_tables():
    """Asegura que las tablas críticas existan."""
    try:
        with get_db_cursor(commit=True) as cur:
            # Tabla de notificaciones (si no existe)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notificaciones (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    tipo VARCHAR(50), 
                    asunto VARCHAR(255),
                    mensaje TEXT NOT NULL,
                    leida BOOLEAN DEFAULT FALSE,
                    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    fecha_envio TIMESTAMP WITH TIME ZONE,
                    metadata JSONB
                );
                CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificaciones(usuario_id);
                CREATE INDEX IF NOT EXISTS idx_notif_leida ON notificaciones(leida);
            """)
            
            # Tabla de chat
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_eventos (
                    id SERIAL PRIMARY KEY,
                    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    mensaje TEXT NOT NULL,
                    fecha_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Tablas críticas verificadas.")
    except Exception as e:
        print(f"Advertencia en init_critical_tables: {e}")

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
