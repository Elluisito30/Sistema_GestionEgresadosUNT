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

    codigo = st.text_input("Código de voucher", placeholder="Ej: VCH-20260316-AB12CD34")

    if codigo and st.button("Buscar voucher", type="primary"):
        pago = Pago.get_by_voucher(codigo.strip())

        if not pago:
            st.error("No se encontró un voucher con ese código.")
            return

        if pago.validado:
            st.info("Este voucher ya fue validado previamente.")
        mostrar_voucher(pago.id)

    st.markdown("---")
    st.subheader("Últimos vouchers pendientes")
    pendientes = Pago.obtener_pendientes_validacion(limit=20)

    if not pendientes:
        st.success("No hay vouchers pendientes de validación.")
        return

    for pago_id, codigo_voucher, email, concepto, monto, fecha_pago in pendientes:
        with st.container(border=True):
            st.markdown(f"**{codigo_voucher}**")
            st.caption(f"{email} | {concepto} | S/. {monto:.2f} | {fecha_pago.strftime('%d/%m/%Y %H:%M')}")
            if st.button("Ver detalle", key=f"ver_pago_admin_{pago_id}"):
                mostrar_voucher(pago_id)
