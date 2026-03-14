"""
Decoradores para control de acceso y validaciones.
"""
import streamlit as st
from functools import wraps
from typing import Callable, List
from src.utils.session import add_notification

def login_required(func: Callable):
    """
    Decorador que verifica que el usuario esté autenticado.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get('authenticated', False):
            st.warning("Debes iniciar sesión para acceder a esta página")
            st.switch_page("app.py")
            return
        return func(*args, **kwargs)
    return wrapper

def role_required(allowed_roles: List[str]):
    """
    Decorador que verifica que el usuario tenga un rol permitido.
    
    Args:
        allowed_roles: Lista de roles permitidos
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False):
                st.warning("Debes iniciar sesión")
                st.switch_page("app.py")
                return
            
            user_role = st.session_state.user.get('rol')
            if user_role not in allowed_roles:
                st.error("No tienes permisos para acceder a esta página")
                st.switch_page("src/pages/dashboard.py")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(func: Callable):
    """
    Decorador específico para administradores.
    """
    return role_required(['administrador'])(func)

def empleador_required(func: Callable):
    """
    Decorador específico para empleadores.
    """
    return role_required(['administrador', 'empleador'])(func)

def egresado_required(func: Callable):
    """
    Decorador específico para egresados.
    """
    return role_required(['administrador', 'egresado'])(func)

def validate_form(validation_func: Callable):
    """
    Decorador para validar formularios.
    
    Args:
        validation_func: Función de validación que retorna (bool, dict_errores)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener datos del formulario del session_state
            form_data = st.session_state.get('form_data', {})
            
            # Validar
            is_valid, errors = validation_func(form_data)
            
            if not is_valid:
                for field, error in errors.items():
                    st.error(f"{field}: {error}")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def handle_errors(error_message: str = "Ha ocurrido un error"):
    """
    Decorador para manejar excepciones de manera uniforme.
    
    Args:
        error_message: Mensaje de error por defecto
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                add_notification(f"{error_message}: {str(e)}", "error")
                st.exception(e)
                return None
        return wrapper
    return decorator

def log_action(action: str):
    """
    Decorador para registrar acciones en bitácora.
    
    Args:
        action: Nombre de la acción a registrar
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from src.auth import registrar_en_bitacora
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Registrar en bitácora
            if st.session_state.get('authenticated'):
                user = st.session_state.user
                registrar_en_bitacora(
                    usuario_id=user.get('id'),
                    perfil=user.get('rol'),
                    accion=action,
                    modulo=func.__module__,
                    detalle=f"Ejecutó {func.__name__}"
                )
            
            return result
        return wrapper
    return decorator

def rate_limit(max_calls: int = 10, period: int = 60):
    """
    Decorador para limitar la tasa de llamadas.
    
    Args:
        max_calls: Número máximo de llamadas permitidas
        period: Período de tiempo en segundos
    """
    def decorator(func: Callable):
        from collections import deque
        from time import time
        
        calls = deque()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time()
            
            # Limpiar llamadas antiguas
            while calls and calls[0] < now - period:
                calls.popleft()
            
            # Verificar límite
            if len(calls) >= max_calls:
                add_notification(f"Demasiadas solicitudes. Espera {period} segundos.", "warning")
                return None
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator