"""
Módulo de gestión de empresas para administradores.
Permite ver, aprobar y gestionar empresas registradas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.database import get_db_cursor
from src.utils.session import add_notification

def show():
    """Muestra la página de gestión de empresas."""
    
    st.title("🏢 Gestión de Empresas")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs([
        "📋 Pendientes de Aprobación",
        "✅ Empresas Activas",
        "📊 Estadísticas"
    ])
    
    with tab1:
        mostrar_empresas_pendientes()
    
    with tab2:
        mostrar_empresas_activas()
    
    with tab3:
        mostrar_estadisticas_empresas()

def mostrar_empresas_pendientes():
    """Muestra las empresas pendientes de aprobación."""
    
    st.subheader("Empresas Pendientes de Aprobación")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                e.id,
                e.ruc,
                e.razon_social,
                e.nombre_comercial,
                e.sector_economico,
                e.tamano_empresa,
                e.email_contacto,
                e.telefono_contacto,
                e.fecha_registro,
                COUNT(o.id) as total_ofertas
            FROM empresas e
            LEFT JOIN ofertas o ON e.id = o.empresa_id
            WHERE e.estado = 'pendiente'
            GROUP BY e.id
            ORDER BY e.fecha_registro ASC
        """)
        
        empresas = cur.fetchall()
        
        if not empresas:
            st.success("No hay empresas pendientes de aprobación.")
            return
        
        for empresa in empresas:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"### {empresa[2]}")
                    st.markdown(f"**RUC:** {empresa[1]} | **Sector:** {empresa[4]}")
                    st.markdown(f"**Contacto:** {empresa[6]} | {empresa[7]}")
                    st.markdown(f"**Registro:** {empresa[8].strftime('%d/%m/%Y')}")
                
                with col2:
                    st.metric("Ofertas", empresa[9])
                
                with col3:
                    if st.button("✅ Aprobar", key=f"apr_{empresa[0]}", use_container_width=True):
                        aprobar_empresa(empresa[0])
                    if st.button("❌ Rechazar", key=f"rej_{empresa[0]}", use_container_width=True):
                        rechazar_empresa(empresa[0])
                
                with st.expander("Ver detalles completos"):
                    mostrar_detalles_empresa(empresa[0])
                
                st.markdown("---")

def mostrar_empresas_activas():
    """Muestra las empresas activas en el sistema."""
    
    st.subheader("Empresas Activas")
    
    # Filtros de búsqueda
    col1, col2 = st.columns(2)
    with col1:
        busqueda = st.text_input("🔍 Buscar por RUC o Razón Social", placeholder="Ingrese término...")
    with col2:
        sector = st.selectbox(
            "Sector Económico",
            options=['Todos', 'Tecnología', 'Salud', 'Educación', 'Finanzas', 'Construcción', 'Otros']
        )
    
    query = """
        SELECT 
            e.id,
            e.ruc,
            e.razon_social,
            e.sector_economico,
            e.tamano_empresa,
            e.email_contacto,
            e.telefono_contacto,
            e.fecha_aprobacion,
            COUNT(DISTINCT em.id) as total_empleadores,
            COUNT(DISTINCT o.id) as total_ofertas
        FROM empresas e
        LEFT JOIN empleadores em ON e.id = em.empresa_id
        LEFT JOIN ofertas o ON e.id = o.empresa_id
        WHERE e.estado = 'activa'
    """
    params = []
    
    if busqueda:
        query += """ AND (
            e.ruc ILIKE %s OR 
            e.razon_social ILIKE %s OR
            e.nombre_comercial ILIKE %s
        )"""
        busqueda_param = f"%{busqueda}%"
        params.extend([busqueda_param, busqueda_param, busqueda_param])
    
    if sector != 'Todos':
        query += " AND e.sector_economico = %s"
        params.append(sector)
    
    query += """
        GROUP BY e.id
        ORDER BY e.razon_social
        LIMIT 100
    """
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        empresas = cur.fetchall()
        
        if empresas:
            # Convertir a DataFrame para mostrar
            df = pd.DataFrame(
                empresas,
                columns=['ID', 'RUC', 'Razón Social', 'Sector', 'Tamaño',
                        'Email', 'Teléfono', 'Aprobación', 'Empleadores', 'Ofertas']
            )
            
            # Formatear fechas
            df['Aprobación'] = pd.to_datetime(df['Aprobación']).dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                df[['RUC', 'Razón Social', 'Sector', 'Tamaño', 'Empleadores', 'Ofertas']],
                use_container_width=True,
                hide_index=True
            )
            
            # Opción para ver detalles de cada empresa
            empresa_seleccionada = st.selectbox(
                "Seleccionar empresa para ver detalles",
                options=df['ID'].tolist(),
                format_func=lambda x: df[df['ID'] == x]['Razón Social'].iloc[0]
            )
            
            if empresa_seleccionada:
                with st.expander("Detalles de la empresa", expanded=True):
                    mostrar_detalles_empresa(empresa_seleccionada)
        else:
            st.info("No se encontraron empresas con los filtros aplicados.")

def mostrar_estadisticas_empresas():
    """Muestra estadísticas de empresas en el sistema."""
    
    st.subheader("Estadísticas de Empresas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with get_db_cursor() as cur:
        # Total empresas
        cur.execute("SELECT COUNT(*) FROM empresas")
        total = cur.fetchone()[0]
        col1.metric("Total Empresas", total)
        
        # Empresas por estado
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE estado = 'activa') as activas,
                COUNT(*) FILTER (WHERE estado = 'pendiente') as pendientes,
                COUNT(*) FILTER (WHERE estado = 'rechazada') as rechazadas
            FROM empresas
        """)
        activas, pendientes, rechazadas = cur.fetchone()
        col2.metric("Activas", activas)
        col3.metric("Pendientes", pendientes)
        col4.metric("Rechazadas", rechazadas)
    
    st.markdown("---")
    
    # Gráfico de empresas por sector
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT sector_economico, COUNT(*)
            FROM empresas
            WHERE estado = 'activa'
            GROUP BY sector_economico
            ORDER BY COUNT(*) DESC
        """)
        datos_sector = cur.fetchall()
        
        if datos_sector:
            df_sector = pd.DataFrame(datos_sector, columns=['Sector', 'Cantidad'])
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Empresas por Sector")
                st.bar_chart(df_sector.set_index('Sector'))
            
            with col_b:
                st.subheader("Distribución por Tamaño")
                cur.execute("""
                    SELECT tamano_empresa, COUNT(*)
                    FROM empresas
                    WHERE estado = 'activa'
                    GROUP BY tamano_empresa
                """)
                df_tamano = pd.DataFrame(cur.fetchall(), columns=['Tamaño', 'Cantidad'])
                if not df_tamano.empty:
                    st.dataframe(df_tamano)
    
    # Empresas con más ofertas
    st.subheader("Top 10 Empresas con más Ofertas")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                e.razon_social,
                COUNT(o.id) as total_ofertas,
                COUNT(DISTINCT o.id) FILTER (WHERE o.activa) as ofertas_activas
            FROM empresas e
            LEFT JOIN ofertas o ON e.id = o.empresa_id
            WHERE e.estado = 'activa'
            GROUP BY e.id, e.razon_social
            HAVING COUNT(o.id) > 0
            ORDER BY total_ofertas DESC
            LIMIT 10
        """)
        top_empresas = cur.fetchall()
        
        if top_empresas:
            df_top = pd.DataFrame(
                top_empresas,
                columns=['Empresa', 'Total Ofertas', 'Ofertas Activas']
            )
            st.dataframe(df_top, use_container_width=True, hide_index=True)

def mostrar_detalles_empresa(empresa_id):
    """Muestra los detalles completos de una empresa."""
    
    with get_db_cursor() as cur:
        # Datos de la empresa
        cur.execute("""
            SELECT *
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        columnas = [desc[0] for desc in cur.description]
        empresa = dict(zip(columnas, cur.fetchone()))
        
        # Mostrar información
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Legal**")
            st.write(f"**RUC:** {empresa['ruc']}")
            st.write(f"**Razón Social:** {empresa['razon_social']}")
            st.write(f"**Nombre Comercial:** {empresa.get('nombre_comercial', 'N/A')}")
            st.write(f"**Sector:** {empresa.get('sector_economico', 'N/A')}")
            st.write(f"**Tamaño:** {empresa.get('tamano_empresa', 'N/A')}")
        
        with col2:
            st.markdown("**Contacto**")
            st.write(f"**Email:** {empresa.get('email_contacto', 'N/A')}")
            st.write(f"**Teléfono:** {empresa.get('telefono_contacto', 'N/A')}")
            st.write(f"**Dirección:** {empresa.get('direccion', 'N/A')}")
            st.write(f"**Sitio Web:** {empresa.get('sitio_web', 'N/A')}")
        
        # Lista de empleadores de la empresa
        st.subheader("Empleadores Registrados")
        cur.execute("""
            SELECT 
                u.email,
                e.nombres,
                e.apellidos,
                e.cargo,
                e.es_administrador_empresa
            FROM empleadores e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.empresa_id = %s
        """, (empresa_id,))
        
        empleadores = cur.fetchall()
        if empleadores:
            df_emp = pd.DataFrame(
                empleadores,
                columns=['Email', 'Nombres', 'Apellidos', 'Cargo', 'Es Admin']
            )
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
        else:
            st.info("No hay empleadores registrados para esta empresa")
        
        # Ofertas de la empresa
        st.subheader("Ofertas Publicadas")
        cur.execute("""
            SELECT 
                titulo,
                tipo,
                modalidad,
                fecha_publicacion,
                fecha_limite_postulacion,
                activa,
                (SELECT COUNT(*) FROM postulaciones WHERE oferta_id = o.id) as postulaciones
            FROM ofertas o
            WHERE empresa_id = %s
            ORDER BY fecha_publicacion DESC
            LIMIT 20
        """, (empresa_id,))
        
        ofertas = cur.fetchall()
        if ofertas:
            df_ofertas = pd.DataFrame(
                ofertas,
                columns=['Título', 'Tipo', 'Modalidad', 'Publicación', 
                        'Límite', 'Activa', 'Postulaciones']
            )
            st.dataframe(df_ofertas, use_container_width=True, hide_index=True)
        else:
            st.info("Esta empresa aún no ha publicado ofertas")

def aprobar_empresa(empresa_id):
    """Aprueba una empresa pendiente."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Actualizar estado de la empresa
            cur.execute("""
                UPDATE empresas
                SET estado = 'activa',
                    fecha_aprobacion = NOW(),
                    aprobado_por = %s
                WHERE id = %s
            """, (st.session_state.user['id'], empresa_id))
            
            # Notificar a los empleadores de la empresa
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                SELECT u.id, 'email', 'Empresa aprobada',
                       'Su empresa ha sido aprobada en el sistema. Ya puede publicar ofertas.'
                FROM empleadores e
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.empresa_id = %s
            """, (empresa_id,))
            
            # Registrar en bitácora
            cur.execute("""
                INSERT INTO bitacora_auditoria
                (usuario_id, perfil_utilizado, accion, modulo, detalle)
                VALUES (%s, %s, 'UPDATE', 'empresas', %s)
            """, (
                st.session_state.user['id'],
                st.session_state.user['rol'],
                f"Empresa aprobada: {empresa_id}"
            ))
        
        add_notification("Empresa aprobada exitosamente", "success")
        st.rerun()
        
    except Exception as e:
        add_notification(f"Error al aprobar empresa: {str(e)}", "error")

def rechazar_empresa(empresa_id):
    """Rechaza una empresa pendiente."""
    
    motivo = st.text_area("Motivo del rechazo", key=f"motivo_{empresa_id}")
    
    if st.button("Confirmar Rechazo", key=f"conf_{empresa_id}"):
        try:
            with get_db_cursor(commit=True) as cur:
                # Actualizar estado
                cur.execute("""
                    UPDATE empresas
                    SET estado = 'rechazada'
                    WHERE id = %s
                """, (empresa_id,))
                
                # Notificar rechazo
                cur.execute("""
                    INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                    SELECT u.id, 'email', 'Empresa no aprobada',
                           'Su empresa no ha sido aprobada. Motivo: ' || %s
                    FROM empleadores e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE e.empresa_id = %s
                """, (motivo, empresa_id))
                
                # Registrar en bitácora
                cur.execute("""
                    INSERT INTO bitacora_auditoria
                    (usuario_id, perfil_utilizado, accion, modulo, detalle)
                    VALUES (%s, %s, 'UPDATE', 'empresas', %s)
                """, (
                    st.session_state.user['id'],
                    st.session_state.user['rol'],
                    f"Empresa rechazada: {empresa_id} - Motivo: {motivo}"
                ))
            
            add_notification("Empresa rechazada", "warning")
            st.rerun()
            
        except Exception as e:
            add_notification(f"Error al rechazar empresa: {str(e)}", "error")