"""
Módulo de eventos y networking.
Organizado por pestañas para una mejor experiencia de usuario.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.utils.database import get_db_cursor
from src.utils.decorators import login_required
from src.models.evento import Evento
from src.utils.notifications import NotificationSystem
from src.utils.email import enviar_notificacion_evento
from src.utils.pdf_generator import generar_pdf_constancia

@login_required
def show():
    """Muestra el módulo de eventos y networking organizado por pestañas."""
    st.title("📅 Eventos y Networking")
    
    # Crear pestañas principales
    tab_proximos, tab_constancias, tab_networking = st.tabs([
        "🚀 Próximos Eventos", 
        "📜 Mis Constancias", 
        "🤝 Networking y Comunidad"
    ])
    
    usuario_id = st.session_state.user['id']
    hoy = datetime.now(timezone.utc)
    
    # --- PESTAÑA 1: PRÓXIMOS EVENTOS ---
    with tab_proximos:
        st.subheader("Explora nuevos eventos")
        
        # Filtro por tipo
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "feria_laboral", "webinar", "charla", "curso"], key="filter_proximos")
        
        eventos = Evento.get_all()
        if filtro_tipo != "Todos":
            eventos = [e for e in eventos if e.tipo == filtro_tipo]
            
        # Solo mostrar eventos que NO han terminado
        eventos_futuros = [e for e in eventos if (e.fecha_fin if e.fecha_fin.tzinfo else e.fecha_fin.replace(tzinfo=timezone.utc)) >= hoy]
        
        if not eventos_futuros:
            st.info("No hay eventos programados en este momento.")
        else:
            for ev in eventos_futuros:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"### {ev.titulo}")
                        st.write(ev.descripcion)
                        st.caption(f"📅 **Fecha:** {ev.fecha_inicio.strftime('%d/%m/%Y %H:%M')} | 📍 **Lugar:** {ev.lugar}")
                        if not ev.es_gratuito:
                            st.warning(f"💰 Precio: S/. {ev.precio}")
                    
                    with c2:
                        # Comprobar inscripción
                        with get_db_cursor() as cur:
                            cur.execute("SELECT 1 FROM inscripciones_eventos WHERE evento_id = %s AND usuario_id = %s", (ev.id, usuario_id))
                            ya_inscrito = cur.fetchone() is not None

                        if ya_inscrito:
                            st.success("✅ Ya estás inscrito")
                        else:
                            if st.button("📝 Inscribirme", key=f"btn_ins_{ev.id}", type="primary"):
                                exito, mensaje = Evento.inscribir_usuario(ev.id, usuario_id)
                                if exito:
                                    st.success("¡Inscripción exitosa!")
                                    NotificationSystem.create(usuario_id, "Inscripción a Evento", f"Te has inscrito a {ev.titulo}")
                                    enviar_notificacion_evento(st.session_state.user['email'], ev.titulo, ev.fecha_inicio.strftime('%d/%m/%Y'))
                                    st.rerun()
                                else:
                                    st.error(mensaje)

    # --- PESTAÑA 2: MIS CONSTANCIAS ---
    with tab_constancias:
        st.subheader("Eventos finalizados y certificados")
        
        # Obtener eventos donde el usuario está inscrito y el evento ya terminó
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.titulo, e.fecha_inicio, e.fecha_fin, ie.asistio
                FROM eventos e
                JOIN inscripciones_eventos ie ON e.id = ie.evento_id
                WHERE ie.usuario_id = %s AND e.fecha_fin < %s
                ORDER BY e.fecha_fin DESC
            """, (usuario_id, hoy))
            eventos_pasados = cur.fetchall()
            
        if not eventos_pasados:
            st.info("Aún no tienes eventos finalizados en tu historial.")
        else:
            for ev_id, titulo, f_ini, f_fin, asistio in eventos_pasados:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"#### {titulo}")
                        st.caption(f"📅 Finalizó el: {f_fin.strftime('%d/%m/%Y')}")
                        if asistio:
                            st.success("Asistencia confirmada")
                        else:
                            st.error("No se registró asistencia")
                    
                    with col2:
                        if asistio:
                            # Obtener nombre para el PDF
                            with get_db_cursor() as cur:
                                cur.execute("SELECT nombres, apellido_paterno, apellido_materno FROM egresados WHERE usuario_id = %s", (usuario_id,))
                                datos_egr = cur.fetchone()
                                nombre_pdf = f"{datos_egr[0]} {datos_egr[1]} {datos_egr[2]}" if datos_egr else st.session_state.user['email']

                            pdf_data = generar_pdf_constancia(nombre_pdf, titulo, f_ini.strftime('%d/%m/%Y'))
                            st.download_button(
                                label="📜 PDF",
                                data=pdf_data,
                                file_name=f"constancia_{titulo.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"dl_hist_{ev_id}"
                            )

    # --- PESTAÑA 3: NETWORKING Y COMUNIDAD ---
    with tab_networking:
        st.subheader("Conecta con otros participantes")
        
        # Solo mostrar chat de eventos en los que el usuario está inscrito (actuales o futuros)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.titulo 
                FROM eventos e
                JOIN inscripciones_eventos ie ON e.id = ie.evento_id
                WHERE ie.usuario_id = %s AND e.activo = TRUE
                ORDER BY e.fecha_inicio ASC
            """, (usuario_id,))
            mis_eventos_chat = cur.fetchall()

        if not mis_eventos_chat:
            st.warning("Inscríbete en un evento para acceder a su comunidad de chat.")
        else:
            # Seleccionar evento para el chat
            opciones_chat = {titulo: eid for eid, titulo in mis_eventos_chat}
            sel_titulo = st.selectbox("Selecciona la comunidad del evento:", options=list(opciones_chat.keys()))
            sel_id = opciones_chat[sel_titulo]
            
            with st.container(border=True):
                st.markdown(f"### Chat: {sel_titulo}")
                
                # Mostrar mensajes
                mensajes = Evento.get_mensajes_chat(sel_id)
                
                # Scrollable area simulada con container
                with st.container(height=400):
                    if not mensajes:
                        st.caption("No hay mensajes aún. ¡Sé el primero en saludar!")
                    else:
                        for msg, fecha, email, rol in mensajes:
                            is_me = email == st.session_state.user['email']
                            align = "right" if is_me else "left"
                            color = "#e3f2fd" if is_me else "#f5f5f5"
                            
                            st.markdown(f"""
                                <div style='text-align: {align}; margin-bottom: 10px;'>
                                    <div style='display: inline-block; background-color: {color}; padding: 8px 15px; border-radius: 15px; max-width: 80%;'>
                                        <p style='margin: 0; font-size: 0.8rem; color: #666;'><b>{email}</b> ({rol})</p>
                                        <p style='margin: 5px 0;'>{msg}</p>
                                        <p style='margin: 0; font-size: 0.7rem; color: #999;'>{fecha.strftime('%H:%M')}</p>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                # Formulario para enviar mensaje
                with st.form("chat_form_new", clear_on_submit=True):
                    col_input, col_btn = st.columns([4, 1])
                    with col_input:
                        nuevo_msg = st.text_input("Mensaje...", placeholder="Escribe algo...")
                    with col_btn:
                        if st.form_submit_button("Enviar", use_container_width=True):
                            if nuevo_msg:
                                exito, error = Evento.enviar_mensaje_chat(sel_id, usuario_id, nuevo_msg)
                                if exito:
                                    st.rerun()
                                else:
                                    st.error(error)
