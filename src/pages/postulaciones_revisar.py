"""
Módulo de revisión de postulaciones para empleadores.
Permite filtrar, revisar y actualizar el estado de las postulaciones
recibidas a las ofertas de la empresa, con opción de exportar un PDF
por cada postulación.
"""
import streamlit as st
import pandas as pd
from datetime import date
import re

from src.utils.database import get_db_cursor
from src.utils.session import add_notification, render_notifications
from src.models.postulacion import Postulacion
from src.utils.pdf_generator import generar_pdf_postulaciones_lista


ESTADOS_VALIDOS = [
    ("recibido", "📩 Recibido"),
    ("en_revision", "🔍 En revisión"),
    ("entrevista", "📅 Entrevista"),
    ("seleccionado", "✅ Seleccionado"),
    ("descartado", "❌ Descartado"),
]


def _slugify_filename(texto):
    base = (texto or "postulacion").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "postulacion"


def _obtener_empresa_id_empleador(usuario_id: int):
    """Obtiene el ID de la empresa asociada a un empleador."""
    with get_db_cursor() as cur:
        cur.execute(
            "SELECT empresa_id FROM empleadores WHERE usuario_id = %s",
            (usuario_id,),
        )
        res = cur.fetchone()
        return res[0] if res else None


def _obtener_ofertas_empresa(empresa_id: int):
    """Obtiene las ofertas de la empresa (id, titulo)."""
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT id, titulo
            FROM ofertas
            WHERE empresa_id = %s
            ORDER BY fecha_publicacion DESC
            """,
            (empresa_id,),
        )
        return cur.fetchall()


def _buscar_postulaciones(empresa_id: int, oferta_id=None, estado=None, fecha_desde=None, fecha_hasta=None):
    """Busca postulaciones aplicando los filtros seleccionados."""
    query = """
        SELECT
            p.id,
            o.titulo AS oferta,
            e.razon_social AS empresa,
            eg.nombres || ' ' || eg.apellido_paterno AS egresado,
            p.fecha_postulacion,
            p.estado,
            p.comentario_revision
        FROM postulaciones p
        JOIN ofertas o ON p.oferta_id = o.id
        JOIN empresas e ON o.empresa_id = e.id
        JOIN egresados eg ON p.egresado_id = eg.id
        WHERE o.empresa_id = %s
    """
    params = [empresa_id]

    if oferta_id:
        query += " AND o.id = %s"
        params.append(oferta_id)

    if estado and estado != "todos":
        query += " AND p.estado = %s"
        params.append(estado)

    if fecha_desde:
        query += " AND p.fecha_postulacion::date >= %s"
        params.append(fecha_desde)

    if fecha_hasta:
        query += " AND p.fecha_postulacion::date <= %s"
        params.append(fecha_hasta)

    query += " ORDER BY p.fecha_postulacion DESC"

    with get_db_cursor() as cur:
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def show():
    """Muestra la página de revisión de postulaciones para empleadores."""
    user = st.session_state.user
    rol = user["rol"]

    st.title("👥 Revisar Postulaciones")
    render_notifications()

    if rol != "empleador":
        st.error("Solo los empleadores pueden acceder a esta página.")
        return

    empresa_id = _obtener_empresa_id_empleador(user["id"])
    if not empresa_id:
        st.warning("No se encontró una empresa asociada a tu usuario.")
        return

    # Estado interno para acciones
    if "post_rev_modo" not in st.session_state:
        st.session_state.post_rev_modo = "ver"
    if "post_rev_id" not in st.session_state:
        st.session_state.post_rev_id = None

    # --- Filtros superiores ---
    with st.container():
        st.subheader("🔍 Filtros de búsqueda")

        ofertas = _obtener_ofertas_empresa(empresa_id)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

        with col1:
            opciones_ofertas = [None] + [o[0] for o in ofertas]
            seleccion_oferta = st.selectbox(
                "Oferta",
                options=opciones_ofertas,
                format_func=lambda oid: "Todas mis ofertas" if oid is None else next((o[1] for o in ofertas if o[0] == oid), "Oferta"),
            )

        with col2:
            estados_labels = ["Todos los estados"] + [etq for _, etq in ESTADOS_VALIDOS]
            seleccion_estado = st.selectbox("Estado de postulación", options=estados_labels)

        with col3:
            fecha_desde = st.date_input("Desde", value=None, key="post_rev_desde")

        with col4:
            fecha_hasta = st.date_input("Hasta", value=None, key="post_rev_hasta")

    # Resolver filtros seleccionados
    oferta_id = seleccion_oferta if seleccion_oferta is not None else None

    estado_valor = None
    if seleccion_estado != "Todos los estados":
        for val, etq in ESTADOS_VALIDOS:
            if etq == seleccion_estado:
                estado_valor = val
                break

    postulaciones = _buscar_postulaciones(
        empresa_id=empresa_id,
        oferta_id=oferta_id,
        estado=estado_valor or "todos",
        fecha_desde=fecha_desde if isinstance(fecha_desde, date) else None,
        fecha_hasta=fecha_hasta if isinstance(fecha_hasta, date) else None,
    )

    if not postulaciones:
        st.info("No se encontraron postulaciones con los filtros aplicados.")
        return

    # --- Métricas rápidas ---
    col_a, col_b, col_c, col_d = st.columns(4)
    total = len(postulaciones)
    en_revision = sum(1 for p in postulaciones if p["estado"] in ["recibido", "en_revision"])
    entrevistas = sum(1 for p in postulaciones if p["estado"] == "entrevista")
    seleccionados = sum(1 for p in postulaciones if p["estado"] == "seleccionado")

    col_a.metric("Total postulaciones", total)
    col_b.metric("En proceso", en_revision)
    col_c.metric("Entrevistas", entrevistas)
    col_d.metric("Seleccionados", seleccionados)

    st.markdown("---")

    # --- Contenido principal en pestañas ---
    tab_lista, tab_acciones = st.tabs(["📋 Listar postulaciones", "🛠️ Panel de acciones"])

    # TAB 1: Listado + exportación
    with tab_lista:
        st.subheader("📋 Lista de postulaciones")
        df = pd.DataFrame(postulaciones)
        df["fecha_postulacion"] = pd.to_datetime(df["fecha_postulacion"]).dt.strftime(
            "%d/%m/%Y %H:%M"
        )

        estado_map = dict(ESTADOS_VALIDOS)
        df["Estado"] = df["estado"].map(lambda x: estado_map.get(x, x))

        st.dataframe(
            df[["fecha_postulacion", "oferta", "egresado", "Estado"]],
            use_container_width=True,
            hide_index=True,
        )

        # Botón para descargar PDF de todas las postulaciones listadas
        pdf_lista = generar_pdf_postulaciones_lista(postulaciones)
        st.download_button(
            label="📄 Descargar PDF de todas las postulaciones listadas",
            data=pdf_lista,
            file_name="Postulaciones_listado.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # TAB 2: Panel de acciones
    with tab_acciones:
        st.subheader("🛠️ Panel de acciones sobre una postulación")

        opciones_post = {
            f"{p['egresado']} - {p['oferta']} ({p['fecha_postulacion']})": p["id"]
            for p in postulaciones
        }

        seleccion_claves = st.multiselect(
            "Selecciona una o varias postulaciones:",
            options=list(opciones_post.keys()),
        )
        ids_seleccionados = [opciones_post[k] for k in seleccion_claves]

        col_acc1, col_acc2, col_acc3 = st.columns(3)
        with col_acc1:
            if len(ids_seleccionados) == 1 and st.button("👁️ Ver detalle"):
                st.session_state.post_rev_id = ids_seleccionados[0]
                st.session_state.post_rev_modo = "ver"
                st.rerun()
        with col_acc2:
            if len(ids_seleccionados) == 1 and st.button("✏️ Editar / Cambiar estado"):
                st.session_state.post_rev_id = ids_seleccionados[0]
                st.session_state.post_rev_modo = "editar"
                st.rerun()
        with col_acc3:
            if len(ids_seleccionados) > 1:
                nuevo_estado = st.selectbox("Estado masivo:", [val for val, _ in ESTADOS_VALIDOS])
                if st.button("🔄 Cambiar estado en lote"):
                    _cambiar_estado_lote(ids_seleccionados, nuevo_estado)
                    add_notification(f"Se actualizaron {len(ids_seleccionados)} postulaciones a '{nuevo_estado}'.", "success")
                    st.rerun()

        # Renderizar detalle si hay una selección activa
        if st.session_state.post_rev_id:
            _render_detalle_postulacion(st.session_state.post_rev_id, modo=st.session_state.post_rev_modo)


def _cambiar_estado_lote(ids, nuevo_estado):
    if not ids:
        return
    with get_db_cursor(commit=True) as cur:
        cur.executemany(
            "UPDATE postulaciones SET estado = %s, fecha_estado_actual = NOW() WHERE id = %s",
            [(nuevo_estado, pid) for pid in ids],
        )


def _render_detalle_postulacion(postulacion_id: int, modo: str = "ver"):
    """Muestra el detalle de una postulación específica.

    modo:
        - 'ver': solo lectura + descarga PDF
        - 'editar': permite cambiar estado y comentario
    """
    from src.utils.pdf_generator import generar_pdf_postulacion  # import local para evitar ciclos

    # Recuperar datos completos desde el modelo y la BD
    postulacion_obj = Postulacion.get_by_id(postulacion_id)
    if not postulacion_obj:
        st.error("No se encontró la postulación seleccionada.")
        return

    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                p.id,
                o.titulo AS oferta,
                e.razon_social AS empresa,
                eg.nombres,
                eg.apellido_paterno,
                eg.apellido_materno,
                eg.carrera_principal,
                eg.facultad,
                eg.url_cv,
                p.fecha_postulacion,
                p.estado,
                p.comentario_revision
            FROM postulaciones p
            JOIN ofertas o ON p.oferta_id = o.id
            JOIN empresas e ON o.empresa_id = e.id
            JOIN egresados eg ON p.egresado_id = eg.id
            WHERE p.id = %s
            """,
            (postulacion_id,),
        )
        row = cur.fetchone()

    if not row:
        st.error("No se pudo cargar la información detallada de la postulación.")
        return

    (
        _pid,
        titulo_oferta,
        empresa,
        nombres,
        ape_pat,
        ape_mat,
        carrera,
        facultad,
        url_cv,
        fecha_post,
        estado_actual,
        comentario_actual,
    ) = row

    nombre_completo = f"{nombres} {ape_pat} {ape_mat or ''}".strip()

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 👤 {nombre_completo}")
            st.caption(f"💼 {titulo_oferta} | 🏢 {empresa}")
            st.write(f"🎓 {carrera} - {facultad}")
            st.write(f"📅 Postulado el: {fecha_post.strftime('%d/%m/%Y %H:%M')}")

        with col2:
            estado_map = dict(ESTADOS_VALIDOS)
            etiqueta_estado = estado_map.get(estado_actual, estado_actual)
            st.markdown("**Estado actual:**")
            st.write(etiqueta_estado)
            if url_cv:
                st.markdown(f"[📄 Ver CV]({url_cv})")

        st.markdown("---")

        # Comentarios y cambio de estado (solo en modo edición)
        if modo == "editar":
            st.markdown("#### ✏️ Actualizar estado y comentarios")
            nuevo_estado_label = st.selectbox(
                "Nuevo estado",
                options=[etq for _, etq in ESTADOS_VALIDOS],
                index=[i for i, (v, _) in enumerate(ESTADOS_VALIDOS) if v == estado_actual][0]
                if estado_actual in dict(ESTADOS_VALIDOS)
                else 0,
            )
            comentario = st.text_area(
                "Comentario para el egresado (opcional)",
                value=comentario_actual or "",
                help="Este comentario quedará registrado junto a la postulación.",
            )

            submitted = st.button("💾 Guardar cambios", use_container_width=True)
        else:
            nuevo_estado_label = None
            comentario = None
            submitted = False

        # Botón de descarga de PDF (fuera del form por restricción de Streamlit)
        pdf_bytes = generar_pdf_postulacion(
            {
                "oferta": titulo_oferta,
                "empresa": empresa,
                "nombre_egresado": nombre_completo,
                "carrera": carrera,
                "facultad": facultad,
                "fecha_postulacion": fecha_post,
                "estado": estado_actual,
                "comentario": comentario_actual,
            }
        )
        st.download_button(
            label="📄 Descargar PDF de esta postulación",
            data=pdf_bytes,
            file_name=f"Postulacion_{_slugify_filename(titulo_oferta)}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        if submitted and modo == "editar":
            # Traducir label a valor interno
            nuevo_estado_val = None
            for val, etq in ESTADOS_VALIDOS:
                if etq == nuevo_estado_label:
                    nuevo_estado_val = val
                    break

            if not nuevo_estado_val:
                st.error("Estado seleccionado no válido.")
                return

            empresa_id = _obtener_empresa_id_empleador(st.session_state.user["id"])
            ok, msg = postulacion_obj.cambiar_estado(
                nuevo_estado_val,
                comentario=comentario.strip() or None,
                empresa_id=empresa_id,
            )
            if ok:
                add_notification(msg, "success")
                # Limpiar selección y refrescar tabla
                st.session_state.post_rev_id = None
                st.session_state.post_rev_modo = "ver"
                st.rerun()
            else:
                st.error(msg)

