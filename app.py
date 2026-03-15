import streamlit as st
from src.auth import login_usuario, logout_usuario, validar_correo_unt
from src.utils.session import init_session_state, render_notifications
from src.pages import dashboard

st.set_page_config(
    page_title="Sistema de Egresados UNT",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

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
    dashboard.show()