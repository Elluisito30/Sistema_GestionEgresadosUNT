import streamlit as st
import pandas as pd
import plotly.express as px
from src.auth import logout_usuario
from src.utils.database import get_db_cursor

# Importar páginas de módulos (para navegación futura)
# from src.pages import egresados_mi_perfil, ofertas_buscar, etc.

def show():
    """Función principal que renderiza el dashboard y la navegación."""

    user = st.session_state.user
    rol = user['rol']

    # --- BARRA LATERAL (Menú Contextual) ---
    with st.sidebar:
        st.image("https://www.unitru.edu.pe/images/logo_unt.png", width=100)  # Logo
        st.markdown(f"### ¡Bienvenido, {user['email']}!")
        st.markdown(f"**Rol:** `{rol.capitalize()}`")
        st.markdown("---")

        # Menú de navegación basado en el rol
        if rol == 'administrador':
            menu_options = {
                "🏠 Dashboard Principal": "dashboard",
                "👥 Egresados": "egresados",
                "🏢 Empresas": "empresas",
                "💼 Ofertas": "ofertas_admin",
                "📅 Eventos": "eventos",
                "💰 Pagos": "pagos_admin",
                "📊 Reportes": "reportes",
                "📝 Encuestas": "encuestas",
                "🔍 Consultas Avanzadas": "consultas",
                "📋 Bitácora": "auditoria",
                "👤 Mi Perfil": "perfil"
            }
        elif rol == 'egresado':
            menu_options = {
                "🏠 Mi Dashboard": "dashboard",
                "👤 Mi Perfil": "perfil",
                "💼 Buscar Ofertas": "buscar_ofertas",
                "📋 Mis Postulaciones": "mis_postulaciones",
                "📅 Eventos": "eventos",
                "📄 Mis Pagos": "mis_pagos",
                "📝 Encuestas Pendientes": "encuestas"
            }
        elif rol == 'empleador':
            menu_options = {
                "🏠 Dashboard Empresa": "dashboard",
                "🏢 Mi Empresa": "mi_empresa",
                "📢 Gestionar Ofertas": "gestionar_ofertas",
                "👥 Revisar Postulaciones": "revisar_postulaciones",
                "📅 Mis Eventos": "eventos",
                "👤 Mi Perfil": "perfil"
            }
        else:
            menu_options = {"🏠 Dashboard": "dashboard"}

        # Selector de página
        selected_page = st.radio("Navegación", options=list(menu_options.keys()), index=0)
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            logout_usuario()

    # --- CONTENIDO PRINCIPAL (DASHBOARD) ---
    # Por ahora, solo implementamos el dashboard principal según el rol.
    # La lógica de cambio de página se implementaría con condicionales o un patrón de enrutamiento.

    st.title(f"Dashboard de {rol.capitalize()}")

    # --- DASHBOARD PARA ADMINISTRADOR ---
    if rol == 'administrador':
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with get_db_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM egresados")
                total_egresados = cur.fetchone()[0]
            st.metric("Total Egresados", f"{total_egresados:,}")

        with col2:
            with get_db_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'pendiente'")
                empresas_pendientes = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'activa'")
                empresas_activas = cur.fetchone()[0]
            st.metric("Empresas", f"{empresas_activas} activas", delta=f"{empresas_pendientes} pendientes")

        with col3:
            with get_db_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM ofertas WHERE activa = TRUE")
                ofertas_activas = cur.fetchone()[0]
            st.metric("Ofertas Activas", f"{ofertas_activas:,}")

        with col4:
            with get_db_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM postulaciones WHERE estado = 'recibido'")
                postulaciones_nuevas = cur.fetchone()[0]
            st.metric("Postulaciones Nuevas", f"{postulaciones_nuevas:,}")

        st.markdown("---")
        st.subheader("📈 Egresados Registrados por Mes")
        # Usar la vista creada
        df_egresados_mes = pd.read_sql("SELECT * FROM v_egresados_por_mes LIMIT 12", con=get_db_connection().__enter__())
        if not df_egresados_mes.empty:
            fig = px.line(df_egresados_mes, x='mes', y='total_egresados', title='Tendencia de Registros')
            st.plotly_chart(fig, use_container_width=True)

        # ... (más KPIs y gráficos)

    # --- DASHBOARD PARA EGRESADO ---
    elif rol == 'egresado':
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Completitud de mi Perfil")
            # Aquí iría lógica para calcular el % del perfil completado
            st.progress(0.75, text="75% completado")

            st.subheader("📋 Mis Postulaciones Recientes")
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
                df_post = pd.DataFrame(postulaciones, columns=['Oferta', 'Estado', 'Fecha'])
                st.dataframe(df_post, use_container_width=True)
            else:
                st.info("No te has postulado a ninguna oferta aún.")

        with col2:
            st.subheader("💼 Ofertas Recomendadas")
            # Aquí lógica más compleja de recomendación
            st.write("(Basado en tu perfil)")
            # Simular ofertas
            st.info("Ingeniero de Software - Remoto")
            st.info("Prácticas en Data Science - Presencial")

    # --- DASHBOARD PARA EMPLEADOR ---
    elif rol == 'empleador':
        # Obtener el ID de la empresa del empleador
        with get_db_cursor() as cur:
            cur.execute("SELECT empresa_id FROM empleadores WHERE usuario_id = %s", (user['id'],))
            res = cur.fetchone()
            if res:
                empresa_id = res[0]
                # Datos de la empresa
                cur.execute("SELECT razon_social, estado FROM empresas WHERE id = %s", (empresa_id,))
                empresa_data = cur.fetchone()
                if empresa_data:
                    st.subheader(f"Empresa: {empresa_data[0]} (Estado: {empresa_data[1]})")

                # Métricas de ofertas
                cur.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE activa = TRUE) as activas,
                        COUNT(*) FILTER (WHERE activa = FALSE) as cerradas,
                        (SELECT COUNT(*) FROM postulaciones p JOIN ofertas o ON p.oferta_id = o.id WHERE o.empresa_id = %s) as total_postulaciones
                    FROM ofertas
                    WHERE empresa_id = %s
                """, (empresa_id, empresa_id))
                activas, cerradas, total_post = cur.fetchone()

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

    # --- ENRUTAMIENTO (Muy básico) ---
    # En una implementación real, aquí usarías un if/elif para cargar la página seleccionada
    # Por ejemplo:
    # if selected_page == "👤 Mi Perfil":
    #     egresados_mi_perfil.show()
    # else:
    #     ... (mostrar dashboard por defecto)

    # Pie de página (opcional)
    st.markdown("---")
    st.caption("Universidad Nacional de Trujillo - Sistema de Gestión de Egresados v1.0")