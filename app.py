import streamlit as st
from src.auth import login_usuario, logout_usuario, validar_correo_unt
from src.utils.session import init_session_state
from src.pages import dashboard

# Configuración de la página (debe ser el primer comando de Streamlit)
st.set_page_config(
    page_title="Sistema de Egresados UNT",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# Inicializar el estado de la sesión
init_session_state()

# CSS Personalizado para un diseño más limpio
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

# Lógica de Login / Router
if not st.session_state.get('authenticated', False):
    # --- PANTALLA DE LOGIN ---
    st.title("🎓 Sistema de Gestión de Egresados y Oferta Laboral - UNT")
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
        # Enlaces para recuperar contraseña o registrarse (a implementar)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Registrarse como Egresado"):
                st.info("Funcionalidad de registro próximamente.")
        with col_b:
            if st.button("¿Olvidó su contraseña?"):
                st.info("Funcionalidad de recuperación próximamente.")

else:
    # --- USUARIO AUTENTICADO ---
    # El router: muestra el dashboard y la barra lateral con el menú contextual
    dashboard.show()