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
            fig = px.line(df_egresados_mes, x='mes', y='total_egresados', title='Tendencia de Registros')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No se pudo conectar a la base de datos para recuperar las métricas.")

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

def load_page(page_name):
    """Carga dinámicamente el módulo desde src.pages."""
    try:
        module_name = f"src.pages.{page_name}"
        module = importlib.import_module(module_name)
        if hasattr(module, 'show'):
            module.show()
        else:
            st.warning(f"La página '{page_name}' no provee una función 'show()'.")
    except ModuleNotFoundError:
        st.info(f"Página en construcción: {page_name}")

def show():
    user = st.session_state.user
    rol = user['rol']

    with st.sidebar:
        st.image("https://www.unitru.edu.pe/images/logo_unt.png", width=100)
        st.markdown(f"### ¡Bienvenido, {user['email']}!")
        st.markdown(f"**Rol:** `{rol.capitalize()}`")
        st.markdown("---")

        if rol == 'administrador':
            menu_options = {
                "🏠 Dashboard Principal": "dashboard",
                "👥 Egresados": "egresados_lista",
                "🏢 Empresas": "empresas_lista",
                "💼 Ofertas": "ofertas_gestionar",
                "📅 Eventos": "eventos_gestionar",
                "💰 Pagos": "pagos_admin",
                "📊 Reportes": "reportes_dashboard",
                "📝 Encuestas": "encuestas_disenar",
                "🔍 Consultas Avanzadas": "consultas_avanzadas",
                "📋 Bitácora": "auditoria_bitacora",
                "👤 Mi Perfil": "perfil_mi_cuenta"
            }
        elif rol == 'egresado':
            menu_options = {
                "🏠 Mi Dashboard": "dashboard",
                "👤 Mi Perfil": "egresados_mi_perfil",
                "💼 Buscar Ofertas": "ofertas_buscar",
                "📋 Mis Postulaciones": "postulaciones_seguimiento",
                "📅 Eventos": "eventos_calendario",
                "📄 Mis Pagos": "pagos_mis_vouchers",
                "📝 Encuestas Pendientes": "encuestas_responder"
            }
        elif rol == 'empleador':
            menu_options = {
                "🏠 Dashboard Empresa": "dashboard",
                "🏢 Mi Empresa": "empresa_perfil",
                "📢 Gestionar Ofertas": "ofertas_gestionar",
                "👥 Revisar Postulaciones": "postulaciones_revisar",
                "📅 Mis Eventos": "eventos_gestionar",
                "👤 Mi Perfil": "perfil_mi_cuenta"
            }
        else:
            menu_options = {"🏠 Dashboard": "dashboard"}

        selected_label = st.radio("Navegación", options=list(menu_options.keys()), index=0)
        selected_page = menu_options[selected_label]

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            logout_usuario()

    # Enrutamiento Principal
    if selected_page == "dashboard":
        if rol == 'administrador':
            render_admin_dashboard(user)
        elif rol == 'egresado':
            render_egresado_dashboard(user)
        elif rol == 'empleador':
            render_empleador_dashboard(user)
    else:
        # Cargar otra página usando importlib
        load_page(selected_page)

    st.markdown("---")
    st.caption("Universidad Nacional de Trujillo - Sistema de Gestión de Egresados v1.0")