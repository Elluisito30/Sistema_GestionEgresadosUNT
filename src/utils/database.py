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
                # Asegurar que DB_CONFIG sea string UTF-8 si es necesario
                params = {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in DB_CONFIG.items()}
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20, **params
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
        params = {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in DB_CONFIG.items()}
        return psycopg2.connect(**params)

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

            # Tabla de asignaciones de encuesta
            cur.execute("""
                CREATE TABLE IF NOT EXISTS asignaciones_encuesta (
                    id SERIAL PRIMARY KEY,
                    encuesta_id INTEGER NOT NULL REFERENCES encuestas(id) ON DELETE CASCADE,
                    egresado_id INTEGER NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
                    fecha_asignacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(encuesta_id, egresado_id)
                );
            """)
            
            # Asegurar columnas en encuestas
            cur.execute("ALTER TABLE encuestas ADD COLUMN IF NOT EXISTS dirigida_a VARCHAR(50) DEFAULT 'todos';")
            cur.execute("ALTER TABLE encuestas ADD COLUMN IF NOT EXISTS categoria VARCHAR(100);")
            cur.execute("ALTER TABLE encuestas ADD COLUMN IF NOT EXISTS es_obligatoria BOOLEAN DEFAULT FALSE;")
            
            # Limpiar valores NULL para encuestas antiguas y forzar vigencia para depuración
            cur.execute("UPDATE encuestas SET dirigida_a = 'todos' WHERE dirigida_a IS NULL;")
            cur.execute("UPDATE encuestas SET categoria = 'General' WHERE categoria IS NULL;")
            cur.execute("UPDATE encuestas SET es_obligatoria = FALSE WHERE es_obligatoria IS NULL;")
            
            # Forzar que las encuestas activas estén en rango de fecha actual
            cur.execute("""
                UPDATE encuestas 
                SET fecha_inicio = CURRENT_DATE - INTERVAL '1 day',
                    fecha_fin = CURRENT_DATE + INTERVAL '30 days'
                WHERE activa = true;
            """)
            
            print("Tablas críticas verificadas y fechas actualizadas.")
    except Exception as e:
        st.error(f"Error crítico en init_critical_tables: {e}")
        print(f"Error en init_critical_tables: {e}")

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
