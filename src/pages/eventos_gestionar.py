"""
Módulo de gestión de eventos para administradores y empleadores.
Permite crear, editar y eliminar eventos con validaciones avanzadas.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.decorators import role_required
from src.models.evento import Evento
from src.utils.notifications import NotificationSystem

@role_required(['administrador', 'empleador'])
def show():
    """Muestra la interfaz de gestión de eventos organizada por pestañas."""
    st.title("📅 Gestión de Eventos")
    
    # Manejo de mensaje informativo al hacer clic en editar
    if st.session_state.get('switch_to_edit', False):
        st.info("💡 Por favor, dirígete a la pestaña '✏️ Editar Evento' para realizar los cambios.")
        # No podemos cambiar la pestaña de st.tabs programáticamente, 
        # así que el mensaje guía al usuario.
        st.session_state.switch_to_edit = False

    # Restaurar st.tabs
    tab1, tab2, tab3 = st.tabs(["📝 Mis Eventos", "➕ Crear Nuevo Evento", "✏️ Editar Evento"])
    
    with tab1:
        mostrar_eventos()
        
    with tab2:
        formulario_evento()
        
    with tab3:
        formulario_editar_evento()

def mostrar_eventos():
    """Lista los eventos existentes con métricas rápidas."""
    eventos = Evento.get_all()
    
    if not eventos:
        st.info("No hay eventos registrados.")
        return

    for ev in eventos:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### {ev.titulo}")
                st.write(f"**Tipo:** {ev.tipo} | **Fecha:** {ev.fecha_inicio.strftime('%d/%m/%Y %H:%M')}")
                st.write(f"**Lugar:** {ev.lugar}")
            
            with col2:
                inscritos = Evento.get_inscritos(ev.id)
                st.metric("Inscritos", len(inscritos))
            
            with col3:
                if st.button("👥 Ver Inscritos", key=f"insc_{ev.id}"):
                    st.session_state.ver_inscritos = ev.id
                    st.rerun()
                if st.button("✏️ Editar", key=f"edit_btn_{ev.id}"):
                    st.session_state.evento_a_editar = ev.id
                    st.session_state.switch_to_edit = True # Flag para cambiar pestaña
                    st.rerun()
            
            # Ver inscritos si está seleccionado
            if 'ver_inscritos' in st.session_state and st.session_state.ver_inscritos == ev.id:
                with st.expander("Lista de Inscritos", expanded=True):
                    if inscritos:
                        df_insc = pd.DataFrame(inscritos, columns=['ID', 'Email', 'Fecha Insc.', 'Asistencia'])
                        st.dataframe(df_insc, use_container_width=True)
                        
                        if st.button("Cerrar Lista"):
                            del st.session_state.ver_inscritos
                            st.rerun()
                    else:
                        st.info("No hay inscritos aún.")

def formulario_evento():
    """Formulario para crear un nuevo evento con validaciones dinámicas."""
    st.subheader("Crear un nuevo evento")
    
    # Usamos st.container para las validaciones dinámicas fuera del form si es necesario, 
    # pero para bloquear campos en Streamlit usualmente usamos el estado de widgets.
    
    es_gratuito = st.checkbox("¿Es Gratuito?", value=True, key="new_es_gratuito")
    
    with st.form("form_nuevo_evento"):
        titulo = st.text_input("Título del Evento")
        descripcion = st.text_area("Descripción")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha Inicio", datetime.now())
            hora_inicio = st.time_input("Hora Inicio", datetime.now().time())
        with col2:
            fecha_fin = st.date_input("Fecha Fin", datetime.now())
            hora_fin = st.time_input("Hora Fin", (datetime.now() + timedelta(hours=2)).time())
            
        col3, col4 = st.columns(2)
        with col3:
            tipo = st.selectbox("Tipo de Evento", ["feria_laboral", "webinar", "charla", "curso"])
            capacidad = st.number_input("Capacidad Máxima", min_value=1, value=50)
        with col4:
            # El campo precio se bloquea si es_gratuito está marcado
            precio = st.number_input(
                "Precio (S/.)", 
                min_value=0.0, 
                value=0.0, 
                step=0.1, 
                disabled=es_gratuito
            )
            
        lugar = st.text_input("Lugar (Link o Dirección)")
        
        if st.form_submit_button("Guardar Evento"):
            # Validaciones de negocio
            dt_inicio = datetime.combine(fecha_inicio, hora_inicio)
            dt_fin = datetime.combine(fecha_fin, hora_fin)
            
            if not titulo:
                st.error("El título es obligatorio.")
                return

            # Validación de horarios
            if fecha_inicio == fecha_fin and hora_fin <= hora_inicio:
                st.error("La hora de fin debe ser posterior a la hora de inicio para el mismo día.")
                return
            elif dt_fin <= dt_inicio:
                st.error("La fecha y hora de fin deben ser posteriores al inicio.")
                return

            try:
                nuevo_ev = Evento(
                    titulo=titulo,
                    descripcion=descripcion,
                    fecha_inicio=dt_inicio,
                    fecha_fin=dt_fin,
                    lugar=lugar,
                    tipo=tipo,
                    capacidad_maxima=capacidad,
                    es_gratuito=es_gratuito,
                    precio=0.0 if es_gratuito else precio,
                    publicado_por=st.session_state.user['id']
                )
                nuevo_ev.save()
                st.success(f"¡Evento '{titulo}' creado exitosamente!")
                st.balloons()
            except Exception as e:
                st.error(f"Error crítico al guardar el evento: {str(e)}")

def formulario_editar_evento():
    """Formulario para editar un evento existente y notificar a los inscritos."""
    st.subheader("Editar Evento")
    
    if 'evento_a_editar' not in st.session_state:
        st.warning("Selecciona un evento de la pestaña 'Mis Eventos' para editar.")
        return

    ev = Evento.get_by_id(st.session_state.evento_a_editar)
    if not ev:
        st.error("No se pudo cargar el evento seleccionado.")
        return

    st.info(f"Editando: **{ev.titulo}**")
    
    # Estado dinámico para el precio en edición
    es_gratuito_edit = st.checkbox("¿Es Gratuito?", value=ev.es_gratuito, key="edit_es_gratuito")

    with st.form("form_editar_evento"):
        nuevo_titulo = st.text_input("Título", value=ev.titulo)
        nueva_desc = st.text_area("Descripción", value=ev.descripcion)
        
        col1, col2 = st.columns(2)
        with col1:
            f_ini = st.date_input("Fecha Inicio", ev.fecha_inicio.date())
            h_ini = st.time_input("Hora Inicio", ev.fecha_inicio.time())
        with col2:
            f_fin = st.date_input("Fecha Fin", ev.fecha_fin.date())
            h_fin = st.time_input("Hora Fin", ev.fecha_fin.time())
            
        col3, col4 = st.columns(2)
        with col3:
            nuevo_tipo = st.selectbox(
                "Tipo", 
                ["feria_laboral", "webinar", "charla", "curso"], 
                index=["feria_laboral", "webinar", "charla", "curso"].index(ev.tipo)
            )
            nueva_capacidad = st.number_input("Capacidad", min_value=1, value=ev.capacidad_maxima)
        with col4:
            nuevo_precio = st.number_input(
                "Precio (S/.)", 
                min_value=0.0, 
                value=float(ev.precio or 0.0), 
                disabled=es_gratuito_edit
            )
            
        nuevo_lugar = st.text_input("Lugar", value=ev.lugar)
        
        if st.form_submit_button("Actualizar y Notificar"):
            dt_inicio = datetime.combine(f_ini, h_ini)
            dt_fin = datetime.combine(f_fin, h_fin)

            # Validaciones
            if dt_fin <= dt_inicio:
                st.error("Error: Los horarios no son válidos.")
                return

            try:
                # Detectar cambios críticos para notificar
                cambio_horario = ev.fecha_inicio != dt_inicio or ev.fecha_fin != dt_fin
                cambio_lugar = ev.lugar != nuevo_lugar

                # Actualizar objeto
                ev.titulo = nuevo_titulo
                ev.descripcion = nueva_desc
                ev.fecha_inicio = dt_inicio
                ev.fecha_fin = dt_fin
                ev.tipo = nuevo_tipo
                ev.capacidad_maxima = nueva_capacidad
                ev.es_gratuito = es_gratuito_edit
                ev.precio = 0.0 if es_gratuito_edit else nuevo_precio
                ev.lugar = nuevo_lugar
                
                ev.save()
                st.success("Evento actualizado correctamente.")

                # Notificar a inscritos si hubo cambios importantes
                if cambio_horario or cambio_lugar:
                    inscritos = Evento.get_inscritos(ev.id)
                    count = 0
                    for ins_id, email, _, _ in inscritos:
                        # Buscamos el usuario_id asociado a este email o usamos el id directo
                        # El primer campo de get_inscritos es u.id
                        detalle = f"El evento '{ev.titulo}' ha sido modificado. "
                        if cambio_horario:
                            detalle += f"Nuevo horario: {dt_inicio.strftime('%d/%m %H:%M')}. "
                        if cambio_lugar:
                            detalle += f"Nueva ubicación: {nuevo_lugar}."
                        
                        NotificationSystem.create(
                            usuario_id=ins_id,
                            asunto="⚠️ Actualización de Evento",
                            mensaje=detalle,
                            tipo="sistema"
                        )
                        count += 1
                    
                    if count > 0:
                        st.info(f"Se enviaron {count} notificaciones a los participantes inscritos.")
                
                # Limpiar estado de edición
                del st.session_state.evento_a_editar
                st.rerun()

            except Exception as e:
                st.error(f"Error al actualizar: {str(e)}")
