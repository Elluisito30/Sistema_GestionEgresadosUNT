"""
Módulo de gestión de ofertas laborales.
Permite a empresas y administradores crear, editar y cerrar ofertas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from src.utils.database import get_db_cursor
from src.utils.session import add_notification

def show():
    user = st.session_state.user
    rol = user['rol']
    
    st.title("📢 Gestión de Ofertas Laborales")
    
    if rol == 'egresado':
        st.error("No tienes permisos para acceder a esta página.")
        return

    # Tabs para organizar
    if rol == 'administrador':
        tab1, tab2 = st.tabs(["🔍 Todas las Ofertas", "➕ Nueva Oferta (Admin)"])
    else:
        tab1, tab2 = st.tabs(["📋 Mis Ofertas", "➕ Publicar Nueva Oferta"])

    with tab1:
        mostrar_lista_ofertas(user, rol)
    
    with tab2:
        mostrar_formulario_oferta(user, rol)

def obtener_empresa_id(usuario_id):
    """Obtiene el ID de la empresa para un empleador."""
    with get_db_cursor() as cur:
        cur.execute("SELECT empresa_id FROM empleadores WHERE usuario_id = %s", (usuario_id,))
        res = cur.fetchone()
        return res[0] if res else None

def mostrar_lista_ofertas(user, rol):
    st.subheader("Ofertas Publicadas")
    
    query = """
        SELECT 
            o.id, o.titulo, o.tipo, o.modalidad, o.fecha_publicacion, 
            o.fecha_limite_postulacion, o.activa,
            e.razon_social as empresa,
            (SELECT COUNT(*) FROM postulaciones WHERE oferta_id = o.id) as postulaciones
        FROM ofertas o
        JOIN empresas e ON o.empresa_id = e.id
    """
    params = []
    
    if rol == 'empleador':
        empresa_id = obtener_empresa_id(user['id'])
        query += " WHERE o.empresa_id = %s"
        params.append(empresa_id)
    
    query += " ORDER BY o.fecha_publicacion DESC"
    
    try:
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            ofertas = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        if not ofertas:
            st.info("No hay ofertas publicadas aún.")
            return
            
        df = pd.DataFrame(ofertas)
        df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion']).dt.strftime('%d/%m/%Y')
        df['fecha_limite'] = pd.to_datetime(df['fecha_limite_postulacion']).dt.strftime('%d/%m/%Y')
        df['Estado'] = df['activa'].map({True: '✅ Activa', False: '❌ Cerrada'})
        
        cols_to_show = ['titulo', 'empresa', 'tipo', 'modalidad', 'fecha_publicacion', 'fecha_limite', 'postulaciones', 'Estado']
        if rol == 'empleador':
            cols_to_show.remove('empresa')
            
        st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
        
        # Acciones rápidas
        st.subheader("Acciones")
        selected_id = st.selectbox("Seleccionar oferta para gestionar:", options=[o['id'] for o in ofertas], format_func=lambda x: next(o['titulo'] for o in ofertas if o['id'] == x))
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Toggle Estado (Activa/Cerrada)", key="btn_toggle"):
                toggle_oferta_estado(selected_id)
        with col_b:
            if st.button("Ver Postulaciones", key="btn_ver_post"):
                st.session_state.selected_oferta_id = selected_id
                st.session_state.current_page = "postulaciones_revisar"
                st.rerun()

    except Exception as e:
        st.error(f"Error al cargar ofertas: {e}")

def toggle_oferta_estado(oferta_id):
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE ofertas SET activa = NOT activa WHERE id = %s", (oferta_id,))
        add_notification("Estado de la oferta actualizado", "success")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def mostrar_formulario_oferta(user, rol):
    st.subheader("Detalles de la Oferta")
    
    empresa_id = None
    if rol == 'empleador':
        empresa_id = obtener_empresa_id(user['id'])
        if not empresa_id:
            st.error("No tienes una empresa asociada.")
            return
    else:
        # Admin elige empresa
        with get_db_cursor() as cur:
            cur.execute("SELECT id, razon_social FROM empresas WHERE estado = 'activa'")
            empresas = cur.fetchall()
            empresa_id = st.selectbox("Empresa", options=[e[0] for e in empresas], format_func=lambda x: next(e[1] for e in empresas if e[0] == x))

    with st.form("form_nueva_oferta"):
        titulo = st.text_input("Título de la Posición *")
        descripcion = st.text_area("Descripción del Puesto *")
        
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", options=['empleo', 'pasantia', 'practicas'])
            modalidad = st.selectbox("Modalidad", options=['presencial', 'remoto', 'hibrido'])
        
        with col2:
            salario_min = st.number_input("Salario Mínimo (S/.)", min_value=0, value=0)
            salario_max = st.number_input("Salario Máximo (S/.)", min_value=0, value=0)
        
        fecha_limite = st.date_input("Fecha Límite de Postulación", value=date.today() + pd.DateOffset(months=1))
        
        carreras = st.multiselect("Carreras Objetivo", options=["Informática", "Sistemas", "Administración", "Contabilidad", "Derecho", "Medicina", "Ingeniería Industrial"])
        
        submitted = st.form_submit_button("Publicar Oferta", type="primary")
        
        if submitted:
            if not titulo or not descripcion:
                st.error("Título y descripción son obligatorios.")
            else:
                crear_oferta(empresa_id, titulo, descripcion, tipo, modalidad, salario_min, salario_max, fecha_limite, carreras)

def crear_oferta(empresa_id, titulo, descripcion, tipo, modalidad, s_min, s_max, f_limite, carreras):
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO ofertas 
                (empresa_id, titulo, descripcion, tipo, modalidad, salario_min, salario_max, fecha_limite_postulacion, carrera_objetivo, activa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
            """, (empresa_id, titulo, descripcion, tipo, modalidad, s_min, s_max, f_limite, carreras))
        add_notification("Oferta publicada exitosamente", "success")
        st.rerun()
    except Exception as e:
        st.error(f"Error al crear oferta: {e}")
