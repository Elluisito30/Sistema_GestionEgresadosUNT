"""
Modelo de Empleador para el sistema.
Representa un usuario que trabaja para una empresa.
"""
from datetime import datetime
from src.utils.database import get_db_cursor
from .user import User
from .empresa import Empresa

class Empleador:
    """Clase que representa un empleador (usuario de empresa)."""
    
    def __init__(self, id=None, usuario_id=None, empresa_id=None,
                 nombres=None, apellidos=None, cargo=None,
                 telefono=None, es_administrador_empresa=False):
        self.id = id
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id
        self.nombres = nombres
        self.apellidos = apellidos
        self.cargo = cargo
        self.telefono = telefono
        self.es_administrador_empresa = es_administrador_empresa
        self._user = None
        self._empresa = None
    
    @property
    def user(self):
        """Obtiene el usuario asociado."""
        if not self._user and self.usuario_id:
            self._user = User.get_by_id(self.usuario_id)
        return self._user
    
    @property
    def empresa(self):
        """Obtiene la empresa asociada."""
        if not self._empresa and self.empresa_id:
            self._empresa = Empresa.get_by_id(self.empresa_id)
        return self._empresa
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleador."""
        return f"{self.nombres} {self.apellidos}"
    
    @classmethod
    def get_by_usuario_id(cls, usuario_id):
        """Obtiene un empleador por ID de usuario."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM empleadores WHERE usuario_id = %s", (usuario_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_id(cls, empleador_id):
        """Obtiene un empleador por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM empleadores WHERE id = %s", (empleador_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_empresa(cls, empresa_id):
        """Obtiene todos los empleadores de una empresa."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM empleadores WHERE empresa_id = %s", (empresa_id,))
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    def get_ofertas_publicadas(self, limit=10):
        """Obtiene las ofertas publicadas por este empleador."""
        from .oferta import Oferta
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id FROM ofertas
                WHERE publicado_por = %s
                ORDER BY fecha_publicacion DESC
                LIMIT %s
            ``, (self.id, limit))
            
            return [Oferta.get_by_id(row[0]) for row in cur.fetchall()]
    
    def get_postulaciones_pendientes(self):
        """Obtiene las postulaciones pendientes de revisión."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.*
                FROM postulaciones p
                JOIN ofertas o ON p.oferta_id = o.id
                WHERE o.publicado_por = %s
                AND p.estado = 'recibido'
                ORDER BY p.fecha_postulacion ASC
            ``, (self.id,))
            
            from .postulacion import Postulacion
            columns = [desc[0] for desc in cur.description]
            return [Postulacion(**dict(zip(columns, row))) for row in cur.fetchall()]
    
    def puede_publicar_ofertas(self):
        """Verifica si el empleador puede publicar ofertas."""
        return self.empresa and self.empresa.estado == 'activa'
    
    def save(self):
        """Guarda o actualiza el empleador en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE empleadores
                    SET nombres = %s,
                        apellidos = %s,
                        cargo = %s,
                        telefono = %s,
                        es_administrador_empresa = %s
                    WHERE id = %s
                ``, (
                    self.nombres, self.apellidos, self.cargo,
                    self.telefono, self.es_administrador_empresa, self.id
                ))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO empleadores (
                        usuario_id, empresa_id, nombres, apellidos,
                        cargo, telefono, es_administrador_empresa
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ``, (
                    self.usuario_id, self.empresa_id, self.nombres,
                    self.apellidos, self.cargo, self.telefono,
                    self.es_administrador_empresa
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'usuario_id': str(self.usuario_id) if self.usuario_id else None,
            'empresa_id': str(self.empresa_id) if self.empresa_id else None,
            'nombre_completo': self.nombre_completo,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'cargo': self.cargo,
            'telefono': self.telefono,
            'es_administrador_empresa': self.es_administrador_empresa
        }