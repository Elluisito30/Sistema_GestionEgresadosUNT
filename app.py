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

# Lógica de Login / Router
if not st.session_state.get('authenticated', False):
    # --- PANTALLA DE LOGIN ---
    st.title("🎓 Sistema de Gestión de Egresados y Oferta Laboral - UNT")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Correo Electrónico Institucional")
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

        st.markdown("---")
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