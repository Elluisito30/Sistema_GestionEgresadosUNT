"""
Módulo de encuestas para egresados.
Permite responder encuestas de seguimiento.
"""
import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.utils.database import get_db_cursor
from src.utils.session import add_notification


def show():
    """Muestra la página de encuestas para egresados."""
    
    st.title("📝 Encuestas de Seguimiento")
    
    user = st.session_state.user
    
    # Verificar que sea egresado
    if user['rol'] != 'egresado':
        st.error("Esta página es solo para egresados")
        return
    
    # Obtener ID del egresado
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM egresados WHERE usuario_id = %s", (user['id'],))
        egresado = cur.fetchone()
        
        if not egresado:
            st.error("Complete su perfil de egresado primero")
            return
        
        egresado_id = egresado[0]

    encuesta_actual = st.session_state.get('encuesta_actual')
    if encuesta_actual and encuesta_actual.get('egresado_id') == egresado_id:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("Tienes una encuesta en progreso. Puedes continuarla o salir guardando tu avance.")
        with col2:
            if st.button("❌ Cerrar encuesta", key="cerrar_encuesta_actual", use_container_width=True):
                del st.session_state.encuesta_actual
                st.rerun()
        mostrar_pregunta_actual()
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["📋 Encuestas Pendientes", "✅ Encuestas Completadas"])
    
    with tab1:
        mostrar_encuestas_pendientes(egresado_id)
    
    with tab2:
        mostrar_encuestas_completadas(egresado_id)

def mostrar_encuestas_pendientes(egresado_id):
    """Muestra las encuestas pendientes de responder."""
    
    st.subheader("Encuestas Pendientes")
    
    # Verificar si la columna dirigida_a existe para evitar errores de migración
    has_dirigida_a = False
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='encuestas' AND column_name='dirigida_a'
            """)
            has_dirigida_a = bool(cur.fetchone())
    except:
        pass

    with get_db_cursor() as cur:
        # Debug: Verificar si hay encuestas activas
        cur.execute("SELECT COUNT(*) FROM encuestas WHERE activa = true")
        total_activas = cur.fetchone()[0]
        
        query = """
            SELECT 
                e.id,
                e.titulo,
                e.descripcion,
                e.fecha_inicio,
                e.fecha_fin,
                e.categoria,
                e.es_obligatoria,
                (
                    SELECT COUNT(*) 
                    FROM respuestas_encuesta r 
                    WHERE r.encuesta_id = e.id 
                    AND r.egresado_id = %s
                ) as respondidas,
                (
                    SELECT COUNT(*) 
                    FROM preguntas_encuesta p 
                    WHERE p.encuesta_id = e.id
                ) as total_preguntas
            FROM encuestas e
            WHERE COALESCE(e.activa, true) = true
            AND DATE(e.fecha_inicio) <= CURRENT_DATE
            AND DATE(e.fecha_fin) >= (CURRENT_DATE - INTERVAL '1 day')
        """
        
        params = [egresado_id]
        
        if has_dirigida_a:
            query += """
                AND (COALESCE(e.dirigida_a, 'todos') = 'todos' OR EXISTS (
                    SELECT 1 FROM asignaciones_encuesta a 
                    WHERE a.encuesta_id = e.id AND a.egresado_id = %s
                ))
            """
            params.append(egresado_id)
            
        query += """
            AND NOT EXISTS (
                SELECT 1 
                FROM respuestas_encuesta r 
                WHERE r.encuesta_id = e.id 
                AND r.egresado_id = %s
                GROUP BY r.encuesta_id
                HAVING COUNT(DISTINCT r.pregunta_id) = (
                    SELECT COUNT(*) 
                    FROM preguntas_encuesta p 
                    WHERE p.encuesta_id = e.id
                )
            )
            ORDER BY e.es_obligatoria DESC, e.fecha_fin ASC
        """
        params.append(egresado_id)
        
        cur.execute(query, params)
        
        encuestas = cur.fetchall()
        
        if not encuestas:
            if total_activas > 0:
                st.info(f"Tienes {total_activas} encuestas activas en el sistema, pero ninguna está asignada a ti o está fuera de fecha.")
            else:
                st.success("¡No tienes encuestas pendientes! Gracias por mantenerte al día.")
            return
        
        for encuesta in encuestas:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    obligatoria_tag = "⚠️ [OBLIGATORIA]" if encuesta[6] else ""
                    st.markdown(f"### {encuesta[1]} {obligatoria_tag}")
                    st.caption(f"Categoría: {encuesta[5]}")
                    st.markdown(encuesta[2] or "Sin descripción")
                    
                    dias_restantes = (encuesta[4] - datetime.now().date()).days
                    st.markdown(f"📅 **Vence en:** {dias_restantes} días")
                    
                    progreso = encuesta[7] / encuesta[8] if encuesta[8] > 0 else 0
                    st.progress(progreso, text=f"Progreso: {encuesta[7]}/{encuesta[8]} preguntas")
                
                with col2:
                    st.write("") # Spacer
                    st.write("") # Spacer
                    if encuesta[7] > 0:
                        if st.button("📝 Continuar", key=f"ans_cont_{encuesta[0]}", 
                                 use_container_width=True):
                            responder_encuesta(encuesta[0], egresado_id)
                            st.rerun()
                    else:
                        if st.button("🎯 Iniciar", key=f"ans_start_{encuesta[0]}", type="primary",
                                 use_container_width=True):
                            responder_encuesta(encuesta[0], egresado_id)
                            st.rerun()

def mostrar_encuestas_completadas(egresado_id):
    """Muestra las encuestas ya completadas por el egresado."""
    
    st.subheader("Encuestas Completadas")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                e.id,
                e.titulo,
                e.descripcion,
                e.fecha_fin,
                MAX(r.fecha_respuesta) as ultima_respuesta
            FROM encuestas e
            JOIN respuestas_encuesta r ON e.id = r.encuesta_id
            WHERE r.egresado_id = %s
            GROUP BY e.id, e.titulo, e.descripcion, e.fecha_fin
            ORDER BY ultima_respuesta DESC
        """, (egresado_id,))
        
        encuestas = cur.fetchall()
        
        if not encuestas:
            st.info("Aún no has completado ninguna encuesta.")
            return
        
        for encuesta in encuestas:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {encuesta[1]}")
                    st.markdown(encuesta[2] or "")
                    st.markdown(f"✅ **Completada:** {encuesta[4].strftime('%d/%m/%Y')}")
                
                with col2:
                    if st.button("📋 Ver respuestas", key=f"ans_view_{encuesta[0]}"):
                        ver_respuestas_encuesta(encuesta[0], egresado_id)
                
                st.markdown("---")

def responder_encuesta(encuesta_id, egresado_id):
    """Inicia o continúa una encuesta."""
    
    st.session_state.encuesta_actual = {
        'id': encuesta_id,
        'egresado_id': egresado_id,
        'pregunta_actual': 0,
        'respuestas': {}
    }
    
    # Cargar respuestas existentes y retomar en la primera pregunta pendiente.
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT pregunta_id, respuesta
            FROM respuestas_encuesta
            WHERE encuesta_id = %s AND egresado_id = %s
        """, (encuesta_id, egresado_id))
        
        for pregunta_id, respuesta in cur.fetchall():
            st.session_state.encuesta_actual['respuestas'][pregunta_id] = respuesta

        cur.execute("""
            SELECT id
            FROM preguntas_encuesta
            WHERE encuesta_id = %s
            ORDER BY id
        """, (encuesta_id,))
        preguntas_ids = [pregunta_id for pregunta_id, in cur.fetchall()]

    for index, pregunta_id in enumerate(preguntas_ids):
        if pregunta_id not in st.session_state.encuesta_actual['respuestas']:
            st.session_state.encuesta_actual['pregunta_actual'] = index
            break
    else:
        st.session_state.encuesta_actual['pregunta_actual'] = len(preguntas_ids)

def mostrar_pregunta_actual():
    """Muestra la pregunta actual de la encuesta."""
    
    encuesta = st.session_state.encuesta_actual
    encuesta_id = encuesta['id']
    egresado_id = encuesta['egresado_id']
    pregunta_idx = encuesta['pregunta_actual']
    
    with get_db_cursor() as cur:
        # Obtener todas las preguntas
        cur.execute("""
            SELECT id, texto_pregunta, tipo_respuesta, opciones
            FROM preguntas_encuesta
            WHERE encuesta_id = %s
            ORDER BY id
        """, (encuesta_id,))
        
        preguntas = cur.fetchall()
        
        if pregunta_idx >= len(preguntas):
            # Encuesta completada
            st.success("¡Has completado todas las preguntas!")
            
            if st.button("✅ Finalizar Encuesta"):
                del st.session_state.encuesta_actual
                st.rerun()
            return
        
        pregunta_actual = preguntas[pregunta_idx]
        pregunta_id = pregunta_actual[0]
        texto = pregunta_actual[1]
        tipo = pregunta_actual[2]
        opciones = pregunta_actual[3]
        
        # Título de la encuesta
        cur.execute("SELECT titulo FROM encuestas WHERE id = %s", (encuesta_id,))
        titulo = cur.fetchone()[0]
    
    st.subheader(f"Encuesta: {titulo}")
    
    col_p1, col_p2 = st.columns([4, 1])
    with col_p1:
        st.progress((pregunta_idx + 1) / len(preguntas), 
                   text=f"Pregunta {pregunta_idx + 1} de {len(preguntas)}")
    with col_p2:
        st.markdown(f"**{int(((pregunta_idx + 1) / len(preguntas)) * 100)}%**")

    with st.container(border=True):
        st.markdown(f"### {texto}")
        
        # Obtener respuesta previa si existe
        respuesta_previa = encuesta['respuestas'].get(pregunta_id, "")
        
        respuesta = None
        if tipo == 'texto':
            respuesta = st.text_area("Su respuesta:", value=respuesta_previa, height=150, placeholder="Escriba aquí...")
        elif tipo == 'opcion_multiple':
            try:
                ops = json.loads(opciones) if isinstance(opciones, str) else opciones
            except:
                ops = []
            
            index_previa = 0
            if respuesta_previa in ops:
                index_previa = ops.index(respuesta_previa)
            
            respuesta = st.radio("Seleccione una opción:", options=ops, index=index_previa)
        elif tipo == 'escala':
            val_previa = 5
            try:
                val_previa = int(respuesta_previa)
            except:
                pass
            respuesta = st.select_slider("Calificación (1 al 10):", options=list(range(1, 11)), value=val_previa)
        
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            if pregunta_idx > 0:
                if st.button("⬅️ Anterior", use_container_width=True):
                    encuesta['pregunta_actual'] -= 1
                    st.rerun()
        
        with c2:
            if st.button("💾 Guardar y Salir", use_container_width=True):
                guardar_respuesta(encuesta_id, egresado_id, pregunta_id, str(respuesta))
                del st.session_state.encuesta_actual
                add_notification("Progreso guardado correctamente", "info")
                st.rerun()
        
        with c3:
            label_sig = "Finalizar ✅" if pregunta_idx == len(preguntas) - 1 else "Siguiente ➡️"
            if st.button(label_sig, type="primary", use_container_width=True):
                if respuesta or tipo != 'texto': # Validar que haya respondido algo
                    guardar_respuesta(encuesta_id, egresado_id, pregunta_id, str(respuesta))
                    encuesta['pregunta_actual'] += 1
                    st.rerun()
                else:
                    st.warning("Por favor, responda la pregunta antes de continuar.")

def guardar_respuesta(encuesta_id, egresado_id, pregunta_id, respuesta):
    """Guarda la respuesta de una pregunta."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Verificar si ya existe respuesta
            cur.execute("""
                SELECT id FROM respuestas_encuesta
                WHERE encuesta_id = %s AND pregunta_id = %s AND egresado_id = %s
            """, (encuesta_id, pregunta_id, egresado_id))
            
            existe = cur.fetchone()
            
            if existe:
                # Actualizar
                cur.execute("""
                    UPDATE respuestas_encuesta
                    SET respuesta = %s, fecha_respuesta = NOW()
                    WHERE id = %s
                """, (str(respuesta), existe[0]))
            else:
                # Insertar nueva
                cur.execute("""
                    INSERT INTO respuestas_encuesta
                    (encuesta_id, pregunta_id, egresado_id, respuesta)
                    VALUES (%s, %s, %s, %s)
                """, (encuesta_id, pregunta_id, egresado_id, str(respuesta)))
            
            # Actualizar sesión
            if 'encuesta_actual' in st.session_state:
                st.session_state.encuesta_actual['respuestas'][pregunta_id] = respuesta
            
    except Exception as e:
        add_notification(f"Error al guardar respuesta: {str(e)}", "error")

def ver_respuestas_encuesta(encuesta_id, egresado_id):
    """Muestra las respuestas de una encuesta completada."""
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                p.texto_pregunta,
                r.respuesta,
                r.fecha_respuesta
            FROM respuestas_encuesta r
            JOIN preguntas_encuesta p ON r.pregunta_id = p.id
            WHERE r.encuesta_id = %s AND r.egresado_id = %s
            ORDER BY p.id
        """, (encuesta_id, egresado_id))
        
        respuestas = cur.fetchall()
        
        if respuestas:
            st.subheader("Tus Respuestas")
            
            for i, (pregunta, respuesta, fecha) in enumerate(respuestas, 1):
                with st.expander(f"Pregunta {i}"):
                    st.markdown(f"**{pregunta}**")
                    st.markdown(f"Respuesta: {respuesta}")
                    st.caption(f"Respondida: {fecha.strftime('%d/%m/%Y %H:%M')}")