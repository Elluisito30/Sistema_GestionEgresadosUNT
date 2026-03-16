"""
Modelo de Empleador para el sistema.
Representa un usuario que trabaja para una empresa.
"""
from datetime import datetime
import logging
from src.utils.database import get_db_cursor
from .user import User
from .empresa import Empresa

logger = logging.getLogger(__name__)

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
            """, (self.id, limit))
            
            return [Oferta.get_by_id(row[0]) for row in cur.fetchall()]
    
    def get_postulaciones_pendientes(self):
        """Obtiene las postulaciones pendientes de revisión."""
        from .postulacion import Postulacion
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.*
                FROM postulaciones p
                JOIN ofertas o ON p.oferta_id = o.id
                WHERE o.publicado_por = %s
                AND p.estado = 'recibido'
                ORDER BY p.fecha_postulacion ASC
            """, (self.id,))
            columns = [desc[0] for desc in cur.description]
            return [Postulacion(**dict(zip(columns, row))) for row in cur.fetchall()]

    @classmethod
    def listar_detallado_por_empresa(cls, empresa_id):
        """
        Lista empleadores de una empresa incluyendo datos del usuario (email, fecha_registro).
        Devuelve una lista de diccionarios.
        """
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        em.id,
                        em.usuario_id,
                        em.empresa_id,
                        em.nombres,
                        em.apellidos,
                        em.cargo,
                        em.telefono,
                        em.es_administrador_empresa,
                        u.email,
                        u.fecha_registro,
                        u.activo
                    FROM empleadores em
                    JOIN usuarios u ON em.usuario_id = u.id
                    WHERE em.empresa_id = %s
                    ORDER BY em.es_administrador_empresa DESC, em.apellidos ASC, em.nombres ASC
                    """,
                    (empresa_id,),
                )
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            logger.exception("Error listando empleadores detallados empresa_id=%s", empresa_id)
            return []

    @classmethod
    def vincular_usuario_existente(
        cls,
        email,
        empresa_id,
        nombres,
        apellidos,
        cargo=None,
        telefono=None,
        es_administrador_empresa=False,
    ):
        """
        Vincula un usuario EXISTENTE (por email) como empleador de una empresa.
        No crea usuarios nuevos, para no interferir con autenticación/contraseñas.

        Retorna: (ok: bool, msg: str, empleador: Empleador|None)
        """
        try:
            email = (email or "").strip()
            if not email or not empresa_id or not nombres or not apellidos:
                return False, "Email, empresa, nombres y apellidos son obligatorios.", None

            user = User.get_by_email(email)
            if not user:
                return False, "No existe un usuario con ese email. Debe registrarse primero.", None

            # Evitar duplicados / conflictos
            existing = cls.get_by_usuario_id(user.id)
            if existing and existing.empresa_id == empresa_id:
                return False, "El usuario ya está vinculado como empleador a esta empresa.", existing
            if existing and existing.empresa_id != empresa_id:
                return (
                    False,
                    "El usuario ya está vinculado a otra empresa. No se puede vincular en paralelo.",
                    existing,
                )

            nuevo = cls(
                usuario_id=user.id,
                empresa_id=empresa_id,
                nombres=nombres,
                apellidos=apellidos,
                cargo=cargo,
                telefono=telefono,
                es_administrador_empresa=bool(es_administrador_empresa),
            )
            ok, msg = nuevo.save()
            if ok:
                return True, "Empleador vinculado correctamente.", nuevo
            return False, msg, None
        except Exception as e:
            logger.exception("Error vinculando empleador email=%s empresa_id=%s", email, empresa_id)
            return False, f"Error al vincular empleador: {str(e)}", None

    def actualizar_cargo_y_admin(self, cargo=None, es_administrador_empresa=None, telefono=None):
        """
        Actualiza campos permitidos del empleador.
        Retorna (ok, msg).
        """
        try:
            if cargo is not None:
                self.cargo = cargo
            if telefono is not None:
                self.telefono = telefono
            if es_administrador_empresa is not None:
                self.es_administrador_empresa = bool(es_administrador_empresa)
            return self.save()
        except Exception as e:
            logger.exception("Error actualizando empleador_id=%s", self.id)
            return False, f"Error al actualizar empleador: {str(e)}"
    
    def puede_publicar_ofertas(self):
        """Verifica si el empleador puede publicar ofertas (la empresa debe estar activa)."""
        return self.empresa and self.empresa.estado == 'activa'
    
    def save(self):
        """Guarda o actualiza el empleador en la base de datos."""
        try:
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
                    """, (
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
                    """, (
                        self.usuario_id, self.empresa_id, self.nombres,
                        self.apellidos, self.cargo, self.telefono,
                        self.es_administrador_empresa
                    ))
                    self.id = cur.fetchone()[0]
            return True, "Empleador guardado correctamente."
        except Exception as e:
            return False, f"Error al guardar el empleador: {str(e)}"
    
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
