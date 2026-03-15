"""
Modelo de Evento para el sistema.
Representa un evento (feria, webinar, charla, curso).
"""
from datetime import datetime
from src.utils.database import get_db_cursor

class Evento:
    """Clase que representa un evento."""
    
    def __init__(self, id=None, publicado_por=None, titulo=None,
                 descripcion=None, tipo=None, fecha_inicio=None,
                 fecha_fin=None, lugar=None, capacidad_maxima=None,
                 es_gratuito=True, precio=None, imagen_promocional_url=None,
                 activo=True):
        self.id = id
        self.publicado_por = publicado_por
        self.titulo = titulo
        self.descripcion = descripcion
        self.tipo = tipo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.lugar = lugar
        self.capacidad_maxima = capacidad_maxima
        self.es_gratuito = es_gratuito
        self.precio = precio
        self.imagen_promocional_url = imagen_promocional_url
        self.activo = activo
    
    @classmethod
    def get_by_id(cls, evento_id):
        """Obtiene un evento por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM eventos WHERE id = %s", (evento_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_proximos(cls, limit=20):
        """Obtiene los próximos eventos."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM eventos
                WHERE activo = true
                AND fecha_inicio > NOW()
                ORDER BY fecha_inicio ASC
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    def get_inscritos(self):
        """Obtiene los inscritos al evento."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    u.email,
                    CASE 
                        WHEN e.id IS NOT NULL THEN e.nombres || ' ' || e.apellido_paterno
                        ELSE 'Empleador'
                    END as nombre,
                    i.fecha_inscripcion,
                    i.asistio
                FROM inscripciones_eventos i
                JOIN usuarios u ON i.usuario_id = u.id
                LEFT JOIN egresados e ON u.id = e.usuario_id
                WHERE i.evento_id = %s
                ORDER BY i.fecha_inscripcion DESC
            """, (self.id,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def contar_inscritos(self):
        """Cuenta el número de inscritos."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM inscripciones_eventos
                WHERE evento_id = %s
            """, (self.id,))
            return cur.fetchone()[0]
    
    def cupo_disponible(self):
        """Verifica si hay cupo disponible."""
        if not self.capacidad_maxima:
            return True
        return self.contar_inscritos() < self.capacidad_maxima
    
    def porcentaje_cupo(self):
        """Calcula el porcentaje de cupo ocupado."""
        if not self.capacidad_maxima:
            return 0
        inscritos = self.contar_inscritos()
        return (inscritos / self.capacidad_maxima) * 100
    
    def inscribir_usuario(self, usuario_id, pago_id=None):
        """Inscribe un usuario al evento."""
        if not self.cupo_disponible():
            return False, "No hay cupo disponible"
        
        with get_db_cursor(commit=True) as cur:
            # Verificar si ya está inscrito
            cur.execute("""
                SELECT id FROM inscripciones_eventos
                WHERE evento_id = %s AND usuario_id = %s
            """, (self.id, usuario_id))
            
            if cur.fetchone():
                return False, "Ya estás inscrito en este evento"
            
            # Insertar inscripción
            cur.execute("""
                INSERT INTO inscripciones_eventos (evento_id, usuario_id, pago_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (self.id, usuario_id, pago_id))
            
            return True, "Inscripción exitosa"
    
    def marcar_asistencia(self, usuario_id, asistio=True):
        """Marca la asistencia de un usuario."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE inscripciones_eventos
                SET asistio = %s
                WHERE evento_id = %s AND usuario_id = %s
            """, (asistio, self.id, usuario_id))
    
    def save(self):
        """Guarda o actualiza el evento en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE eventos
                    SET titulo = %s,
                        descripcion = %s,
                        tipo = %s,
                        fecha_inicio = %s,
                        fecha_fin = %s,
                        lugar = %s,
                        capacidad_maxima = %s,
                        es_gratuito = %s,
                        precio = %s,
                        imagen_promocional_url = %s,
                        activo = %s
                    WHERE id = %s
                """, (
                    self.titulo, self.descripcion, self.tipo,
                    self.fecha_inicio, self.fecha_fin, self.lugar,
                    self.capacidad_maxima, self.es_gratuito, self.precio,
                    self.imagen_promocional_url, self.activo, self.id
                ))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO eventos (
                        publicado_por, titulo, descripcion, tipo,
                        fecha_inicio, fecha_fin, lugar, capacidad_maxima,
                        es_gratuito, precio, imagen_promocional_url, activo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    self.publicado_por, self.titulo, self.descripcion, self.tipo,
                    self.fecha_inicio, self.fecha_fin, self.lugar,
                    self.capacidad_maxima, self.es_gratuito, self.precio,
                    self.imagen_promocional_url, self.activo
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'lugar': self.lugar,
            'capacidad_maxima': self.capacidad_maxima,
            'es_gratuito': self.es_gratuito,
            'precio': float(self.precio) if self.precio else None,
            'activo': self.activo,
            'inscritos': self.contar_inscritos(),
            'porcentaje_cupo': self.porcentaje_cupo()
        }