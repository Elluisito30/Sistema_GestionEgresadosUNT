"""
Módulo de gestión de eventos para administradores y empleadores.
Permite crear, editar y eliminar eventos.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.session import add_notification
from src.utils.validators import validar_fecha, sanitizar_entrada

def show():
    """Muestra la página de gestión de eventos."""
    
    st.title("📅 Gestión de Eventos")
    
    user = st.session_state.user
    rol = user['rol']
    
    # Tabs para diferentes acciones
    tab1, tab2, tab3 = st.tabs([
        "➕ Crear Evento",
        "📋 Mis Eventos",
        "📊 Estadísticas"
    ])
    
    with tab1:
        if rol in ['administrador', 'empleador']:
            crear_evento(rol, user['id'])
        else:
            st.error("No tienes permisos para crear eventos")
    
    with tab2:
        mostrar_mis_eventos(rol, user['id'])
    
    with tab3:
        mostrar_estadisticas_eventos()

def crear_evento(rol, usuario_id):
    """Formulario para crear un nuevo evento."""
    
    st.subheader("Crear Nuevo Evento")
    
    with st.form("form_evento"):
        # Información básica
        titulo = st.text_input("Título del Evento *", max_chars=200)
        descripcion = st.text_area("Descripción *", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox(
                "Tipo de Evento *",
                options=['feria_laboral', 'webinar', 'charla', 'curso'],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            lugar = st.text_input("Lugar *", placeholder="Ej: Auditorio UNT, Online (Zoom), etc.")
        
        # Fechas
        st.subheader("Fechas y Horarios")
        col3, col4 = st.columns(2)
        
        with col3:
            fecha_inicio = st.date_input("Fecha de Inicio *", min_value=date.today())
            hora_inicio = st.time_input("Hora de Inicio *", value=datetime.now().time())
        
        with col4:
            fecha_fin = st.date_input("Fecha de Fin *", min_value=fecha_inicio)
            hora_fin = st.time_input("Hora de Fin *", value=(datetime.now() + timedelta(hours=2)).time())
        
        # Capacidad y precio
        st.subheader("Capacidad y Precio")
        col5, col6 = st.columns(2)
        
        with col5:
            capacidad = st.number_input(
                "Capacidad máxima",
                min_value=1,
                max_value=10000,
                value=100,
                help="Dejar en 0 si no hay límite"
            )
        
        with col6:
            es_gratuito = st.checkbox("Evento gratuito", value=True)
            if not es_gratuito:
                precio = st.number_input(
                    "Precio (S/.)",
                    min_value=0.01,
                    max_value=10000.0,
                    step=10.0,
                    format="%.2f"
                )
        
        # Imagen
        st.subheader("Imagen Promocional")
        imagen = st.file_uploader(
            "Subir imagen del evento",
            type=['jpg', 'jpeg', 'png', 'gif'],
            help="Tamaño recomendado: 800x400 píxeles"
        )
        
        submitted = st.form_submit_button("Crear Evento", type="primary", use_container_width=True)
        
        if submitted:
            if not titulo or not descripcion or not lugar:
                st.error("Por favor complete todos los campos obligatorios")
                return
            
            guardar_evento(
                titulo, descripcion, tipo, lugar,
                datetime.combine(fecha_inicio, hora_inicio),
                datetime.combine(fecha_fin, hora_fin),
                capacidad if capacidad > 0 else None,
                es_gratuito,
                precio if not es_gratuito else None,
                imagen,
                usuario_id
            )

def guardar_evento(titulo, descripcion, tipo, lugar, fecha_inicio, fecha_fin,
                  capacidad, es_gratuito, precio, imagen, usuario_id):
    """Guarda un nuevo evento en la base de datos."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Guardar imagen si se subió
            imagen_url = None
            if imagen:
                # Aquí iría la lógica para guardar la imagen
                # Por ahora simulamos
                imagen_url = f"/app/storage/eventos/{datetime.now().timestamp()}_{imagen.name}"
            
            cur.execute("""
                INSERT INTO eventos (
                    publicado_por, titulo, descripcion, tipo,
                    fecha_inicio, fecha_fin, lugar, capacidad_maxima,
                    es_gratuito, precio, imagen_promocional_url, activo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                RETURNING id
            """, (
                usuario_id, titulo, descripcion, tipo,
                fecha_inicio, fecha_fin, lugar, capacidad,
                es_gratuito, precio, imagen_url
            ))
            
            evento_id = cur.fetchone()[0]
            
            # Notificar a egresados interesados (simplificado)
            cur.execute("""
                INSERT INTO notificaciones (usuario_id, tipo, asunto, mensaje)
                SELECT id, 'email', 'Nuevo evento: ' || %s,
                       'Se ha publicado un nuevo evento que podría interesarte: ' || %s
                FROM usuarios
                WHERE rol = 'egresado' AND activo = true
                LIMIT 100
            """, (titulo, titulo))
            
            add_notification(f"Evento creado exitosamente con ID: {evento_id}", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al crear evento: {str(e)}", "error")

def mostrar_mis_eventos(rol, usuario_id):
    """Muestra los eventos creados por el usuario."""
    
    st.subheader("Mis Eventos")
    
    query = """
        SELECT 
            e.id,
            e.titulo,
            e.tipo,
            e.fecha_inicio,
            e.fecha_fin,
            e.lugar,
            e.capacidad_maxima,
            e.es_gratuito,
            e.precio,
            e.activo,
            COUNT(i.id) as inscritos
        FROM eventos e
        LEFT JOIN inscripciones_eventos i ON e.id = i.evento_id
        WHERE e.publicado_por = %s
        GROUP BY e.id
        ORDER BY e.fecha_inicio DESC
    """
    
    with get_db_cursor() as cur:
        cur.execute(query, (usuario_id,))
        eventos = cur.fetchall()
        
        if not eventos:
            st.info("No has creado ningún evento todavía.")
            return
        
        for evento in eventos:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    estado = "🟢 Activo" if evento[9] else "🔴 Inactivo"
                    st.markdown(f"**{evento[1]}** - {estado}")
                    st.markdown(f"📅 {evento[3].strftime('%d/%m/%Y %H:%M')}")
                    st.markdown(f"📍 {evento[5]}")
                
                with col2:
                    st.metric("Inscritos", evento[10])
                    if evento[6]:  # capacidad
                        porcentaje = (evento[10] / evento[6]) * 100
                        st.caption(f"{porcentaje:.1f}% del cupo")
                
                with col3:
                    if evento[7]:  # gratuito
                        st.markdown("🆓 Gratuito")
                    else:
                        st.markdown(f"💰 S/. {evento[8]:.2f}")
                
                with col4:
                    if st.button("✏️ Editar", key=f"edit_{evento[0]}"):
                        st.session_state.evento_editando = evento[0]
                        st.rerun()
                    
                    if st.button("👥 Ver inscritos", key=f"ins_{evento[0]}"):
                        mostrar_inscritos(evento[0])
                    
                    if evento[9]:  # activo
                        if st.button("🔴 Desactivar", key=f"des_{evento[0]}"):
                            cambiar_estado_evento(evento[0], False)
                    else:
                        if st.button("🟢 Activar", key=f"act_{evento[0]}"):
                            cambiar_estado_evento(evento[0], True)
                
                st.markdown("---")
    
    # Editor de evento si hay uno seleccionado
    if 'evento_editando' in st.session_state:
        editar_evento(st.session_state.evento_editando)

def editar_evento(evento_id):
    """Permite editar un evento existente."""
    
    st.subheader("Editar Evento")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT titulo, descripcion, tipo, lugar, fecha_inicio, fecha_fin,
                   capacidad_maxima, es_gratuito, precio, activo
            FROM eventos
            WHERE id = %s
        """, (evento_id,))
        
        evento = cur.fetchone()
        
        if not evento:
            st.error("Evento no encontrado")
            del st.session_state.evento_editando
            st.rerun()
        
        with st.form("form_editar_evento"):
            titulo = st.text_input("Título", value=evento[0])
            descripcion = st.text_area("Descripción", value=evento[1], height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox(
                    "Tipo",
                    options=['feria_laboral', 'webinar', 'charla', 'curso'],
                    index=['feria_laboral', 'webinar', 'charla', 'curso'].index(evento[2]),
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                lugar = st.text_input("Lugar", value=evento[3])
            
            with col2:
                fecha_inicio = st.date_input("Fecha Inicio", value=evento[4].date())
                hora_inicio = st.time_input("Hora Inicio", value=evento[4].time())
                fecha_fin = st.date_input("Fecha Fin", value=evento[5].date())
                hora_fin = st.time_input("Hora Fin", value=evento[5].time())
            
            col3, col4 = st.columns(2)
            with col3:
                capacidad = st.number_input(
                    "Capacidad máxima",
                    min_value=1,
                    max_value=10000,
                    value=evento[6] or 100
                )
            
            with col4:
                es_gratuito = st.checkbox("Gratuito", value=evento[7])
                if not es_gratuito:
                    precio = st.number_input(
                        "Precio",
                        min_value=0.01,
                        max_value=10000.0,
                        value=evento[8] or 0.0,
                        format="%.2f"
                    )
                else:
                    precio = None
            
            activo = st.checkbox("Evento activo", value=evento[9])
            
            col5, col6 = st.columns(2)
            with col5:
                if st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True):
                    actualizar_evento(
                        evento_id, titulo, descripcion, tipo, lugar,
                        datetime.combine(fecha_inicio, hora_inicio),
                        datetime.combine(fecha_fin, hora_fin),
                        capacidad, es_gratuito, precio, activo
                    )
            
            with col6:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    del st.session_state.evento_editando
                    st.rerun()

def actualizar_evento(evento_id, titulo, descripcion, tipo, lugar,
                     fecha_inicio, fecha_fin, capacidad, es_gratuito,
                     precio, activo):
    """Actualiza un evento existente."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE eventos
                SET titulo = %s,
                    descripcion = %s,
                    tipo = %s,
                    lugar = %s,
                    fecha_inicio = %s,
                    fecha_fin = %s,
                    capacidad_maxima = %s,
                    es_gratuito = %s,
                    precio = %s,
                    activo = %s
                WHERE id = %s
            """, (
                titulo, descripcion, tipo, lugar,
                fecha_inicio, fecha_fin, capacidad,
                es_gratuito, precio, activo, evento_id
            ))
            
            add_notification("Evento actualizado exitosamente", "success")
            del st.session_state.evento_editando
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al actualizar: {str(e)}", "error")

def cambiar_estado_evento(evento_id, activo):
    """Activa o desactiva un evento."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE eventos
                SET activo = %s
                WHERE id = %s
            """, (activo, evento_id))
            
            estado = "activado" if activo else "desactivado"
            add_notification(f"Evento {estado} exitosamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al cambiar estado: {str(e)}", "error")

def mostrar_inscritos(evento_id):
    """Muestra la lista de inscritos a un evento."""
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                u.email,
                CASE 
                    WHEN e.id IS NOT NULL THEN e.nombres || ' ' || e.apellido_paterno
                    ELSE 'Empleador'
                END as nombre_completo,
                i.fecha_inscripcion,
                i.asistio,
                i.pago_id
            FROM inscripciones_eventos i
            JOIN usuarios u ON i.usuario_id = u.id
            LEFT JOIN egresados e ON u.id = e.usuario_id
            WHERE i.evento_id = %s
            ORDER BY i.fecha_inscripcion DESC
        """, (evento_id,))
        
        inscritos = cur.fetchall()
        
        if not inscritos:
            st.info("No hay inscritos en este evento")
            return
        
        st.subheader(f"Inscritos al Evento ({len(inscritos)})")
        
        df = pd.DataFrame(
            inscritos,
            columns=['Email', 'Nombre', 'Fecha Inscripción', 'Asistió', 'Pago ID']
        )
        
        st.dataframe(df, use_container_width=True)
        
        # Opción para marcar asistencia
        if st.button("📝 Marcar asistencia masiva"):
            st.info("Funcionalidad en desarrollo")

def mostrar_estadisticas_eventos():
    """Muestra estadísticas de eventos."""
    
    st.subheader("Estadísticas de Eventos")
    
    with get_db_cursor() as cur:
        # Totales
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE fecha_inicio > NOW()) as proximos,
                COUNT(*) FILTER (WHERE fecha_fin < NOW()) as pasados,
                SUM(CASE WHEN es_gratuito THEN 1 ELSE 0 END) as gratuitos,
                SUM(CASE WHEN NOT es_gratuito THEN 1 ELSE 0 END) as pagados
            FROM eventos
            WHERE activo = true
        """)
        
        total, proximos, pasados, gratuitos, pagados = cur.fetchone()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Eventos", total or 0)
        col2.metric("Próximos", proximos or 0)
        col3.metric("Pasados", pasados or 0)
        col4.metric("Gratuitos", gratuitos or 0)
        col5.metric("Pagados", pagados or 0)
        
        st.markdown("---")
        
        # Eventos por tipo
        cur.execute("""
            SELECT tipo, COUNT(*)
            FROM eventos
            WHERE activo = true
            GROUP BY tipo
        """)
        
        df_tipo = pd.DataFrame(cur.fetchall(), columns=['Tipo', 'Cantidad'])
        
        if not df_tipo.empty:
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Eventos por Tipo")
                st.bar_chart(df_tipo.set_index('Tipo'))
            
            with col_b:
                st.subheader("Inscripciones por Mes")
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('month', fecha_inscripcion)::date as mes,
                        COUNT(*) as inscripciones
                    FROM inscripciones_eventos
                    WHERE fecha_inscripcion > NOW() - INTERVAL '6 months'
                    GROUP BY mes
                    ORDER BY mes
                """)
                
                df_insc = pd.DataFrame(cur.fetchall(), columns=['Mes', 'Inscripciones'])
                if not df_insc.empty:
                    st.line_chart(df_insc.set_index('Mes'))