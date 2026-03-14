import bcrypt
import streamlit as st
from src.utils.database import get_db_cursor
from src.config import SECRET_KEY  # Aunque no lo usamos directamente para hash aquí
import re
from email_validator import validate_email, EmailNotValidError

def hash_password(password):
    """Genera un hash seguro de la contraseña."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verifica si la contraseña coincide con el hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validar_correo_unt(email):
    """Valida que el correo sea del dominio institucional (ej. @unitru.edu.pe)."""
    try:
        validation = validate_email(email, check_deliverability=False)
        email = validation.email
        if not email.endswith('@unitru.edu.pe'): # Ajustar al dominio real
            return False, "El correo debe ser del dominio @unitru.edu.pe"
        return True, email
    except EmailNotValidError as e:
        return False, str(e)

def login_usuario(email, password):
    """Autentica un usuario y retorna sus datos si es exitoso."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, email, password_hash, rol, activo
            FROM usuarios
            WHERE email = %s
        """, (email,))
        user = cur.fetchone()

    if user:
        user_id, db_email, db_password_hash, rol, activo = user
        if not activo:
            return None, "Usuario inactivo. Contacte al administrador."
        if verify_password(password, db_password_hash):
            # Registrar en bitácora
            registrar_en_bitacora(user_id, rol, 'LOGIN', 'autenticacion', 'Login exitoso')
            # Actualizar último acceso
            with get_db_cursor(commit=True) as cur:
                cur.execute("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s", (user_id,))
            return {"id": user_id, "email": db_email, "rol": rol}, None
        else:
            registrar_en_bitacora(None, None, 'LOGIN_FALLIDO', 'autenticacion', f'Intento fallido para {email}')
            return None, "Contraseña incorrecta."
    else:
        registrar_en_bitacora(None, None, 'LOGIN_FALLIDO', 'autenticacion', f'Intento fallido para email no existente: {email}')
        return None, "Usuario no encontrado."

def registrar_en_bitacora(usuario_id, perfil, accion, modulo, detalle):
    """Función helper para registrar acciones en la bitácora."""
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO bitacora_auditoria
                (usuario_id, perfil_utilizado, accion, modulo, detalle, direccion_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (usuario_id, perfil, accion, modulo, detalle, st.query_params.get('ip', 'desconocida')))
    except Exception as e:
        # No detener la app si falla la bitácora, solo loguear
        print(f"Error al registrar en bitácora: {e}")

def logout_usuario():
    """Cierra la sesión del usuario."""
    if 'user' in st.session_state:
        registrar_en_bitacora(
            st.session_state.user['id'],
            st.session_state.user['rol'],
            'LOGOUT',
            'autenticacion',
            'Logout exitoso'
        )
    # Limpiar el estado de sesión
    for key in ['user', 'authenticated']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()