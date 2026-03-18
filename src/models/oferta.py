"""
Modelo de Oferta Laboral para el sistema.
Representa una oferta de trabajo publicada por una empresa.
"""
from datetime import datetime, date
from src.utils.database import get_db_cursor

class Oferta:
    """Clase que representa una oferta laboral."""
    
    def __init__(self, id=None, empresa_id=None, publicado_por=None,
                 egresado_propietario_id=None,
                 titulo=None, descripcion=None, requisitos=None,
                 tipo=None, modalidad=None, ubicacion=None,
                 salario_min=None, salario_max=None,
                 fecha_publicacion=None, fecha_limite_postulacion=None,
                 activa=True, carrera_objetivo=None):
        self.id = id
        self.empresa_id = empresa_id
        self.publicado_por = publicado_por
        self.egresado_propietario_id = egresado_propietario_id
        self.titulo = titulo
        self.descripcion = descripcion
        self.requisitos = requisitos
        self.tipo = tipo
        self.modalidad = modalidad
        self.ubicacion = ubicacion
        self.salario_min = salario_min
        self.salario_max = salario_max
        self.fecha_publicacion = fecha_publicacion or datetime.now()
        self.fecha_limite_postulacion = fecha_limite_postulacion
        self.activa = activa
        self.carrera_objetivo = carrera_objetivo or []
    
    @classmethod
    def get_by_id(cls, oferta_id):
        """Obtiene una oferta por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM ofertas WHERE id = %s", (oferta_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_activas(cls, limit=50):
        """Obtiene las ofertas activas."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM ofertas
                WHERE activa = true
                AND fecha_limite_postulacion >= CURRENT_DATE
                ORDER BY fecha_publicacion DESC
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    @classmethod
    def get_by_empresa(cls, empresa_id, activas_only=False):
        """Obtiene ofertas de una empresa específica."""
        query = "SELECT * FROM ofertas WHERE empresa_id = %s"
        params = [empresa_id]
        
        if activas_only:
            query += " AND activa = true"
        
        query += " ORDER BY fecha_publicacion DESC"
        
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    def get_postulaciones(self, estado=None):
        """Obtiene las postulaciones a esta oferta."""
        from .postulacion import Postulacion
        query = "SELECT * FROM postulaciones WHERE oferta_id = %s"
        params = [self.id]
        
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        
        query += " ORDER BY fecha_postulacion DESC"
        
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [Postulacion(**dict(zip(columns, row))) for row in cur.fetchall()]
    
    def get_estadisticas(self):
        """Obtiene estadísticas de la oferta."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE estado = 'recibido') as recibidos,
                    COUNT(*) FILTER (WHERE estado = 'en_revision') as revision,
                    COUNT(*) FILTER (WHERE estado = 'entrevista') as entrevistas,
                    COUNT(*) FILTER (WHERE estado = 'seleccionado') as seleccionados,
                    COUNT(*) FILTER (WHERE estado = 'descartado') as descartados
                FROM postulaciones
                WHERE oferta_id = %s
            """, (self.id,))
            
            row = cur.fetchone()
            if row:
                return {
                    'total': row[0],
                    'recibidos': row[1],
                    'en_revision': row[2],
                    'entrevista': row[3],
                    'seleccionado': row[4],
                    'descartado': row[5]
                }
            return {}
    
    def cerrar(self):
        """Cierra la oferta (desactiva)."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE ofertas SET activa = false WHERE id = %s", (self.id,))
            self.activa = False
    
    def esta_activa(self):
        """Verifica si la oferta está activa y vigente."""
        return (self.activa and 
                self.fecha_limite_postulacion >= date.today())
    
    def dias_restantes(self):
        """Calcula los días restantes para postular."""
        if not self.fecha_limite_postulacion:
            return 0
        return (self.fecha_limite_postulacion - date.today()).days
    
    def save(self):
        """Guarda o actualiza la oferta en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE ofertas
                    SET titulo = %s,
                        descripcion = %s,
                        requisitos = %s,
                        tipo = %s,
                        modalidad = %s,
                        ubicacion = %s,
                        salario_min = %s,
                        salario_max = %s,
                        fecha_limite_postulacion = %s,
                        activa = %s,
                        carrera_objetivo = %s,
                        egresado_propietario_id = %s
                    WHERE id = %s
                """, (
                    self.titulo, self.descripcion, self.requisitos,
                    self.tipo, self.modalidad, self.ubicacion,
                    self.salario_min, self.salario_max,
                    self.fecha_limite_postulacion, self.activa,
                    self.carrera_objetivo, self.egresado_propietario_id, self.id
                ))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO ofertas (
                        empresa_id, publicado_por, egresado_propietario_id,
                        titulo, descripcion, requisitos, tipo, modalidad,
                        ubicacion, salario_min, salario_max,
                        fecha_limite_postulacion, carrera_objetivo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    self.empresa_id, self.publicado_por, self.egresado_propietario_id,
                    self.titulo, self.descripcion, self.requisitos,
                    self.tipo, self.modalidad, self.ubicacion,
                    self.salario_min, self.salario_max,
                    self.fecha_limite_postulacion, self.carrera_objetivo
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'empresa_id': str(self.empresa_id) if self.empresa_id else None,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'requisitos': self.requisitos,
            'tipo': self.tipo,
            'modalidad': self.modalidad,
            'ubicacion': self.ubicacion,
            'salario_min': float(self.salario_min) if self.salario_min else None,
            'salario_max': float(self.salario_max) if self.salario_max else None,
            'fecha_publicacion': self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
            'fecha_limite_postulacion': self.fecha_limite_postulacion.isoformat() if self.fecha_limite_postulacion else None,
            'activa': self.activa,
            'carrera_objetivo': self.carrera_objetivo,
            'dias_restantes': self.dias_restantes()
        }