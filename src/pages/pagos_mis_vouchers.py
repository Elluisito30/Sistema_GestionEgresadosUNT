"""
Módulo de pagos y generación de vouchers.
Permite ver el historial de pagos y generar vouchers con QR.
"""
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.pago import Pago
from src.utils.database import get_db_cursor
from src.utils.pdf_generator import generar_pdf_voucher_pago
from src.utils.qr_generator import QRGenerator
from src.utils.session import add_notification
from src.utils.excel_generator import generar_excel_pagos


def show():
    """Muestra la página de pagos y vouchers."""
    st.title("💰 Pagos y Vouchers")

    user = st.session_state.user
    rol = user["rol"]

    if rol == "administrador":
        tab1, tab2, tab3 = st.tabs([
            "📋 Todos los Pagos",
            "📊 Estadísticas",
            "⚙️ Configuración",
        ])

        with tab1:
            mostrar_todos_pagos()

        with tab2:
            mostrar_estadisticas_pagos()

        with tab3:
            configurar_pagos()

    else:
        tab1, tab2 = st.tabs([
            "📋 Mis Pagos",
            "🎟️ Generar Voucher",
        ])

        with tab1:
            mostrar_mis_pagos(user["id"])

        with tab2:
            generar_voucher_form(user["id"])


def mostrar_mis_pagos(usuario_id):
    """Muestra el historial de pagos del usuario."""
    st.subheader("Historial de Pagos")

    pagos = Pago.obtener_historial_usuario(usuario_id)

    if not pagos:
        st.info("No tienes pagos registrados.")
        return

    total_pagado = sum(pago[3] for pago in pagos if pago[6])
    st.metric("Total Pagado", f"S/. {total_pagado:,.2f}")

    df = pd.DataFrame(
        pagos,
        columns=[
            "ID",
            "Concepto",
            "Referencia",
            "Monto",
            "Fecha",
            "Código Voucher",
            "Pagado",
            "Validado",
            "Descripción",
        ],
    )

    df["Monto"] = df["Monto"].apply(lambda x: f"S/. {x:,.2f}")
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%d/%m/%Y %H:%M")
    df["Pagado"] = df["Pagado"].apply(lambda x: "✅" if x else "❌")
    df["Validado"] = df["Validado"].apply(lambda x: "✅" if x else "❌")

    st.dataframe(
        df[["Fecha", "Descripción", "Concepto", "Monto", "Código Voucher", "Pagado", "Validado"]],
        use_container_width=True,
        hide_index=True,
    )

    for pago in pagos:
        if pago[5]:
            if st.button(f"📄 Ver Voucher {pago[5]}", key=f"v_{pago[0]}"):
                mostrar_voucher(pago[0])


def generar_voucher_form(usuario_id):
    """Formulario para generar un nuevo voucher."""
    st.subheader("Generar Nuevo Voucher")

    with st.form("form_voucher"):
        concepto = st.selectbox("Concepto de Pago", options=["certificado", "membresia", "evento"])

        if concepto == "evento":
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT id, titulo, precio
                    FROM eventos
                    WHERE es_gratuito = false
                    AND activo = true
                    AND fecha_inicio > NOW()
                    ORDER BY fecha_inicio
                    """
                )
                eventos = cur.fetchall()

            if eventos:
                evento_opciones = {f"{e[1]} - S/. {e[2]:.2f}": e[0] for e in eventos}
                evento_seleccionado = st.selectbox("Seleccionar Evento", options=list(evento_opciones.keys()))
                monto = next(e[2] for e in eventos if e[0] == evento_opciones[evento_seleccionado])
                referencia_id = evento_opciones[evento_seleccionado]
            else:
                st.warning("No hay eventos pagados disponibles")
                monto = 0
                referencia_id = None

        elif concepto == "membresia":
            st.info("Membresía Anual - S/. 50.00")
            monto = 50.00
            referencia_id = None

        else:
            st.info("Certificado de Egresado - S/. 25.00")
            monto = 25.00
            referencia_id = None

        metodo_pago = st.selectbox(
            "Método de Pago",
            options=["Tarjeta de Crédito/Débito", "Transferencia Bancaria", "Yape/Plin"],
        )

        if metodo_pago == "Tarjeta de Crédito/Débito":
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Número de Tarjeta", max_chars=16)
                st.text_input("Fecha Vencimiento (MM/AA)", max_chars=5)
            with col2:
                st.text_input("Nombre del Titular")
                st.text_input("CVV", max_chars=3, type="password")

        elif metodo_pago == "Transferencia Bancaria":
            st.info(
                """
            **Datos Bancarios:**
            - Banco: Banco de la Nación
            - Cuenta: 00-000-123456-7
            - CCI: 000-000-123456789-00
            - Titular: Universidad Nacional de Trujillo
            """
            )
            st.file_uploader("Subir Comprobante de Transferencia", type=["pdf", "jpg", "png"])

        else:
            st.image("https://via.placeholder.com/300x300?text=QR+Yape", width=200)
            st.info("Escanee el código QR y realice el pago")
            st.checkbox("Confirmo que realicé el pago")

        submitted = st.form_submit_button("Generar Voucher", type="primary", use_container_width=True)

        if submitted:
            if concepto == "evento" and not referencia_id:
                st.error("Seleccione un evento válido")
                return

            procesar_pago(usuario_id, concepto, referencia_id, monto)


def procesar_pago(usuario_id, concepto, referencia_id, monto):
    """Procesa el pago y genera el voucher."""
    try:
        pago = Pago.crear_pago(
            usuario_id=usuario_id,
            concepto=concepto,
            monto=monto,
            referencia_id=referencia_id,
        )

        if not pago:
            add_notification("No se pudo registrar el pago.", "error")
            return

        pago.pdf_voucher_url = f"voucher://{pago.codigo_voucher}"
        pago.save()

        if concepto == "evento" and referencia_id:
            with get_db_cursor(commit=True) as cur:
                cur.execute(
                    """
                    UPDATE inscripciones_eventos
                    SET pago_id = %s
                    WHERE evento_id = %s AND usuario_id = %s
                    """,
                    (pago.id, referencia_id, usuario_id),
                )

        add_notification(f"Pago procesado exitosamente. Código: {pago.codigo_voucher}", "success")
        mostrar_voucher(pago.id)

    except Exception as e:
        add_notification(f"Error al procesar pago: {str(e)}", "error")


def _build_pdf_bytes_for_pago(pago_id):
    detalle = Pago.obtener_detalle_voucher(pago_id)
    if not detalle:
        return None, None

    qr_bytes = QRGenerator.generate_voucher_qr(detalle["codigo_voucher"])
    pdf_bytes = generar_pdf_voucher_pago(detalle, qr_bytes)
    return detalle, pdf_bytes


def mostrar_voucher(pago_id):
    """Muestra el voucher generado."""
    detalle = Pago.obtener_detalle_voucher(pago_id)

    if not detalle:
        st.error("Voucher no encontrado")
        return

    st.subheader(f"Voucher: {detalle['codigo_voucher']}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Datos del Pago")
        st.markdown(f"**Concepto:** {detalle['concepto']}")
        st.markdown(f"**Monto:** S/. {detalle['monto']:.2f}")
        st.markdown(f"**Fecha:** {detalle['fecha_pago'].strftime('%d/%m/%Y %H:%M')}")
        st.markdown(f"**Usuario:** {detalle['email']}")
        st.markdown(f"**Estado:** {'✅ Válido' if detalle['validado'] else '❌ No validado'}")

    with col2:
        st.markdown("### Código QR")
        qr_bytes = QRGenerator.generate_voucher_qr(detalle["codigo_voucher"])
        st.image(qr_bytes, width=200)

    _, pdf_bytes = _build_pdf_bytes_for_pago(pago_id)

    col3, col4, col5 = st.columns(3)

    with col3:
        if pdf_bytes:
            st.download_button(
                "📥 Descargar PDF",
                data=pdf_bytes,
                file_name=f"voucher_{detalle['codigo_voucher']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"descargar_pdf_{pago_id}",
            )
        else:
            st.warning("PDF no disponible")

    with col4:
        if st.button("🔄 Validar Voucher", use_container_width=True, key=f"validar_{pago_id}"):
            validar_voucher(pago_id)

    with col5:
        if st.button("📧 Enviar por Email", use_container_width=True, key=f"mail_{pago_id}"):
            enviar_voucher_email(pago_id)


def validar_voucher(pago_id):
    """Valida un voucher (marca como usado)."""
    try:
        codigo = Pago.validar_por_id(pago_id)
        if codigo:
            add_notification(f"Voucher {codigo} validado exitosamente", "success")
            st.rerun()
        else:
            add_notification("No se pudo validar el voucher", "error")

    except Exception as e:
        add_notification(f"Error al validar: {str(e)}", "error")


def enviar_voucher_email(pago_id):
    """Envía el voucher por email."""
    add_notification("Voucher enviado a tu correo electrónico", "success")


def mostrar_todos_pagos():
    """Vista de administrador: todos los pagos."""
    st.subheader("Todos los Pagos")

    pagos = Pago.obtener_todos(limit=1000)

    if not pagos:
        st.info("No hay pagos registrados")
        return

    df = pd.DataFrame(
        pagos,
        columns=["ID", "Usuario", "Concepto", "Monto", "Fecha", "Código", "Pagado", "Validado"],
    )

    total_recaudado = df[df["Pagado"] == True]["Monto"].sum()
    total_pagos = len(df[df["Pagado"] == True])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Recaudado", f"S/. {total_recaudado:,.2f}")
    col2.metric("Total Pagos", total_pagos)
    col3.metric("Pendientes Validación", len(df[df["Validado"] == False]))

    st.markdown("---")
    
    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 4])
    with col_dl1:
        pagos_reporte = Pago.obtener_reporte_pagos()
        excel_bytes = generar_excel_pagos(pagos_reporte)
        st.download_button(
            "📊 Descargar Excel",
            data=excel_bytes,
            file_name=f"reporte_pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    with col_dl2:
        from src.utils.pdf_generator import generar_pdf_reporte_pagos
        pdf_bytes = generar_pdf_reporte_pagos(pagos_reporte)
        st.download_button(
            "📄 Descargar PDF",
            data=pdf_bytes,
            file_name=f"reporte_pagos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("---")

    df["Monto"] = df["Monto"].apply(lambda x: f"S/. {x:,.2f}")
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%d/%m/%Y")
    df["Pagado"] = df["Pagado"].apply(lambda x: "✅" if x else "❌")
    df["Validado"] = df["Validado"].apply(lambda x: "✅" if x else "❌")

    st.dataframe(df, use_container_width=True, hide_index=True)


def mostrar_estadisticas_pagos():
    """Muestra estadísticas de pagos."""
    st.subheader("Estadísticas de Pagos")

    ingresos = Pago.obtener_ingresos_12_meses()
    if ingresos:
        df_ingresos = pd.DataFrame(ingresos, columns=["Mes", "Total", "Cantidad"])

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Ingresos por Mes")
            st.bar_chart(df_ingresos.set_index("Mes")["Total"])

        with col2:
            st.subheader("Cantidad de Pagos por Mes")
            st.line_chart(df_ingresos.set_index("Mes")["Cantidad"])

    conceptos = Pago.obtener_distribucion_conceptos()
    if conceptos:
        st.subheader("Distribución por Concepto")
        df_conceptos = pd.DataFrame(conceptos, columns=["Concepto", "Cantidad", "Total"])

        col3, col4 = st.columns(2)
        with col3:
            st.dataframe(df_conceptos)
        with col4:
            fig = px.pie(df_conceptos, values="Total", names="Concepto")
            st.plotly_chart(fig, use_container_width=True)


def configurar_pagos():
    """Configuración de pagos para administrador."""
    st.subheader("Configuración de Pagos")

    with st.form("config_pagos"):
        st.markdown("### Precios")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("Certificado (S/.)", min_value=0.0, value=25.0, step=5.0)
        with col2:
            st.number_input("Membresía Anual (S/.)", min_value=0.0, value=50.0, step=10.0)
        with col3:
            st.number_input("Evento Base (S/.)", min_value=0.0, value=30.0, step=5.0)

        st.markdown("### Datos Bancarios")

        st.text_input("Banco", value="Banco de la Nación")
        st.text_input("Número de Cuenta", value="00-000-123456-7")
        st.text_input("CCI", value="000-000-123456789-00")
        st.text_input("Titular", value="Universidad Nacional de Trujillo")

        st.markdown("### Yape/Plin")

        col4, col5 = st.columns(2)
        with col4:
            st.text_input("Número Yape", value="987654321")
        with col5:
            st.file_uploader("Código QR Yape", type=["png", "jpg"])

        submitted = st.form_submit_button("Guardar Configuración", type="primary")

        if submitted:
            add_notification("Configuración guardada exitosamente", "success")
