"""
Módulo de búsqueda de ofertas laborales para egresados.
Permite filtrar y postularse a ofertas disponibles.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from src.utils.database import get_db_cursor
from src.utils.session import add_notification, render_notifications
from src.utils.pdf_generator import generar_pdf_oferta_detalle

def show():
    """Muestra la página de búsqueda de ofertas."""
    user = st.session_state.user
    if user.get('rol') != 'egresado':
        st.error("Solo egresados pueden acceder a esta página.")
        return

    st.title("💼 Buscar Ofertas Laborales")
    render_notifications()
    
    # Inicializar filtros en sesión si no existen
    if 'filtros_ofertas' not in st.session_state:
        st.session_state.filtros_ofertas = {}
    
    with st.expander("🔍 Filtros de búsqueda", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            palabra_clave = st.text_input(
                "Palabra clave",
                value=st.session_state.filtros_ofertas.get('palabra_clave', ''),
                placeholder="Ej: Ingeniero, Python, Ventas..."
            )
            tipo_oferta = st.selectbox(
                "Tipo de Oferta",
                options=['Todos', 'empleo', 'pasantia', 'practicas'],
                index=0
            )
        with col2:
            modalidad = st.selectbox(
                "Modalidad",
                options=['Todas', 'presencial', 'remoto', 'hibrido'],
                index=0
            )
            fecha_hasta = st.date_input(
                "Mostrar ofertas hasta",
                value=date.today() + pd.DateOffset(months=1),
                min_value=date.today()
            )
        with col3:
            salario_min = st.number_input("Salario mínimo (S/)", min_value=0, value=0, step=500)
            salario_max = st.number_input("Salario máximo (S/)", min_value=0, value=10000, step=500)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Aplicar Filtros", use_container_width=True):
                guardar_filtros(palabra_clave, tipo_oferta, modalidad, salario_min, salario_max, fecha_hasta)
                st.rerun()
        with b2:
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
            o.requisitos,
            o.ubicacion,
            e.razon_social as empresa,
            e.ruc as empresa_ruc,
            e.logo_url,
            e.sitio_web,
            COUNT(p_all.id) as total_postulaciones,
            p_user.estado as mi_estado,
            p_user.fecha_postulacion as mi_fecha_postulacion,
            p_user.comentario_revision as mi_comentario
        FROM ofertas o
        JOIN empresas e ON o.empresa_id = e.id
        LEFT JOIN postulaciones p_all ON o.id = p_all.oferta_id
        LEFT JOIN postulaciones p_user ON o.id = p_user.oferta_id 
            AND p_user.egresado_id = (SELECT id FROM egresados WHERE usuario_id = %s)
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
        GROUP BY 
            o.id, o.titulo, o.descripcion, o.tipo, o.modalidad, o.salario_min, 
            o.salario_max, o.fecha_publicacion, o.fecha_limite_postulacion, 
            o.requisitos, o.ubicacion, e.razon_social, e.ruc, e.logo_url, e.sitio_web,
            p_user.estado, p_user.fecha_postulacion, p_user.comentario_revision
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
            if oferta.get('ubicacion'):
                badges.append(f"🗺️ {oferta['ubicacion']}")
            
            if oferta['salario_min'] and oferta['salario_max']:
                badges.append(f"💰 S/ {oferta['salario_min']} - {oferta['salario_max']}")
            elif oferta['salario_min']:
                badges.append(f"💰 Desde S/ {oferta['salario_min']}")
            
            st.write(" | ".join(badges))
            st.write(f"{oferta['descripcion'][:150]}...")
            st.caption(f"Publicado: {oferta['fecha_publicacion'].strftime('%d/%m/%Y')} | Límite: {oferta['fecha_limite_postulacion'].strftime('%d/%m/%Y')}")

        with col3:
            st.write("") # Espaciador
            if oferta.get('mi_estado'):
                st.success(f"✅ Postulado")
                with st.expander("📝 Detalle Seguimiento"):
                    st.write(f"**Estado:** {oferta['mi_estado'].replace('_', ' ').capitalize()}")
                    st.write(f"**Fecha:** {oferta['mi_fecha_postulacion'].strftime('%d/%m/%Y')}")
                    if oferta.get('mi_comentario'):
                        st.info(f"**Nota:** {oferta['mi_comentario']}")
            else:
                if st.button("Postular Ahora", key=f"post_{oferta['id']}", type="primary", use_container_width=True):
                    postular_a_oferta(oferta['id'])

            salario_txt = "No especificado"
            if oferta.get('salario_min') and oferta.get('salario_max'):
                salario_txt = f"S/ {oferta['salario_min']} - S/ {oferta['salario_max']}"
            elif oferta.get('salario_min'):
                salario_txt = f"Desde S/ {oferta['salario_min']}"

            pdf_data = {
                "titulo": oferta.get("titulo"),
                "tipo": oferta.get("tipo"),
                "modalidad": oferta.get("modalidad"),
                "ubicacion": oferta.get("ubicacion") or "No especificada",
                "salario": salario_txt,
                "fecha_publicacion": oferta.get("fecha_publicacion").strftime("%d/%m/%Y") if oferta.get("fecha_publicacion") else "",
                "fecha_limite": oferta.get("fecha_limite_postulacion").strftime("%d/%m/%Y") if oferta.get("fecha_limite_postulacion") else "",
                "activa": True,
                "descripcion": oferta.get("descripcion"),
                "requisitos": oferta.get("requisitos"),
            }
            pdf_bytes = generar_pdf_oferta_detalle(
                empresa_data={"razon_social": oferta.get("empresa"), "ruc": oferta.get("empresa_ruc")},
                oferta_data=pdf_data,
                public_url=oferta.get("sitio_web"),
            )
            st.download_button(
                "📄 PDF Oferta",
                data=pdf_bytes,
                file_name=f"Oferta_{str(oferta.get('titulo', 'detalle')).strip().replace(' ', '_')[:40]}.pdf",
                mime="application/pdf",
                key=f"pdf_of_{oferta['id']}",
                use_container_width=True,
            )
        
        st.markdown("---")

def postular_a_oferta(oferta_id):
    """Registra la postulación del egresado a una oferta."""
    
    usuario_id = st.session_state.user['id']
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Obtener el ID del egresado
            cur.execute("SELECT id FROM egresados WHERE usuario_id = %s", (usuario_id,))
            res = cur.fetchone()
            if not res:
                add_notification("Error: No se encontró perfil de egresado.", "error")
                return
            
            egresado_id = res[0]
            
            # Insertar postulación
            cur.execute("""
                INSERT INTO postulaciones (oferta_id, egresado_id, fecha_postulacion, estado)
                VALUES (%s, %s, NOW(), 'recibido')
                ON CONFLICT (oferta_id, egresado_id) DO NOTHING
                RETURNING id
            """, (oferta_id, egresado_id))

            inserted = cur.fetchone()
            if inserted:
                add_notification("¡Postulación enviada con éxito!", "success")
            else:
                add_notification("Ya estabas postulado a esta oferta.", "warning")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al postular: {str(e)}", "error")