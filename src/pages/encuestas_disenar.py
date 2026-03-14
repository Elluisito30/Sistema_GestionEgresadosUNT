"""
Módulo de diseño de encuestas para administradores.
Permite crear y gestionar encuestas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.session import add_notification
import json

def show():
    """Muestra la página de diseño de encuestas."""
    
    st.title("📝 Diseño de Encuestas")
    
    user = st.session_state.user
    
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "➕ Nueva Encuesta",
        "📋 Encuestas Activas",
        "📊 Resultados"
    ])
    
    with tab1:
        crear_encuesta(user['id'])
    
    with tab2:
        gestionar_encuestas()
    
    with tab3:
        ver_resultados_encuestas()

def crear_encuesta(admin_id):
    """Formulario para crear una nueva encuesta."""
    
    st.subheader("Crear Nueva Encuesta de Seguimiento")
    
    # Inicializar estado para la nueva encuesta
    if 'nueva_encuesta' not in st.session_state:
        st.session_state.nueva_encuesta = {
            'titulo': '',
            'descripcion': '',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=30),
            'preguntas': []
        }
    
    if 'editando_pregunta' not in st.session_state:
        st.session_state.editando_pregunta = -1
    
    # Formulario principal
    with st.form("form_encuesta"):
        titulo = st.text_input("Título de la Encuesta *", 
                               value=st.session_state.nueva_encuesta['titulo'])
        descripcion = st.text_area("Descripción", 
                                  value=st.session_state.nueva_encuesta['descripcion'],
                                  height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de Inicio *", 
                                        value=st.session_state.nueva_encuesta['fecha_inicio'])
        with col2:
            fecha_fin = st.date_input("Fecha de Fin *", 
                                     value=st.session_state.nueva_encuesta['fecha_fin'],
                                     min_value=fecha_inicio)
        
        submitted = st.form_submit_button("Guardar Información Básica")
        
        if submitted:
            st.session_state.nueva_encuesta.update({
                'titulo': titulo,
                'descripcion': descripcion,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            add_notification("Información guardada", "success")
    
    st.markdown("---")
    
    # Gestión de preguntas
    st.subheader("Preguntas de la Encuesta")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("➕ Agregar Nueva Pregunta", type="primary"):
            st.session_state.editando_pregunta = len(st.session_state.nueva_encuesta['preguntas'])
    
    with col2:
        st.write(f"Total preguntas: {len(st.session_state.nueva_encuesta['preguntas'])}")
    
    # Editor de pregunta
    if st.session_state.editando_pregunta >= 0:
        idx = st.session_state.editando_pregunta
        
        # Si es nueva, crear pregunta vacía
        if idx >= len(st.session_state.nueva_encuesta['preguntas']):
            st.session_state.nueva_encuesta['preguntas'].append({
                'texto': '',
                'tipo': 'texto',
                'opciones': []
            })
        
        pregunta = st.session_state.nueva_encuesta['preguntas'][idx]
        
        with st.container(border=True):
            st.markdown(f"**Pregunta {idx + 1}**")
            
            texto = st.text_input("Texto de la pregunta *", value=pregunta['texto'],
                                 key=f"texto_{idx}")
            
            tipo = st.selectbox(
                "Tipo de respuesta",
                options=['texto', 'opcion_multiple', 'escala'],
                format_func=lambda x: {
                    'texto': 'Texto libre',
                    'opcion_multiple': 'Opción múltiple',
                    'escala': 'Escala numérica (1-10)'
                }[x],
                index=['texto', 'opcion_multiple', 'escala'].index(pregunta['tipo']),
                key=f"tipo_{idx}"
            )
            
            if tipo == 'opcion_multiple':
                st.markdown("**Opciones de respuesta** (una por línea)")
                opciones_text = st.text_area(
                    "Ingrese las opciones",
                    value='\n'.join(pregunta['opciones']),
                    key=f"opciones_{idx}"
                )
                opciones = [o.strip() for o in opciones_text.split('\n') if o.strip()]
            else:
                opciones = []
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 Guardar Pregunta", key=f"guardar_{idx}"):
                    st.session_state.nueva_encuesta['preguntas'][idx] = {
                        'texto': texto,
                        'tipo': tipo,
                        'opciones': opciones if tipo == 'opcion_multiple' else []
                    }
                    st.session_state.editando_pregunta = -1
                    st.rerun()
            
            with col_b:
                if st.button("❌ Cancelar", key=f"cancel_{idx}"):
                    if idx >= len(st.session_state.nueva_encuesta['preguntas']) or \
                       not st.session_state.nueva_encuesta['preguntas'][idx]['texto']:
                        # Si es nueva y vacía, eliminar
                        st.session_state.nueva_encuesta['preguntas'].pop(idx)
                    st.session_state.editando_pregunta = -1
                    st.rerun()
    
    # Lista de preguntas existentes
    for i, pregunta in enumerate(st.session_state.nueva_encuesta['preguntas']):
        if i != st.session_state.editando_pregunta:
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                
                with col_a:
                    st.markdown(f"**Pregunta {i + 1}:** {pregunta['texto']}")
                    tipo_texto = {
                        'texto': '📝 Texto libre',
                        'opcion_multiple': '🔘 Opción múltiple',
                        'escala': '📊 Escala 1-10'
                    }[pregunta['tipo']]
                    st.caption(f"Tipo: {tipo_texto}")
                    
                    if pregunta['tipo'] == 'opcion_multiple' and pregunta['opciones']:
                        st.caption(f"Opciones: {', '.join(pregunta['opciones'])}")
                
                with col_b:
                    if st.button("✏️ Editar", key=f"edit_{i}"):
                        st.session_state.editando_pregunta = i
                        st.rerun()
                
                with col_c:
                    if st.button("🗑️ Eliminar", key=f"del_{i}"):
                        st.session_state.nueva_encuesta['preguntas'].pop(i)
                        if st.session_state.editando_pregunta > i:
                            st.session_state.editando_pregunta -= 1
                        st.rerun()
    
    st.markdown("---")
    
    # Botón final para guardar encuesta
    if st.button("💾 GUARDAR ENCUESTA COMPLETA", type="primary", use_container_width=True):
        guardar_encuesta_completa(admin_id)

def guardar_encuesta_completa(admin_id):
    """Guarda la encuesta completa en la base de datos."""
    
    encuesta = st.session_state.nueva_encuesta
    
    # Validaciones
    if not encuesta['titulo']:
        add_notification("El título es obligatorio", "error")
        return
    
    if len(encuesta['preguntas']) == 0:
        add_notification("Debe agregar al menos una pregunta", "error")
        return
    
    for i, p in enumerate(encuesta['preguntas']):
        if not p['texto']:
            add_notification(f"La pregunta {i+1} no tiene texto", "error")
            return
        if p['tipo'] == 'opcion_multiple' and len(p['opciones']) < 2:
            add_notification(f"La pregunta {i+1} debe tener al menos 2 opciones", "error")
            return
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Insertar encuesta
            cur.execute("""
                INSERT INTO encuestas (titulo, descripcion, fecha_inicio, fecha_fin, creada_por)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                encuesta['titulo'],
                encuesta['descripcion'],
                encuesta['fecha_inicio'],
                encuesta['fecha_fin'],
                admin_id
            ))
            
            encuesta_id = cur.fetchone()[0]
            
            # Insertar preguntas
            for pregunta in encuesta['preguntas']:
                cur.execute("""
                    INSERT INTO preguntas_encuesta (encuesta_id, texto_pregunta, tipo_respuesta, opciones)
                    VALUES (%s, %s, %s, %s)
                """, (
                    encuesta_id,
                    pregunta['texto'],
                    pregunta['tipo'],
                    json.dumps(pregunta['opciones']) if pregunta['opciones'] else None
                ))
            
            add_notification(f"Encuesta creada exitosamente con ID: {encuesta_id}", "success")
            
            # Limpiar estado
            del st.session_state.nueva_encuesta
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al guardar encuesta: {str(e)}", "error")

def gestionar_encuestas():
    """Muestra y permite gestionar encuestas existentes."""
    
    st.subheader("Encuestas Activas")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                e.id,
                e.titulo,
                e.descripcion,
                e.fecha_inicio,
                e.fecha_fin,
                e.activa,
                COUNT(DISTINCT p.id) as total_preguntas,
                COUNT(DISTINCT r.egresado_id) as total_respuestas
            FROM encuestas e
            LEFT JOIN preguntas_encuesta p ON e.id = p.encuesta_id
            LEFT JOIN respuestas_encuesta r ON e.id = r.encuesta_id
            GROUP BY e.id
            ORDER BY e.fecha_inicio DESC
        """)
        
        encuestas = cur.fetchall()
        
        if not encuestas:
            st.info("No hay encuestas creadas")
            return
        
        for encuesta in encuestas:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    estado = "🟢 Activa" if encuesta[5] else "🔴 Inactiva"
                    st.markdown(f"### {encuesta[1]} - {estado}")
                    st.markdown(encuesta[2] or "")
                    st.markdown(f"📅 **Período:** {encuesta[3]} al {encuesta[4]}")
                    st.markdown(f"📊 **Preguntas:** {encuesta[6]} | **Respuestas:** {encuesta[7]}")
                
                with col2:
                    if st.button("📋 Ver", key=f"view_{encuesta[0]}"):
                        ver_encuesta_detalle(encuesta[0])
                    
                    if st.button("📊 Resultados", key=f"res_{encuesta[0]}"):
                        st.session_state.encuesta_resultado = encuesta[0]
                        st.rerun()
                
                with col3:
                    if encuesta[5]:  # activa
                        if st.button("🔴 Desactivar", key=f"des_{encuesta[0]}"):
                            cambiar_estado_encuesta(encuesta[0], False)
                    else:
                        if st.button("🟢 Activar", key=f"act_{encuesta[0]}"):
                            cambiar_estado_encuesta(encuesta[0], True)
                    
                    if st.button("🗑️ Eliminar", key=f"del_{encuesta[0]}"):
                        eliminar_encuesta(encuesta[0])

def cambiar_estado_encuesta(encuesta_id, activo):
    """Activa o desactiva una encuesta."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE encuestas SET activa = %s WHERE id = %s", (activo, encuesta_id))
            
            estado = "activada" if activo else "desactivada"
            add_notification(f"Encuesta {estado} exitosamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al cambiar estado: {str(e)}", "error")

def eliminar_encuesta(encuesta_id):
    """Elimina una encuesta (solo si no tiene respuestas)."""
    
    try:
        with get_db_cursor() as cur:
            # Verificar si tiene respuestas
            cur.execute("SELECT COUNT(*) FROM respuestas_encuesta WHERE encuesta_id = %s", (encuesta_id,))
            if cur.fetchone()[0] > 0:
                add_notification("No se puede eliminar una encuesta con respuestas", "error")
                return
            
            # Eliminar preguntas primero (por FK)
            cur.execute("DELETE FROM preguntas_encuesta WHERE encuesta_id = %s", (encuesta_id,))
            
            # Eliminar encuesta
            cur.execute("DELETE FROM encuestas WHERE id = %s", (encuesta_id,))
            
            add_notification("Encuesta eliminada exitosamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al eliminar: {str(e)}", "error")

def ver_resultados_encuestas():
    """Muestra los resultados de las encuestas."""
    
    st.subheader("Resultados de Encuestas")
    
    if 'encuesta_resultado' in st.session_state:
        mostrar_resultados_encuesta(st.session_state.encuesta_resultado)
    else:
        # Selector de encuesta
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, titulo, fecha_inicio, fecha_fin
                FROM encuestas
                ORDER BY fecha_inicio DESC
            """)
            
            encuestas = cur.fetchall()
            
            if encuestas:
                opciones = {f"{e[1]} ({e[2]} - {e[3]})": e[0] for e in encuestas}
                seleccion = st.selectbox("Seleccionar Encuesta", options=list(opciones.keys()))
                
                if seleccion:
                    mostrar_resultados_encuesta(opciones[seleccion])
            else:
                st.info("No hay encuestas disponibles")

def mostrar_resultados_encuesta(encuesta_id):
    """Muestra los resultados detallados de una encuesta."""
    
    with get_db_cursor() as cur:
        # Datos de la encuesta
        cur.execute("SELECT titulo, descripcion FROM encuestas WHERE id = %s", (encuesta_id,))
        titulo, descripcion = cur.fetchone()
        
        st.subheader(f"Resultados: {titulo}")
        if descripcion:
            st.caption(descripcion)
        
        # Estadísticas generales
        cur.execute("""
            SELECT 
                COUNT(DISTINCT egresado_id) as total_encuestados,
                COUNT(*) as total_respuestas,
                MIN(fecha_respuesta) as primera_respuesta,
                MAX(fecha_respuesta) as ultima_respuesta
            FROM respuestas_encuesta
            WHERE encuesta_id = %s
        """, (encuesta_id,))
        
        stats = cur.fetchone()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Encuestados", stats[0] or 0)
        col2.metric("Total Respuestas", stats[1] or 0)
        if stats[2]:
            col3.metric("Primera Respuesta", stats[2].strftime('%d/%m/%Y'))
        if stats[3]:
            col4.metric("Última Respuesta", stats[3].strftime('%d/%m/%Y'))
        
        st.markdown("---")
        
        # Resultados por pregunta
        cur.execute("""
            SELECT 
                p.id,
                p.texto_pregunta,
                p.tipo_respuesta,
                r.respuesta
            FROM preguntas_encuesta p
            LEFT JOIN respuestas_encuesta r ON p.id = r.pregunta_id
            WHERE p.encuesta_id = %s
            ORDER BY p.id
        """, (encuesta_id,))
        
        resultados = cur.fetchall()
        
        if not resultados:
            st.info("No hay respuestas para esta encuesta")
            return
        
        # Agrupar por pregunta
        preguntas = {}
        for p_id, texto, tipo, respuesta in resultados:
            if p_id not in preguntas:
                preguntas[p_id] = {
                    'texto': texto,
                    'tipo': tipo,
                    'respuestas': []
                }
            if respuesta:
                preguntas[p_id]['respuestas'].append(respuesta)
        
        for p_id, data in preguntas.items():
            with st.expander(f"📊 {data['texto']}", expanded=True):
                if data['tipo'] == 'texto':
                    # Mostrar respuestas de texto
                    st.markdown("**Respuestas:**")
                    for i, r in enumerate(data['respuestas'], 1):
                        st.markdown(f"{i}. {r}")
                
                elif data['tipo'] == 'opcion_multiple':
                    # Gráfico de barras para opción múltiple
                    from collections import Counter
                    conteo = Counter(data['respuestas'])
                    
                    df = pd.DataFrame(
                        [(op, conteo.get(op, 0)) for op in set(data['respuestas'])],
                        columns=['Opción', 'Cantidad']
                    ).sort_values('Cantidad', ascending=False)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.bar_chart(df.set_index('Opción'))
                    
                    with col_b:
                        st.dataframe(df, hide_index=True)
                
                elif data['tipo'] == 'escala':
                    # Histograma para escala
                    valores = [int(r) for r in data['respuestas'] if r.isdigit()]
                    if valores:
                        df_valores = pd.DataFrame(valores, columns=['Valor'])
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.bar_chart(df_valores['Valor'].value_counts().sort_index())
                        
                        with col_b:
                            st.markdown(f"**Promedio:** {sum(valores)/len(valores):.2f}")
                            st.markdown(f"**Mínimo:** {min(valores)}")
                            st.markdown(f"**Máximo:** {max(valores)}")