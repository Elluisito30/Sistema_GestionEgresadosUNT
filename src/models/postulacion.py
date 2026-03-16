"""
Modelo de Postulación para el sistema.
Representa la postulación de un egresado a una oferta.
"""
from datetime import datetime
from src.utils.database import get_db_cursor

class Postulacion:
    """Clase que representa una postulación laboral."""
    
    def __init__(self, id=None, oferta_id=None, egresado_id=None,
                 fecha_postulacion=None, estado='recibido',
                 cv_usado_url=None, fecha_estado_actual=None,
                 comentario_revision=None):
        self.id = id
        self.oferta_id = oferta_id
        self.egresado_id = egresado_id
        self.fecha_postulacion = fecha_postulacion or datetime.now()
        self.estado = estado
        self.cv_usado_url = cv_usado_url
        self.fecha_estado_actual = fecha_estado_actual or datetime.now()
        self.comentario_revision = comentario_revision
    
    @classmethod
    def get_by_id(cls, postulacion_id):
        """Obtiene una postulación por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM postulaciones WHERE id = %s", (postulacion_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_egresado(cls, egresado_id, limit=20):
        """Obtiene postulaciones de un egresado."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.*, o.titulo as oferta_titulo, e.razon_social as empresa
                FROM postulaciones p
                JOIN ofertas o ON p.oferta_id = o.id
                JOIN empresas e ON o.empresa_id = e.id
                WHERE p.egresado_id = %s
                ORDER BY p.fecha_postulacion DESC
                LIMIT %s
            """, (egresado_id, limit))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    @classmethod
    def get_by_oferta(cls, oferta_id):
        """Obtiene postulaciones de una oferta."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.*, eg.nombres, eg.apellido_paterno, eg.url_cv
                FROM postulaciones p
                JOIN egresados eg ON p.egresado_id = eg.id
                WHERE p.oferta_id = %s
                ORDER BY p.fecha_postulacion ASC
            """, (oferta_id,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def cambiar_estado(self, nuevo_estado, comentario=None, empresa_id=None):
        """Cambia el estado de la postulación."""
        estados_validos = ['recibido', 'en_revision', 'entrevista', 
                          'seleccionado', 'descartado']
        
        if nuevo_estado not in estados_validos:
            return False, "Estado no válido"
        
        with get_db_cursor(commit=True) as cur:
            # Validación de pertenencia para evitar cambios de estado fuera de la empresa autorizada
            if empresa_id:
                cur.execute(
                    """
                    SELECT 1
                    FROM postulaciones p
                    JOIN ofertas o ON p.oferta_id = o.id
                    WHERE p.id = %s AND o.empresa_id = %s
                    """,
                    (self.id, empresa_id),
                )
                if not cur.fetchone():
                    return False, "No autorizado para actualizar esta postulación"

            cur.execute("""
                UPDATE postulaciones
                SET estado = %s,
                    fecha_estado_actual = NOW(),
                    comentario_revision = COALESCE(%s, comentario_revision)
                WHERE id = %s
                RETURNING id
            """, (nuevo_estado, comentario, self.id))
            
            if cur.fetchone():
                self.estado = nuevo_estado
                self.fecha_estado_actual = datetime.now()
                if comentario:
                    self.comentario_revision = comentario
                
                # Notificar al egresado
                self.notificar_cambio_estado()
                
                return True, "Estado actualizado exitosamente"
            
            return False, "Error al actualizar estado"
    
    def notificar_cambio_estado(self):
        """Notifica al egresado sobre el cambio de estado."""
        with get_db_cursor(commit=True) as cur:
            # Obtener datos para la notificación
            cur.execute("""
                SELECT u.id, o.titulo
                FROM postulaciones p
                JOIN egresados e ON p.egresado_id = e.id
                JOIN usuarios u ON e.usuario_id = u.id
                JOIN ofertas o ON p.oferta_id = o.id
                WHERE p.id = %s
            """, (self.id,))
            
            res = cur.fetchone()
            if not res:
                return

            usuario_id, oferta_titulo = res
            
            # Crear notificación
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                VALUES (%s, 'sistema', 'Estado de postulación actualizado',
                        'Tu postulación a "' || %s || '" ha cambiado a: ' || %s)
            """, (usuario_id, oferta_titulo, self.estado))
    
    def get_dias_en_estado(self):
        """Obtiene los días que lleva en el estado actual."""
        if not self.fecha_estado_actual:
            return 0
        return (datetime.now() - self.fecha_estado_actual).days
    
    def save(self):
        """Guarda o actualiza la postulación en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE postulaciones
                    SET estado = %s,
                        cv_usado_url = %s,
                        comentario_revision = %s
                    WHERE id = %s
                """, (self.estado, self.cv_usado_url, self.comentario_revision, self.id))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO postulaciones (
                        oferta_id, egresado_id, cv_usado_url
                    ) VALUES (%s, %s, %s)
                    RETURNING id
                """, (self.oferta_id, self.egresado_id, self.cv_usado_url))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'oferta_id': str(self.oferta_id) if self.oferta_id else None,
            'egresado_id': str(self.egresado_id) if self.egresado_id else None,
            'fecha_postulacion': self.fecha_postulacion.isoformat() if self.fecha_postulacion else None,
            'estado': self.estado,
            'cv_usado_url': self.cv_usado_url,
            'fecha_estado_actual': self.fecha_estado_actual.isoformat() if self.fecha_estado_actual else None,
            'comentario_revision': self.comentario_revision,
            'dias_en_estado': self.get_dias_en_estado()
        }