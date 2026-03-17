"""
Vista administrativa de pagos.
Consolida el monitoreo, validación y revisión de vouchers.
"""
import streamlit as st

from src.models.pago import Pago
from src.pages.pagos_mis_vouchers import mostrar_estadisticas_pagos, mostrar_todos_pagos, mostrar_voucher


def show():
    """Muestra la vista administrativa de pagos."""
    user = st.session_state.user
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return

    st.title("💰 Administración de Pagos")

    tab1, tab2, tab3 = st.tabs([
        "📋 Todos los pagos",
        "📊 Estadísticas",
        "✅ Validación de vouchers",
    ])

    with tab1:
        mostrar_todos_pagos()

    with tab2:
        mostrar_estadisticas_pagos()

    with tab3:
        mostrar_panel_validacion()


def mostrar_panel_validacion():
    """Permite revisar y validar vouchers por código."""
    st.subheader("Validación de vouchers")

    # Inicializar estado de selección si no existe
    if 'admin_selected_pago_id' not in st.session_state:
        st.session_state.admin_selected_pago_id = None

    codigo = st.text_input("Código de voucher", placeholder="Ej: VCH-20260316-AB12CD34")

    if codigo and st.button("Buscar voucher", type="primary"):
        pago_data = Pago.get_by_voucher(codigo.strip())

        if not pago_data:
            st.error("No se encontró un voucher con ese código.")
            st.session_state.admin_selected_pago_id = None
        else:
            if pago_data.validado:
                st.info("Este voucher ya fue validado previamente.")
            st.session_state.admin_selected_pago_id = pago_data.id

    st.markdown("---")
    
    # Mostrar detalle si hay uno seleccionado
    if st.session_state.admin_selected_pago_id:
        mostrar_voucher(st.session_state.admin_selected_pago_id)
        if st.button("Cerrar detalle"):
            st.session_state.admin_selected_pago_id = None
            st.rerun()

    st.subheader("Últimos vouchers pendientes")
    pendientes = Pago.obtener_pendientes_validacion(limit=20)

    if not pendientes:
        st.success("No hay vouchers pendientes de validación.")
        return

    for pago_id, codigo_voucher, email, concepto, monto, fecha_pago in pendientes:
        with st.container(border=True):
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(f"**{codigo_voucher}**")
                st.caption(f"{email} | {concepto} | S/. {monto:.2f} | {fecha_pago.strftime('%d/%m/%Y %H:%M')}")
            with col_btn:
                if st.button("Ver detalle", key=f"ver_pago_admin_{pago_id}"):
                    st.session_state.admin_selected_pago_id = pago_id
                    st.rerun()
