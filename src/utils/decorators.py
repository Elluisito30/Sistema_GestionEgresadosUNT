"""
Decoradores para control de acceso y validaciones.
"""
import streamlit as st
from functools import wraps
from typing import Callable, List, Optional
from src.utils.session import add_notification

def login_required(func: Callable):
    """
    Decorador que asegura que el usuario esté autenticado.
    Si no lo está, redirige o muestra un error.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in st.session_state or st.session_state.user is None:
            st.warning("Debes iniciar sesión para acceder a esta página.")
            if st.button("Ir al Login"):
                st.session_state.authenticated = False
                st.rerun()
            return None
        return func(*args, **kwargs)
    return wrapper

def role_required(roles: List[str]):
    """
    Decorador para restringir el acceso basado en el rol del usuario.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user' not in st.session_state:
                st.error("Acceso denegado. No se encontró sesión.")
                return None
            
            user_role = st.session_state.user.get('rol')
            if user_role not in roles:
                st.error(f"Acceso restringido. Tu rol '{user_role}' no tiene permisos para esta sección.")
                return None
                
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_permission(permission: str):
    """
    Decorador (opcional) para granularidad fina si se implementa un sistema de permisos.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Lógica de permisos aquí
            return func(*args, **kwargs)
        return wrapper
    return decorator
