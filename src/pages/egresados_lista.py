import streamlit as st
import pandas as pd
import bcrypt
from src.utils.database import get_db_cursor
from src.utils.pdf_generator import generar_pdf_reporte_generico
from src.utils.session import get_session_id, is_admin

def show():
    """Muestra la lista de egresados para los administradores."""
    st.title("👥 Gestión de Egresados")

    # Pestañas para "Ver", "Registrar" y "Editar"
    tab_ver, tab_registrar, tab_editar = st.tabs(["Ver Egresados", "➕ Registrar Nuevo Egresado", "✏️ Editar Egresado"])

    with tab_ver:
        render_lista_egresados()

    with tab_registrar:
        render_crear_egresado_form()

    with tab_editar:
        render_editar_egresado_form()

def render_crear_egresado_form():
    """Renderiza el formulario para crear un nuevo egresado."""
    with st.form("crear_egresado_form", clear_on_submit=True):
        st.subheader("Datos de la Cuenta")
        email = st.text_input("Correo Electrónico del Egresado", key="email_create")
        password = st.text_input("Contraseña Provisional", type="password", key="password_create")
        confirm_password = st.text_input("Confirmar Contraseña Provisional", type="password", key="confirm_password_create")

        st.subheader("Información Personal")
        nombres = st.text_input("Nombres", key="nombres_create")
        apellido_paterno = st.text_input("Apellido Paterno", key="apellido_paterno_create")
        apellido_materno = st.text_input("Apellido Materno", key="apellido_materno_create")
        dni = st.text_input("DNI (8 dígitos)", max_chars=8, key="dni_create")
        
        st.subheader("Información Académica")
        carrera_principal = st.text_input("Carrera Principal", key="carrera_create")
        facultad = st.text_input("Facultad", key="facultad_create")
        anio_egreso = st.number_input("Año de Egreso", min_value=1950, max_value=2026, step=1, key="anio_egreso_create")

        submitted = st.form_submit_button("Crear Egresado", use_container_width=True)

        if submitted:
            if not all([email, password, confirm_password, nombres, apellido_paterno, dni, carrera_principal, facultad, anio_egreso]):
                st.error("Todos los campos son obligatorios.")
                return

            if password != confirm_password:
                st.error("Las contraseñas no coinciden.")
                return

            if len(dni) != 8 or not dni.isdigit():
                st.error("El DNI debe contener 8 dígitos numéricos.")
                return

            try:
                with get_db_cursor(commit=True) as cur:
                    cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                    if cur.fetchone():
                        st.error(f"El correo electrónico '{email}' ya está registrado.")
                        return

                    cur.execute("SELECT id FROM egresados WHERE dni = %s", (dni,))
                    if cur.fetchone():
                        st.error(f"El DNI '{dni}' ya está registrado.")
                        return

                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    admin_id = get_session_id()

                    cur.execute(
                        "INSERT INTO usuarios (email, password_hash, rol, email_confirmado, activo) VALUES (%s, %s, 'egresado', TRUE, TRUE) RETURNING id",
                        (email, hashed_password)
                    )
                    usuario_id = cur.fetchone()[0]

                    cur.execute(
                        """INSERT INTO egresados (usuario_id, nombres, apellido_paterno, apellido_materno, dni, carrera_principal, facultad, anio_egreso, creado_por)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (usuario_id, nombres, apellido_paterno, apellido_materno, dni, carrera_principal, facultad, anio_egreso, admin_id)
                    )
                    
                    st.success(f"¡Egresado '{nombres} {apellido_paterno}' creado con éxito!")
                    st.balloons()

            except Exception as e:
                st.error(f"Ocurrió un error al crear el egresado: {e}")

def render_editar_egresado_form():
    """Renderiza el formulario tradicional para editar un egresado existente."""
    st.header("✏️ Formulario de Edición")
    
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.dni, e.nombres || ' ' || e.apellido_paterno as nombre_completo 
                FROM egresados e 
                ORDER BY e.apellido_paterno ASC
            """)
            egresados_list = cur.fetchall()
            
        if not egresados_list:
            st.info("No hay egresados para editar.")
            return

        # Selector de egresado
        opciones = {f"{eg[2]} (DNI: {eg[1]})": eg[0] for eg in egresados_list}
        seleccionado = st.selectbox("Selecciona el egresado a editar", options=["-- Seleccionar --"] + list(opciones.keys()))

        if seleccionado != "-- Seleccionar --":
            egresado_id = opciones[seleccionado]
            
            # Cargar datos actuales
            with get_db_cursor() as cur:
                cur.execute("""
                    SELECT 
                        e.nombres, e.apellido_paterno, e.apellido_materno, e.dni,
                        e.carrera_principal, e.facultad, e.anio_egreso,
                        u.email, u.activo
                    FROM egresados e
                    JOIN usuarios u ON e.usuario_id = u.id
                    WHERE e.id = %s
                """, (egresado_id,))
                data = cur.fetchone()

            if data:
                with st.form("edit_egresado_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nombres = st.text_input("Nombres", value=data[0])
                        ap_paterno = st.text_input("Apellido Paterno", value=data[1])
                        ap_materno = st.text_input("Apellido Materno", value=data[2] or "")
                        dni = st.text_input("DNI (Solo lectura)", value=data[3], disabled=True)
                    
                    with col2:
                        email = st.text_input("Email", value=data[7])
                        carrera = st.text_input("Carrera Principal", value=data[4])
                        facultad = st.text_input("Facultad", value=data[5])
                        anio = st.number_input("Año de Egreso", value=int(data[6] or 2023), min_value=1950, max_value=2026)
                    
                    activo = st.toggle("Cuenta Activa", value=data[8])

                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_save, btn_cancel = st.columns(2)
                    
                    with btn_save:
                        guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    with btn_cancel:
                        # En un st.form, el botón de cancelar puede ser un simple botón que no envía el form
                        # Pero para resetear la vista, necesitamos que se refresque la página
                        cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                    if guardar:
                        try:
                            with get_db_cursor(commit=True) as cur:
                                # 1. Actualizar tabla usuarios (email y activo)
                                cur.execute("SELECT usuario_id FROM egresados WHERE id = %s", (egresado_id,))
                                usuario_id = cur.fetchone()[0]
                                cur.execute("""
                                    UPDATE usuarios SET email = %s, activo = %s WHERE id = %s
                                """, (email, activo, usuario_id))
                                
                                # 2. Actualizar tabla egresados
                                cur.execute("""
                                    UPDATE egresados SET 
                                        nombres = %s, apellido_paterno = %s, apellido_materno = %s,
                                        carrera_principal = %s, facultad = %s, anio_egreso = %s
                                    WHERE id = %s
                                """, (nombres, ap_paterno, ap_materno, carrera, facultad, anio, egresado_id))
                                
                            st.success("¡Cambios guardados correctamente!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar los cambios: {e}")
                    
                    if cancelar:
                        st.rerun()

    except Exception as e:
        st.error(f"Error al cargar el formulario de edición: {e}")

def render_lista_egresados():
    """Renderiza la tabla de egresados para visualización."""
    st.header("Listado de Egresados Registrados")
    st.markdown("Esta es una vista de solo lectura. Para realizar cambios o registrar nuevos alumnos, utiliza las otras pestañas.")

    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    e.id,
                    e.nombres, 
                    e.apellido_paterno,
                    e.apellido_materno,
                    e.dni,
                    e.carrera_principal,
                    e.anio_egreso,
                    u.email,
                    u.activo
                FROM egresados e
                JOIN usuarios u ON e.usuario_id = u.id
                ORDER BY e.apellido_paterno ASC
            """)
            resultados = cur.fetchall()
            
            if resultados:
                df = pd.DataFrame(resultados, columns=[
                    'id', 'Nombres', 'Apellido Paterno', 'Apellido Materno', 'DNI', 
                    'Carrera', 'Año Egreso', 'Email', 'Activo'
                ])

                # --- Métricas y Descarga ---
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Registrados", len(df))
                col2.metric("Cuentas Activas", df['Activo'].sum())
                
                with col3:
                    st.write("") # Espaciador
                    pdf_data = df.to_dict('records')
                    pdf_bytes = generar_pdf_reporte_generico(pdf_data, "Reporte de Egresados")
                    st.download_button(
                        label="📄 Descargar Reporte PDF",
                        data=pdf_bytes,
                        file_name=f"reporte_egresados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        key="download_egresados_pdf_list"
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)

                # Vista de solo lectura
                st.dataframe(
                    df,
                    column_config={
                        "id": None,
                        "Activo": st.column_config.CheckboxColumn("Activo"),
                        "Año Egreso": st.column_config.NumberColumn("Año Egreso", format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay egresados registrados en el sistema por el momento.")
                
    except Exception as e:
        st.error(f"Error cargando la lista de egresados: {e}")
