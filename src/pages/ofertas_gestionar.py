"""
Modulo de gestion de ofertas laborales.
Permite crear, editar, cerrar y exportar ofertas con control por rol.
"""

from datetime import date
import re

import pandas as pd
import streamlit as st

from src.utils.database import get_db_cursor
from src.utils.pdf_generator import generar_pdf_oferta_detalle, generar_pdf_ofertas_lista
from src.utils.session import add_notification, render_notifications

TIPOS_OFERTA = ["empleo", "pasantia", "practicas"]
MODALIDADES = ["presencial", "remoto", "hibrido"]
CARRERAS_BASE = [
    "Informatica",
    "Sistemas",
    "Administracion",
    "Contabilidad",
    "Derecho",
    "Medicina",
    "Ingenieria Industrial",
]


def _slugify_filename(texto):
    base = (texto or "documento").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "documento"


def _etiqueta_oferta(oferta):
    fecha = ""
    if oferta.get("fecha_publicacion"):
        fecha = pd.to_datetime(oferta["fecha_publicacion"]).strftime("%d/%m/%Y")
    estado = "Activa" if oferta.get("activa") else "Cerrada"
    return f"{oferta.get('titulo', 'Sin titulo')} - {oferta.get('empresa', 'Sin empresa')} ({fecha}) [{estado}]"


def show():
    user = st.session_state.user
    rol = user["rol"]

    st.title("📢 Gestión de Ofertas Laborales")
    render_notifications()

    if rol not in ["administrador", "empleador", "egresado"]:
        st.error("No tienes permisos para acceder a esta pagina.")
        return

    if rol == "administrador":
        tab1, tab2 = st.tabs(["🔎 Gestión y Analisis", "➕ Nueva Oferta (Admin)"])
    elif rol == "empleador":
        tab1, tab2 = st.tabs(["📋 Mis Ofertas", "➕ Publicar Nueva Oferta"])
    else: # egresado
        tab1, tab2 = st.tabs(["📋 Mis Emprendimientos/Ofertas", "➕ Publicar como Egresado"])

    with tab1:
        _mostrar_lista_gestion(user, rol)

    with tab2:
        _mostrar_formulario_crear(user, rol)


def _obtener_id_egresado(usuario_id):
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM egresados WHERE usuario_id = %s", (usuario_id,))
        row = cur.fetchone()
        return row[0] if row else None


def _obtener_empleador(usuario_id):
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, empresa_id
            FROM empleadores
            WHERE usuario_id = %s
            """,
            (usuario_id,),
        )
        row = cur.fetchone()
        if not row:
            return None, None
        return row[0], row[1]


def _obtener_empresas_activas():
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, razon_social, ruc, sitio_web
            FROM empresas
            WHERE estado = 'activa'
            ORDER BY razon_social ASC
            """
        )
        rows = cur.fetchall()
    return [
        {"id": r[0], "razon_social": r[1], "ruc": r[2], "sitio_web": r[3]} for r in rows
    ]


def _buscar_ofertas(rol, user_id, termino=None, estado=None, tipo=None, modalidad=None):
    query = """
        SELECT
            o.id,
            o.empresa_id,
            o.titulo,
            o.descripcion,
            o.requisitos,
            o.tipo,
            o.modalidad,
            o.ubicacion,
            o.salario_min,
            o.salario_max,
            o.fecha_publicacion,
            o.fecha_limite_postulacion,
        o.activa,
        o.carrera_objetivo,
        COALESCE(e.razon_social, 'Emprendimiento Egresado') AS empresa,
        e.ruc AS empresa_ruc,
        e.sitio_web,
        COUNT(p.id) AS postulaciones
    FROM ofertas o
    LEFT JOIN empresas e ON e.id = o.empresa_id
    LEFT JOIN postulaciones p ON p.oferta_id = o.id
    WHERE 1=1
"""
    params = []

    if rol == "empleador":
        _, empresa_id = _obtener_empleador(user_id)
        if not empresa_id:
            return []
        query += " AND o.empresa_id = %s"
        params.append(empresa_id)
    elif rol == "egresado":
        egresado_id = _obtener_id_egresado(user_id)
        query += " AND o.egresado_propietario_id = %s"
        params.append(egresado_id)

    if termino:
        query += " AND (o.titulo ILIKE %s OR o.descripcion ILIKE %s OR e.razon_social ILIKE %s)"
        like = f"%{termino.strip()}%"
        params.extend([like, like, like])

    if estado == "activas":
        query += " AND o.activa = TRUE"
    elif estado == "cerradas":
        query += " AND o.activa = FALSE"

    if tipo and tipo != "todos":
        query += " AND o.tipo = %s"
        params.append(tipo)

    if modalidad and modalidad != "todas":
        query += " AND o.modalidad = %s"
        params.append(modalidad)

    query += """
        GROUP BY 
            o.id, o.empresa_id, o.titulo, o.descripcion, o.requisitos, o.tipo, 
            o.modalidad, o.ubicacion, o.salario_min, o.salario_max, 
            o.fecha_publicacion, o.fecha_limite_postulacion, o.activa, 
            o.carrera_objetivo, e.razon_social, e.ruc, e.sitio_web
        ORDER BY o.fecha_publicacion DESC
    """

    with get_db_cursor() as cur:
        cur.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def _puede_gestionar_oferta(oferta_id, rol, user_id):
    if rol == "administrador":
        return True

    if rol == "empleador":
        _, empresa_id = _obtener_empleador(user_id)
        if not empresa_id:
            return False
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM ofertas WHERE id = %s AND empresa_id = %s",
                (oferta_id, empresa_id),
            )
            return bool(cur.fetchone())
    
    if rol == "egresado":
        egresado_id = _obtener_id_egresado(user_id)
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM ofertas WHERE id = %s AND egresado_propietario_id = %s",
                (oferta_id, egresado_id),
            )
            return bool(cur.fetchone())
    
    return False


def _validar_campos_oferta(titulo, descripcion, fecha_limite, salario_min, salario_max):
    if not titulo or not titulo.strip():
        return False, "El titulo es obligatorio."
    if not descripcion or not descripcion.strip():
        return False, "La descripcion es obligatoria."
    if fecha_limite < date.today():
        return False, "La fecha limite no puede ser menor a hoy."
    if salario_min and salario_max and salario_max < salario_min:
        return False, "El salario maximo no puede ser menor al salario minimo."
    return True, "OK"


def _mostrar_lista_gestion(user, rol):
    st.subheader("Panel de Ofertas")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        termino = st.text_input("Buscar oferta", placeholder="Titulo, descripcion o empresa")
    with col2:
        estado = st.selectbox("Estado", options=["todas", "activas", "cerradas"], index=0)
    with col3:
        tipo = st.selectbox("Tipo", options=["todos"] + TIPOS_OFERTA, index=0)
    with col4:
        modalidad = st.selectbox("Modalidad", options=["todas"] + MODALIDADES, index=0)

    # Eliminar el cache para asegurar que se vean los cambios inmediatamente
    ofertas = _buscar_ofertas(
        rol=rol,
        user_id=user["id"],
        termino=termino,
        estado=estado,
        tipo=tipo,
        modalidad=modalidad,
    )

    if not ofertas:
        st.info("No hay ofertas con los filtros seleccionados.")
        return

    tab_analisis, tab_gestion = st.tabs(["📊 Analisis", "🛠️ Gestion"])

    with tab_analisis:
        total = len(ofertas)
        activas = sum(1 for o in ofertas if o["activa"])
        cerradas = total - activas
        total_postulaciones = sum(int(o.get("postulaciones", 0) or 0) for o in ofertas)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total ofertas", total)
        m2.metric("Activas", activas)
        m3.metric("Cerradas", cerradas)
        m4.metric("Postulaciones", total_postulaciones)

        df = pd.DataFrame(ofertas)
        df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"]).dt.strftime("%d/%m/%Y")
        df["fecha_limite_postulacion"] = pd.to_datetime(df["fecha_limite_postulacion"]).dt.strftime("%d/%m/%Y")
        df["estado"] = df["activa"].map(lambda x: "Activa" if x else "Cerrada")

        def alerta_vencimiento(row):
            try:
                dias = (pd.to_datetime(row["fecha_limite_postulacion"], dayfirst=True) - pd.to_datetime(date.today())).days
                if row["activa"] and 0 <= dias <= 7:
                    return f"⚠️ {dias} días"
                if row["activa"] and dias < 0:
                    return "❌ Vencida"
                return ""
            except Exception:
                return ""

        df["alerta"] = df.apply(alerta_vencimiento, axis=1)

        cols = ["titulo", "empresa", "tipo", "modalidad", "fecha_publicacion", "fecha_limite_postulacion", "postulaciones", "estado", "alerta"]
        if rol == "empleador":
            cols.remove("empresa")

        page_size = 20
        total_rows = len(df)
        max_page = max(1, (total_rows + page_size - 1) // page_size)
        page = st.number_input(
            "Pagina",
            min_value=1,
            max_value=max_page,
            value=1,
            step=1,
            key="ofertas_analisis_pagina",
            help="Navega entre paginas de resultados",
        )
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df_page = df.iloc[start_idx:end_idx]

        st.dataframe(
            df_page[cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "titulo": "Titulo",
                "empresa": "Empresa",
                "tipo": "Tipo",
                "modalidad": "Modalidad",
                "fecha_publicacion": "Publicacion",
                "fecha_limite_postulacion": "Limite",
                "postulaciones": "Postulaciones",
                "estado": "Estado",
                "alerta": st.column_config.TextColumn("Alerta", help="Vacantes proximas a vencer o vencidas"),
            },
        )

        pdf_bytes = generar_pdf_ofertas_lista(ofertas, titulo="Listado de Ofertas Filtradas")
        st.download_button(
            "📄 Exportar listado filtrado (PDF)",
            data=pdf_bytes,
            file_name="Ofertas_filtradas.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with tab_gestion:
        indices = list(range(len(ofertas)))
        seleccion = st.selectbox(
            "Seleccionar oferta para gestionar",
            options=indices,
            format_func=lambda idx: _etiqueta_oferta(ofertas[idx]),
        )
        oferta = ofertas[seleccion]
        oferta_id = oferta["id"]

        st.markdown("---")
        st.markdown(f"### {oferta['titulo']}")
        st.caption(f"Empresa: {oferta['empresa']} | Publicada: {pd.to_datetime(oferta['fecha_publicacion']).strftime('%d/%m/%Y')}")

        salario_txt = "No especificado"
        if oferta.get("salario_min") and oferta.get("salario_max"):
            salario_txt = f"S/ {oferta['salario_min']} - {oferta['salario_max']}"
        elif oferta.get("salario_min"):
            salario_txt = f"Desde S/ {oferta['salario_min']}"

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"Tipo: {oferta['tipo']}")
            st.write(f"Modalidad: {oferta['modalidad']}")
            st.write(f"Ubicacion: {oferta.get('ubicacion') or 'No especificada'}")
        with c2:
            st.write(f"Salario: {salario_txt}")
            st.write(f"Limite: {pd.to_datetime(oferta['fecha_limite_postulacion']).strftime('%d/%m/%Y')}")
            st.write(f"Estado: {'Activa' if oferta['activa'] else 'Cerrada'}")
            try:
                dias = (pd.to_datetime(oferta["fecha_limite_postulacion"], dayfirst=True) - pd.to_datetime(date.today())).days
                if oferta["activa"] and dias <= 7 and dias >= 0:
                    st.warning(f"⚠️ Vacante por vencer: {dias} días restantes", icon="⚠️")
                elif oferta["activa"] and dias < 0:
                    st.error("❌ Vacante vencida", icon="❌")
            except Exception:
                pass

        st.write("Descripcion:")
        st.info(oferta.get("descripcion") or "Sin descripcion")

        empresa_data = {
            "razon_social": oferta.get("empresa"),
            "ruc": oferta.get("empresa_ruc"),
        }
        oferta_pdf_data = {
            "titulo": oferta.get("titulo"),
            "tipo": oferta.get("tipo"),
            "modalidad": oferta.get("modalidad"),
            "ubicacion": oferta.get("ubicacion") or "No especificada",
            "salario": salario_txt,
            "fecha_publicacion": pd.to_datetime(oferta.get("fecha_publicacion")).strftime("%d/%m/%Y") if oferta.get("fecha_publicacion") else "",
            "fecha_limite": pd.to_datetime(oferta.get("fecha_limite_postulacion")).strftime("%d/%m/%Y") if oferta.get("fecha_limite_postulacion") else "",
            "activa": oferta.get("activa"),
            "descripcion": oferta.get("descripcion"),
            "requisitos": oferta.get("requisitos"),
        }
        pdf_ind = generar_pdf_oferta_detalle(
            empresa_data=empresa_data,
            oferta_data=oferta_pdf_data,
            public_url=oferta.get("sitio_web"),
        )
        nombre_archivo_pdf = f"Oferta_{_slugify_filename(oferta.get('titulo'))}.pdf"
        st.download_button(
            "📄 Descargar ficha de oferta (PDF)",
            data=pdf_ind,
            file_name=nombre_archivo_pdf,
            mime="application/pdf",
            use_container_width=True,
        )

        a1, a2 = st.columns(2)
        with a1:
            if st.button("🔄 Cambiar estado Activa/Cerrada", use_container_width=True):
                _toggle_estado_oferta(oferta_id, user, rol)
        with a2:
            if st.button("👥 Ver postulaciones", use_container_width=True):
                st.session_state.selected_oferta_id = oferta_id
                st.session_state.current_page = "postulaciones_revisar"
                st.rerun()

        with st.expander("✏️ Editar oferta", expanded=False):
            with st.form(f"form_edit_{oferta_id}"):
                if rol == "egresado":
                    titulo = st.text_input("Título del emprendimiento o servicio", value=oferta.get("titulo") or "")
                    descripcion = st.text_area("Descripción detallada", value=oferta.get("descripcion") or "")
                    requisitos = st.text_area("Habilidades / Experiencia requerida (Opcional)", value=oferta.get("requisitos") or "")
                else:
                    titulo = st.text_input("Titulo", value=oferta.get("titulo") or "")
                    descripcion = st.text_area("Descripcion", value=oferta.get("descripcion") or "")
                    requisitos = st.text_area("Requisitos", value=oferta.get("requisitos") or "")

                ec1, ec2 = st.columns(2)
                with ec1:
                    if rol == "egresado":
                        tipos_grad = ["servicio", "emprendimiento", "proyecto"]
                        tipo = st.selectbox(
                            "Tipo de oferta",
                            options=tipos_grad,
                            index=tipos_grad.index(oferta.get("tipo")) if oferta.get("tipo") in tipos_grad else 0,
                        )
                    else:
                        tipo = st.selectbox(
                            "Tipo",
                            options=TIPOS_OFERTA,
                            index=TIPOS_OFERTA.index(oferta.get("tipo")) if oferta.get("tipo") in TIPOS_OFERTA else 0,
                        )
                    modalidad = st.selectbox(
                        "Modalidad",
                        options=MODALIDADES,
                        index=MODALIDADES.index(oferta.get("modalidad")) if oferta.get("modalidad") in MODALIDADES else 0,
                    )
                    ubicacion = st.text_input("Ubicacion", value=oferta.get("ubicacion") or "")

                with ec2:
                    if rol == "egresado":
                        salario_min = st.number_input("Precio/Salario base (S/)", min_value=0, value=int(oferta.get("salario_min") or 0), step=100)
                        salario_max = st.number_input("Precio/Salario máximo (S/)", min_value=0, value=int(oferta.get("salario_max") or 0), step=100)
                    else:
                        salario_min = st.number_input("Salario minimo", min_value=0, value=int(oferta.get("salario_min") or 0), step=100)
                        salario_max = st.number_input("Salario maximo", min_value=0, value=int(oferta.get("salario_max") or 0), step=100)
                    fecha_limite = st.date_input(
                        "Válido hasta",
                        value=pd.to_datetime(oferta.get("fecha_limite_postulacion")).date() if oferta.get("fecha_limite_postulacion") else date.today(),
                        min_value=date.today(),
                    )

                carreras_actuales = oferta.get("carrera_objetivo") or []
                if not isinstance(carreras_actuales, list):
                    carreras_actuales = []
                carreras = st.multiselect("Carreras relacionadas", options=CARRERAS_BASE, default=[c for c in carreras_actuales if c in CARRERAS_BASE])

                guardar = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
                if guardar:
                    success_edit = False
                    try:
                        ok, msg = _actualizar_oferta(
                            oferta_id=oferta_id,
                            user=user,
                            rol=rol,
                            titulo=titulo,
                            descripcion=descripcion,
                            requisitos=requisitos,
                            tipo=tipo,
                            modalidad=modalidad,
                            ubicacion=ubicacion,
                            salario_min=salario_min,
                            salario_max=salario_max,
                            fecha_limite=fecha_limite,
                            carreras=carreras,
                        )
                        if ok:
                            add_notification(msg, "success")
                            success_edit = True
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error(f"Error: {e}")
                    
                    if success_edit:
                        st.rerun()


def _toggle_estado_oferta(oferta_id, user, rol):
    if not _puede_gestionar_oferta(oferta_id, rol, user["id"]):
        st.error("No tienes permisos para gestionar esta oferta.")
        return

    success = False
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE ofertas SET activa = NOT activa WHERE id = %s", (oferta_id,))
        add_notification("Estado de la oferta actualizado.", "success")
        success = True
    except Exception as exc:
        st.error(f"Error al actualizar estado: {exc}")
    
    if success:
        st.rerun()


def _mostrar_formulario_crear(user, rol):
    st.subheader("Publicar Nueva Oferta")

    empresa_id = None
    egresado_id = None

    if rol == "empleador":
        _, empresa_id = _obtener_empleador(user["id"])
        if not empresa_id:
            st.error("No tienes una empresa asociada.")
            return
    elif rol == "egresado":
        egresado_id = _obtener_id_egresado(user["id"])
        if not egresado_id:
            st.error("No se encontró tu perfil de egresado.")
            return
    else: # administrador
        empresas = _obtener_empresas_activas()
        if not empresas:
            st.warning("No hay empresas activas para publicar ofertas.")
            return
        empresa_id = st.selectbox(
            "Empresa",
            options=[e["id"] for e in empresas],
            format_func=lambda eid: next(e["razon_social"] for e in empresas if e["id"] == eid),
        )

    with st.form("form_nueva_oferta"):
        if rol == "egresado":
            st.info("💡 Como egresado, puedes publicar tus emprendimientos, servicios o disponibilidad para proyectos.")
            titulo = st.text_input("Título del emprendimiento o servicio (Ej: Consultoría en Sistemas)")
            descripcion = st.text_area("Descripción detallada de lo que ofreces")
            requisitos = st.text_area("Habilidades / Experiencia requerida (Opcional)")
        else:
            titulo = st.text_input("Título de la posición")
            descripcion = st.text_area("Descripción del puesto")
            requisitos = st.text_area("Requisitos")

        c1, c2 = st.columns(2)
        with c1:
            if rol == "egresado":
                tipos_grad = ["servicio", "emprendimiento", "proyecto"]
                tipo = st.selectbox("Tipo de oferta", options=tipos_grad)
            else:
                tipo = st.selectbox("Tipo", options=TIPOS_OFERTA)
            modalidad = st.selectbox("Modalidad", options=MODALIDADES)
            ubicacion = st.text_input("Ubicación")
        with c2:
            if rol == "egresado":
                salario_min = st.number_input("Precio/Salario base (S/)", min_value=0, value=0, step=100)
                salario_max = st.number_input("Precio/Salario máximo (S/)", min_value=0, value=0, step=100)
            else:
                salario_min = st.number_input("Salario mínimo (S/)", min_value=0, value=0, step=100)
                salario_max = st.number_input("Salario máximo (S/)", min_value=0, value=0, step=100)
            fecha_limite = st.date_input("Válido hasta", value=date.today())

        carreras = st.multiselect("Carreras relacionadas", options=CARRERAS_BASE)

        submitted = st.form_submit_button("Publicar oferta", type="primary", use_container_width=True)
        if submitted:
            success_crear = False
            try:
                ok, msg = _crear_oferta(
                    empresa_id=empresa_id,
                    publicado_por=user["id"],
                    egresado_id=egresado_id,
                    titulo=titulo,
                    descripcion=descripcion,
                    requisitos=requisitos,
                    tipo=tipo,
                    modalidad=modalidad,
                    ubicacion=ubicacion,
                    salario_min=salario_min,
                    salario_max=salario_max,
                    fecha_limite=fecha_limite,
                    carreras=carreras,
                )
                if ok:
                    add_notification(msg, "success")
                    success_crear = True
                else:
                    st.error(msg)
            except Exception as e:
                st.error(f"Error: {e}")
            
            if success_crear:
                st.rerun()


def _crear_oferta(
    empresa_id,
    publicado_por,
    egresado_id,
    titulo,
    descripcion,
    requisitos,
    tipo,
    modalidad,
    ubicacion,
    salario_min,
    salario_max,
    fecha_limite,
    carreras,
):
    ok, msg = _validar_campos_oferta(titulo, descripcion, fecha_limite, salario_min, salario_max)
    if not ok:
        return False, msg

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO ofertas (
                    empresa_id,
                    publicado_por,
                    egresado_propietario_id,
                    titulo,
                    descripcion,
                    requisitos,
                    tipo,
                    modalidad,
                    ubicacion,
                    salario_min,
                    salario_max,
                    fecha_limite_postulacion,
                    carrera_objetivo,
                    activa
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (
                    empresa_id,
                    publicado_por,
                    egresado_id,
                    titulo.strip(),
                    descripcion.strip(),
                    (requisitos or "").strip() or None,
                    tipo,
                    modalidad,
                    (ubicacion or "").strip() or None,
                    salario_min or None,
                    salario_max or None,
                    fecha_limite,
                    carreras or None,
                ),
            )
        return True, "Oferta publicada exitosamente."
    except Exception as exc:
        return False, f"Error al crear oferta: {exc}"


def _actualizar_oferta(
    oferta_id,
    user,
    rol,
    titulo,
    descripcion,
    requisitos,
    tipo,
    modalidad,
    ubicacion,
    salario_min,
    salario_max,
    fecha_limite,
    carreras,
):
    if not _puede_gestionar_oferta(oferta_id, rol, user["id"]):
        return False, "No autorizado para editar esta oferta."

    ok, msg = _validar_campos_oferta(titulo, descripcion, fecha_limite, salario_min, salario_max)
    if not ok:
        return False, msg

    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE ofertas
                SET titulo = %s,
                    descripcion = %s,
                    requisitos = %s,
                    tipo = %s,
                    modalidad = %s,
                    ubicacion = %s,
                    salario_min = %s,
                    salario_max = %s,
                    fecha_limite_postulacion = %s,
                    carrera_objetivo = %s
                WHERE id = %s
                """,
                (
                    titulo.strip(),
                    descripcion.strip(),
                    (requisitos or "").strip() or None,
                    tipo,
                    modalidad,
                    (ubicacion or "").strip() or None,
                    salario_min or None,
                    salario_max or None,
                    fecha_limite,
                    carreras or None,
                    oferta_id,
                ),
            )
        return True, "Oferta actualizada correctamente."
    except Exception as exc:
        return False, f"Error al actualizar oferta: {exc}"
