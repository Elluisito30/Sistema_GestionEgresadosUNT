"""
Modelo de Encuesta para el sistema.
Representa una encuesta de seguimiento a egresados.
"""
from datetime import datetime
from src.utils.database import get_db_cursor
import json

class Encuesta:
    """Clase que representa una encuesta."""
    
    def __init__(self, id=None, titulo=None, descripcion=None,
                 fecha_inicio=None, fecha_fin=None, activa=True,
                 creada_por=None):
        self.id = id
        self.titulo = titulo
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.activa = activa
        self.creada_por = creada_por
    
    @classmethod
    def get_by_id(cls, encuesta_id):
        """Obtiene una encuesta por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM encuestas WHERE id = %s", (encuesta_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_activas(cls):
        """Obtiene las encuestas activas."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM encuestas
                WHERE activa = true
                AND fecha_inicio <= CURRENT_DATE
                AND fecha_fin >= CURRENT_DATE
                ORDER BY fecha_fin ASC
            """)
            
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    def get_preguntas(self):
        """Obtiene las preguntas de la encuesta."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM preguntas_encuesta
                WHERE encuesta_id = %s
                ORDER BY id
            """, (self.id,))
            
            columns = [desc[0] for desc in cur.description]
            preguntas = []
            for row in cur.fetchall():
                pregunta = dict(zip(columns, row))
                if pregunta['opciones']:
                    pregunta['opciones'] = json.loads(pregunta['opciones'])
                preguntas.append(pregunta)
            
            return preguntas
    
    def get_respuestas(self, egresado_id=None):
        """Obtiene las respuestas de la encuesta."""
        query = """
            SELECT r.*, p.texto_pregunta
            FROM respuestas_encuesta r
            JOIN preguntas_encuesta p ON r.pregunta_id = p.id
            WHERE r.encuesta_id = %s
        """
        params = [self.id]
        
        if egresado_id:
            query += " AND r.egresado_id = %s"
            params.append(egresado_id)
        
        query += " ORDER BY r.pregunta_id"
        
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_estadisticas(self):
        """Obtiene estadísticas de la encuesta."""
        with get_db_cursor() as cur:
            # Total de egresados que han respondido
            cur.execute("""
                SELECT COUNT(DISTINCT egresado_id)
                FROM respuestas_encuesta
                WHERE encuesta_id = %s
            """, (self.id,))
            total_respondieron = cur.fetchone()[0] or 0
            
            # Total de preguntas
            cur.execute("""
                SELECT COUNT(*) FROM preguntas_encuesta
                WHERE encuesta_id = %s
            """, (self.id,))
            total_preguntas = cur.fetchone()[0] or 0
            
            # Tasa de respuesta por pregunta
            cur.execute("""
                SELECT 
                    p.texto_pregunta,
                    COUNT(r.id) as respuestas
                FROM preguntas_encuesta p
                LEFT JOIN respuestas_encuesta r ON p.id = r.pregunta_id
                WHERE p.encuesta_id = %s
                GROUP BY p.id, p.texto_pregunta
            """, (self.id,))
            
            respuestas_por_pregunta = cur.fetchall()
            
            return {
                'total_respondieron': total_respondieron,
                'total_preguntas': total_preguntas,
                'respuestas_por_pregunta': respuestas_por_pregunta
            }
    
    def egresado_ha_respondido(self, egresado_id):
        """Verifica si un egresado ha respondido la encuesta completa."""
        with get_db_cursor() as cur:
            # Total de preguntas
            cur.execute("""
                SELECT COUNT(*) FROM preguntas_encuesta
                WHERE encuesta_id = %s
            """, (self.id,))
            total_preguntas = cur.fetchone()[0]
            
            # Respuestas del egresado
            cur.execute("""
                SELECT COUNT(DISTINCT pregunta_id)
                FROM respuestas_encuesta
                WHERE encuesta_id = %s AND egresado_id = %s
            """, (self.id, egresado_id))
            respuestas = cur.fetchone()[0]
            
            return respuestas >= total_preguntas
    
    def get_progreso_egresado(self, egresado_id):
        """Obtiene el progreso de un egresado en la encuesta."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT r.pregunta_id) as respondidas,
                    COUNT(p.id) as total
                FROM preguntas_encuesta p
                LEFT JOIN respuestas_encuesta r 
                    ON p.id = r.pregunta_id 
                    AND r.egresado_id = %s
                WHERE p.encuesta_id = %s
            """, (egresado_id, self.id))
            
            respondidas, total = cur.fetchone()
            return {
                'respondidas': respondidas or 0,
                'total': total or 0,
                'porcentaje': ((respondidas or 0) / (total or 1)) * 100
            }
    
    def save(self):
        """Guarda o actualiza la encuesta en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE encuestas
                    SET titulo = %s,
                        descripcion = %s,
                        fecha_inicio = %s,
                        fecha_fin = %s,
                        activa = %s
                    WHERE id = %s
                """, (
                    self.titulo, self.descripcion,
                    self.fecha_inicio, self.fecha_fin,
                    self.activa, self.id
                ))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO encuestas (
                        titulo, descripcion, fecha_inicio, fecha_fin, creada_por
                    ) VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    self.titulo, self.descripcion,
                    self.fecha_inicio, self.fecha_fin,
                    self.creada_por
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'activa': self.activa
        }