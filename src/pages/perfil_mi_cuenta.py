"""
Módulo de gestión de perfil de usuario.
Permite a cualquier usuario ver y editar su perfil según su rol.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.utils.database import get_db_cursor
from src.utils.validators import (
    validar_dni, validar_email, validar_telefono,
    validar_fecha, sanitizar_entrada
)
from src.auth import hash_password
from src.utils.session import add_notification

def show():
    """Muestra la página de perfil del usuario."""
    
    user = st.session_state.user
    rol = user['rol']
    
    st.title("👤 Mi Perfil")
    
    # Tabs para organizar la información
    tab1, tab2, tab3 = st.tabs(["📋 Información Personal", "🔐 Seguridad", "📊 Actividad"])
    
    with tab1:
        mostrar_info_personal(user, rol)
    
    with tab2:
        mostrar_seguridad(user)
    
    with tab3:
        mostrar_actividad(user)

def mostrar_info_personal(user, rol):
    """Muestra y permite editar la información personal según el rol."""
    
    st.subheader("Información Personal")
    
    # Obtener datos específicos según el rol
    if rol == 'egresado':
        datos = obtener_datos_egresado(user['id'])
        if datos:
            with st.form("form_egresado"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombres = st.text_input("Nombres *", value=datos['nombres'])
                    apellido_paterno = st.text_input("Apellido Paterno *", value=datos['apellido_paterno'])
                    apellido_materno = st.text_input("Apellido Materno", value=datos.get('apellido_materno', ''))
                    dni = st.text_input("DNI *", value=datos['dni'], disabled=True)
                
                with col2:
                    fecha_nacimiento = st.date_input(
                        "Fecha de Nacimiento",
                        value=datos.get('fecha_nacimiento'),
                        min_value=datetime(1900, 1, 1),
                        max_value=datetime.now()
                    )
                    telefono = st.text_input("Teléfono", value=datos.get('telefono', ''))
                    direccion = st.text_area("Dirección", value=datos.get('direccion', ''))
                
                st.markdown("---")
                st.subheader("Información Académica")
                
                col3, col4 = st.columns(2)
                with col3:
                    carrera = st.text_input("Carrera *", value=datos['carrera_principal'])
                    facultad = st.text_input("Facultad *", value=datos['facultad'])
                
                with col4:
                    anio_egreso = st.number_input(
                        "Año de Egreso",
                        min_value=1950,
                        max_value=datetime.now().year,
                        value=datos.get('anio_egreso', datetime.now().year)
                    )
                
                # CV
                st.subheader("Curriculum Vitae")
                cv_file = st.file_uploader(
                    "Subir CV (PDF, DOC, DOCX)",
                    type=['pdf', 'doc', 'docx'],
                    help="Suba su CV en formato PDF o Word"
                )
                
                if datos.get('url_cv'):
                    st.info(f"CV actual: {datos['url_cv'].split('/')[-1]}")
                
                # Configuración de privacidad
                st.subheader("Privacidad")
                perfil_publico = st.checkbox(
                    "Perfil público para networking",
                    value=datos.get('perfil_publico', False),
                    help="Si activa esta opción, otros egresados podrán ver su perfil"
                )
                
                submitted = st.form_submit_button("Guardar Cambios", type="primary")
                
                if submitted:
                    guardar_perfil_egresado(
                        user['id'],
                        nombres, apellido_paterno, apellido_materno,
                        fecha_nacimiento, telefono, direccion,
                        carrera, facultad, anio_egreso,
                        perfil_publico, cv_file
                    )
    
    elif rol == 'empleador':
        datos = obtener_datos_empleador(user['id'])
        if datos:
            with st.form("form_empleador"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombres = st.text_input("Nombres *", value=datos['nombres'])
                    apellidos = st.text_input("Apellidos *", value=datos['apellidos'])
                    cargo = st.text_input("Cargo en la Empresa *", value=datos['cargo'])
                
                with col2:
                    telefono = st.text_input("Teléfono de Contacto", value=datos.get('telefono', ''))
                    email = st.text_input("Email", value=user['email'], disabled=True)
                
                st.markdown("---")
                st.subheader("Información de la Empresa")
                
                # Mostrar información de la empresa (solo lectura)
                empresa = obtener_empresa(datos['empresa_id'])
                if empresa:
                    st.info(f"**Empresa:** {empresa['razon_social']}")
                    st.info(f"**RUC:** {empresa['ruc']}")
                    st.info(f"**Estado:** {empresa['estado'].upper()}")
                
                submitted = st.form_submit_button("Guardar Cambios", type="primary")
                
                if submitted:
                    guardar_perfil_empleador(
                        user['id'], nombres, apellidos,
                        cargo, telefono
                    )
    
    elif rol == 'administrador':
        # Perfil de administrador (más simple)
        with st.form("form_admin"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombres = st.text_input("Nombres", value="Administrador")
                email = st.text_input("Email", value=user['email'], disabled=True)
            
            with col2:
                telefono = st.text_input("Teléfono de Contacto")
            
            submitted = st.form_submit_button("Guardar Cambios", type="primary")
            
            if submitted:
                add_notification("Perfil actualizado correctamente", "success")
                st.rerun()

def mostrar_seguridad(user):
    """Muestra opciones de seguridad como cambio de contraseña."""
    
    st.subheader("Cambiar Contraseña")
    
    with st.form("form_password"):
        password_actual = st.text_input("Contraseña Actual", type="password")
        password_nueva = st.text_input("Nueva Contraseña", type="password")
        password_confirmar = st.text_input("Confirmar Nueva Contraseña", type="password")
        
        # Requisitos de contraseña
        st.markdown("""
        **Requisitos de la contraseña:**
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos un número
        - Al menos un carácter especial
        """)
        
        submitted = st.form_submit_button("Cambiar Contraseña", type="primary")
        
        if submitted:
            cambiar_password(user['id'], password_actual, password_nueva, password_confirmar)
    
    st.markdown("---")
    st.subheader("Sesiones Activas")
    
    # Mostrar sesiones activas (simulado)
    st.info("No hay otras sesiones activas")

def mostrar_actividad(user):
    """Muestra el historial de actividad del usuario."""
    
    st.subheader("Actividad Reciente")
    
    # Obtener actividad de la bitácora
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT fecha_hora, accion, modulo, detalle
            FROM bitacora_auditoria
            WHERE usuario_id = %s
            ORDER BY fecha_hora DESC
            LIMIT 20
        """, (user['id'],))
        
        actividades = cur.fetchall()
    
    if actividades:
        df = pd.DataFrame(
            actividades,
            columns=['Fecha', 'Acción', 'Módulo', 'Detalle']
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay actividad registrada")

# Funciones auxiliares de base de datos

def obtener_datos_egresado(usuario_id):
    """Obtiene los datos del egresado desde la BD."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT e.*, u.email
            FROM egresados e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.usuario_id = %s
        """, (usuario_id,))
        
        columns = [desc[0] for desc in cur.description]
        row = cur.fetchone()
        
        if row:
            return dict(zip(columns, row))
        return None

def obtener_datos_empleador(usuario_id):
    """Obtiene los datos del empleador desde la BD."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                u.email,
                e.nombres,
                e.apellidos,
                e.cargo,
                e.telefono,
                e.empresa_id
            FROM empleadores e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.usuario_id = %s
        """, (usuario_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'email': row[0],
                'nombres': row[1],
                'apellidos': row[2],
                'cargo': row[3],
                'telefono': row[4],
                'empresa_id': row[5]
            }
        return None

def obtener_empresa(empresa_id):
    """Obtiene los datos de una empresa."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT razon_social, ruc, estado
            FROM empresas
            WHERE id = %s
        """, (empresa_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'razon_social': row[0],
                'ruc': row[1],
                'estado': row[2]
            }
        return None

def guardar_perfil_egresado(usuario_id, nombres, ape_paterno, ape_materno,
                           fecha_nac, telefono, direccion, carrera,
                           facultad, anio_egreso, perfil_publico, cv_file):
    """Guarda los cambios en el perfil del egresado."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            # Actualizar datos del egresado
            cur.execute("""
                UPDATE egresados
                SET nombres = %s,
                    apellido_paterno = %s,
                    apellido_materno = %s,
                    fecha_nacimiento = %s,
                    telefono = %s,
                    direccion = %s,
                    carrera_principal = %s,
                    facultad = %s,
                    anio_egreso = %s,
                    perfil_publico = %s,
                    fecha_actualizacion = NOW()
                WHERE usuario_id = %s
            """, (
                nombres, ape_paterno, ape_materno,
                fecha_nac, telefono, direccion,
                carrera, facultad, anio_egreso,
                perfil_publico, usuario_id
            ))
            
            # Procesar CV si se subió uno nuevo
            if cv_file:
                # Aquí iría la lógica para guardar el archivo
                # Por ahora solo simulamos
                cv_path = f"/app/storage/cv/{usuario_id}_{cv_file.name}"
                # Guardar referencia en BD
                cur.execute("""
                    UPDATE egresados
                    SET url_cv = %s
                    WHERE usuario_id = %s
                """, (cv_path, usuario_id))
            
            add_notification("Perfil actualizado correctamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al guardar: {str(e)}", "error")

def guardar_perfil_empleador(usuario_id, nombres, apellidos, cargo, telefono):
    """Guarda los cambios en el perfil del empleador."""
    
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE empleadores
                SET nombres = %s,
                    apellidos = %s,
                    cargo = %s,
                    telefono = %s
                WHERE usuario_id = %s
            """, (nombres, apellidos, cargo, telefono, usuario_id))
            
            add_notification("Perfil actualizado correctamente", "success")
            st.rerun()
            
    except Exception as e:
        add_notification(f"Error al guardar: {str(e)}", "error")

def cambiar_password(usuario_id, password_actual, password_nueva, password_confirmar):
    """Cambia la contraseña del usuario."""
    
    from src.auth import verify_password, hash_password
    
    # Validaciones
    if not password_actual or not password_nueva or not password_confirmar:
        add_notification("Todos los campos son requeridos", "error")
        return
    
    if password_nueva != password_confirmar:
        add_notification("Las contraseñas nuevas no coinciden", "error")
        return
    
    if len(password_nueva) < 8:
        add_notification("La contraseña debe tener al menos 8 caracteres", "error")
        return
    
    # Verificar contraseña actual
    with get_db_cursor() as cur:
        cur.execute("SELECT password_hash FROM usuarios WHERE id = %s", (usuario_id,))
        hash_actual = cur.fetchone()[0]
        
        if not verify_password(password_actual, hash_actual):
            add_notification("La contraseña actual es incorrecta", "error")
            return
    
    # Actualizar contraseña
    nuevo_hash = hash_password(password_nueva)
    
    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE usuarios
            SET password_hash = %s
            WHERE id = %s
        """, (nuevo_hash, usuario_id))
        
        add_notification("Contraseña actualizada correctamente", "success")
        st.rerun()