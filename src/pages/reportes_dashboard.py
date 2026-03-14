"""
Módulo de reportes y estadísticas avanzadas.
Permite generar reportes en diferentes formatos.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.session import add_notification
import io
import base64

def show():
    """Muestra la página de reportes."""
    
    st.title("📊 Reportes y Estadísticas")
    
    user = st.session_state.user
    
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return
    
    # Tabs para diferentes tipos de reportes
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Egresados",
        "🏢 Empresas",
        "💼 Ofertas",
        "💰 Financiero",
        "📈 Exportar"
    ])
    
    with tab1:
        reportes_egresados()
    
    with tab2:
        reportes_empresas()
    
    with tab3:
        reportes_ofertas()
    
    with tab4:
        reportes_financieros()
    
    with tab5:
        exportar_datos()

def reportes_egresados():
    """Reportes de egresados."""
    
    st.subheader("Estadísticas de Egresados")
    
    # Filtros de tiempo
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=365), key="egr_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=date.today(), key="egr_hasta")
    
    with get_db_cursor() as cur:
        # Total egresados
        cur.execute("SELECT COUNT(*) FROM egresados")
        total_egresados = cur.fetchone()[0]
        
        # Nuevos egresados en el período
        cur.execute("""
            SELECT COUNT(*) 
            FROM egresados e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE u.fecha_registro::date BETWEEN %s AND %s
        """, (fecha_desde, fecha_hasta))
        nuevos_egresados = cur.fetchone()[0]
        
        # Egresados por carrera
        cur.execute("""
            SELECT carrera_principal, COUNT(*)
            FROM egresados
            GROUP BY carrera_principal
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        egresados_carrera = cur.fetchall()
        
        # Egresados por año de egreso
        cur.execute("""
            SELECT anio_egreso, COUNT(*)
            FROM egresados
            WHERE anio_egreso IS NOT NULL
            GROUP BY anio_egreso
            ORDER BY anio_egreso
        """)
        egresados_anio = cur.fetchall()
        
        # KPIs
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Total Egresados", f"{total_egresados:,}")
        col_b.metric("Nuevos (período)", f"{nuevos_egresados:,}")
        col_c.metric("Con CV subido", "75%")  # Ejemplo
        col_d.metric("Perfiles públicos", "60%")  # Ejemplo
        
        st.markdown("---")
        
        # Gráficos
        col3, col4 = st.columns(2)
        
        with col3:
            if egresados_carrera:
                st.subheader("Top 10 Carreras")
                df_carrera = pd.DataFrame(egresados_carrera, columns=['Carrera', 'Cantidad'])
                fig = px.bar(df_carrera, x='Carrera', y='Cantidad', title='Egresados por Carrera')
                st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            if egresados_anio:
                st.subheader("Egresados por Año")
                df_anio = pd.DataFrame(egresados_anio, columns=['Año', 'Cantidad'])
                fig = px.line(df_anio, x='Año', y='Cantidad', title='Tendencia de Egresados')
                st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada
        st.subheader("Distribución Detallada")
        
        cur.execute("""
            SELECT 
                carrera_principal,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE perfil_publico) as publicos,
                AVG(EXTRACT(YEAR FROM age(fecha_nacimiento)))::int as edad_promedio
            FROM egresados
            GROUP BY carrera_principal
            ORDER BY total DESC
        """)
        
        detalle = cur.fetchall()
        if detalle:
            df_detalle = pd.DataFrame(
                detalle,
                columns=['Carrera', 'Total', 'Perfiles Públicos', 'Edad Promedio']
            )
            st.dataframe(df_detalle, use_container_width=True, hide_index=True)

def reportes_empresas():
    """Reportes de empresas."""
    
    st.subheader("Estadísticas de Empresas")
    
    with get_db_cursor() as cur:
        # Totales por estado
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE estado = 'activa') as activas,
                COUNT(*) FILTER (WHERE estado = 'pendiente') as pendientes,
                COUNT(*) FILTER (WHERE estado = 'rechazada') as rechazadas
            FROM empresas
        """)
        total, activas, pendientes, rechazadas = cur.fetchone()
        
        # Empresas por sector
        cur.execute("""
            SELECT sector_economico, COUNT(*)
            FROM empresas
            WHERE estado = 'activa'
            GROUP BY sector_economico
            ORDER BY COUNT(*) DESC
        """)
        empresas_sector = cur.fetchall()
        
        # Empresas por tamaño
        cur.execute("""
            SELECT tamano_empresa, COUNT(*)
            FROM empresas
            WHERE estado = 'activa'
            GROUP BY tamano_empresa
        """)
        empresas_tamano = cur.fetchall()
        
        # Top empresas con más ofertas
        cur.execute("""
            SELECT 
                e.razon_social,
                COUNT(o.id) as total_ofertas,
                COUNT(o.id) FILTER (WHERE o.activa) ofertas_activas
            FROM empresas e
            LEFT JOIN ofertas o ON e.id = o.empresa_id
            WHERE e.estado = 'activa'
            GROUP BY e.id, e.razon_social
            HAVING COUNT(o.id) > 0
            ORDER BY total_ofertas DESC
            LIMIT 10
        """)
        top_empresas = cur.fetchall()
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Empresas", total or 0)
        col2.metric("Activas", activas or 0)
        col3.metric("Pendientes", pendientes or 0)
        col4.metric("Rechazadas", rechazadas or 0)
        
        st.markdown("---")
        
        # Gráficos
        col5, col6 = st.columns(2)
        
        with col5:
            if empresas_sector:
                st.subheader("Empresas por Sector")
                df_sector = pd.DataFrame(empresas_sector, columns=['Sector', 'Cantidad'])
                fig = px.pie(df_sector, values='Cantidad', names='Sector', title='Distribución por Sector')
                st.plotly_chart(fig, use_container_width=True)
        
        with col6:
            if empresas_tamano:
                st.subheader("Empresas por Tamaño")
                df_tamano = pd.DataFrame(empresas_tamano, columns=['Tamaño', 'Cantidad'])
                fig = px.bar(df_tamano, x='Tamaño', y='Cantidad', title='Distribución por Tamaño')
                st.plotly_chart(fig, use_container_width=True)
        
        # Top empresas
        if top_empresas:
            st.subheader("Top 10 Empresas con más Ofertas")
            df_top = pd.DataFrame(
                top_empresas,
                columns=['Empresa', 'Total Ofertas', 'Ofertas Activas']
            )
            st.dataframe(df_top, use_container_width=True, hide_index=True)

def reportes_ofertas():
    """Reportes de ofertas laborales."""
    
    st.subheader("Estadísticas de Ofertas Laborales")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=180), key="of_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=date.today(), key="of_hasta")
    
    with get_db_cursor() as cur:
        # Métricas generales
        cur.execute("""
            SELECT 
                COUNT(*) as total_ofertas,
                COUNT(*) FILTER (WHERE activa) as activas,
                COUNT(*) FILTER (WHERE NOT activa) as cerradas,
                AVG(salario_min)::numeric(10,2) as salario_promedio_min,
                AVG(salario_max)::numeric(10,2) as salario_promedio_max
            FROM ofertas
            WHERE fecha_publicacion::date BETWEEN %s AND %s
        """, (fecha_desde, fecha_hasta))
        
        total, activas, cerradas, sal_min, sal_max = cur.fetchone()
        
        # Ofertas por tipo
        cur.execute("""
            SELECT tipo, COUNT(*)
            FROM ofertas
            WHERE fecha_publicacion::date BETWEEN %s AND %s
            GROUP BY tipo
        """, (fecha_desde, fecha_hasta))
        ofertas_tipo = cur.fetchall()
        
        # Ofertas por modalidad
        cur.execute("""
            SELECT modalidad, COUNT(*)
            FROM ofertas
            WHERE fecha_publicacion::date BETWEEN %s AND %s
            GROUP BY modalidad
        """, (fecha_desde, fecha_hasta))
        ofertas_modalidad = cur.fetchall()
        
        # Postulaciones por estado
        cur.execute("""
            SELECT estado, COUNT(*)
            FROM postulaciones p
            JOIN ofertas o ON p.oferta_id = o.id
            WHERE o.fecha_publicacion::date BETWEEN %s AND %s
            GROUP BY estado
        """, (fecha_desde, fecha_hasta))
        postulaciones_estado = cur.fetchall()
        
        # KPIs
        col3, col4, col5, col6 = st.columns(4)
        col3.metric("Total Ofertas", total or 0)
        col4.metric("Activas", activas or 0)
        col5.metric("Cerradas", cerradas or 0)
        if sal_min and sal_max:
            col6.metric("Salario Promedio", f"S/. {sal_min:.0f} - {sal_max:.0f}")
        
        st.markdown("---")
        
        # Gráficos
        col7, col8 = st.columns(2)
        
        with col7:
            if ofertas_tipo:
                st.subheader("Ofertas por Tipo")
                df_tipo = pd.DataFrame(ofertas_tipo, columns=['Tipo', 'Cantidad'])
                fig = px.bar(df_tipo, x='Tipo', y='Cantidad', title='Distribución por Tipo')
                st.plotly_chart(fig, use_container_width=True)
        
        with col8:
            if ofertas_modalidad:
                st.subheader("Ofertas por Modalidad")
                df_modal = pd.DataFrame(ofertas_modalidad, columns=['Modalidad', 'Cantidad'])
                fig = px.pie(df_modal, values='Cantidad', names='Modalidad')
                st.plotly_chart(fig, use_container_width=True)
        
        # Postulaciones
        if postulaciones_estado:
            st.subheader("Estado de Postulaciones")
            df_post = pd.DataFrame(postulaciones_estado, columns=['Estado', 'Cantidad'])
            
            col9, col10 = st.columns(2)
            with col9:
                fig = px.bar(df_post, x='Estado', y='Cantidad', 
                           title='Postulaciones por Estado',
                           color='Estado')
                st.plotly_chart(fig, use_container_width=True)
            
            with col10:
                # Embudo de selección
                estados_orden = ['recibido', 'en_revision', 'entrevista', 'seleccionado']
                df_funnel = df_post[df_post['Estado'].isin(estados_orden)]
                if not df_funnel.empty:
                    fig = px.funnel(df_funnel, x='Cantidad', y='Estado',
                                  title='Embudo de Selección')
                    st.plotly_chart(fig, use_container_width=True)

def reportes_financieros():
    """Reportes financieros."""
    
    st.subheader("Reportes Financieros")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        año = st.selectbox("Año", options=range(2020, date.today().year + 1), index=4)
    with col2:
        mes = st.selectbox("Mes", options=range(1, 13), 
                          format_func=lambda x: datetime(2000, x, 1).strftime('%B'),
                          index=date.today().month - 1)
    
    with get_db_cursor() as cur:
        # Ingresos totales
        cur.execute("""
            SELECT 
                COALESCE(SUM(monto), 0) as total_ingresos,
                COUNT(*) as total_pagos,
                COUNT(*) FILTER (WHERE validado) as pagos_validados
            FROM pagos
            WHERE pagado = true
            AND EXTRACT(YEAR FROM fecha_pago) = %s
            AND EXTRACT(MONTH FROM fecha_pago) = %s
        """, (año, mes))
        
        total_ingresos, total_pagos, pagos_validados = cur.fetchone()
        
        # Ingresos por concepto
        cur.execute("""
            SELECT concepto, COUNT(*), SUM(monto)
            FROM pagos
            WHERE pagado = true
            AND EXTRACT(YEAR FROM fecha_pago) = %s
            AND EXTRACT(MONTH FROM fecha_pago) = %s
            GROUP BY concepto
        """, (año, mes))
        ingresos_concepto = cur.fetchall()
        
        # Ingresos diarios
        cur.execute("""
            SELECT 
                fecha_pago::date as fecha,
                SUM(monto) as total
            FROM pagos
            WHERE pagado = true
            AND EXTRACT(YEAR FROM fecha_pago) = %s
            AND EXTRACT(MONTH FROM fecha_pago) = %s
            GROUP BY fecha_pago::date
            ORDER BY fecha
        """, (año, mes))
        ingresos_diarios = cur.fetchall()
        
        # KPIs
        st.subheader(f"Resumen {datetime(año, mes, 1).strftime('%B %Y')}")
        
        col3, col4, col5 = st.columns(3)
        col3.metric("Total Ingresos", f"S/. {total_ingresos:,.2f}")
        col4.metric("Total Transacciones", total_pagos)
        col5.metric("Tasa Validación", f"{(pagos_validados/total_pagos*100):.1f}%" if total_pagos > 0 else "0%")
        
        st.markdown("---")
        
        # Gráficos
        col6, col7 = st.columns(2)
        
        with col6:
            if ingresos_concepto:
                st.subheader("Ingresos por Concepto")
                df_concepto = pd.DataFrame(
                    ingresos_concepto,
                    columns=['Concepto', 'Cantidad', 'Monto']
                )
                fig = px.pie(df_concepto, values='Monto', names='Concepto')
                st.plotly_chart(fig, use_container_width=True)
        
        with col7:
            if ingresos_diarios:
                st.subheader("Ingresos Diarios")
                df_diario = pd.DataFrame(
                    ingresos_diarios,
                    columns=['Fecha', 'Monto']
                )
                fig = px.line(df_diario, x='Fecha', y='Monto', title='Evolución Diaria')
                st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada de conceptos
        if ingresos_concepto:
            st.subheader("Detalle por Concepto")
            df_detalle = pd.DataFrame(
                ingresos_concepto,
                columns=['Concepto', 'Cantidad', 'Monto Total']
            )
            df_detalle['Monto Total'] = df_detalle['Monto Total'].apply(lambda x: f"S/. {x:,.2f}")
            st.dataframe(df_detalle, use_container_width=True, hide_index=True)

def exportar_datos():
    """Exporta datos a diferentes formatos."""
    
    st.subheader("Exportar Datos")
    
    tipo_reporte = st.selectbox(
        "Seleccionar tipo de reporte",
        options=['Egresados', 'Empresas', 'Ofertas', 'Pagos', 'Postulaciones']
    )
    
    formato = st.selectbox(
        "Formato de exportación",
        options=['Excel', 'CSV', 'PDF']
    )
    
    fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=30))
    fecha_hasta = st.date_input("Fecha hasta", value=date.today())
    
    if st.button("📥 Generar Reporte", type="primary", use_container_width=True):
        generar_exportacion(tipo_reporte, formato, fecha_desde, fecha_hasta)

def generar_exportacion(tipo, formato, fecha_desde, fecha_hasta):
    """Genera y descarga el reporte."""
    
    try:
        with get_db_cursor() as cur:
            if tipo == 'Egresados':
                cur.execute("""
                    SELECT 
                        u.email,
                        e.nombres,
                        e.apellido_paterno,
                        e.apellido_materno,
                        e.dni,
                        e.carrera_principal,
                        e.facultad,
                        e.anio_egreso,
                        e.telefono,
                        u.fecha_registro
                    FROM egresados e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE u.fecha_registro::date BETWEEN %s AND %s
                    ORDER BY u.fecha_registro DESC
                """, (fecha_desde, fecha_hasta))
                
                datos = cur.fetchall()
                columnas = ['Email', 'Nombres', 'Apellido Paterno', 'Apellido Materno',
                           'DNI', 'Carrera', 'Facultad', 'Año Egreso', 'Teléfono', 'Fecha Registro']
            
            elif tipo == 'Empresas':
                cur.execute("""
                    SELECT 
                        ruc,
                        razon_social,
                        sector_economico,
                        tamano_empresa,
                        email_contacto,
                        telefono_contacto,
                        estado,
                        fecha_registro
                    FROM empresas
                    WHERE fecha_registro::date BETWEEN %s AND %s
                    ORDER BY fecha_registro DESC
                """, (fecha_desde, fecha_hasta))
                
                datos = cur.fetchall()
                columnas = ['RUC', 'Razón Social', 'Sector', 'Tamaño',
                           'Email', 'Teléfono', 'Estado', 'Fecha Registro']
            
            elif tipo == 'Ofertas':
                cur.execute("""
                    SELECT 
                        o.titulo,
                        e.razon_social,
                        o.tipo,
                        o.modalidad,
                        o.salario_min,
                        o.salario_max,
                        o.fecha_publicacion,
                        o.fecha_limite_postulacion,
                        o.activa,
                        COUNT(p.id) as postulaciones
                    FROM ofertas o
                    JOIN empresas e ON o.empresa_id = e.id
                    LEFT JOIN postulaciones p ON o.id = p.oferta_id
                    WHERE o.fecha_publicacion::date BETWEEN %s AND %s
                    GROUP BY o.id, e.razon_social
                    ORDER BY o.fecha_publicacion DESC
                """, (fecha_desde, fecha_hasta))
                
                datos = cur.fetchall()
                columnas = ['Título', 'Empresa', 'Tipo', 'Modalidad',
                           'Salario Mínimo', 'Salario Máximo', 'Fecha Publicación',
                           'Fecha Límite', 'Activa', 'Postulaciones']
            
            elif tipo == 'Pagos':
                cur.execute("""
                    SELECT 
                        p.codigo_voucher,
                        u.email,
                        p.concepto,
                        p.monto,
                        p.fecha_pago,
                        p.pagado,
                        p.validado
                    FROM pagos p
                    JOIN usuarios u ON p.usuario_id = u.id
                    WHERE p.fecha_pago::date BETWEEN %s AND %s
                    ORDER BY p.fecha_pago DESC
                """, (fecha_desde, fecha_hasta))
                
                datos = cur.fetchall()
                columnas = ['Voucher', 'Usuario', 'Concepto', 'Monto',
                           'Fecha Pago', 'Pagado', 'Validado']
            
            elif tipo == 'Postulaciones':
                cur.execute("""
                    SELECT 
                        o.titulo as oferta,
                        e.razon_social as empresa,
                        eg.nombres || ' ' || eg.apellido_paterno as egresado,
                        p.estado,
                        p.fecha_postulacion,
                        p.fecha_estado_actual
                    FROM postulaciones p
                    JOIN ofertas o ON p.oferta_id = o.id
                    JOIN empresas e ON o.empresa_id = e.id
                    JOIN egresados eg ON p.egresado_id = eg.id
                    WHERE p.fecha_postulacion::date BETWEEN %s AND %s
                    ORDER BY p.fecha_postulacion DESC
                """, (fecha_desde, fecha_hasta))
                
                datos = cur.fetchall()
                columnas = ['Oferta', 'Empresa', 'Egresado', 'Estado',
                           'Fecha Postulación', 'Última Actualización']
            
            # Crear DataFrame
            df = pd.DataFrame(datos, columns=columnas)
            
            # Exportar según formato
            if formato == 'Excel':
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name=tipo)
                
                b64 = base64.b64encode(output.getvalue()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="reporte_{tipo}_{date.today()}.xlsx">Descargar Excel</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            elif formato == 'CSV':
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:text/csv;base64,{b64}" download="reporte_{tipo}_{date.today()}.csv">Descargar CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            elif formato == 'PDF':
                st.warning("Exportación a PDF próximamente disponible")
            
            add_notification(f"Reporte de {tipo} generado exitosamente", "success")
            
    except Exception as e:
        add_notification(f"Error al generar reporte: {str(e)}", "error")