"""
Módulo de auditoría y bitácora.
Permite visualizar todas las acciones del sistema.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.session import add_notification

def show():
    """Muestra la página de auditoría."""
    
    st.title("📋 Bitácora de Auditoría")
    
    user = st.session_state.user
    
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return
    
    # Filtros
    st.subheader("Filtros de Búsqueda")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=7))
    
    with col2:
        fecha_hasta = st.date_input("Hasta", value=date.today())
    
    with col3:
        with get_db_cursor() as cur:
            cur.execute("SELECT DISTINCT accion FROM bitacora_auditoria ORDER BY accion")
            acciones = [a[0] for a in cur.fetchall()]
            acciones.insert(0, "Todas")
            accion_filtro = st.selectbox("Acción", options=acciones)
    
    with col4:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT modulo 
                FROM bitacora_auditoria 
                WHERE modulo IS NOT NULL 
                ORDER BY modulo
            """)
            modulos = [m[0] for m in cur.fetchall()]
            modulos.insert(0, "Todos")
            modulo_filtro = st.selectbox("Módulo", options=modulos)
    
    # Búsqueda por usuario
    email_usuario = st.text_input("🔍 Email de Usuario", placeholder="Ej: admin@unitru.edu.pe")
    
    # Botones
    col5, col6 = st.columns(2)
    with col5:
        buscar = st.button("🔍 Buscar", type="primary", use_container_width=True)
    with col6:
        limpiar = st.button("🗑️ Limpiar Filtros", use_container_width=True)
    
    if limpiar:
        st.rerun()
    
    if buscar or 'ultima_busqueda' in st.session_state:
        mostrar_bitacora(fecha_desde, fecha_hasta, accion_filtro, 
                        modulo_filtro, email_usuario)

def mostrar_bitacora(fecha_desde, fecha_hasta, accion_filtro, modulo_filtro, email_usuario):
    """Muestra los registros de la bitácora con los filtros aplicados."""
    
    query = """
        SELECT 
            b.fecha_hora,
            u.email,
            b.perfil_utilizado,
            b.accion,
            b.modulo,
            b.detalle,
            b.direccion_ip
        FROM bitacora_auditoria b
        LEFT JOIN usuarios u ON b.usuario_id = u.id
        WHERE b.fecha_hora::date BETWEEN %s AND %s
    """
    params = [fecha_desde, fecha_hasta]
    
    if accion_filtro != "Todas":
        query += " AND b.accion = %s"
        params.append(accion_filtro)
    
    if modulo_filtro != "Todos":
        query += " AND b.modulo = %s"
        params.append(modulo_filtro)
    
    if email_usuario:
        query += " AND u.email ILIKE %s"
        params.append(f"%{email_usuario}%")
    
    query += " ORDER BY b.fecha_hora DESC LIMIT 10000"
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        registros = cur.fetchall()
        
        if not registros:
            st.info("No se encontraron registros con los filtros seleccionados")
            return
        
        # Métricas
        st.subheader(f"📊 Resumen ({len(registros)} registros)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Acciones más comunes
        df_temp = pd.DataFrame(registros, columns=['Fecha', 'Usuario', 'Perfil', 'Acción', 'Módulo', 'Detalle', 'IP'])
        
        col1.metric("Total Acciones", len(registros))
        col2.metric("Usuarios Distintos", df_temp['Usuario'].nunique())
        col3.metric("Acción más común", df_temp['Acción'].mode().iloc[0] if not df_temp.empty else "N/A")
        col4.metric("Módulo más activo", df_temp['Módulo'].mode().iloc[0] if not df_temp.empty else "N/A")
        
        st.markdown("---")
        
        # Mostrar tabla
        st.subheader("Registros Detallados")
        
        # Paginación
        registros_por_pagina = 100
        total_paginas = (len(registros) + registros_por_pagina - 1) // registros_por_pagina
        
        if 'pagina_actual' not in st.session_state:
            st.session_state.pagina_actual = 1
        
        col_pag1, col_pag2, col_pag3 = st.columns([1, 3, 1])
        
        with col_pag1:
            if st.button("⬅️ Anterior") and st.session_state.pagina_actual > 1:
                st.session_state.pagina_actual -= 1
                st.rerun()
        
        with col_pag2:
            st.markdown(f"<h5 style='text-align: center'>Página {st.session_state.pagina_actual} de {total_paginas}</h5>", 
                       unsafe_allow_html=True)
        
        with col_pag3:
            if st.button("Siguiente ➡️") and st.session_state.pagina_actual < total_paginas:
                st.session_state.pagina_actual += 1
                st.rerun()
        
        # Mostrar registros de la página actual
        inicio = (st.session_state.pagina_actual - 1) * registros_por_pagina
        fin = min(inicio + registros_por_pagina, len(registros))
        
        registros_pagina = registros[inicio:fin]
        
        df = pd.DataFrame(
            registros_pagina,
            columns=['Fecha y Hora', 'Usuario', 'Perfil', 'Acción', 'Módulo', 'Detalle', 'Dirección IP']
        )
        
        # Formatear fecha
        df['Fecha y Hora'] = pd.to_datetime(df['Fecha y Hora']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Detalle": st.column_config.TextColumn("Detalle", width="large"),
                "Dirección IP": st.column_config.TextColumn("IP", width="small")
            }
        )
        
        # Gráficos de tendencia
        st.markdown("---")
        st.subheader("📈 Tendencias")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Acciones por día
            df['Fecha'] = pd.to_datetime(df['Fecha y Hora']).dt.date
            acciones_dia = df.groupby('Fecha').size().reset_index(name='Cantidad')
            
            if not acciones_dia.empty:
                st.subheader("Acciones por Día")
                st.bar_chart(acciones_dia.set_index('Fecha'))
        
        with col_g2:
            # Acciones por módulo
            acciones_modulo = df.groupby('Módulo').size().reset_index(name='Cantidad')
            
            if not acciones_modulo.empty:
                st.subheader("Acciones por Módulo")
                st.bar_chart(acciones_modulo.set_index('Módulo'))
        
        # Exportar resultados
        st.markdown("---")
        if st.button("📥 Exportar Resultados", use_container_width=True):
            exportar_bitacora(df)

def exportar_bitacora(df):
    """Exporta la bitácora a CSV."""
    
    import io
    import base64
    
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:text/csv;base64,{b64}" download="bitacora_{date.today()}.csv">Descargar CSV</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    add_notification("Archivo exportado exitosamente", "success")