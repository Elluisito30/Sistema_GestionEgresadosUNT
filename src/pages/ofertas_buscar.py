"""
Módulo de búsqueda de ofertas laborales para egresados.
Permite filtrar y postularse a ofertas disponibles.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from src.utils.database import get_db_cursor
from src.utils.session import add_notification, set_filter, get_filter

def show():
    """Muestra la página de búsqueda de ofertas."""
    
    st.title("💼 Buscar Ofertas Laborales")
    
    # Inicializar filtros en sesión si no existen
    if 'filtros_ofertas' not in st.session_state:
        st.session_state.filtros_ofertas = {}
    
    # Sidebar con filtros
    with st.sidebar:
        st.header("Filtros de Búsqueda")
        
        # Búsqueda por palabra clave
        palabra_clave = st.text_input(
            "🔍 Palabra clave",
            value=st.session_state.filtros_ofertas.get('palabra_clave', ''),
            placeholder="Ej: Ingeniero, Python, Ventas..."
        )
        
        st.markdown("---")
        
        # Filtros principales
        tipo_oferta = st.selectbox(
            "Tipo de Oferta",
            options=['Todos', 'empleo', 'pasantia', 'practicas'],
            index=0
        )
        
        modalidad = st.selectbox(
            "Modalidad",
            options=['Todas', 'presencial', 'remoto', 'hibrido'],
            index=0
        )
        
        # Rango salarial
        st.subheader("Rango Salarial (S/.)")
        salario_min = st.number_input("Mínimo", min_value=0, value=0, step=500)
        salario_max = st.number_input("Máximo", min_value=0, value=10000, step=500)
        
        # Fecha límite
        st.subheader("Fecha Límite")
        fecha_hasta = st.date_input(
            "Mostrar ofertas hasta",
            value=date.today() + pd.DateOffset(months=1),
            min_value=date.today()
        )
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aplicar Filtros", use_container_width=True):
                guardar_filtros(palabra_clave, tipo_oferta, modalidad,
                              salario_min, salario_max, fecha_hasta)
                st.rerun()
        
        with col2:
            if st.button("Limpiar Filtros", use_container_width=True):
                st.session_state.filtros_ofertas = {}
                st.rerun()
    
    # Contenido principal
    ofertas = buscar_ofertas()
    
    if not ofertas:
        st.info("No se encontraron ofertas con los filtros seleccionados.")
        return
    
    # Mostrar estadísticas
    st.subheader(f"📊 {len(ofertas)} ofertas encontradas")
    
    # Mostrar ofertas en tarjetas
    for oferta in ofertas:
        mostrar_tarjeta_oferta(oferta)

def guardar_filtros(palabra_clave, tipo_oferta, modalidad, salario_min, salario_max, fecha_hasta):
    """Guarda los filtros en la sesión."""
    st.session_state.filtros_ofertas = {
        'palabra_clave': palabra_clave,
        'tipo_oferta': None if tipo_oferta == 'Todos' else tipo_oferta,
        'modalidad': None if modalidad == 'Todas' else modalidad,
        'salario_min': salario_min if salario_min > 0 else None,
        'salario_max': salario_max if salario_max < 10000 else None,
        'fecha_hasta': fecha_hasta
    }

def buscar_ofertas():
    """Busca ofertas en la BD aplicando los filtros."""
    
    filtros = st.session_state.filtros_ofertas
    query = """
        SELECT 
            o.id,
            o.titulo,
            o.descripcion,
            o.tipo,
            o.modalidad,
            o.salario_min,
            o.salario_max,
            o.fecha_publicacion,
            o.fecha_limite_postulacion,
            e.razon_social as empresa,
            e.logo_url,
            COUNT(p.id) as total_postulaciones,
            BOOL_OR(p.egresado_id = (SELECT id FROM egresados WHERE usuario_id = %s)) as ya_postulado
        FROM ofertas o
        JOIN empresas e ON o.empresa_id = e.id
        LEFT JOIN postulaciones p ON o.id = p.oferta_id
        WHERE o.activa = true
        AND o.fecha_limite_postulacion >= CURRENT_DATE
    """
    params = [st.session_state.user['id']]
    
    # Aplicar filtros
    if filtros.get('palabra_clave'):
        query += """ AND (
            o.titulo ILIKE %s OR 
            o.descripcion ILIKE %s OR
            e.razon_social ILIKE %s
        )"""
        palabra = f"%{filtros['palabra_clave']}%"
        params.extend([palabra, palabra, palabra])
    
    if filtros.get('tipo_oferta'):
        query += " AND o.tipo = %s"
        params.append(filtros['tipo_oferta'])
    
    if filtros.get('modalidad'):
        query += " AND o.modalidad = %s"
        params.append(filtros['modalidad'])
    
    if filtros.get('salario_min'):
        query += " AND o.salario_max >= %s"
        params.append(filtros['salario_min'])
    
    if filtros.get('salario_max'):
        query += " AND o.salario_min <= %s"
        params.append(filtros['salario_max'])
    
    if filtros.get('fecha_hasta'):
        query += " AND o.fecha_limite_postulacion <= %s"
        params.append(filtros['fecha_hasta'])
    
    query += """
        GROUP BY o.id, e.razon_social, e.logo_url
        ORDER BY o.fecha_publicacion DESC
        LIMIT 50
    """
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        resultados = []
        for row in cur.fetchall():
            resultados.append(dict(zip(columns, row)))
        
        return resultados

def mostrar_tarjeta_oferta(oferta):
    """Muestra una oferta en formato de tarjeta."""
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Logo de la empresa
            if oferta.get('logo_url'):
                st.image(oferta['logo_url'], width=80)
            else:
                st.markdown("🏢")
        
        with col2:
            st.markdown(f"### {oferta['titulo']}")
            st.markdown(f"**{oferta['empresa']}**")
            
            # Detalles en badges
            badges = []
            badges.append(f"📍 {oferta['modalidad'].capitalize()}")
            badges.append(f"📋 {oferta['tipo'].capitalize()}")
            if oferta['salario_min'] and oferta