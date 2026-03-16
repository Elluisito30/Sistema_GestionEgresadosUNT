"""
Modulo de seguimiento de postulaciones para egresados.
Incluye filtros, KPIs y exportacion PDF individual y grupal.
"""

import pandas as pd
import streamlit as st
from datetime import date
import re

from src.utils.database import get_db_cursor
from src.utils.pdf_generator import generar_pdf_postulaciones_lista, generar_pdf_postulacion
from src.utils.session import render_notifications

ESTADO_MAP = {
    "recibido": "📩 Recibido",
    "en_revision": "🔍 En revision",
    "entrevista": "📅 Entrevista",
    "seleccionado": "✅ Seleccionado",
    "descartado": "❌ Descartado",
}


def _slugify_filename(texto):
    base = (texto or "postulacion").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "postulacion"


def show():
    st.title("📋 Seguimiento de Mis Postulaciones")
    render_notifications()

    user = st.session_state.user
    if user.get("rol") != "egresado":
        st.error("Solo egresados pueden acceder a esta pagina.")
        return

    usuario_id = user["id"]

    estado_filtro = st.selectbox(
        "Filtrar por estado",
        options=["todos", "recibido", "en_revision", "entrevista", "seleccionado", "descartado"],
        index=0,
    )

    c1, c2 = st.columns(2)
    with c1:
        fecha_desde = st.date_input("Desde", value=None, key="seg_post_desde")
    with c2:
        fecha_hasta = st.date_input("Hasta", value=None, key="seg_post_hasta")

    @st.cache_data(show_spinner=False, ttl=300)
    def cached_postulaciones(usuario_id, estado_filtro, fecha_desde, fecha_hasta):
        query = """
            SELECT
                p.id,
                o.titulo as oferta,
                e.razon_social as empresa,
                eg.nombres || ' ' || eg.apellido_paterno as egresado,
                eg.carrera_principal,
                eg.facultad,
                p.fecha_postulacion,
                p.estado,
                p.comentario_revision
            FROM postulaciones p
            JOIN ofertas o ON p.oferta_id = o.id
            JOIN empresas e ON o.empresa_id = e.id
            JOIN egresados eg ON p.egresado_id = eg.id
            WHERE p.egresado_id = (SELECT id FROM egresados WHERE usuario_id = %s)
        """
        params = [usuario_id]
        if estado_filtro != "todos":
            query += " AND p.estado = %s"
            params.append(estado_filtro)
        if isinstance(fecha_desde, date):
            query += " AND p.fecha_postulacion::date >= %s"
            params.append(fecha_desde)
        if isinstance(fecha_hasta, date):
            query += " AND p.fecha_postulacion::date <= %s"
            params.append(fecha_hasta)
        query += " ORDER BY p.fecha_postulacion DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    postulaciones = cached_postulaciones(usuario_id, estado_filtro, fecha_desde, fecha_hasta)

    if not postulaciones:
        st.info("No se encontraron postulaciones con los filtros aplicados.")
        if st.button("Buscar Ofertas"):
            st.session_state.current_page = "ofertas_buscar"
            st.rerun()
        return

    total = len(postulaciones)
    en_proceso = sum(1 for p in postulaciones if p["estado"] in ["recibido", "en_revision", "entrevista"])
    finalizadas = total - en_proceso

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Postulaciones", total)
    m2.metric("En Proceso", en_proceso)
    m3.metric("Finalizadas", finalizadas)

    st.markdown("---")

    df = pd.DataFrame(postulaciones)
    df["fecha_postulacion"] = pd.to_datetime(df["fecha_postulacion"]).dt.strftime("%d/%m/%Y %H:%M")
    df["estado_label"] = df["estado"].map(lambda x: ESTADO_MAP.get(x, x))

    # Paginación
    page_size = 20
    total_rows = len(df)
    max_page = max(1, (total_rows + page_size - 1) // page_size)
    page = st.number_input("Página", min_value=1, max_value=max_page, value=1, step=1, help="Navega entre páginas de resultados")
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_page = df.iloc[start_idx:end_idx]

    st.dataframe(
        df_page[["fecha_postulacion", "oferta", "empresa", "estado_label"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "fecha_postulacion": "Fecha",
            "oferta": "Oferta",
            "empresa": "Empresa",
            "estado_label": "Estado",
        },
    )

    pdf_lista = generar_pdf_postulaciones_lista(postulaciones)
    st.download_button(
        "📄 Descargar listado filtrado (PDF)",
        data=pdf_lista,
        file_name="Mis_postulaciones.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.subheader("Detalle individual")
    opciones = {
        f"{p['oferta']} - {p['empresa']} ({pd.to_datetime(p['fecha_postulacion']).strftime('%d/%m/%Y %H:%M')})": p
        for p in postulaciones
    }
    seleccion = st.selectbox("Seleccionar postulación", options=list(opciones.keys()))
    post = opciones[seleccion]

    with st.container(border=True):
        st.write(f"Estado actual: {ESTADO_MAP.get(post['estado'], post['estado'])}")
        if post.get("comentario_revision"):
            st.info(f"Comentario del empleador:\n\n{post['comentario_revision']}")
        else:
            st.caption("Aun no hay comentarios del empleador.")

        pdf_ind = generar_pdf_postulacion(
            {
                "oferta": post.get("oferta"),
                "empresa": post.get("empresa"),
                "nombre_egresado": post.get("egresado"),
                "carrera": post.get("carrera_principal"),
                "facultad": post.get("facultad"),
                "fecha_postulacion": post.get("fecha_postulacion"),
                "estado": post.get("estado"),
                "comentario": post.get("comentario_revision"),
            }
        )
        nombre_pdf = f"Postulacion_{_slugify_filename(post.get('oferta'))}.pdf"
        st.download_button(
            "📄 Descargar esta postulación (PDF)",
            data=pdf_ind,
            file_name=nombre_pdf,
            mime="application/pdf",
            use_container_width=True,
        )
