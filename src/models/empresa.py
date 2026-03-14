"""
Modelo de Empresa para el sistema.
Representa una empresa registrada en el sistema.
"""
from datetime import datetime
from src.utils.database import get_db_cursor

class Empresa:
    """Clase que representa una empresa."""
    
    def __init__(self, id=None, ruc=None, razon_social=None, 
                 nombre_comercial=None, sector_economico=None,
                 tamano_empresa=None, direccion=None, telefono_contacto=None,
                 email_contacto=None, sitio_web=None, estado='pendiente',
                 fecha_registro=None, fecha_aprobacion=None,
                 aprobado_por=None, logo_url=None):
        self.id = id
        self.ruc = ruc
        self.razon_social = razon_social
        self.nombre_comercial = nombre_comercial
        self.sector_economico = sector_economico
        self.tamano_empresa = tamano_empresa
        self.direccion = direccion
        self.telefono_contacto = telefono_contacto
        self.email_contacto = email_contacto
        self.sitio_web = sitio_web
        self.estado = estado
        self.fecha_registro = fecha_registro or datetime.now()
        self.fecha_aprobacion = fecha_aprobacion
        self.aprobado_por = aprobado_por
        self.logo_url = logo_url
    
    @classmethod
    def get_by_id(cls, empresa_id):
        """Obtiene una empresa por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM empresas WHERE id = %s", (empresa_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_ruc(cls, ruc):
        """Obtiene una empresa por su RUC."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM empresas WHERE ruc = %s", (ruc,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_pendientes(cls):
        """Obtiene todas las empresas pendientes de aprobación."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM empresas 
                WHERE estado = 'pendiente'
                ORDER BY fecha_registro ASC
            """)
            
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    def get_empleadores(self):
        """Obtiene todos los empleadores de la empresa."""
        from .empleador import Empleador
        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM empleadores WHERE empresa_id = %s", (self.id,))
            return [Empleador.get_by_id(row[0]) for row in cur.fetchall()]
    
    def get_ofertas(self, activas_only=False):
        """Obtiene las ofertas de la empresa."""
        from .oferta import Oferta
        query = "SELECT id FROM ofertas WHERE empresa_id = %s"
        params = [self.id]
        
        if activas_only:
            query += " AND activa = true"
        
        query += " ORDER BY fecha_publicacion DESC"
        
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return [Oferta.get_by_id(row[0]) for row in cur.fetchall()]
    
    def get_estadisticas(self):
        """Obtiene estadísticas de la empresa."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_ofertas,
                    COUNT(*) FILTER (WHERE activa) as ofertas_activas,
                    COUNT(DISTINCT p.id) as total_postulaciones,
                    COUNT(DISTINCT e.id) as total_empleadores
                FROM ofertas o
                LEFT JOIN postulaciones p ON o.id = p.oferta_id
                CROSS JOIN (
                    SELECT COUNT(*) as id FROM empleadores WHERE empresa_id = %s
                ) e
                WHERE o.empresa_id = %s
                GROUP BY e.id
            ``, (self.id, self.id))
            
            row = cur.fetchone()
            if row:
                return {
                    'total_ofertas': row[0] or 0,
                    'ofertas_activas': row[1] or 0,
                    'total_postulaciones': row[2] or 0,
                    'total_empleadores': row[3] or 0
                }
            return {
                'total_ofertas': 0,
                'ofertas_activas': 0,
                'total_postulaciones': 0,
                'total_empleadores': 0
            }
    
    def aprobar(self, admin_id):
        """Aprueba la empresa."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE empresas
                SET estado = 'activa',
                    fecha_aprobacion = NOW(),
                    aprobado_por = %s
                WHERE id = %s
            ``, (admin_id, self.id))
            self.estado = 'activa'
            self.fecha_aprobacion = datetime.now()
            self.aprobado_por = admin_id
        
        # Notificar a empleadores
        self.notificar_aprobacion()
    
    def rechazar(self, admin_id, motivo):
        """Rechaza la empresa."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE empresas
                SET estado = 'rechazada',
                    aprobado_por = %s
                WHERE id = %s
            ``, (admin_id, self.id))
            self.estado = 'rechazada'
            self.aprobado_por = admin_id
        
        # Notificar rechazo
        self.notificar_rechazo(motivo)
    
    def notificar_aprobacion(self):
        """Notifica a los empleadores sobre la aprobación."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                SELECT u.id, 'email', 'Empresa aprobada',
                       'Su empresa ha sido aprobada en el sistema'
                FROM empleadores e
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.empresa_id = %s
            ``, (self.id,))
    
    def notificar_rechazo(self, motivo):
        """Notifica a los empleadores sobre el rechazo."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                SELECT u.id, 'email', 'Empresa no aprobada',
                       'Su empresa no ha sido aprobada. Motivo: ' || %s
                FROM empleadores e
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.empresa_id = %s
            ``, (motivo, self.id))
    
    def save(self):
        """Guarda o actualiza la empresa en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE empresas
                    SET ruc = %s,
                        razon_social = %s,
                        nombre_comercial = %s,
                        sector_economico = %s,
                        tamano_empresa = %s,
                        direccion = %s,
                        telefono_contacto = %s,
                        email_contacto = %s,
                        sitio_web = %s,
                        logo_url = %s
                    WHERE id = %s
                ``, (
                    self.ruc, self.razon_social, self.nombre_comercial,
                    self.sector_economico, self.tamano_empresa, self.direccion,
                    self.telefono_contacto, self.email_contacto, self.sitio_web,
                    self.logo_url, self.id
                ))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO empresas (
                        ruc, razon_social, nombre_comercial, sector_economico,
                        tamano_empresa, direccion, telefono_contacto, email_contacto,
                        sitio_web, estado, logo_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ``, (
                    self.ruc, self.razon_social, self.nombre_comercial,
                    self.sector_economico, self.tamano_empresa, self.direccion,
                    self.telefono_contacto, self.email_contacto, self.sitio_web,
                    self.estado, self.logo_url
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'ruc': self.ruc,
            'razon_social': self.razon_social,
            'nombre_comercial': self.nombre_comercial,
            'sector_economico': self.sector_economico,
            'tamano_empresa': self.tamano_empresa,
            'direccion': self.direccion,
            'telefono_contacto': self.telefono_contacto,
            'email_contacto': self.email_contacto,
            'sitio_web': self.sitio_web,
            'estado': self.estado,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'fecha_aprobacion': self.fecha_aprobacion.isoformat() if self.fecha_aprobacion else None,
            'logo_url': self.logo_url
        }