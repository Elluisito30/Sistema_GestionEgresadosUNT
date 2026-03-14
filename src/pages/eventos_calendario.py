"""
Módulo de eventos y networking.
Muestra calendario de eventos y permite inscripciones.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from src.utils.database import get_db_cursor
from src.utils.session import add_notification
import calendar

def show():
    """Muestra la página de calendario de eventos."""
    
    st.title("📅 Calendario de Eventos")
    
    user = st.session_state.user
    rol = user['rol']
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs([
        "📋 Próximos Eventos",
        "🗓️ Calendario",
        "📝 Mis Inscripciones"
    ])
    
    with tab1:
        mostrar_proximos_eventos(rol)
    
    with tab2:
        mostrar_vista_calendario()
    
    with tab3:
        mostrar_mis_inscripciones(user['id'])

def mostrar_proximos_eventos(rol):
    """Muestra la lista de próximos eventos."""
    
    st.subheader("Próximos Eventos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filtro = st.selectbox(
            "Tipo de Evento",
            options=['Todos', 'feria_laboral', 'webinar', 'charla', 'curso']
        )
    
    with col2:
        fecha_desde = st.date_input(
            "Desde",
            value=date.today()
        )
    
    with col3:
        fecha_hasta = st.date_input(
            "Hasta",
            value=date.today() + timedelta(days=60)
        )
    
    # Construir query
    query = """
        SELECT 
            e.id,
            e.titulo,
            e.descripcion,
            e.tipo,
            e.fecha_inicio,
            e.fecha_fin,
            e.lugar,
            e.capacidad_maxima,
            e.es_gratuito,
            e.precio,
            e.imagen_promocional_url,
            u.email as organizador,
            COUNT(i.id) as inscritos,
            BOOL_OR(i.usuario_id = %s) as ya_inscrito
        FROM eventos e
        JOIN usuarios u ON e.publicado_por = u.id
        LEFT JOIN inscripciones_eventos i ON e.id = i.evento_id
        WHERE e.activo = true
        AND e.fecha_inicio >= %s
        AND e.fecha_fin <= %s
    """
    params = [st.session_state.user['id'], fecha_desde, fecha_hasta]
    
    if tipo_filtro != 'Todos':
        query += " AND e.tipo = %s"
        params.append(tipo_filtro)
    
    query += """
        GROUP BY e.id, u.email
        ORDER BY e.fecha_inicio ASC
    """
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        eventos = cur.fetchall()
        
        if not eventos:
            st.info("No hay eventos programados para las fechas seleccionadas.")
            return
        
        for evento in eventos:
            mostrar_tarjeta_evento(evento, rol)

def mostrar_tarjeta_evento(evento, rol):
    """Muestra un evento en formato de tarjeta."""
    
    (id, titulo, descripcion, tipo, fecha_inicio, fecha_fin,
     lugar, capacidad, gratuito, precio, imagen, organizador,
     inscritos, ya_inscrito) = evento
    
    with st.container():
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            # Imagen o ícono del evento
            if imagen:
                st.image(imagen, width=200)
            else:
                # Mostrar ícono según tipo
                iconos = {
                    'feria_laboral': '🏢',
                    'webinar': '💻',
                    'charla': '🎤',
                    'curso': '📚'
                }
                st.markdown(f"<h1 style='text-align: center'>{iconos.get(tipo, '📅')}</h1>", 
                          unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"### {titulo}")
            st.markdown(f"**Tipo:** {tipo.replace('_', ' ').title()}")
            st.markdown(f"**Fecha:** {fecha_inicio.strftime('%d/%m/%Y %H:%M')} - {fecha_fin.strftime('%d/%m/%Y %H:%M')}")
            st.markdown(f"**Lugar:** {lugar}")
            st.markdown(f"**Organizado por:** {organizador}")
            
            # Capacidad
            if capacidad:
                porcentaje = (inscritos / capacidad) * 100
                st.progress(porcentaje / 100, text=f"Inscritos: {inscritos}/{capacidad} ({porcentaje:.1f}%)")
        
        with col3:
            # Precio
            if gratuito:
                st.markdown("### 🆓 GRATUITO")
            else:
                st.markdown(f"### 💰 S/. {precio:.2f}")
            
            # Botón de inscripción
            if ya_inscrito:
                st.button("✅ Ya inscrito", disabled=True, use_container_width=True)
                
                if st.button("📄 Ver constancia", key=f"const_{id}", use_container_width=True):
                    generar_constancia(id, st.session_state.user['id'])
            else:
                if capacidad and inscritos >= capacidad:
                    st.button("❌ Cupo lleno", disabled=True, use_container_width=True)
                else:
                    if st.button("📝 Inscribirme", key=f"ins_{id}", use_container_width=True):
                        inscribirse_evento(id)
        
        # Descripción en expander
        with st.expander("Ver descripción completa"):
            st.markdown(descripcion)
        
        st.markdown("---")

def mostrar_vista_calendario():
    """Muestra una vista de calendario con los eventos."""
    
    st.subheader("Calendario de Eventos")
    
    # Obtener eventos del mes
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                fecha_inicio::date as fecha,
                COUNT(*) as total_eventos,
                STRING_AGG(titulo, ' | ') as titulos
            FROM eventos
            WHERE activo = true
            AND fecha_inicio::date BETWEEN %s AND %s
            GROUP BY fecha_inicio::date
            ORDER BY fecha
        """, (primer_dia, ultimo_dia))
        
        eventos_por_dia = cur.fetchall()
    
    # Crear DataFrame para el calendario
    dias_mes = []
    for dia in range(1, ultimo_dia.day + 1):
        fecha_actual = date(hoy.year, hoy.month, dia)
        eventos_dia = [e for e in eventos_por_dia if e[0] == fecha_actual]
        
        if eventos_dia:
            dias_mes.append({
                'Día': dia,
                'Eventos': eventos_dia[0][1],
                'Títulos': eventos_dia[0][2]
            })
        else:
            dias_mes.append({
                'Día': dia,
                'Eventos': 0,
                'Títulos': ''
            })
    
    df_calendario = pd.DataFrame(dias_mes)
    
    # Mostrar calendario en grid
    cols = st.columns(7)
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    for i, dia in enumerate(dias_semana):
        cols[i].markdown(f"**{dia}**")
    
    # Determinar primer día de la semana
    primer_dia_semana = primer_dia.weekday()  # 0 = lunes
    
    # Mostrar días en blanco antes del primer día
    for i in range(primer_dia_semana):
        cols[i].write("")
    
    # Mostrar días del mes
    for dia in df_calendario.itertuples():
        col_idx = (dia.Día + primer_dia_semana - 1) % 7
        with cols[col_idx]:
            if dia.Eventos > 0:
                with st.container():
                    st.markdown(f"**{dia.Día}**")
                    st.markdown(f"🎉 {dia.Eventos}")
                    if st.button("Ver", key=f"cal_{dia.Día}"):
                        st.info(dia.Títulos)
            else:
                st.markdown(f"**{dia.Día}**")

def mostrar_mis_inscripciones(usuario_id):
    """Muestra los eventos a los que el usuario está inscrito."""
    
    st.subheader("Mis Inscripciones")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                e.titulo,
                e.tipo,
                e.fecha_inicio,
                e.fecha_fin,
                e.lugar,
                i.fecha_inscripcion,
                i.asistio,
                i.pago_id,
                e.id as evento_id
            FROM inscripciones_eventos i
            JOIN eventos e ON i.evento_id = e.id
            WHERE i.usuario_id = %s
            ORDER BY e.fecha_inicio DESC
        """, (usuario_id,))
        
        inscripciones = cur.fetchall()
        
        if not inscripciones:
            st.info("No estás inscrito en ningún evento.")
            return
        
        # Separar en eventos pasados y futuros
        ahora = datetime.now()
        futuros = []
        pasados = []
        
        for ins in inscripciones:
            if ins[2] > ahora:  # fecha_inicio > ahora
                futuros.append(ins)
            else:
                pasados.append(ins)
        
        if futuros:
            st.subheader("📌 Próximos Eventos")
            for ins in futuros:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{ins[0]}**")
                        st.markdown(f"📅 {ins[2].strftime('%d/%m/%Y %H:%M')} | 📍 {ins[4]}")
                    
                    with col2:
                        if st.button("Cancelar inscripción", key=f"cancel_{ins[8]}"):
                            cancelar_inscripcion(ins[8], usuario_id)
                    
                    st.markdown("---")
        
        if pasados:
            st.subheader("✅ Eventos Pasados")
            for ins in pasados:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{ins[0]}**")
                        st.markdown(f"📅 {ins[2].strftime('%d/%m/%Y')}")
                    
                    with col2:
                        if ins[6]:  # asistio
                            st.markdown("✅ Asistió")
                        else:
                            st.markdown("❌ No asistió")
                    
                    with col3:
                        if not ins[7]:  # no tiene constancia
                            if st.button("📄 Generar constancia", key=f"const_{ins[8]}"):
                                generar_constancia(ins[8], usuario_id)
                    
                    st.markdown("---")

def inscribirse_evento(evento_id):
    """Procesa la inscripción a un evento."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Verificar si el evento es gratuito o de pago
            cur.execute("""
                SELECT es_gratuito, precio, capacidad_maxima,
                       (SELECT COUNT(*) FROM inscripciones_eventos WHERE evento_id = %s) as inscritos
                FROM eventos
                WHERE id = %s
            """, (evento_id, evento_id))
            
            gratuito, precio, capacidad, inscritos = cur.fetchone()
            
            # Verificar capacidad
            if capacidad and inscritos >= capacidad:
                add_notification("El evento ha alcanzado su capacidad máxima", "error")
                return
            
            if gratuito:
                # Inscripción gratuita
                cur.execute("""
                    INSERT INTO inscripciones_eventos (evento_id, usuario_id)
                    VALUES (%s, %s)
                """, (evento_id, st.session_state.user['id']))
                
                add_notification("¡Inscripción exitosa!", "success")
            else:
                # Redirigir a pago
                st.session_state.pago_pendiente = {
                    'evento_id': evento_id,
                    'monto': precio,
                    'concepto': 'evento'
                }
                st.switch_page("pages/pagos_realizar.py")
            
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al inscribirse: {str(e)}", "error")

def cancelar_inscripcion(evento_id, usuario_id):
    """Cancela una inscripción a evento."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                DELETE FROM inscripciones_eventos
                WHERE evento_id = %s AND usuario_id = %s
            """, (evento_id, usuario_id))
            
            add_notification("Inscripción cancelada exitosamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al cancelar: {str(e)}", "error")

def generar_constancia(evento_id, usuario_id):
    """Genera una constancia de participación."""
    
    try:
        with get_db_cursor() as cur:
            # Verificar asistencia
            cur.execute("""
                UPDATE inscripciones_eventos
                SET asistio = true
                WHERE evento_id = %s AND usuario_id = %s
                RETURNING id
            """, (evento_id, usuario_id))
            
            if not cur.fetchone():
                add_notification("No se encontró la inscripción", "error")
                return
            
            # Obtener datos para la constancia
            cur.execute("""
                SELECT 
                    e.titulo,
                    e.fecha_inicio,
                    e.fecha_fin,
                    u.nombres || ' ' || u.apellido_paterno as nombre_completo
                FROM eventos e
                CROSS JOIN egresados u
                WHERE e.id = %s AND u.usuario_id = %s
            """, (evento_id, usuario_id))
            
            datos = cur.fetchone()
            
            if not datos:
                add_notification("No se encontraron los datos necesarios", "error")
                return
            
            # Aquí iría la lógica para generar el PDF
            # Por ahora simulamos
            add_notification(f"Constancia generada para: {datos[3]} - {datos[0]}", "success")
            
    except Exception as e:
        add_notification(f"Error al generar constancia: {str(e)}", "error")