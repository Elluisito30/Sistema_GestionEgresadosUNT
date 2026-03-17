import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.database import get_db_cursor
from src.utils.session import render_notifications, add_notification
from src.models.empresa import Empresa
from src.utils.pdf_generator import generar_pdf_empresas_seleccionadas, generar_pdf_reporte_generico

def show():
    """Muestra la página de gestión de empresas."""
    
    st.title("🏢 Gestión de Empresas")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Pendientes de Aprobación",
        "🏢 Directorio / Filtros",
        "📊 Estadísticas",
        "➕ Crear Empresa",
        "✏️ Editar Empresa"
    ])
    
    with tab1:
        mostrar_empresas_pendientes()
    
    with tab2:
        mostrar_empresas_activas()
    
    with tab3:
        mostrar_estadisticas_empresas()

    with tab4:
        crear_empresa_admin()

    with tab5:
        editar_empresa_admin()

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

    # Lógica de Query (compartida entre visualización y reporte)
    query = """
        SELECT ruc, razon_social, sector_economico, tamano_empresa, email_contacto, estado
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

    # Botón para descargar reporte de lo que se está viendo (con filtros aplicados)
    col_exp1, col_exp2 = st.columns([3, 1])
    with col_exp2:
        if rows:
            pdf_bytes = generar_pdf_reporte_generico(rows, f"Directorio de Empresas ({estado})")
            st.download_button(
                "📄 Reporte PDF (Filtros actual)",
                data=pdf_bytes,
                file_name=f"Directorio_Empresas_{estado}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_export_all_empresas"
            )

    if rows:
        # Crear DataFrame con selección múltiple
        df = pd.DataFrame(rows)
        df["seleccionar"] = False
        
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

        # Exportación múltiple a PDF (lógica simplificada)
        seleccionadas = edited[edited["seleccionar"] == True]  # noqa: E712
        if not seleccionadas.empty:
            empresas_sel = seleccionadas[['ruc', 'razon_social', 'sector_economico', 'tamano_empresa', 'estado']].to_dict('records')

            # KPIs del grupo (reusando lógica existente)
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
                key="btn_export_sel_empresas"
            )
        
        # Ver detalles individuales + ficha PDF por empresa
        # Reusamos los IDs de 'rows' que ya tenemos
        with get_db_cursor() as cur:
            # Necesitamos los IDs originales para ver detalles
            cur.execute(query.replace("ruc, razon_social, sector_economico, tamano_empresa, email_contacto, estado", "id, ruc, razon_social"), params)
            empresas_ids = {r[1]: (r[0], r[2]) for r in cur.fetchall()}

        selected_ruc = st.selectbox(
            "Seleccione una empresa para ver detalles:",
            options=list(empresas_ids.keys()),
            format_func=lambda r: empresas_ids[r][1],
        )

        if selected_ruc:
            emp_id, emp_nombre = empresas_ids[selected_ruc]
            with st.expander(f"Detalles de {emp_nombre}", expanded=True):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    mostrar_detalles_empresa(emp_id)
                with col_b:
                    # Obtenemos el objeto Empresa real para generar su ficha
                    emp_obj = Empresa.get_by_id(emp_id)
                    
                    # Botón para editar (Admin)
                    if st.button("✏️ Editar Información", key=f"btn_edit_{emp_id}", use_container_width=True):
                        st.session_state.admin_editing_empresa_id = emp_id
                        st.session_state.current_tab = 4 # Tab 5 (índice 4)
                        st.rerun()

                    ok, ficha_pdf = emp_obj.generar_ficha_pdf()
                    if ok:
                        st.download_button(
                            "📄 Ficha PDF Individual",
                            data=ficha_pdf,
                            file_name=f"Ficha_Empresa_{emp_nombre}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"btn_ficha_pdf_{emp_id}"
                        )
                    else:
                        st.caption(str(ficha_pdf))
    else:
        st.warning("No se encontraron empresas con los filtros seleccionados.")


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

def editar_empresa_admin():
    """Formulario de edición de empresa (solo admin)."""
    user = st.session_state.user
    if user.get("rol") != "administrador":
        st.warning("🔒 Solo administradores pueden editar empresas desde aquí.")
        return

    st.subheader("✏️ Editar información de empresa")
    
    # Selección de empresa a editar
    empresa_id = st.session_state.get("admin_editing_empresa_id")
    
    with get_db_cursor() as cur:
        cur.execute("SELECT id, razon_social, ruc FROM empresas ORDER BY razon_social ASC")
        empresas_list = cur.fetchall()
        
    if not empresas_list:
        st.info("No hay empresas registradas.")
        return
        
    empresa_options = {r[0]: f"{r[1]} ({r[2]})" for r in empresas_list}
    
    # Si no hay una empresa seleccionada desde el directorio, mostrar selector
    selected_id = st.selectbox(
        "Seleccione la empresa a editar",
        options=list(empresa_options.keys()),
        format_func=lambda x: empresa_options[x],
        index=list(empresa_options.keys()).index(empresa_id) if empresa_id in empresa_options else 0,
        key="admin_edit_empresa_selector"
    )
    
    if selected_id:
        emp = Empresa.get_by_id(selected_id)
        if emp:
            with st.form("form_editar_empresa_admin"):
                col1, col2 = st.columns(2)
                with col1:
                    ruc = st.text_input("RUC *", value=emp.ruc)
                    razon_social = st.text_input("Razón social *", value=emp.razon_social)
                    nombre_comercial = st.text_input("Nombre comercial", value=emp.nombre_comercial or "")
                    sector = st.text_input("Sector económico", value=emp.sector_economico or "")
                with col2:
                    tamano = st.selectbox(
                        "Tamaño", 
                        options=["micro", "pequeña", "mediana", "grande"],
                        index=["micro", "pequeña", "mediana", "grande"].index(emp.tamano_empresa) if emp.tamano_empresa in ["micro", "pequeña", "mediana", "grande"] else 0
                    )
                    direccion = st.text_input("Dirección", value=emp.direccion or "")
                    telefono = st.text_input("Teléfono", value=emp.telefono_contacto or "")
                    email = st.text_input("Email de contacto", value=emp.email_contacto or "")
                    web = st.text_input("Sitio web", value=emp.sitio_web or "")
                    logo = st.text_input("URL del Logo", value=emp.logo_url or "")
                
                estado = st.selectbox(
                    "Estado de la empresa",
                    options=["activa", "pendiente", "rechazada"],
                    index=["activa", "pendiente", "rechazada"].index(emp.estado) if emp.estado in ["activa", "pendiente", "rechazada"] else 0
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                with col_btn2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if submitted:
                    if not ruc or not razon_social:
                        st.error("RUC y Razón social son obligatorios.")
                        return
                    
                    emp.ruc = ruc
                    emp.razon_social = razon_social
                    emp.nombre_comercial = nombre_comercial
                    emp.sector_economico = sector
                    emp.tamano_empresa = tamano
                    emp.direccion = direccion
                    emp.telefono_contacto = telefono
                    emp.email_contacto = email
                    emp.sitio_web = web
                    emp.estado = estado
                    emp.logo_url = logo
                    
                    ok, msg = emp.save()
                    if ok:
                        add_notification("Empresa actualizada correctamente.", "success")
                        st.session_state.pop("admin_editing_empresa_id", None)
                        st.rerun()
                    else:
                        st.error(msg)
                
                if cancelar:
                    st.session_state.pop("admin_editing_empresa_id", None)
                    st.rerun()

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