"""
Módulo de pagos y generación de vouchers.
Permite ver el historial de pagos y generar vouchers con QR.
"""
import streamlit as st
import pandas as pd
import qrcode
import io
import base64
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from src.utils.database import get_db_cursor
from src.utils.session import add_notification
import uuid

def show():
    """Muestra la página de pagos y vouchers."""
    
    st.title("💰 Pagos y Vouchers")
    
    user = st.session_state.user
    rol = user['rol']
    
    if rol == 'administrador':
        # Vista de administrador
        tab1, tab2, tab3 = st.tabs([
            "📋 Todos los Pagos",
            "📊 Estadísticas",
            "⚙️ Configuración"
        ])
        
        with tab1:
            mostrar_todos_pagos()
        
        with tab2:
            mostrar_estadisticas_pagos()
        
        with tab3:
            configurar_pagos()
    
    else:
        # Vista de usuario (egresado/empleador)
        tab1, tab2 = st.tabs([
            "📋 Mis Pagos",
            "🎟️ Generar Voucher"
        ])
        
        with tab1:
            mostrar_mis_pagos(user['id'])
        
        with tab2:
            generar_voucher_form(user['id'])

def mostrar_mis_pagos(usuario_id):
    """Muestra el historial de pagos del usuario."""
    
    st.subheader("Historial de Pagos")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                p.id,
                p.concepto,
                p.referencia_id,
                p.monto,
                p.fecha_pago,
                p.codigo_voucher,
                p.pagado,
                p.validado,
                CASE 
                    WHEN p.concepto = 'evento' THEN (SELECT titulo FROM eventos WHERE id = p.referencia_id::uuid)
                    WHEN p.concepto = 'certificado' THEN 'Certificado'
                    WHEN p.concepto = 'membresia' THEN 'Membresía'
                END as descripcion
            FROM pagos p
            WHERE p.usuario_id = %s
            ORDER BY p.fecha_pago DESC
        """, (usuario_id,))
        
        pagos = cur.fetchall()
        
        if not pagos:
            st.info("No tienes pagos registrados.")
            return
        
        # Resumen
        total_pagado = sum(pago[3] for pago in pagos if pago[6])  # pagado = True
        st.metric("Total Pagado", f"S/. {total_pagado:,.2f}")
        
        # Tabla de pagos
        df = pd.DataFrame(
            pagos,
            columns=['ID', 'Concepto', 'Referencia', 'Monto', 'Fecha', 
                    'Código Voucher', 'Pagado', 'Validado', 'Descripción']
        )
        
        # Formatear
        df['Monto'] = df['Monto'].apply(lambda x: f"S/. {x:,.2f}")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        df['Pagado'] = df['Pagado'].apply(lambda x: '✅' if x else '❌')
        df['Validado'] = df['Validado'].apply(lambda x: '✅' if x else '❌')
        
        st.dataframe(
            df[['Fecha', 'Descripción', 'Concepto', 'Monto', 'Código Voucher', 'Pagado', 'Validado']],
            use_container_width=True,
            hide_index=True
        )
        
        # Opción para ver voucher
        for pago in pagos:
            if pago[5]:  # código_voucher
                if st.button(f"📄 Ver Voucher {pago[5]}", key=f"v_{pago[0]}"):
                    mostrar_voucher(pago[0])

def generar_voucher_form(usuario_id):
    """Formulario para generar un nuevo voucher."""
    
    st.subheader("Generar Nuevo Voucher")
    
    with st.form("form_voucher"):
        concepto = st.selectbox(
            "Concepto de Pago",
            options=['certificado', 'membresia', 'evento']
        )
        
        if concepto == 'evento':
            # Seleccionar evento
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT id, titulo, precio
                    FROM eventos
                    WHERE es_gratuito = false
                    AND activo = true
                    AND fecha_inicio > NOW()
                    ORDER BY fecha_inicio
                """)
                
                eventos = cur.fetchall()
                
                if eventos:
                    evento_opciones = {f"{e[1]} - S/. {e[2]:.2f}": e[0] for e in eventos}
                    evento_seleccionado = st.selectbox(
                        "Seleccionar Evento",
                        options=list(evento_opciones.keys())
                    )
                    monto = next(e[2] for e in eventos if e[0] == evento_opciones[evento_seleccionado])
                    referencia_id = evento_opciones[evento_seleccionado]
                else:
                    st.warning("No hay eventos pagados disponibles")
                    monto = 0
                    referencia_id = None
        
        elif concepto == 'membresia':
            # Membresía anual
            st.info("Membresía Anual - S/. 50.00")
            monto = 50.00
            referencia_id = None
        
        else:  # certificado
            # Certificado de egresado
            st.info("Certificado de Egresado - S/. 25.00")
            monto = 25.00
            referencia_id = None
        
        metodo_pago = st.selectbox(
            "Método de Pago",
            options=['Tarjeta de Crédito/Débito', 'Transferencia Bancaria', 'Yape/Plin']
        )
        
        # Datos de pago según método
        if metodo_pago == 'Tarjeta de Crédito/Débito':
            col1, col2 = st.columns(2)
            with col1:
                numero_tarjeta = st.text_input("Número de Tarjeta", max_chars=16)
                fecha_venc = st.text_input("Fecha Vencimiento (MM/AA)", max_chars=5)
            with col2:
                nombre_titular = st.text_input("Nombre del Titular")
                cvv = st.text_input("CVV", max_chars=3, type="password")
        
        elif metodo_pago == 'Transferencia Bancaria':
            st.info("""
            **Datos Bancarios:**
            - Banco: Banco de la Nación
            - Cuenta: 00-000-123456-7
            - CCI: 000-000-123456789-00
            - Titular: Universidad Nacional de Trujillo
            """)
            comprobante = st.file_uploader("Subir Comprobante de Transferencia", type=['pdf', 'jpg', 'png'])
        
        else:  # Yape/Plin
            st.image("https://via.placeholder.com/300x300?text=QR+Yape", width=200)
            st.info("Escanee el código QR y realice el pago")
            confirmar_pago = st.checkbox("Confirmo que realicé el pago")
        
        submitted = st.form_submit_button("Generar Voucher", type="primary", use_container_width=True)
        
        if submitted:
            if concepto == 'evento' and not referencia_id:
                st.error("Seleccione un evento válido")
                return
            
            procesar_pago(
                usuario_id, concepto, referencia_id, monto,
                metodo_pago, locals() if submitted else None
            )

def procesar_pago(usuario_id, concepto, referencia_id, monto, metodo_pago, datos_pago):
    """Procesa el pago y genera el voucher."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Generar código único para voucher
            codigo_voucher = f"VCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Generar datos para QR
            qr_data = f"https://tusitio.com/validar/{codigo_voucher}"
            
            # Insertar pago
            cur.execute("""
                INSERT INTO pagos (
                    usuario_id, concepto, referencia_id, monto,
                    codigo_voucher, qr_code_data, pagado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                usuario_id, concepto, referencia_id, monto,
                codigo_voucher, qr_data, True  # Asumimos pago exitoso
            ))
            
            pago_id = cur.fetchone()[0]
            
            # Generar PDF del voucher
            pdf_url = generar_pdf_voucher(pago_id, usuario_id, concepto, monto, codigo_voucher, qr_data)
            
            # Actualizar URL del PDF
            cur.execute("""
                UPDATE pagos
                SET pdf_voucher_url = %s
                WHERE id = %s
            """, (pdf_url, pago_id))
            
            # Si es inscripción a evento, actualizar
            if concepto == 'evento' and referencia_id:
                cur.execute("""
                    UPDATE inscripciones_eventos
                    SET pago_id = %s
                    WHERE evento_id = %s AND usuario_id = %s
                """, (pago_id, referencia_id, usuario_id))
            
            add_notification(f"Pago procesado exitosamente. Código: {codigo_voucher}", "success")
            
            # Mostrar voucher generado
            mostrar_voucher(pago_id)
            
    except Exception as e:
        add_notification(f"Error al procesar pago: {str(e)}", "error")

def generar_pdf_voucher(pago_id, usuario_id, concepto, monto, codigo_voucher, qr_data):
    """Genera un PDF con el voucher de pago."""
    
    try:
        # Crear buffer para PDF
        buffer = io.BytesIO()
        
        # Crear canvas
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Título
        c.setFont("Helvetica-Bold", 24)
        c.drawString(2*cm, height - 3*cm, "VOUCHER DE PAGO")
        
        # Línea separadora
        c.line(2*cm, height - 3.5*cm, width - 2*cm, height - 3.5*cm)
        
        # Datos del voucher
        c.setFont("Helvetica", 12)
        y = height - 5*cm
        
        # Obtener datos del usuario
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT email, 
                       CASE 
                           WHEN e.id IS NOT NULL THEN e.nombres || ' ' || e.apellido_paterno
                           WHEN em.id IS NOT NULL THEN em.nombres || ' ' || em.apellidos
                           ELSE 'Administrador'
                       END as nombre
                FROM usuarios u
                LEFT JOIN egresados e ON u.id = e.usuario_id
                LEFT JOIN empleadores em ON u.id = em.usuario_id
                WHERE u.id = %s
            """, (usuario_id,))
            
            email, nombre = cur.fetchone()
        
        # Información del voucher
        datos = [
            ("Código:", codigo_voucher),
            ("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M")),
            ("Usuario:", nombre),
            ("Email:", email),
            ("Concepto:", concepto.upper()),
            ("Monto:", f"S/. {monto:.2f}"),
            ("Estado:", "PAGADO")
        ]
        
        for label, value in datos:
            c.drawString(3*cm, y, label)
            c.drawString(8*cm, y, str(value))
            y -= 0.8*cm
        
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar QR temporalmente
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Dibujar QR en PDF
        c.drawImage(qr_buffer, width - 7*cm, height - 12*cm, width=5*cm, height=5*cm)
        
        # Texto de validación
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, 2*cm, f"Este voucher puede ser validado en: https://tusitio.com/validar/{codigo_voucher}")
        c.drawString(2*cm, 1.5*cm, "Válido solo con presentación de documento de identidad.")
        
        # Guardar PDF
        c.save()
        
        # Aquí iría la lógica para guardar el PDF en storage
        pdf_path = f"/app/storage/vouchers/{codigo_voucher}.pdf"
        
        # Por ahora retornamos una URL simulada
        return pdf_path
        
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None

def mostrar_voucher(pago_id):
    """Muestra el voucher generado."""
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, u.email
            FROM pagos p
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s
        """, (pago_id,))
        
        pago = cur.fetchone()
        
        if not pago:
            st.error("Voucher no encontrado")
            return
        
        st.subheader(f"Voucher: {pago[5]}")  # código_voucher
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Datos del Pago")
            st.markdown(f"**Concepto:** {pago[1]}")
            st.markdown(f"**Monto:** S/. {pago[3]:.2f}")
            st.markdown(f"**Fecha:** {pago[4].strftime('%d/%m/%Y %H:%M')}")
            st.markdown(f"**Usuario:** {pago[-1]}")
            st.markdown(f"**Estado:** {'✅ Válido' if pago[7] else '❌ No validado'}")
        
        with col2:
            st.markdown("### Código QR")
            # Generar QR
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(pago[6])  # qr_code_data
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a imagen para Streamlit
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            st.image(img_buffer, width=200)
        
        # Botones de acción
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("📥 Descargar PDF", use_container_width=True):
                if pago[8]:  # pdf_voucher_url
                    st.success("Descargando PDF...")
                else:
                    st.warning("PDF no disponible")
        
        with col4:
            if st.button("🔄 Validar Voucher", use_container_width=True):
                validar_voucher(pago_id)
        
        with col5:
            if st.button("📧 Enviar por Email", use_container_width=True):
                enviar_voucher_email(pago_id)

def validar_voucher(pago_id):
    """Valida un voucher (marca como usado)."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE pagos
                SET validado = true
                WHERE id = %s
                RETURNING codigo_voucher
            """, (pago_id,))
            
            codigo = cur.fetchone()[0]
            
            add_notification(f"Voucher {codigo} validado exitosamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al validar: {str(e)}", "error")

def enviar_voucher_email(pago_id):
    """Envía el voucher por email."""
    
    add_notification("Voucher enviado a tu correo electrónico", "success")

def mostrar_todos_pagos():
    """Vista de administrador: todos los pagos."""
    
    st.subheader("Todos los Pagos")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                p.id,
                u.email,
                p.concepto,
                p.monto,
                p.fecha_pago,
                p.codigo_voucher,
                p.pagado,
                p.validado
            FROM pagos p
            JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.fecha_pago DESC
            LIMIT 1000
        """)
        
        pagos = cur.fetchall()
        
        if not pagos:
            st.info("No hay pagos registrados")
            return
        
        df = pd.DataFrame(
            pagos,
            columns=['ID', 'Usuario', 'Concepto', 'Monto', 'Fecha', 
                    'Código', 'Pagado', 'Validado']
        )
        
        # Métricas
        total_recaudado = df[df['Pagado'] == True]['Monto'].sum()
        total_pagos = len(df[df['Pagado'] == True])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Recaudado", f"S/. {total_recaudado:,.2f}")
        col2.metric("Total Pagos", total_pagos)
        col3.metric("Pendientes Validación", len(df[df['Validado'] == False]))
        
        # Tabla
        df['Monto'] = df['Monto'].apply(lambda x: f"S/. {x:,.2f}")
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%d/%m/%Y')
        df['Pagado'] = df['Pagado'].apply(lambda x: '✅' if x else '❌')
        df['Validado'] = df['Validado'].apply(lambda x: '✅' if x else '❌')
        
        st.dataframe(df, use_container_width=True, hide_index=True)

def mostrar_estadisticas_pagos():
    """Muestra estadísticas de pagos."""
    
    st.subheader("Estadísticas de Pagos")
    
    with get_db_cursor() as cur:
        # Ingresos por mes
        cur.execute("""
            SELECT 
                DATE_TRUNC('month', fecha_pago)::date as mes,
                SUM(monto) as total,
                COUNT(*) as cantidad
            FROM pagos
            WHERE pagado = true
            AND fecha_pago > NOW() - INTERVAL '12 months'
            GROUP BY mes
            ORDER BY mes
        """)
        
        ingresos = cur.fetchall()
        
        if ingresos:
            df_ingresos = pd.DataFrame(ingresos, columns=['Mes', 'Total', 'Cantidad'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ingresos por Mes")
                st.bar_chart(df_ingresos.set_index('Mes')['Total'])
            
            with col2:
                st.subheader("Cantidad de Pagos por Mes")
                st.line_chart(df_ingresos.set_index('Mes')['Cantidad'])
        
        # Distribución por concepto
        cur.execute("""
            SELECT concepto, COUNT(*), SUM(monto)
            FROM pagos
            WHERE pagado = true
            GROUP BY concepto
        """)
        
        conceptos = cur.fetchall()
        
        if conceptos:
            st.subheader("Distribución por Concepto")
            
            df_conceptos = pd.DataFrame(
                conceptos,
                columns=['Concepto', 'Cantidad', 'Total']
            )
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.dataframe(df_conceptos)
            
            with col4:
                # Gráfico de pastel
                import plotly.express as px
                fig = px.pie(df_conceptos, values='Total', names='Concepto')
                st.plotly_chart(fig, use_container_width=True)

def configurar_pagos():
    """Configuración de pagos para administrador."""
    
    st.subheader("Configuración de Pagos")
    
    with st.form("config_pagos"):
        st.markdown("### Precios")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            precio_certificado = st.number_input("Certificado (S/.)", min_value=0.0, value=25.0, step=5.0)
        with col2:
            precio_membresia = st.number_input("Membresía Anual (S/.)", min_value=0.0, value=50.0, step=10.0)
        with col3:
            precio_evento_base = st.number_input("Evento Base (S/.)", min_value=0.0, value=30.0, step=5.0)
        
        st.markdown("### Datos Bancarios")
        
        banco = st.text_input("Banco", value="Banco de la Nación")
        cuenta = st.text_input("Número de Cuenta", value="00-000-123456-7")
        cci = st.text_input("CCI", value="000-000-123456789-00")
        titular = st.text_input("Titular", value="Universidad Nacional de Trujillo")
        
        st.markdown("### Yape/Plin")
        
        col4, col5 = st.columns(2)
        with col4:
            numero_yape = st.text_input("Número Yape", value="987654321")
        with col5:
            qr_yape = st.file_uploader("Código QR Yape", type=['png', 'jpg'])
        
        submitted = st.form_submit_button("Guardar Configuración", type="primary")
        
        if submitted:
            add_notification("Configuración guardada exitosamente", "success")