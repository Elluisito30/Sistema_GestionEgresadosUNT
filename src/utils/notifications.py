"""
Sistema de notificaciones internas.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.utils.database import get_db_cursor
from src.utils.email import send_email

class NotificationSystem:
    """Sistema de notificaciones."""

    @staticmethod
    def create(usuario_id: str, asunto: str, mensaje: str, tipo: str = 'sistema', 
               metadata: Optional[dict] = None, email_copy: bool = False):
        """Crea una notificación interna."""
        try:
            import json
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO notificaciones (usuario_id, asunto, mensaje, tipo, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (usuario_id, asunto, mensaje, tipo, json.dumps(metadata) if metadata else None))
            
            if email_copy:
                # Obtener el correo del usuario
                with get_db_cursor() as cur:
                    cur.execute("SELECT email FROM usuarios WHERE id = %s", (usuario_id,))
                    res = cur.fetchone()
                    if res:
                        send_email(res[0], asunto, mensaje)
            
            return True
        except Exception as e:
            print(f"Error al crear notificación: {e}")
            return False

    @staticmethod
    def get_unread(usuario_id: str):
        """Retorna las notificaciones no leídas de un usuario."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, asunto, mensaje, tipo, metadata, leida, fecha_creacion
                FROM notificaciones
                WHERE usuario_id = %s AND leida = FALSE
                ORDER BY fecha_creacion DESC
            """, (usuario_id,))
            return cur.fetchall()

    @staticmethod
    def mark_as_read(notificacion_id: str):
        """Marca una notificación como leída."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE notificaciones SET leida = TRUE WHERE id = %s", (notificacion_id,))

    @staticmethod
    def mark_all_as_read(usuario_id: str):
        """Marca todas las notificaciones como leídas."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE notificaciones SET leida = TRUE WHERE usuario_id = %s", (usuario_id,))

    @staticmethod
    def get_history(usuario_id: str, limit: int = 50):
        """Retorna el historial completo de notificaciones de un usuario."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, asunto, mensaje, tipo, metadata, leida, fecha_creacion
                FROM notificaciones
                WHERE usuario_id = %s
                ORDER BY fecha_creacion DESC
                LIMIT %s
            """, (usuario_id, limit))
            return cur.fetchall()
