import streamlit as st
import pandas as pd
import plotly.express as px
import importlib
from src.models.egresado import Egresado
from src.auth import logout_usuario
from src.utils.database import get_db_cursor, get_db_connection

# --- FUNCIONES DE CACHÉ PARA KPIs ---
@st.cache_data(ttl=120)
def get_admin_metrics():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM egresados")
            total_egresados = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'pendiente'")
            empresas_pendientes = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'activa'")
            empresas_activas = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ofertas WHERE activa = TRUE")
            ofertas_activas = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM postulaciones WHERE estado = 'recibido'")
            postulaciones_nuevas = cur.fetchone()[0]
        return total_egresados, empresas_pendientes, empresas_activas, ofertas_activas, postulaciones_nuevas
    except Exception as e:
        return None, None, None, None, None

@st.cache_data(ttl=120)
def get_egresados_por_mes():
    try:
        with get_db_connection() as conn:
            df_egresados_mes = pd.read_sql("SELECT * FROM v_egresados_por_mes LIMIT 12", con=conn)
            return df_egresados_mes
    except Exception as e:
        return None

@st.cache_data(ttl=120)
def get_employer_metrics(empresa_id):
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE activa = TRUE) as activas,
                    COUNT(*) FILTER (WHERE activa = FALSE) as cerradas,
                    (SELECT COUNT(*) FROM postulaciones p JOIN ofertas o ON p.oferta_id = o.id WHERE o.empresa_id = %s) as total_postulaciones
                FROM ofertas
                WHERE empresa_id = %s
            """, (empresa_id, empresa_id))
            return cur.fetchone()
    except Exception:
        return None, None, None

def get_perfil_completitud(usuario_id):
    """Calcula el % de completitud del perfil del egresado usando el modelo."""
    try:
        eg = Egresado.get_by_usuario_id(usuario_id)
        if eg:
            return eg.calcular_completitud_perfil() / 100
        return 0.20 # Base 20% si solo usuario fue creado
    except Exception:
        return 0.0

def get_ofertas_recomendadas(usuario_id, limit=3):
    """Obtiene ofertas sugeridas basadas en la carrera del egresado."""
    try:
        with get_db_cursor() as cur:
            # 1. Obtener la carrera del egresado
            cur.execute("SELECT carrera_principal FROM egresados WHERE usuario_id = %s", (usuario_id,))
            res = cur.fetchone()
            if not res or not res[0]:
                return []
            carrera = res[0]
            
            # 2. Buscar ofertas que contengan esa carrera en su array carrera_objetivo
            # y que estén activas, limitando resultados
            cur.execute("""
                SELECT o.id, o.titulo, o.modalidad, e.nombre_comercial 
                FROM ofertas o
                JOIN empresas e ON o.empresa_id = e.id
                WHERE o.activa = TRUE 
                  AND %s = ANY(o.carrera_objetivo)
                ORDER BY o.fecha_publicacion DESC
                LIMIT %s
            """, (carrera, limit))
            return cur.fetchall()
    except Exception:
        return []

def render_admin_dashboard(user):
    st.title("Dashboard de Administrador")
    col1, col2, col3, col4 = st.columns(4)

    metrics = get_admin_metrics()
    if metrics[0] is not None:
        total_egresados, emp_pendientes, emp_activas, ofertas_activas, post_nuevas = metrics
        
        col1.metric("Total Egresados", f"{total_egresados:,}")
        col2.metric("Empresas", f"{emp_activas} activas", delta=f"{emp_pendientes} pdtes")
        col3.metric("Ofertas Activas", f"{ofertas_activas:,}")
        col4.metric("Postulaciones Nuevas", f"{post_nuevas:,}")

        st.markdown("---")
        st.subheader("📈 Egresados Registrados por Mes")
        df_egresados_mes = get_egresados_por_mes()
        if df_egresados_mes is not None and not df_egresados_mes.empty:
            # Asegurar que el mes sea legible y sin zona horaria para Plotly
            df_egresados_mes['mes'] = pd.to_datetime(df_egresados_mes['mes']).dt.tz_localize(None)
            
            # Usar un gráfico de barras que es más visible con pocos puntos de datos
            fig = px.bar(
                df_egresados_mes, 
                x='mes', 
                y='total_egresados', 
                title='Tendencia de Registros',
                labels={'mes': 'Mes', 'total_egresados': 'Cantidad'},
                color_discrete_sequence=['#0056b3']
            )
            
            # Ajustar el formato del eje X para mostrar el nombre del mes
            fig.update_xaxes(dtick="M1", tickformat="%b %Y")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay suficientes datos históricos para mostrar el gráfico de registros.")

def render_egresado_dashboard(user):
    st.title("Mi Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Completitud de mi Perfil")
        completitud = get_perfil_completitud(user['id'])
        st.progress(completitud, text=f"{(completitud * 100):.0f}% completado")

        st.subheader("📋 Mis Postulaciones Recientes")
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT o.titulo, p.estado, p.fecha_postulacion
                    FROM postulaciones p
                    JOIN ofertas o ON p.oferta_id = o.id
                    WHERE p.egresado_id = (SELECT id FROM egresados WHERE usuario_id = %s)
                    ORDER BY p.fecha_postulacion DESC
                    LIMIT 5
                """, (user['id'],))
                postulaciones = cur.fetchall()
            
            if postulaciones:
                # Estilizar estado
                df_post = pd.DataFrame(postulaciones, columns=['Oferta', 'Estado', 'Fecha'])
                df_post['Fecha'] = pd.to_datetime(df_post['Fecha']).dt.strftime('%d/%m/%Y')
                st.dataframe(df_post, use_container_width=True, hide_index=True)
            else:
                st.info("No te has postulado a ninguna oferta aún.")
        except Exception:
             st.error("Error al cargar las postulaciones recientes.")
    
    with col2:
        st.subheader("💼 Ofertas Recomendadas")
        st.write("Basado en tu carrera profesional:")
        recomendaciones = get_ofertas_recomendadas(user['id'])
        
        if recomendaciones:
            for emp in recomendaciones:
                oferta_id, titulo, modalidad, empresa = emp
                with st.container(border=True):
                    st.markdown(f"**{titulo}** en *{empresa}*")
                    st.caption(f"Modalidad: {modalidad.capitalize()}")
        else:
            st.info("Por el momento no hay ofertas específicas para tu perfil activo. ¡Sigue revisando!")

def render_empleador_dashboard(user):
    st.title("Dashboard Empresa")
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT empresa_id FROM empleadores WHERE usuario_id = %s", (user['id'],))
            res = cur.fetchone()
            if res:
                empresa_id = res[0]
                cur.execute("SELECT razon_social, estado FROM empresas WHERE id = %s", (empresa_id,))
                empresa_data = cur.fetchone()
                if empresa_data:
                    st.subheader(f"Empresa: {empresa_data[0]} (Estado: {empresa_data[1]})")

                activas, cerradas, total_post = get_employer_metrics(empresa_id)
                if activas is not None:
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Ofertas Activas", activas)
                    col_b.metric("Ofertas Cerradas", cerradas)
                    col_c.metric("Total Postulaciones", total_post)

                st.subheader("Postulaciones Pendientes de Revisión")
                cur.execute("""
                    SELECT o.titulo, p.fecha_postulacion, eg.nombres, eg.apellido_paterno
                    FROM postulaciones p
                    JOIN ofertas o ON p.oferta_id = o.id
                    JOIN egresados eg ON p.egresado_id = eg.id
                    WHERE o.empresa_id = %s AND p.estado = 'recibido'
                    ORDER BY p.fecha_postulacion ASC
                    LIMIT 5
                """, (empresa_id,))
                pendientes = cur.fetchall()
                if pendientes:
                    df_pend = pd.DataFrame(pendientes, columns=['Oferta', 'Fecha', 'Nombres', 'Apellidos'])
                    st.dataframe(df_pend)
                else:
                    st.success("¡No hay postulaciones pendientes!")
            else:
                 st.warning("No se encontró información de la empresa asociada a este usuario.")
    except Exception:
        st.error("Error al cargar los datos del empleador.")

def show():
    user = st.session_state.user
    rol = user['rol']

    # El menú lateral ahora se maneja en app.py para ser persistente
    
    if rol == 'administrador':
        render_admin_dashboard(user)
    elif rol == 'egresado':
        render_egresado_dashboard(user)
    elif rol == 'empleador':
        render_empleador_dashboard(user)
    else:
        st.error("Rol de usuario no reconocido.")

    st.markdown("---")
    st.caption("Universidad Nacional de Trujillo - Sistema de Gestión de Egresados v1.0")