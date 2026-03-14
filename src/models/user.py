"""
Modelo de Usuario para el sistema.
Maneja la autenticación y datos básicos de usuarios.
"""
from datetime import datetime
from src.utils.database import get_db_cursor
from src.auth import hash_password, verify_password

class User:
    """Clase que representa un usuario del sistema."""
    
    def __init__(self, id=None, email=None, rol=None, 
                 email_confirmado=False, activo=True, 
                 fecha_registro=None, ultimo_acceso=None):
        self.id = id
        self.email = email
        self.rol = rol
        self.email_confirmado = email_confirmado
        self.activo = activo
        self.fecha_registro = fecha_registro or datetime.now()
        self.ultimo_acceso = ultimo_acceso
    
    @classmethod
    def get_by_id(cls, user_id):
        """Obtiene un usuario por su ID."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, email, rol, email_confirmado, activo, 
                       fecha_registro, ultimo_acceso
                FROM usuarios
                WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_email(cls, email):
        """Obtiene un usuario por su email."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, email, rol, email_confirmado, activo, 
                       fecha_registro, ultimo_acceso
                FROM usuarios
                WHERE email = %s
            """, (email,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    def authenticate(self, password):
        """Verifica la contraseña del usuario."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT password_hash FROM usuarios WHERE id = %s
            """, (self.id,))
            row = cur.fetchone()
            
            if row and verify_password(password, row[0]):
                self.update_last_access()
                return True
            return False
    
    def update_last_access(self):
        """Actualiza la fecha de último acceso."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE usuarios
                SET ultimo_acceso = NOW()
                WHERE id = %s
            """, (self.id,))
    
    def change_password(self, old_password, new_password):
        """Cambia la contraseña del usuario."""
        if not self.authenticate(old_password):
            return False, "Contraseña actual incorrecta"
        
        new_hash = hash_password(new_password)
        
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE usuarios
                SET password_hash = %s
                WHERE id = %s
            """, (new_hash, self.id))
        
        return True, "Contraseña actualizada exitosamente"
    
    def save(self):
        """Guarda o actualiza el usuario en la base de datos."""
        if self.id:
            # Actualizar
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE usuarios
                    SET email = %s,
                        email_confirmado = %s,
                        activo = %s
                    WHERE id = %s
                """, (self.email, self.email_confirmado, self.activo, self.id))
        else:
            # Crear nuevo
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO usuarios (email, rol, email_confirmado, activo)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (self.email, self.rol, self.email_confirmado, self.activo))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'email': self.email,
            'rol': self.rol,
            'email_confirmado': self.email_confirmado,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None
        }