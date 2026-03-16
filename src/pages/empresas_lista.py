import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.database import get_db_cursor
from src.utils.session import render_notifications, add_notification
from src.models.empresa import Empresa
from src.utils.pdf_generator import generar_pdf_empresas_seleccionadas

def show():
    """Muestra la página de gestión de empresas."""
    
    st.title("🏢 Gestión de Empresas")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Pendientes de Aprobación",
        "🏢 Directorio / Filtros",
        "📊 Estadísticas"
        ,
        "➕ Crear Empresa"
    ])
    
    with tab1:
        mostrar_empresas_pendientes()
    
    with tab2:
        mostrar_empresas_activas()
    
    with tab3:
        mostrar_estadisticas_empresas()

    with tab4:
        crear_empresa_admin()

def mostrar_empresas_pendientes():
    """Muestra las empresas pendientes de aprobación."""
    st.subheader("Empresas Esperando Validación")
    
    # Usar el método del modelo
    empresas = Empresa.get_pendientes()
    
    if not empresas:
        st.info("No hay solicitudes de registro pendientes.")
        return
    
    for empresa in empresas:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {empresa.razon_social}")
                st.markdown(f"**RUC:** `{empresa.ruc}` | **Sector:** {empresa.sector_economico}")
                st.markdown(f"**Email:** {empresa.email_contacto} | **Tel:** {empresa.telefono_contacto}")
                st.caption(f"Registrada el: {empresa.fecha_registro.strftime('%d/%m/%Y %H:%M')}")
            
            with col2:
                # Mostrar estadísticas rápidas si existen
                stats = empresa.get_estadisticas()
                st.metric("Empleadores", stats['total_empleadores'])
            
            with col3:
                # Botones de acción
                if st.button("✅ Aprobar", key=f"apr_{empresa.id}", use_container_width=True):
                    aprobar_empresa_action(empresa)
                
                # Botón de rechazo con popover para el motivo
                with st.popover("❌ Rechazar", use_container_width=True):
                    motivo = st.text_area("Motivo del rechazo", placeholder="Explique por qué se rechaza...")
                    if st.button("Confirmar Rechazo", key=f"conf_rej_{empresa.id}"):
                        if motivo:
                            rechazar_empresa_action(empresa, motivo)
                        else:
                            st.error("Debe indicar un motivo.")

def mostrar_empresas_activas():
    """Muestra el directorio con filtros (admin)."""
    st.subheader("Directorio de Empresas")
    
    # Filtros de búsqueda
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        termino = st.text_input("🔍 Buscar", placeholder="Nombre, RUC o Sector...")
    with col2:
        estado = st.selectbox("Estado", options=["activa", "pendiente", "rechazada"], index=0)
    with col3:
        # Sector económico desde BD (activos)
        with get_db_cursor() as cur:
            cur.execute("SELECT DISTINCT sector_economico FROM empresas WHERE sector_economico IS NOT NULL ORDER BY sector_economico")
            sectores = [r[0] for r in cur.fetchall()]
        sector = st.selectbox("Sector", options=["Todos"] + sectores, index=0)

    # Query directa para soportar filtro por estado/sector sin cambiar modelos
    query = """
        SELECT id, ruc, razon_social, sector_economico, tamano_empresa, email_contacto, estado, fecha_registro
        FROM empresas
        WHERE 1=1
    """
    params = []
    if estado:
        query += " AND estado = %s"
        params.append(estado)
    if sector and sector != "Todos":
        query += " AND sector_economico = %s"
        params.append(sector)
    if termino:
        query += " AND (razon_social ILIKE %s OR nombre_comercial ILIKE %s OR ruc LIKE %s OR sector_economico ILIKE %s)"
        t = f"%{termino}%"
        params.extend([t, t, t, t])
    query += " ORDER BY razon_social ASC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    empresas = [Empresa.get_by_id(r["id"]) for r in rows]
    
    if empresas:
        # Crear DataFrame con selección múltiple
        data = []
        for e in empresas:
            d = e.to_dict()
            d["seleccionar"] = False
            data.append(d)
        df = pd.DataFrame(data)
        
        # Selección de columnas para mostrar
        cols_display = ['seleccionar', 'ruc', 'razon_social', 'sector_economico', 'tamano_empresa', 'email_contacto', 'estado']
        edited = st.data_editor(
            df[cols_display],
            column_config={
                "seleccionar": st.column_config.CheckboxColumn("Seleccionar"),
                "ruc": "RUC",
                "razon_social": "Razón Social",
                "sector_economico": "Sector",
                "tamano_empresa": "Tamaño",
                "email_contacto": "Contacto",
                "estado": "Estado"
            },
            use_container_width=True,
            hide_index=True
        )

        # Exportación múltiple a PDF
        seleccionadas = edited[edited["seleccionar"] == True]  # noqa: E712
        if not seleccionadas.empty:
            empresas_sel = []
            for _, row in seleccionadas.iterrows():
                empresas_sel.append(
                    {
                        "ruc": row.get("ruc"),
                        "razon_social": row.get("razon_social"),
                        "sector_economico": row.get("sector_economico"),
                        "tamano_empresa": row.get("tamano_empresa"),
                        "estado": row.get("estado"),
                    }
                )

            # KPIs del grupo
            kpis = {
                "total": len(empresas_sel),
                "activas": sum(1 for e in empresas_sel if e.get("estado") == "activa"),
                "pendientes": sum(1 for e in empresas_sel if e.get("estado") == "pendiente"),
                "rechazadas": sum(1 for e in empresas_sel if e.get("estado") == "rechazada"),
            }
            top_sectores = (
                pd.Series([e.get("sector_economico") for e in empresas_sel])
                .value_counts()
                .head(3)
                .to_dict()
            )
            kpis["top_sectores"] = ", ".join([f"{k}({v})" for k, v in top_sectores.items()]) if top_sectores else "—"

            pdf_group = generar_pdf_empresas_seleccionadas(empresas_sel, kpis)
            st.download_button(
                "📦 Exportar Seleccionadas (PDF)",
                data=pdf_group,
                file_name="Empresas_seleccionadas.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        
        # Ver detalles individuales + ficha PDF por empresa
        selected_ruc = st.selectbox(
            "Seleccione una empresa para ver detalles:",
            options=[e.ruc for e in empresas],
            format_func=lambda r: next(e.razon_social for e in empresas if e.ruc == r),
        )

        if selected_ruc:
            emp = next(e for e in empresas if e.ruc == selected_ruc)
            with st.expander(f"Detalles de {emp.razon_social}", expanded=True):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    mostrar_detalles_empresa(emp.id)
                with col_b:
                    ok, ficha_pdf = emp.generar_ficha_pdf()
                    if ok:
                        st.download_button(
                            "📄 Ficha PDF",
                            data=ficha_pdf,
                            file_name=f"Ficha_Empresa_{emp.razon_social}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    else:
                        st.caption(str(ficha_pdf))
    else:
        st.warning("No se encontraron empresas activas.")


def crear_empresa_admin():
    """Formulario de creación de empresa (solo admin)."""
    user = st.session_state.user
    if user.get("rol") != "administrador":
        st.warning("🔒 Solo administradores pueden crear empresas.")
        return

    st.subheader("➕ Registrar nueva empresa")
    st.caption("Las empresas nuevas se registran como 'pendiente' para validación.")

    with st.form("form_crear_empresa"):
        col1, col2 = st.columns(2)
        with col1:
            ruc = st.text_input("RUC *", placeholder="11 dígitos")
            razon_social = st.text_input("Razón social *")
            nombre_comercial = st.text_input("Nombre comercial")
            sector = st.text_input("Sector económico")
        with col2:
            tamano = st.selectbox("Tamaño", options=["micro", "pequeña", "mediana", "grande"])
            direccion = st.text_input("Dirección")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email de contacto")
            web = st.text_input("Sitio web")

        submitted = st.form_submit_button("💾 Crear empresa", use_container_width=True)
        if submitted:
            if not ruc or not razon_social:
                st.error("RUC y Razón social son obligatorios.")
                return
            if not Empresa.es_ruc_valido(ruc):
                st.error("RUC inválido: deben ser 11 dígitos numéricos.")
                return

            emp = Empresa(
                ruc=ruc,
                razon_social=razon_social,
                nombre_comercial=nombre_comercial,
                sector_economico=sector,
                tamano_empresa=tamano,
                direccion=direccion,
                telefono_contacto=telefono,
                email_contacto=email,
                sitio_web=web,
                estado="pendiente",
            )
            ok, msg = emp.save()
            if ok:
                add_notification("Empresa creada correctamente (pendiente de aprobación).", "success")
                st.rerun()
            else:
                st.error(msg)

def aprobar_empresa_action(empresa):
    """Lógica para el botón de aprobación."""
    admin_id = st.session_state.user['id']
    empresa.aprobar(admin_id)
    add_notification(f"Empresa '{empresa.razon_social}' aprobada con éxito.", "success")
    st.rerun()

def rechazar_empresa_action(empresa, motivo):
    """Lógica para el botón de rechazo."""
    admin_id = st.session_state.user['id']
    empresa.rechazar(admin_id, motivo)
    add_notification(f"Empresa '{empresa.razon_social}' rechazada.", "warning")
    st.rerun()

def mostrar_estadisticas_empresas():
    """Muestra estadísticas generales usando KPIs."""
    st.subheader("Análisis del Sector Empresarial")

    estado_filtro = st.selectbox(
        "Filtrar gráficos por estado",
        options=["Todos", "activa", "pendiente", "rechazada"],
        index=0,
        key="empresas_stats_estado",
    )

    where_estado = ""
    params_estado = []
    if estado_filtro != "Todos":
        where_estado = "WHERE estado = %s"
        params_estado = [estado_filtro]
    
    with get_db_cursor() as cur:
        # KPIs rápidos (aplican el mismo filtro de estado de los gráficos)
        cur.execute("SELECT COUNT(*) FROM empresas")
        total_global = cur.fetchone()[0]

        if estado_filtro == "Todos":
            cur.execute("SELECT COUNT(*) FROM empresas")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'activa'")
            activas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = 'pendiente'")
            pendientes = cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = %s", [estado_filtro])
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = %s AND estado = 'activa'", [estado_filtro])
            activas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM empresas WHERE estado = %s AND estado = 'pendiente'", [estado_filtro])
            pendientes = cur.fetchone()[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Registradas", total)
        c2.metric("Activas", activas)
        c3.metric("Pendientes", pendientes, delta=pendientes, delta_color="inverse")

        if estado_filtro != "Todos":
            st.caption(f"KPIs filtrados por estado '{estado_filtro}'. Total global de empresas: {total_global}.")

        # Distribución por sector económico
        cur.execute(
            f"""
            SELECT
                COALESCE(NULLIF(TRIM(sector_economico), ''), 'Sin especificar') AS sector,
                COUNT(*) AS total
            FROM empresas
            {where_estado}
            GROUP BY 1
            ORDER BY total DESC, sector ASC
            """,
            params_estado,
        )
        sector_rows = cur.fetchall()

        # Distribución por tamaño de empresa
        cur.execute(
            f"""
            SELECT
                COALESCE(NULLIF(TRIM(tamano_empresa), ''), 'Sin especificar') AS tamano,
                COUNT(*) AS total
            FROM empresas
            {where_estado}
            GROUP BY 1
            ORDER BY total DESC, tamano ASC
            """,
            params_estado,
        )
        tamano_rows = cur.fetchall()

    st.markdown("---")
    col_sector, col_tamano = st.columns(2)

    with col_sector:
        st.markdown("#### Distribución por Sector")
        if sector_rows:
            df_sector = pd.DataFrame(sector_rows, columns=["sector", "total"]).set_index("sector")
            st.bar_chart(df_sector["total"], use_container_width=True)
            st.dataframe(
                df_sector.reset_index().rename(columns={"sector": "Sector", "total": "Empresas"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay datos de sector para mostrar.")

    with col_tamano:
        st.markdown("#### Distribución por Tamaño")
        if tamano_rows:
            orden_tamano = {
                "micro": 1,
                "pequeña": 2,
                "mediana": 3,
                "grande": 4,
                "Sin especificar": 99,
            }
            df_tamano = pd.DataFrame(tamano_rows, columns=["tamano", "total"])
            df_tamano["_orden"] = df_tamano["tamano"].map(lambda x: orden_tamano.get(str(x), 98))
            df_tamano = df_tamano.sort_values(by=["_orden", "total"], ascending=[True, False]).drop(columns=["_orden"])
            df_tamano = df_tamano.set_index("tamano")

            st.bar_chart(df_tamano["total"], use_container_width=True)
            st.dataframe(
                df_tamano.reset_index().rename(columns={"tamano": "Tamaño", "total": "Empresas"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay datos de tamaño para mostrar.")

def mostrar_detalles_empresa(empresa_id):
    """Reutiliza la lógica de detalles del modelo y vista."""
    emp = Empresa.get_by_id(empresa_id)
    if not emp:
        st.error("Empresa no encontrada.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Dirección:** {emp.direccion}")
        st.write(f"**Sitio Web:** {emp.sitio_web}")
    with c2:
        st.write(f"**Tamaño:** {emp.tamano_empresa}")
        st.write(f"**Fecha Registro:** {emp.fecha_registro.strftime('%d/%m/%Y')}")
    
    st.markdown("---")
    st.subheader("👥 Empleadores Asociados")
    empleadores = emp.get_empleadores()
    if empleadores:
        for em in empleadores:
            st.write(f"- {em.nombre_completo} ({em.cargo})")
    else:
        st.caption("No hay empleadores vinculados aún.")