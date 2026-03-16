"""
Vista de administracion de ofertas laborales.
Reutiliza el modulo de gestion de ofertas y fuerza restriccion por rol administrador.
"""

import streamlit as st

from src.pages import ofertas_gestionar


def show():
    user = st.session_state.user
    if user.get("rol") != "administrador":
        st.error("Solo administradores pueden acceder a esta pagina.")
        return

    ofertas_gestionar.show()
