import streamlit as st
import pandas as pd
import base64
from src.models.empresa import Empresa
from src.models.empleador import Empleador
from src.utils.database import get_db_cursor
from src.utils.session import add_notification

def show():
    """Muestra el perfil de la empresa adaptado al rol del usuario."""
    from src.utils.pdf_generator import generar_pdf_dashboard_empresa, generar_pdf_oferta_detalle
    user = st.session_state.user
    rol = user['rol']
    
    # 1. Limpieza de iconos: Título sin icono repetido
    st.title("Perfil de Empresa")
    
    # Lógica para obtener el ID de la empresa según el rol
    empresa_id = None
    
    if rol == 'empleador':
        empleador = Empleador.get_by_usuario_id(user['id'])
        if empleador:
            empresa_id = empleador.empresa_id
        else:
            st.error("❌ No se encontró un perfil de empleador asociado a su cuenta.")
            return
    elif rol == 'administrador':
        empresa_id = st.query_params.get('empresa_id', None)
        if not empresa_id:
            st.info("💡 Seleccione una empresa desde la lista de gestión para ver su perfil completo.")
            return
    elif rol == 'egresado':
        empresa_id = st.query_params.get('empresa_id', None)
        if not empresa_id:
            st.warning("⚠️ Debe seleccionar una empresa para ver su perfil.")
            return

    # Obtener datos de la empresa
    empresa = Empresa.get_by_id(empresa_id)
    if not empresa:
        st.error("🏢 Empresa no encontrada.")
        return

    # Caché simple por sesión para PDFs (evita regeneración idéntica)
    if "pdf_cache" not in st.session_state:
        st.session_state.pdf_cache = {}

    # --- ENCABEZADO DEL PERFIL ---
    col_logo, col_info = st.columns([1, 4])
    with col_logo:
        if empresa.logo_url:
            st.image(empresa.logo_url, width=150)
        else:
            st.markdown("<h1 style='font-size: 80px; margin:0;'>🏢</h1>", unsafe_allow_html=True)
    
    with col_info:
        st.header(empresa.razon_social)
        st.caption(f"📍 {empresa.direccion} | 🌐 {empresa.sitio_web or 'Sin sitio web'}")
        
        # Badge de estado
        color = "green" if empresa.estado == 'activa' else "orange" if empresa.estado == 'pendiente' else "red"
        st.markdown(f"<span style='background-color:{color}; color:white; padding:2px 8px; border-radius:10px; font-size:0.8rem;'>{empresa.estado.upper()}</span>", unsafe_allow_html=True)

    st.markdown("---")

    # --- CONTENIDO POR PESTAÑAS ---
    tab_dash, tab_info, tab_ofertas, tab_admin = st.tabs(
        ["📊 Dashboard", "📋 Información General", "💼 Ofertas Laborales", "⚙️ Gestión"]
    )

    with tab_dash:
        st.subheader("📊 Resumen de la empresa")
        stats = empresa.get_estadisticas()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ofertas totales", stats.get("total_ofertas", 0))
        col2.metric("Ofertas activas", stats.get("ofertas_activas", 0))
        col3.metric("Postulaciones", stats.get("total_postulaciones", 0))
        col4.metric("Empleadores", stats.get("total_empleadores", 0))

        st.markdown("---")
        st.subheader("📈 Actividad reciente")
        rows = []
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        o.titulo,
                        o.fecha_publicacion,
                        o.activa,
                        (SELECT COUNT(*) FROM postulaciones p WHERE p.oferta_id = o.id) as postulaciones
                    FROM ofertas o
                    WHERE o.empresa_id = %s
                    ORDER BY o.fecha_publicacion DESC
                    LIMIT 8
                    """,
                    (empresa.id,),
                )
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]

            if rows:
                df = pd.DataFrame(rows)
                df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"]).dt.strftime("%d/%m/%Y")
                df["Estado"] = df["activa"].map(lambda x: "✅ Activa" if x else "❌ Cerrada")
                st.dataframe(
                    df[["titulo", "fecha_publicacion", "Estado", "postulaciones"]],
                    column_config={
                        "titulo": "Oferta",
                        "fecha_publicacion": "Publicación",
                        "postulaciones": "Postulaciones",
                    },
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Aún no hay ofertas publicadas por esta empresa.")
        except Exception as e:
            st.warning(f"No se pudo cargar actividad reciente: {e}")

        # PDF del Dashboard (solo admin o empleador de su empresa)
        st.markdown("---")
        st.subheader("📄 Reportes del Dashboard")
        if rol in ["administrador", "empleador"]:
            dash_key = f"dash_empresa:{empresa.id}"
            if st.button("📄 Descargar resumen del Dashboard (PDF)", use_container_width=True):
                empresa_data = empresa.to_dict()
                pdf = generar_pdf_dashboard_empresa(
                    empresa_data=empresa_data,
                    stats=stats,
                    ofertas_recientes=rows,
                )
                st.session_state.pdf_cache[dash_key] = pdf
                add_notification("PDF del dashboard generado correctamente.", "success")
                st.rerun()

            dash_pdf = st.session_state.pdf_cache.get(dash_key)
            if dash_pdf:
                with st.expander("👁️ Vista previa (Dashboard PDF)", expanded=False):
                    b64 = base64.b64encode(dash_pdf).decode("utf-8")
                    st.components.v1.html(
                        f"""
                        <iframe
                            src="data:application/pdf;base64,{b64}"
                            width="100%"
                            height="420"
                            style="border: 1px solid #e6e6e6; border-radius: 6px;"
                        ></iframe>
                        """,
                        height=440,
                    )
                st.download_button(
                    label="📥 Descargar PDF del Dashboard",
                    data=dash_pdf,
                    file_name=f"Dashboard_{empresa.razon_social}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with tab_info:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Datos Legales")
            st.write(f"**🔢 RUC:** `{empresa.ruc}`")
            st.write(f"**🏭 Sector:** {empresa.sector_economico}")
            st.write(f"**👥 Tamaño:** {empresa.tamano_empresa}")
        
        with c2:
            st.markdown("### Contacto")
            st.write(f"**📧 Email:** {empresa.email_contacto}")
            st.write(f"**📱 Teléfono:** {empresa.telefono_contacto}")
            if empresa.fecha_aprobacion:
                st.write(f"**📅 Aprobada el:** {empresa.fecha_aprobacion.strftime('%d/%m/%Y')}")

    with tab_ofertas:
        st.subheader("💼 Ofertas Publicadas")
        
        # Lógica para mostrar detalles de una oferta seleccionada
        selected_oferta_id = st.session_state.get('view_oferta_id', None)
        
        if selected_oferta_id:
            from src.models.oferta import Oferta
            o = Oferta.get_by_id(selected_oferta_id)
            if o:
                with st.container(border=True):
                    st.button("⬅️ Volver a la lista", on_click=lambda: st.session_state.pop('view_oferta_id', None))
                    st.markdown(f"## {o.titulo}")
                    st.markdown(f"**Tipo:** {o.tipo.capitalize()} | **Modalidad:** {o.modalidad.capitalize()}")
                    st.markdown(f"**Ubicación:** {o.ubicacion}")
                    st.markdown("### Descripción")
                    st.write(o.descripcion)
                    st.markdown("### Requisitos")
                    st.write(o.requisitos)
                    if o.salario_min:
                        st.markdown(f"**Rango Salarial:** S/. {o.salario_min} - S/. {o.salario_max}")
                    st.caption(f"Fecha límite: {o.fecha_limite_postulacion.strftime('%d/%m/%Y')}")
                    
                    if rol == 'egresado':
                        if st.button("🚀 Postular ahora", type="primary", use_container_width=True):
                            st.info("Funcionalidad de postulación en desarrollo.")
                st.markdown("---")

        # Mostrar lista de ofertas
        ofertas = empresa.get_ofertas(activas_only=(rol == 'egresado'))
        
        if ofertas:
            for o in ofertas:
                with st.container(border=True):
                    col_t, col_b, col_pdf = st.columns([3, 1, 1])
                    with col_t:
                        st.markdown(f"**{o.titulo}**")
                        st.caption(f"{o.modalidad.capitalize()} | Publicado: {o.fecha_publicacion.strftime('%d/%m/%Y')}")
                    with col_b:
                        # 3. Fix "Ver Oferta": Usar session_state para mostrar detalles
                        if st.button("👁️ Ver Detalle", key=f"btn_o_{o.id}", use_container_width=True):
                            st.session_state.view_oferta_id = o.id
                            st.rerun()
                    with col_pdf:
                        # PDF por oferta (solo admin o empleador)
                        if rol in ["administrador", "empleador"]:
                            pdf_key = f"oferta_pdf:{o.id}"
                            if st.button("📄 PDF", key=f"pdf_o_{o.id}", use_container_width=True):
                                # Estadísticas de postulaciones por estado (modelo Oferta)
                                try:
                                    stats_post = o.get_estadisticas()
                                except Exception:
                                    stats_post = None

                                salario = "—"
                                if o.salario_min and o.salario_max:
                                    salario = f"S/. {o.salario_min} - {o.salario_max}"
                                elif o.salario_min:
                                    salario = f"Desde S/. {o.salario_min}"

                                oferta_data = {
                                    "titulo": o.titulo,
                                    "tipo": (o.tipo or "").capitalize(),
                                    "modalidad": (o.modalidad or "").capitalize(),
                                    "ubicacion": o.ubicacion or "—",
                                    "salario": salario,
                                    "fecha_publicacion": o.fecha_publicacion.strftime("%d/%m/%Y") if o.fecha_publicacion else "—",
                                    "fecha_limite": o.fecha_limite_postulacion.strftime("%d/%m/%Y") if o.fecha_limite_postulacion else "—",
                                    "activa": bool(o.activa),
                                    "descripcion": o.descripcion,
                                    "requisitos": o.requisitos,
                                }
                                empresa_data = empresa.to_dict()
                                public_url = empresa.sitio_web if empresa.sitio_web else None
                                pdf = generar_pdf_oferta_detalle(
                                    empresa_data=empresa_data,
                                    oferta_data=oferta_data,
                                    estadisticas_postulaciones=stats_post,
                                    public_url=public_url,
                                )
                                st.session_state.pdf_cache[pdf_key] = pdf
                                add_notification("PDF de oferta generado correctamente.", "success")
                                st.rerun()

                            oferta_pdf = st.session_state.pdf_cache.get(pdf_key)
                            if oferta_pdf:
                                st.download_button(
                                    label="⬇️ Descargar",
                                    data=oferta_pdf,
                                    file_name=f"Oferta_{o.titulo}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    key=f"dl_o_{o.id}",
                                )
        else:
            st.info("La empresa no tiene ofertas publicadas actualmente.")

    with tab_admin:
        if rol == 'empleador' or rol == 'administrador':
            st.subheader("🛠️ Panel de Gestión")
            
            # Formulario de edición (Solo para empleador o admin)
            with st.form("edit_empresa_form"):
                st.write("Actualizar información de la empresa")
                new_nombre = st.text_input("Nombre Comercial", value=empresa.nombre_comercial or "")
                new_direccion = st.text_input("Dirección", value=empresa.direccion or "")
                new_web = st.text_input("Sitio Web", value=empresa.sitio_web or "")
                new_email = st.text_input("Email de Contacto", value=empresa.email_contacto or "")
                
                submitted = st.form_submit_button("💾 Guardar Cambios")
                
                if submitted:
                    empresa.nombre_comercial = new_nombre
                    empresa.direccion = new_direccion
                    empresa.sitio_web = new_web
                    empresa.email_contacto = new_email
                    
                    exito, msg = empresa.save()
                    if exito:
                        add_notification(msg, "success")
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            st.subheader("👥 Gestión de empleadores (empresa)")
            st.caption("Este acceso es solo para administrador y administrador de empresa.")
            if rol == "administrador":
                st.info("Abra el módulo 'Gestión de Empleadores' para administrar usuarios por empresa.")
            else:
                empleador = Empleador.get_by_usuario_id(user["id"])
                if empleador and empleador.es_administrador_empresa:
                    st.info("Abra el módulo 'Gestión de Empleadores' para administrar su equipo.")
                else:
                    st.warning("Solo el administrador de la empresa puede gestionar empleadores.")
            
            # Botón para descargar PDF (Solo Admin o Empleador)
            st.markdown("---")
            st.write("📄 **Reportes Profesionales**")
            # Ya se muestra en el encabezado, pero podemos dejarlo aquí también si se desea
            # o eliminar esta parte redundante.
        else:
            st.warning("🔒 Esta sección es privada para la empresa.")
