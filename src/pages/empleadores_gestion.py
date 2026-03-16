"""
Gestión de empleadores (usuarios por empresa) con exportación a PDF.
Visible para administradores y administradores de empresa.
"""
import streamlit as st
import pandas as pd
import base64

from src.utils.database import get_db_cursor
from src.utils.session import add_notification
from src.models.empleador import Empleador
from src.models.empresa import Empresa
from src.models.user import User
from src.utils.pdf_generator import generar_pdf_empleadores_empresa


def _obtener_empleadores_empresa(empresa_id: int):
    with get_db_cursor() as cur:
        cur.execute(
            """
            SELECT
                em.nombres,
                em.apellidos,
                em.cargo,
                u.email,
                u.fecha_registro,
                em.es_administrador_empresa
            FROM empleadores em
            JOIN usuarios u ON em.usuario_id = u.id
            WHERE em.empresa_id = %s
            ORDER BY em.es_administrador_empresa DESC, em.apellidos ASC
            """,
            (empresa_id,),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def show():
    st.title("👥 Gestión de Empleadores")

    user = st.session_state.user
    rol = user.get("rol")

    if rol not in ["administrador", "empleador"]:
        st.error("No tienes permisos para acceder a esta página.")
        return

    # Resolver empresa según rol
    empresa = None
    if rol == "administrador":
        with get_db_cursor() as cur:
            cur.execute("SELECT id, razon_social FROM empresas ORDER BY razon_social ASC")
            empresas = cur.fetchall()
        if not empresas:
            st.info("No hay empresas registradas.")
            return
        empresa_id = st.selectbox(
            "🏢 Seleccionar empresa",
            options=[e[0] for e in empresas],
            format_func=lambda x: next(e[1] for e in empresas if e[0] == x),
        )
        empresa = Empresa.get_by_id(empresa_id)
    else:
        empleador = Empleador.get_by_usuario_id(user["id"])
        if not empleador:
            st.error("No se encontró un perfil de empleador asociado.")
            return
        if not empleador.es_administrador_empresa:
            st.warning("🔒 Solo el administrador de la empresa puede ver este módulo.")
            return
        empresa = Empresa.get_by_id(empleador.empresa_id)

    if not empresa:
        st.error("Empresa no encontrada.")
        return

    # Caché de sesión para PDFs
    if "pdf_cache" not in st.session_state:
        st.session_state.pdf_cache = {}

    st.subheader(f"🏢 {empresa.razon_social}")
    empleadores = _obtener_empleadores_empresa(empresa.id)

    if not empleadores:
        st.info("No hay empleadores asociados a esta empresa.")
        return

    tab1, tab2, tab3 = st.tabs(["📋 Listado", "✏️ Editar", "➕ Vincular empleador"])

    # TAB 1: Tabla
    with tab1:
        st.subheader("📋 Empleadores registrados")
    df = pd.DataFrame(empleadores)
    df["nombre"] = df["nombres"].fillna("") + " " + df["apellidos"].fillna("")
    df["admin"] = df["es_administrador_empresa"].map(lambda x: "✅ Sí" if x else "—")
    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"]).dt.strftime("%d/%m/%Y")

        st.dataframe(
            df[["nombre", "cargo", "email", "fecha_registro", "admin"]],
            column_config={
                "nombre": "Nombre",
                "cargo": "Cargo",
                "email": "Email",
                "fecha_registro": "Registro",
                "admin": "Admin",
            },
            use_container_width=True,
            hide_index=True,
        )

        # Reporte PDF
        st.markdown("---")
        st.subheader("📄 Reportes")

        rep_key = f"empleadores:{empresa.id}"
        if st.button("📋 Reporte de Empleadores", use_container_width=True):
            pdf = generar_pdf_empleadores_empresa(
                empresa_data={"razon_social": empresa.razon_social, "ruc": empresa.ruc},
                empleadores=[
                    {
                        "nombre": (e.get("nombres", "") + " " + e.get("apellidos", "")).strip(),
                        "cargo": e.get("cargo"),
                        "email": e.get("email"),
                        "fecha_registro": e.get("fecha_registro"),
                        "es_administrador_empresa": e.get("es_administrador_empresa"),
                    }
                    for e in empleadores
                ],
            )
            st.session_state.pdf_cache[rep_key] = pdf
            add_notification("Reporte generado correctamente.", "success")
            st.rerun()

        rep_pdf = st.session_state.pdf_cache.get(rep_key)
        if rep_pdf:
            with st.expander("👁️ Vista previa (Reporte de Empleadores)", expanded=False):
                b64 = base64.b64encode(rep_pdf).decode("utf-8")
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
                label="📥 Descargar PDF",
                data=rep_pdf,
                file_name=f"Empleadores_{empresa.razon_social}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    # TAB 2: Editar empleador
    with tab2:
        st.subheader("✏️ Editar empleador")
        opciones = [
            f"{(e.get('nombres','') + ' ' + e.get('apellidos','')).strip()} — {e.get('email')}"
            for e in empleadores
        ]
        selected = st.selectbox("Seleccionar", options=opciones)
        idx = opciones.index(selected)
        sel = empleadores[idx]

        with st.form("form_editar_empleador"):
            cargo = st.text_input("Cargo", value=sel.get("cargo") or "")
            es_admin = st.checkbox("Administrador de empresa", value=bool(sel.get("es_administrador_empresa")))
            submitted = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

            if submitted:
                # Buscar el registro empleador por email -> usuario_id -> empleadores
                u = User.get_by_email(sel.get("email"))
                if not u:
                    st.error("No se encontró el usuario asociado.")
                    return
                em = Empleador.get_by_usuario_id(u.id)
                if not em:
                    st.error("No se encontró el perfil de empleador asociado.")
                    return
                em.cargo = cargo
                em.es_administrador_empresa = es_admin
                ok, msg = em.save()
                if ok:
                    add_notification("Empleador actualizado correctamente.", "success")
                    st.rerun()
                else:
                    st.error(msg)

    # TAB 3: Vincular empleador existente
    with tab3:
        st.subheader("➕ Vincular empleador (usuario existente)")
        st.caption("Por seguridad, este flujo vincula un usuario ya existente por email.")

        with st.form("form_vincular_empleador"):
            email = st.text_input("Email del usuario *", placeholder="usuario@dominio.com")
            nombres = st.text_input("Nombres *")
            apellidos = st.text_input("Apellidos *")
            cargo = st.text_input("Cargo")
            es_admin = st.checkbox("Administrador de empresa", value=False)
            submitted = st.form_submit_button("➕ Vincular", use_container_width=True)

            if submitted:
                if not email or not nombres or not apellidos:
                    st.error("Email, nombres y apellidos son obligatorios.")
                    return
                u = User.get_by_email(email.strip())
                if not u:
                    st.error("No existe un usuario con ese email. Debe registrarse primero.")
                    return
                # Evitar duplicados
                existing = Empleador.get_by_usuario_id(u.id)
                if existing and existing.empresa_id == empresa.id:
                    st.warning("Este usuario ya está vinculado como empleador a la empresa.")
                    return
                if existing and existing.empresa_id != empresa.id:
                    st.warning("Este usuario ya está vinculado a otra empresa. Revise antes de continuar.")
                    return

                nuevo = Empleador(
                    usuario_id=u.id,
                    empresa_id=empresa.id,
                    nombres=nombres,
                    apellidos=apellidos,
                    cargo=cargo,
                    es_administrador_empresa=es_admin,
                )
                ok, msg = nuevo.save()
                if ok:
                    add_notification("Empleador vinculado correctamente.", "success")
                    st.rerun()
                else:
                    st.error(msg)

