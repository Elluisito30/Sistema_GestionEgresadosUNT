"""
Utilidades para la gestión del estado de sesión en Streamlit.
Proporciona funciones para inicializar y manejar la sesión del usuario.
"""
import streamlit as st
from datetime import datetime

def init_session_state():
    """
    Inicializa todas las variables de estado de sesión necesarias.
    Debe llamarse al inicio de la aplicación.
    """
    # Variables de autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Variables de UI/UX
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    # Variables de filtros y búsqueda (persistentes durante la sesión)
    if 'filters' not in st.session_state:
        st.session_state.filters = {}
    
    # Datos temporales para formularios multi-paso
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    
    # Última actividad del usuario
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()

def check_session_timeout(max_minutes=30):
    """
    Verifica si la sesión ha expirado por inactividad.
    
    Args:
        max_minutes (int): Tiempo máximo de inactividad en minutos
    
    Returns:
        bool: True si la sesión es válida, False si expiró
    """
    if not st.session_state.authenticated:
        return False
    
    last_activity = st.session_state.get('last_activity', datetime.now())
    time_diff = (datetime.now() - last_activity).total_seconds() / 60
    
    if time_diff > max_minutes:
        # Sesión expirada
        st.session_state.authenticated = False
        st.session_state.user = None
        return False
    
    # Actualizar última actividad
    st.session_state.last_activity = datetime.now()
    return True

def set_current_page(page_name):
    """
    Establece la página actual en la sesión.
    
    Args:
        page_name (str): Nombre de la página
    """
    st.session_state.current_page = page_name

def get_current_page():
    """
    Obtiene la página actual de la sesión.
    
    Returns:
        str: Nombre de la página actual
    """
    return st.session_state.get('current_page', 'dashboard')

def add_notification(message, type="info"):
    """
    Añade una notificación a la sesión del usuario.
    
    Args:
        message (str): Mensaje de la notificación
        type (str): Tipo de notificación (info, success, warning, error)
    """
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    st.session_state.notifications.append({
        'message': message,
        'type': type,
        'timestamp': datetime.now()
    })

def clear_notifications():
    """Limpia todas las notificaciones de la sesión."""
    st.session_state.notifications = []

def save_form_data(key, data):
    """
    Guarda datos de formulario en la sesión.
    
    Args:
        key (str): Clave para identificar los datos
        data (dict): Datos a guardar
    """
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    
    st.session_state.form_data[key] = data

def get_form_data(key, default=None):
    """
    Recupera datos de formulario de la sesión.
    
    Args:
        key (str): Clave de los datos
        default: Valor por defecto si no existe
    
    Returns:
        dict: Datos guardados o valor por defecto
    """
    return st.session_state.form_data.get(key, default)

def clear_form_data(key=None):
    """
    Limpia datos de formulario.
    
    Args:
        key (str, optional): Clave específica a limpiar. Si es None, limpia todos.
    """
    if key:
        if key in st.session_state.form_data:
            del st.session_state.form_data[key]
    else:
        st.session_state.form_data = {}

def set_filter(key, value):
    """
    Establece un filtro en la sesión.
    
    Args:
        key (str): Nombre del filtro
        value: Valor del filtro
    """
    if 'filters' not in st.session_state:
        st.session_state.filters = {}
    
    st.session_state.filters[key] = value

def get_filter(key, default=None):
    """
    Obtiene un filtro de la sesión.
    
    Args:
        key (str): Nombre del filtro
        default: Valor por defecto si no existe
    
    Returns:
        Valor del filtro o default
    """
    return st.session_state.filters.get(key, default)

def clear_filters():
    """Limpia todos los filtros de la sesión."""
    st.session_state.filters = {}