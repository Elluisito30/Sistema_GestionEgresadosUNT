"""
Modelo de Egresado para el sistema.
Extiende la funcionalidad del usuario con datos específicos de egresados.
"""
from datetime import datetime
from src.utils.database import get_db_cursor
from .user import User

class Egresado:
    """Clase que representa un egresado de la UNT."""
    
    def __init__(self, id=None, usuario_id=None, nombres=None, 
                 apellido_paterno=None, apellido_materno=None, dni=None,
                 fecha_nacimiento=None, telefono=None, direccion=None,
                 carrera_principal=None, facultad=None, anio_egreso=None,
                 url_cv=None, perfil_publico=False, foto_perfil_url=None,
                 fecha_actualizacion=None):
        self.id = id
        self.usuario_id = usuario_id
        self.nombres = nombres
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno
        self.dni = dni
        self.fecha_nacimiento = fecha_nacimiento
        self.telefono = telefono
        self.direccion = direccion
        self.carrera_principal = carrera_principal
        self.facultad = facultad
        self.anio_egreso = anio_egreso
        self.url_cv = url_cv
        self.perfil_publico = perfil_publico
        self.foto_perfil_url = foto_perfil_url
        self.fecha_actualizacion = fecha_actualizacion or datetime.now()
        self._user = None
    
    @property
    def user(self):
        """Obtiene el usuario asociado."""
        if not self._user and self.usuario_id:
            self._user = User.get_by_id(self.usuario_id)
        return self._user
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del egresado."""
        partes = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return ' '.join(partes)
    
    @classmethod
    def get_by_usuario_id(cls, usuario_id):
        """Obtiene un egresado por ID de usuario."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM egresados WHERE usuario_id = %s", (usuario_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_id(cls, egresado_id):
        """Obtiene un egresado por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM egresados WHERE id = %s", (egresado_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_dni(cls, dni):
        """Obtiene un egresado por su DNI."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM egresados WHERE dni = %s", (dni,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    def get_historial_laboral(self):
        """Obtiene el historial laboral del egresado."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM historial_laboral
                WHERE egresado_id = %s
                ORDER BY fecha_inicio DESC
            """, (self.id,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_educacion_continua(self):
        """Obtiene la educación continua del egresado."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM educacion_continua
                WHERE egresado_id = %s
                ORDER BY fecha_fin DESC
            """, (self.id,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_postulaciones(self, limit=10):
        """Obtiene las postulaciones del egresado."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.*, o.titulo as oferta_titulo, e.razon_social as empresa
                FROM postulaciones p
                JOIN ofertas o ON p.oferta_id = o.id
                JOIN empresas e ON o.empresa_id = e.id
                WHERE p.egresado_id = %s
                ORDER BY p.fecha_postulacion DESC
                LIMIT %s
            """, (self.id, limit))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_eventos_inscritos(self):
        """Obtiene los eventos a los que está inscrito."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT e.*, i.fecha_inscripcion, i.asistio
                FROM eventos e
                JOIN inscripciones_eventos i ON e.id = i.evento_id
                WHERE i.usuario_id = %s
                ORDER BY e.fecha_inicio DESC
            ``, (self.usuario_id,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_estadisticas(self):
        """Obtiene estadísticas del egresado."""
        with get_db_cursor() as cur:
            # Total postulaciones
            cur.execute("""
                SELECT 
                    COUNT(*) as total_postulaciones,
                    COUNT(*) FILTER (WHERE estado = 'seleccionado') as seleccionados,
                    COUNT(*) FILTER (WHERE estado = 'entrevista') as entrevistas
                FROM postulaciones
                WHERE egresado_id = %s
            ``, (self.id,))
            
            stats = cur.fetchone()
            
            # Tasa de éxito
            if stats and stats[0] > 0:
                tasa_exito = (stats[1] / stats[0]) * 100
            else:
                tasa_exito = 0
            
            return {
                'total_postulaciones': stats[0] if stats else 0,
                'seleccionados': stats[1] if stats else 0,
                'entrevistas': stats[2] if stats else 0,
                'tasa_exito': round(tasa_exito, 2)
            }
    
    def calcular_completitud_perfil(self):
        """Calcula el porcentaje de completitud del perfil."""
        campos = [
            self.nombres, self.apellido_paterno, self.dni,
            self.fecha_nacimiento, self.telefono, self.direccion,
            self.carrera_principal, self.facultad, self.anio_egreso
        ]
        
        completados = sum(1 for campo in campos if campo)
        return (completados / len(campos)) * 100
    
    def save(self):
        """Guarda o actualiza el egresado en la base de datos."""
        if self.id:
            # Actualizar
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE egresados
                    SET nombres = %s,
                        apellido_paterno = %s,
                        apellido_materno = %s,
                        fecha_nacimiento = %s,
                        telefono = %s,
                        direccion = %s,
                        carrera_principal = %s,
                        facultad = %s,
                        anio_egreso = %s,
                        url_cv = %s,
                        perfil_publico = %s,
                        foto_perfil_url = %s,
                        fecha_actualizacion = NOW()
                    WHERE id = %s
                ``, (
                    self.nombres, self.apellido_paterno, self.apellido_materno,
                    self.fecha_nacimiento, self.telefono, self.direccion,
                    self.carrera_principal, self.facultad, self.anio_egreso,
                    self.url_cv, self.perfil_publico, self.foto_perfil_url,
                    self.id
                ))
        else:
            # Crear nuevo
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO egresados (
                        usuario_id, nombres, apellido_paterno, apellido_materno,
                        dni, fecha_nacimiento, telefono, direccion,
                        carrera_principal, facultad, anio_egreso, perfil_publico
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ``, (
                    self.usuario_id, self.nombres, self.apellido_paterno,
                    self.apellido_materno, self.dni, self.fecha_nacimiento,
                    self.telefono, self.direccion, self.carrera_principal,
                    self.facultad, self.anio_egreso, self.perfil_publico
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'usuario_id': str(self.usuario_id) if self.usuario_id else None,
            'nombre_completo': self.nombre_completo,
            'nombres': self.nombres,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'dni': self.dni,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'carrera_principal': self.carrera_principal,
            'facultad': self.facultad,
            'anio_egreso': self.anio_egreso,
            'url_cv': self.url_cv,
            'perfil_publico': self.perfil_publico,
            'foto_perfil_url': self.foto_perfil_url,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }