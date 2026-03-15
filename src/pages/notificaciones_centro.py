"""
Centro de notificaciones para los usuarios.
"""
import streamlit as st
import pandas as pd
from src.utils.notifications import NotificationSystem
from src.utils.decorators import login_required

@login_required
def show():
    """Muestra el centro de notificaciones."""
    st.title("🔔 Centro de Notificaciones")
    
    usuario_id = st.session_state.user['id']
    
    # Notificaciones no leídas
    notificaciones = NotificationSystem.get_unread(usuario_id)
    
    if not notificaciones:
        st.success("¡Estás al día! No tienes notificaciones nuevas.")
    else:
        st.subheader(f"Tienes {len(notificaciones)} notificaciones nuevas")
        
        if st.button("Marcar todas como leídas"):
            NotificationSystem.mark_all_as_read(usuario_id)
            st.success("Notificaciones marcadas como leídas")
            st.rerun()

        for id_not, asunto, mensaje, tipo, metadata, leida, fecha in notificaciones:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    icon = "ℹ️" if tipo == 'sistema' else "📧" if tipo == 'email' else "📢"
                    st.markdown(f"**{icon} {asunto}**")
                    st.write(mensaje)
                    st.caption(f"Recibido el: {fecha.strftime('%d/%m/%Y %H:%M')}")
                    
                    # Manejar metadata (si hay URL)
                    if metadata and isinstance(metadata, dict) and 'url' in metadata:
                        st.link_button("Ver detalle", metadata['url'])
                with col2:
                    if st.button("Marcar como leída", key=f"read_{id_not}"):
                        NotificationSystem.mark_as_read(id_not)
                        st.rerun()

    # Historial de notificaciones
    st.markdown("---")
    with st.expander("📚 Historial completo de notificaciones", expanded=False):
        historial = NotificationSystem.get_history(usuario_id)
        
        if not historial:
            st.info("No hay notificaciones en tu historial.")
        else:
            # Filtros rápidos para el historial
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_leida = st.selectbox("Estado", ["Todas", "Leídas", "No leídas"], key="hist_status")
            with col_f2:
                filtro_tipo = st.selectbox("Tipo", ["Todos", "sistema", "email"], key="hist_type")

            for id_h, asunto_h, mensaje_h, tipo_h, meta_h, leida_h, fecha_h in historial:
                # Aplicar filtros
                if filtro_leida == "Leídas" and not leida_h: continue
                if filtro_leida == "No leídas" and leida_h: continue
                if filtro_tipo != "Todos" and tipo_h != filtro_tipo.lower(): continue

                with st.container(border=False):
                    status_icon = "✅" if leida_h else "🆕"
                    type_icon = "ℹ️" if tipo_h == 'sistema' else "📧"
                    
                    st.markdown(f"{status_icon} {type_icon} **{asunto_h}**")
                    st.caption(f"Fecha: {fecha_h.strftime('%d/%m/%Y %H:%M')}")
                    
                    with st.expander("Ver mensaje"):
                        st.write(mensaje_h)
                        if meta_h and isinstance(meta_h, dict) and 'url' in meta_h:
                            st.link_button("Ir al enlace", meta_h['url'], key=f"link_h_{id_h}")
                    st.markdown("<hr style='margin:5px 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
