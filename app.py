import streamlit as st
import importlib
from src.auth import login_usuario, logout_usuario, validar_correo_unt
from src.utils.session import init_session_state, render_notifications
from src.pages import dashboard

def load_page(page_name):
    """Carga dinámicamente el módulo desde src.pages."""
    if page_name == 'dashboard':
        dashboard.show()
        return

    module_name = f"src.pages.{page_name}"
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, 'show'):
            module.show()
        elif hasattr(module, 'page'):
            module.page()
        else:
            st.warning(f"La página '{page_name}' no provee una función 'show()' o 'page()'.")
    except ModuleNotFoundError:
        st.info(f"Página en construcción: {page_name}")
    except Exception as e:
        st.error(f"Error al cargar la página '{page_name}': {str(e)}")

st.set_page_config(
    page_title="Sistema de Egresados UNT",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

from src.utils.database import init_critical_tables
init_critical_tables()
init_session_state()
render_notifications()

st.markdown("""
    <style>
    [data-testid="stForm"] {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #0056b3;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #004494;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get('authenticated', False):
    # Título centrado
    st.markdown(
        "<h1 style='text-align: center;'>🎓 Sistema de Gestión de Egresados y Oferta Laboral - UNT</h1>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center;'>Acceso al Sistema</h3>", unsafe_allow_html=True)
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Por favor, complete todos los campos.")
                else:
                    user, error = login_usuario(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error(error)

        st.markdown("<br>", unsafe_allow_html=True)

        # Botón izquierdo + espacio + botón derecho alineado al extremo
        col_a, col_space, col_b = st.columns([1.2, 0.8, 1])
        with col_a:
            if st.button("Registrarse como Egresado", use_container_width=True):
                st.info("Funcionalidad de registro próximamente.")
        with col_b:
            if st.button("¿Olvidó su contraseña?", use_container_width=True):
                st.info("Funcionalidad de recuperación próximamente.")

else:
    with st.sidebar:
        # Logo de la universidad
        st.image("https://upload.wikimedia.org/wikipedia/commons/6/6e/Universidad_Nacional_de_Trujillo_-_Per%C3%BA_vector_logo.png", use_container_width=True)
        
        # Título decorativo
        st.markdown("<h2 style='text-align: center; color: #0056b3;'>🎓 Gestión UNT</h2>", unsafe_allow_html=True)
        st.markdown("---")

        # Información del usuario con estilo
        user = st.session_state.user
        rol = user['rol']
        st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                <p style='margin: 0; font-size: 0.9rem; color: #555;'>Usuario:</p>
                <p style='margin: 0; font-weight: bold;'>👤 {user['email']}</p>
                <p style='margin: 0; font-size: 0.9rem; color: #555; margin-top: 5px;'>Rol:</p>
                <p style='margin: 0; font-weight: bold;'>🛡️ {rol.capitalize()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🧭 Navegación")

        if rol == 'administrador':
            menu_options = {
                "🏠 Dashboard Principal": "dashboard",
                "👥 Egresados": "egresados_lista",
                "🏢 Empresas": "empresas_lista",
                "💼 Ofertas": "ofertas_admin",
                "📅 Eventos": "eventos_gestionar",
                "💰 Pagos": "pagos_admin",
                "📊 Reportes": "reportes_dashboard",
                "📝 Encuestas": "encuestas_disenar",
                "🔍 Consultas Avanzadas": "consultas_avanzadas",
                "📋 Bitácora": "auditoria_bitacora",
                "🔔 Notificaciones": "notificaciones_centro",
                "👤 Mi Perfil": "perfil_mi_cuenta"
            }
        elif rol == 'egresado':
            menu_options = {
                "🏠 Mi Dashboard": "dashboard",
                "👤 Mi Perfil": "egresados_mi_perfil",
                "💼 Buscar Ofertas": "ofertas_buscar",
                "📢 Mis Ofertas (Emprendedor)": "ofertas_gestionar",
                "📋 Mis Postulaciones": "postulaciones_seguimiento",
                "📅 Eventos": "eventos_calendario",
                "📄 Mis Pagos": "pagos_mis_vouchers",
                "📝 Encuestas Pendientes": "encuestas_responder",
                "🔔 Notificaciones": "notificaciones_centro"
            }
        elif rol == 'empleador':
            menu_options = {
                "🏠 Dashboard Empresa": "dashboard",
                "🏢 Mi Empresa": "empresa_perfil",
                "📢 Gestionar Ofertas": "ofertas_gestionar",
                "👥 Revisar Postulaciones": "postulaciones_revisar",
                "📅 Mis Eventos": "eventos_gestionar",
                "🔔 Notificaciones": "notificaciones_centro",
                "👤 Mi Perfil": "perfil_mi_cuenta"
            }
        else:
            menu_options = {"🏠 Dashboard": "dashboard"}

        menu_values = list(menu_options.values())
        current_page = st.session_state.get('current_page', 'dashboard')
        
        try:
            initial_index = menu_values.index(current_page) if current_page in menu_values else 0
        except ValueError:
            initial_index = 0

        selected_label = st.radio("Navegación", options=list(menu_options.keys()), index=initial_index, key="navigation_radio")
        selected_page = menu_options[selected_label]
        
        if selected_page != current_page:
            st.session_state.current_page = selected_page
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_usuario()
            st.rerun()

    # Carga dinámica de la página seleccionada
    load_page(st.session_state.current_page)