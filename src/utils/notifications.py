"""
Sistema de notificaciones internas.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.utils.database import get_db_cursor
from src.utils.email import email_sender

class NotificationSystem:
    """Sistema de notificaciones."""
    
    @staticmethod
    def create_notification(usuario_id: str, tipo: str, asunto: str, 
                           mensaje: str, metadata: Optional[Dict] = None):
        """
        Crea una nueva notificación.
        
        Args:
            usuario_id: ID del usuario destinatario
            tipo: 'sistema' o 'email'
            asunto: Asunto de la notificación
            mensaje: Mensaje de la notificación
            metadata: Datos adicionales (ej. {'oferta_id': '123'})
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, tipo, asunto, mensaje, metadata))
            
            notificacion_id = cur.fetchone()[0]
            
            # Si es tipo email, enviar correo
            if tipo == 'email':
                NotificationSystem._send_email_notification(
                    usuario_id, asunto, mensaje
                )
            
            return notificacion_id
    
    @staticmethod
    def create_bulk_notifications(usuarios_ids: List[str], tipo: str,
                                  asunto: str, mensaje: str,
                                  metadata: Optional[Dict] = None):
        """
        Crea notificaciones para múltiples usuarios.
        """
        notificaciones = []
        with get_db_cursor(commit=True) as cur:
            for usuario_id in usuarios_ids:
                cur.execute("""
                    INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (usuario_id, tipo, asunto, mensaje, metadata))
                
                notificaciones.append(cur.fetchone()[0])
        
        return notificaciones
    
    @staticmethod
    def get_user_notifications(usuario_id: str, limit: int = 50, 
                               only_unread: bool = False) -> List[Dict]:
        """
        Obtiene las notificaciones de un usuario.
        """
        query = """
            SELECT id, tipo, asunto, mensaje, leida, fecha_creacion, metadata
            FROM notificaciones
            WHERE usuario_id = %s
        """
        params = [usuario_id]
        
        if only_unread:
            query += " AND leida = false"
        
        query += " ORDER BY fecha_creacion DESC LIMIT %s"
        params.append(limit)
        
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    @staticmethod
    def mark_as_read(notificacion_id: str):
        """Marca una notificación como leída."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE notificaciones
                SET leida = true
                WHERE id = %s
            """, (notificacion_id,))
    
    @staticmethod
    def mark_all_as_read(usuario_id: str):
        """Marca todas las notificaciones de un usuario como leídas."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE notificaciones
                SET leida = true
                WHERE usuario_id = %s AND leida = false
            """, (usuario_id,))
    
    @staticmethod
    def delete_notification(notificacion_id: str):
        """Elimina una notificación."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM notificaciones WHERE id = %s", (notificacion_id,))
    
    @staticmethod
    def count_unread(usuario_id: str) -> int:
        """Cuenta las notificaciones no leídas de un usuario."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM notificaciones
                WHERE usuario_id = %s AND leida = false
            """, (usuario_id,))
            return cur.fetchone()[0]
    
    @staticmethod
    def _send_email_notification(usuario_id: str, asunto: str, mensaje: str):
        """Envía una notificación por email."""
        with get_db_cursor() as cur:
            cur.execute("SELECT email FROM usuarios WHERE id = %s", (usuario_id,))
            email = cur.fetchone()
            
            if email:
                email_sender.send_notification(email[0], asunto, mensaje)
    
    # Métodos específicos para diferentes tipos de notificaciones
    
    @staticmethod
    def notify_new_offer(egresado_id: str, oferta_titulo: str, oferta_id: str):
        """Notifica a un egresado sobre una nueva oferta relevante."""
        with get_db_cursor() as cur:
            cur.execute("SELECT usuario_id FROM egresados WHERE id = %s", (egresado_id,))
            usuario_id = cur.fetchone()[0]
        
        NotificationSystem.create_notification(
            usuario_id=usuario_id,
            tipo='sistema',
            asunto='Nueva oferta de tu interés',
            mensaje=f'Se ha publicado una nueva oferta: "{oferta_titulo}" que podría interesarte.',
            metadata={'oferta_id': oferta_id}
        )
    
    @staticmethod
    def notify_postulation_status_change(postulacion_id: str, nuevo_estado: str):
        """Notifica a un egresado sobre cambio en estado de postulación."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT u.id, o.titulo
                FROM postulaciones p
                JOIN egresados e ON p.egresado_id = e.id
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN ofertas o ON p.oferta_id = o.id
                WHERE p.id = %s
            """, (postulacion_id,))
            
            usuario_id, oferta_titulo = cur.fetchone()
        
        NotificationSystem.create_notification(
            usuario_id=usuario_id,
            tipo='sistema',
            asunto='Estado de postulación actualizado',
            mensaje=f'Tu postulación para "{oferta_titulo}" ha cambiado a: {nuevo_estado}',
            metadata={'postulacion_id': postulacion_id, 'estado': nuevo_estado}
        )
    
    @staticmethod
    def notify_new_postulation(oferta_id: str, empleador_id: str, egresado_nombre: str):
        """Notifica a un empleador sobre nueva postulación."""
        with get_db_cursor() as cur:
            cur.execute("SELECT usuario_id FROM empleadores WHERE id = %s", (empleador_id,))
            usuario_id = cur.fetchone()[0]
            
            cur.execute("SELECT titulo FROM ofertas WHERE id = %s", (oferta_id,))
            oferta_titulo = cur.fetchone()[0]
        
        NotificationSystem.create_notification(
            usuario_id=usuario_id,
            tipo='sistema',
            asunto='Nueva postulación recibida',
            mensaje=f'Has recibido una nueva postulación de {egresado_nombre} para la oferta "{oferta_titulo}"',
            metadata={'oferta_id': oferta_id}
        )
    
    @staticmethod
    def notify_event_reminder(evento_id: str, usuario_id: str):
        """Envía recordatorio de evento."""
        with get_db_cursor() as cur:
            cur.execute("SELECT titulo, fecha_inicio FROM eventos WHERE id = %s", (evento_id,))
            titulo, fecha = cur.fetchone()
        
        fecha_str = fecha.strftime('%d/%m/%Y %H:%M')
        
        NotificationSystem.create_notification(
            usuario_id=usuario_id,
            tipo='email',
            asunto=f'Recordatorio: {titulo}',
            mensaje=f'Te recordamos que el evento "{titulo}" comenzará el {fecha_str}. ¡No faltes!',
            metadata={'evento_id': evento_id}
        )
    
    @staticmethod
    def notify_company_approved(empresa_id: str):
        """Notifica a los empleadores que su empresa fue aprobada."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT u.id, e.razon_social
                FROM empleadores em
                JOIN usuarios u ON em.usuario_id = u.id
                JOIN empresas e ON em.empresa_id = e.id
                WHERE em.empresa_id = %s
            """, (empresa_id,))
            
            resultados = cur.fetchall()
            razon_social = resultados[0][1] if resultados else "tu empresa"
        
        for usuario_id, _ in resultados:
            NotificationSystem.create_notification(
                usuario_id=usuario_id,
                tipo='email',
                asunto='Empresa aprobada',
                mensaje=f'¡Felicitaciones! {razon_social} ha sido aprobada en el sistema. Ya puedes publicar ofertas.',
                metadata={'empresa_id': empresa_id}
            )
    
    @staticmethod
    def notify_survey_available(encuesta_id: str, egresado_id: str):
        """Notifica a un egresado sobre una nueva encuesta disponible."""
        with get_db_cursor() as cur:
            cur.execute("SELECT usuario_id FROM egresados WHERE id = %s", (egresado_id,))
            usuario_id = cur.fetchone()[0]
            
            cur.execute("SELECT titulo FROM encuestas WHERE id = %s", (encuesta_id,))
            titulo = cur.fetchone()[0]
        
        NotificationSystem.create_notification(
            usuario_id=usuario_id,
            tipo='sistema',
            asunto='Nueva encuesta disponible',
            mensaje=f'Tenemos una nueva encuesta para ti: "{titulo}". Tu opinión es importante.',
            metadata={'encuesta_id': encuesta_id}
        )

# Instancia global
notifications = NotificationSystem()