
from src.utils.database import get_db_cursor

def fix_database():
    print("Verificando existencia de tabla chat_eventos...")
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_eventos (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
                    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    mensaje TEXT NOT NULL,
                    fecha_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_chat_evento_id ON chat_eventos(evento_id);
                CREATE INDEX IF NOT EXISTS idx_chat_fecha_envio ON chat_eventos(fecha_envio);
            """)
            print("Tabla chat_eventos verificada/creada exitosamente.")
    except Exception as e:
        print(f"Error al crear la tabla: {e}")

if __name__ == "__main__":
    fix_database()
