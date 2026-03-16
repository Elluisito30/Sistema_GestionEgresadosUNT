"""
Vista dedicada para resultados de encuestas.
"""
import streamlit as st

from src.pages.encuestas_disenar import ver_resultados_encuestas


def show():
    """Muestra la vista administrativa de resultados de encuestas."""
    user = st.session_state.user
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return

    st.title("📊 Resultados de Encuestas")
    st.caption("Consulta consolidada de respuestas y métricas de seguimiento.")
    ver_resultados_encuestas()
