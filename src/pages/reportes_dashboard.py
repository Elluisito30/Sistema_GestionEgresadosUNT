"""
Módulo de reportes y estadísticas avanzadas.
Permite generar reportes en diferentes formatos.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from src.utils.database import get_db_cursor
from src.utils.session import add_notification, render_notifications
from src.models.empresa import Empresa
from src.utils.pdf_generator import generar_pdf_empresas_seleccionadas, generar_pdf_ofertas_lista
import io
import base64

def show():
    """Muestra la página de reportes."""
    
    st.title("📊 Reportes y Estadísticas")
    render_notifications()
    
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
                fig = px.line(df_anio, x='Año', y='Cantidad', title='Tendencia de Egresados', markers=True)
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

    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns(6)
    with col_f1:
        fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=365), key="rep_emp_desde")
    with col_f2:
        fecha_hasta = st.date_input("Hasta", value=date.today(), key="rep_emp_hasta")
    with col_f3:
        estado = st.selectbox("Estado", options=["todos", "activa", "pendiente", "rechazada"], key="rep_emp_estado")
    with col_f4:
        with get_db_cursor() as cur:
            cur.execute("SELECT DISTINCT COALESCE(NULLIF(TRIM(sector_economico), ''), 'Sin especificar') FROM empresas ORDER BY 1")
            sectores = [r[0] for r in cur.fetchall()]
        sector = st.selectbox("Sector", options=["Todos"] + sectores, key="rep_emp_sector")
    with col_f5:
        with get_db_cursor() as cur:
            cur.execute("SELECT DISTINCT COALESCE(NULLIF(TRIM(tamano_empresa), ''), 'Sin especificar') FROM empresas ORDER BY 1")
            tamanos = [r[0] for r in cur.fetchall()]
        tamano = st.selectbox("Tamaño", options=["Todos"] + tamanos, key="rep_emp_tamano")
    with col_f6:
        termino = st.text_input("Buscar empresa", key="rep_emp_termino", placeholder="Razón social o RUC")

    filtros = ["e.fecha_registro::date BETWEEN %s AND %s"]
    params = [fecha_desde, fecha_hasta]
    if estado != "todos":
        filtros.append("e.estado = %s")
        params.append(estado)
    if sector != "Todos":
        filtros.append("COALESCE(NULLIF(TRIM(e.sector_economico), ''), 'Sin especificar') = %s")
        params.append(sector)
    if tamano != "Todos":
        filtros.append("COALESCE(NULLIF(TRIM(e.tamano_empresa), ''), 'Sin especificar') = %s")
        params.append(tamano)
    if termino:
        filtros.append("(e.razon_social ILIKE %s OR e.ruc ILIKE %s OR COALESCE(e.nombre_comercial, '') ILIKE %s)")
        like = f"%{termino.strip()}%"
        params.extend([like, like, like])
    where_clause = " AND ".join(filtros)
    
    with get_db_cursor() as cur:
        cur.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE estado = 'activa') as activas,
                COUNT(*) FILTER (WHERE estado = 'pendiente') as pendientes,
                COUNT(*) FILTER (WHERE estado = 'rechazada') as rechazadas
            FROM empresas e
            WHERE {where_clause}
        """, params)
        total, activas, pendientes, rechazadas = cur.fetchone()

        cur.execute(f"""
            SELECT COALESCE(AVG(stats.total_ofertas), 0), COALESCE(SUM(stats.total_empleadores), 0)
            FROM empresas e
            LEFT JOIN (
                SELECT
                    emps.id as empresa_id,
                    COUNT(DISTINCT o.id) as total_ofertas,
                    COUNT(DISTINCT em.id) as total_empleadores
                FROM empresas emps
                LEFT JOIN ofertas o ON o.empresa_id = emps.id
                LEFT JOIN empleadores em ON em.empresa_id = emps.id
                GROUP BY emps.id
            ) stats ON stats.empresa_id = e.id
            WHERE {where_clause}
        """, params)
        promedio_ofertas, total_empleadores = cur.fetchone()
        
        cur.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(e.sector_economico), ''), 'Sin especificar') as sector, COUNT(*)
            FROM empresas e
            WHERE {where_clause}
            GROUP BY sector
            ORDER BY COUNT(*) DESC
        """, params)
        empresas_sector = cur.fetchall()
        
        cur.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(e.tamano_empresa), ''), 'Sin especificar') as tamano, COUNT(*)
            FROM empresas e
            WHERE {where_clause}
            GROUP BY tamano
            ORDER BY COUNT(*) DESC
        """, params)
        empresas_tamano = cur.fetchall()
        
        cur.execute(f"""
            SELECT 
                e.razon_social,
                COUNT(o.id) as total_ofertas,
                COUNT(o.id) FILTER (WHERE o.activa) ofertas_activas
            FROM empresas e
            LEFT JOIN ofertas o ON e.id = o.empresa_id
            WHERE {where_clause}
            GROUP BY e.id, e.razon_social
            HAVING COUNT(o.id) > 0
            ORDER BY total_ofertas DESC
            LIMIT 10
        """, params)
        top_empresas = cur.fetchall()

        cur.execute(f"""
            SELECT
                e.id,
                e.ruc,
                e.razon_social,
                COALESCE(NULLIF(TRIM(e.sector_economico), ''), 'Sin especificar') as sector,
                COALESCE(NULLIF(TRIM(e.tamano_empresa), ''), 'Sin especificar') as tamano,
                e.estado,
                e.fecha_registro,
                COUNT(DISTINCT o.id) as ofertas,
                COUNT(DISTINCT em.id) as empleadores
            FROM empresas e
            LEFT JOIN ofertas o ON o.empresa_id = e.id
            LEFT JOIN empleadores em ON em.empresa_id = e.id
            WHERE {where_clause}
            GROUP BY e.id, e.ruc, e.razon_social, sector, tamano, e.estado, e.fecha_registro
            ORDER BY e.fecha_registro DESC, e.razon_social ASC
        """, params)
        detalle_empresas = cur.fetchall()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Empresas", total or 0)
        col2.metric("Activas", activas or 0)
        col3.metric("Pendientes", pendientes or 0)
        col4.metric("Rechazadas", rechazadas or 0)

        col5, col6 = st.columns(2)
        col5.metric("Promedio Ofertas/Empresa", f"{float(promedio_ofertas or 0):.1f}")
        col6.metric("Empleadores Vinculados", int(total_empleadores or 0))
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            if empresas_sector:
                st.subheader("Empresas por Sector")
                df_sector = pd.DataFrame(empresas_sector, columns=['Sector', 'Cantidad'])
                fig = px.pie(df_sector, values='Cantidad', names='Sector', title='Distribución por Sector')
                st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
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

        if detalle_empresas:
            st.subheader("Detalle de Empresas Filtradas")
            df_detalle = pd.DataFrame(
                detalle_empresas,
                columns=['ID', 'RUC', 'Razón Social', 'Sector', 'Tamaño', 'Estado', 'Fecha Registro', 'Ofertas', 'Empleadores']
            )
            df_detalle['Fecha Registro'] = pd.to_datetime(df_detalle['Fecha Registro']).dt.strftime('%d/%m/%Y')
            st.dataframe(
                df_detalle[['RUC', 'Razón Social', 'Sector', 'Tamaño', 'Estado', 'Fecha Registro', 'Ofertas', 'Empleadores']],
                use_container_width=True,
                hide_index=True,
            )

            empresas_pdf = [
                {
                    'ruc': row['RUC'],
                    'razon_social': row['Razón Social'],
                    'sector_economico': row['Sector'],
                    'tamano_empresa': row['Tamaño'],
                    'estado': row['Estado'],
                }
                for _, row in df_detalle.iterrows()
            ]
            kpis_pdf = {
                'total': len(empresas_pdf),
                'activas': int((df_detalle['Estado'] == 'activa').sum()),
                'pendientes': int((df_detalle['Estado'] == 'pendiente').sum()),
                'rechazadas': int((df_detalle['Estado'] == 'rechazada').sum()),
                'top_sectores': ', '.join(
                    [f"{idx}({val})" for idx, val in df_detalle['Sector'].value_counts().head(3).items()]
                ) or '—',
            }
            pdf_empresas = generar_pdf_empresas_seleccionadas(empresas_pdf, kpis_pdf, titulo='Reporte de Empresas Filtradas')
            st.download_button(
                '📄 Exportar empresas filtradas (PDF)',
                data=pdf_empresas,
                file_name='Reporte_empresas_filtradas.pdf',
                mime='application/pdf',
                use_container_width=True,
            )

            empresa_sel_id = st.selectbox(
                'Ver ficha oficial de empresa',
                options=df_detalle['ID'].tolist(),
                format_func=lambda eid: next((row['Razón Social'] for _, row in df_detalle.iterrows() if row['ID'] == eid), 'Empresa'),
            )
            empresa_sel = Empresa.get_by_id(empresa_sel_id)
            if empresa_sel:
                ok_ficha, ficha_pdf = empresa_sel.generar_ficha_pdf()
                if ok_ficha:
                    st.download_button(
                        '🏢 Descargar ficha oficial (PDF)',
                        data=ficha_pdf,
                        file_name=f'Ficha_{empresa_sel.razon_social}.pdf',
                        mime='application/pdf',
                        use_container_width=True,
                    )

def reportes_ofertas():
    """Reportes de ofertas laborales."""
    
    st.subheader("Estadísticas de Ofertas Laborales")

    with get_db_cursor() as cur:
        cur.execute("SELECT DISTINCT e.razon_social FROM ofertas o JOIN empresas e ON e.id = o.empresa_id ORDER BY 1")
        empresas = [r[0] for r in cur.fetchall()]

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=180), key="of_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=date.today(), key="of_hasta")
    with col3:
        tipo_filtro = st.selectbox("Tipo", options=["todos", "empleo", "pasantia", "practicas"], key="rep_of_tipo")
    with col4:
        modalidad_filtro = st.selectbox("Modalidad", options=["todas", "presencial", "remoto", "hibrido"], key="rep_of_modalidad")
    with col5:
        estado_filtro = st.selectbox("Estado", options=["todas", "activas", "cerradas"], key="rep_of_estado")
    with col6:
        empresa_filtro = st.selectbox("Empresa", options=["Todas"] + empresas, key="rep_of_empresa")
    with col7:
        termino = st.text_input("Buscar oferta", key="rep_of_termino", placeholder="Título o empresa")

    filtros = ["o.fecha_publicacion::date BETWEEN %s AND %s"]
    params = [fecha_desde, fecha_hasta]
    if tipo_filtro != 'todos':
        filtros.append('o.tipo = %s')
        params.append(tipo_filtro)
    if modalidad_filtro != 'todas':
        filtros.append('o.modalidad = %s')
        params.append(modalidad_filtro)
    if estado_filtro == 'activas':
        filtros.append('o.activa = TRUE')
    elif estado_filtro == 'cerradas':
        filtros.append('o.activa = FALSE')
    if empresa_filtro != 'Todas':
        filtros.append('e.razon_social = %s')
        params.append(empresa_filtro)
    if termino:
        filtros.append('(o.titulo ILIKE %s OR e.razon_social ILIKE %s OR COALESCE(o.descripcion, \'\') ILIKE %s)')
        like = f"%{termino.strip()}%"
        params.extend([like, like, like])
    where_clause = ' AND '.join(filtros)
    
    with get_db_cursor() as cur:
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_ofertas,
                COUNT(*) FILTER (WHERE activa) as activas,
                COUNT(*) FILTER (WHERE NOT activa) as cerradas,
                AVG(salario_min)::numeric(10,2) as salario_promedio_min,
                AVG(salario_max)::numeric(10,2) as salario_promedio_max
            FROM ofertas o
            JOIN empresas e ON e.id = o.empresa_id
            WHERE {where_clause}
        """, params)
        
        total, activas, cerradas, sal_min, sal_max = cur.fetchone()

        cur.execute(f"""
            SELECT COALESCE(AVG(post_count), 0), COUNT(*) FILTER (
                WHERE o.activa = TRUE AND o.fecha_limite_postulacion::date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            )
            FROM ofertas o
            LEFT JOIN (
                SELECT oferta_id, COUNT(*) as post_count
                FROM postulaciones
                GROUP BY oferta_id
            ) p ON p.oferta_id = o.id
            WHERE {where_clause}
        """, params)
        promedio_postulaciones, por_vencer = cur.fetchone()
        
        cur.execute(f"""
            SELECT tipo, COUNT(*)
            FROM ofertas o
            JOIN empresas e ON e.id = o.empresa_id
            WHERE {where_clause}
            GROUP BY tipo
        """, params)
        ofertas_tipo = cur.fetchall()
        
        cur.execute(f"""
            SELECT modalidad, COUNT(*)
            FROM ofertas o
            JOIN empresas e ON e.id = o.empresa_id
            WHERE {where_clause}
            GROUP BY modalidad
        """, params)
        ofertas_modalidad = cur.fetchall()
        
        cur.execute(f"""
            SELECT estado, COUNT(*)
            FROM postulaciones p
            JOIN ofertas o ON p.oferta_id = o.id
            WHERE {where_clause}
            GROUP BY estado
        """, params)
        postulaciones_estado = cur.fetchall()

        cur.execute(f"""
            SELECT 
                o.id,
                o.titulo,
                e.razon_social,
                o.tipo,
                o.modalidad,
                o.fecha_publicacion,
                o.fecha_limite_postulacion,
                o.activa,
                COUNT(p.id) as postulaciones
            FROM ofertas o
            JOIN empresas e ON e.id = o.empresa_id
            LEFT JOIN postulaciones p ON p.oferta_id = o.id
            WHERE {where_clause}
            GROUP BY o.id, e.razon_social
            ORDER BY o.fecha_publicacion DESC
        """, params)
        detalle_ofertas = cur.fetchall()
        
        col3, col4, col5, col6 = st.columns(4)
        col3.metric("Total Ofertas", total or 0)
        col4.metric("Activas", activas or 0)
        col5.metric("Cerradas", cerradas or 0)
        if sal_min and sal_max:
            col6.metric("Salario Promedio", f"S/. {sal_min:.0f} - {sal_max:.0f}")
        else:
            col6.metric("Salario Promedio", "No disponible")

        col7, col8 = st.columns(2)
        col7.metric("Promedio Postulaciones/Oferta", f"{float(promedio_postulaciones or 0):.1f}")
        col8.metric("Vacantes por Vencer", int(por_vencer or 0))
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            if ofertas_tipo:
                st.subheader("Ofertas por Tipo")
                df_tipo = pd.DataFrame(ofertas_tipo, columns=['Tipo', 'Cantidad'])
                fig = px.bar(df_tipo, x='Tipo', y='Cantidad', title='Distribución por Tipo')
                st.plotly_chart(fig, use_container_width=True)
        
        with col_g2:
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

        if detalle_ofertas:
            st.subheader("Detalle de Ofertas Filtradas")
            df_ofertas = pd.DataFrame(
                detalle_ofertas,
                columns=['ID', 'Título', 'Empresa', 'Tipo', 'Modalidad', 'Fecha Publicación', 'Fecha Límite', 'Activa', 'Postulaciones']
            )
            df_ofertas['Fecha Publicación'] = pd.to_datetime(df_ofertas['Fecha Publicación']).dt.strftime('%d/%m/%Y')
            df_ofertas['Fecha Límite'] = pd.to_datetime(df_ofertas['Fecha Límite']).dt.strftime('%d/%m/%Y')
            df_ofertas['Estado'] = df_ofertas['Activa'].map(lambda x: 'Activa' if x else 'Cerrada')
            st.dataframe(
                df_ofertas[['Título', 'Empresa', 'Tipo', 'Modalidad', 'Fecha Publicación', 'Fecha Límite', 'Postulaciones', 'Estado']],
                use_container_width=True,
                hide_index=True,
            )

            ofertas_pdf = []
            for _, row in df_ofertas.iterrows():
                ofertas_pdf.append(
                    {
                        'titulo': row['Título'],
                        'empresa': row['Empresa'],
                        'tipo': row['Tipo'],
                        'modalidad': row['Modalidad'],
                        'fecha_limite_postulacion': datetime.strptime(row['Fecha Límite'], '%d/%m/%Y'),
                        'activa': row['Estado'] == 'Activa',
                        'postulaciones': row['Postulaciones'],
                    }
                )
            pdf_ofertas = generar_pdf_ofertas_lista(ofertas_pdf, titulo='Reporte de Ofertas Filtradas')
            st.download_button(
                '📄 Exportar ofertas filtradas (PDF)',
                data=pdf_ofertas,
                file_name='Reporte_ofertas_filtradas.pdf',
                mime='application/pdf',
                use_container_width=True,
            )

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
                fig = px.line(df_diario, x='Fecha', y='Monto', title='Evolución Diaria', markers=True)
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
                # Quitar zonas horarias de columnas datetime para compatibilidad con openpyxl/Excel
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        try:
                            df[col] = df[col].dt.tz_localize(None)
                        except Exception:
                            # Si ya es naive o falla, intentamos convertir a string o simplemente ignorar
                            pass
                
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
                if tipo == 'Empresas':
                    empresas_pdf = []
                    for row in datos:
                        empresas_pdf.append(
                            {
                                'ruc': row[0],
                                'razon_social': row[1],
                                'sector_economico': row[2],
                                'tamano_empresa': row[3],
                                'estado': row[6],
                            }
                        )
                    kpis_pdf = {
                        'total': len(empresas_pdf),
                        'activas': sum(1 for e in empresas_pdf if e.get('estado') == 'activa'),
                        'pendientes': sum(1 for e in empresas_pdf if e.get('estado') == 'pendiente'),
                        'rechazadas': sum(1 for e in empresas_pdf if e.get('estado') == 'rechazada'),
                        'top_sectores': ', '.join(
                            pd.Series([e.get('sector_economico') for e in empresas_pdf]).value_counts().head(3).index.tolist()
                        ) if empresas_pdf else '—',
                    }
                    pdf_bytes = generar_pdf_empresas_seleccionadas(empresas_pdf, kpis_pdf, titulo='Reporte de Empresas')
                    st.download_button(
                        'Descargar PDF',
                        data=pdf_bytes,
                        file_name=f'reporte_{tipo}_{date.today()}.pdf',
                        mime='application/pdf',
                        use_container_width=True,
                    )
                elif tipo == 'Ofertas':
                    ofertas_pdf = []
                    for row in datos:
                        ofertas_pdf.append(
                            {
                                'titulo': row[0],
                                'empresa': row[1],
                                'tipo': row[2],
                                'modalidad': row[3],
                                'fecha_limite_postulacion': row[7],
                                'activa': row[8],
                                'postulaciones': row[9],
                            }
                        )
                    pdf_bytes = generar_pdf_ofertas_lista(ofertas_pdf, titulo='Reporte de Ofertas')
                    st.download_button(
                        'Descargar PDF',
                        data=pdf_bytes,
                        file_name=f'reporte_{tipo}_{date.today()}.pdf',
                        mime='application/pdf',
                        use_container_width=True,
                    )
                else:
                    st.warning("Exportación PDF disponible por ahora solo para Empresas y Ofertas.")
            
            add_notification(f"Reporte de {tipo} generado exitosamente", "success")
            
    except Exception as e:
        add_notification(f"Error al generar reporte: {str(e)}", "error")