"""
Módulo de auditoría y bitácora.
Reorganizado por pestañas para mejor trazabilidad y visualización.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.utils.database import get_db_cursor
from src.utils.decorators import role_required
from src.utils.pdf_generator import generar_pdf_bitacora

@role_required(['administrador'])
def show():
    """Muestra la página de auditoría organizada por pestañas."""
    st.title("📋 Bitácora de Auditoría")
    
    # Obtener lista de usuarios para el selector
    with get_db_cursor() as cur:
        cur.execute("SELECT email FROM usuarios ORDER BY email ASC")
        lista_usuarios = ["Todos"] + [row[0] for row in cur.fetchall()]

    # --- SECCIÓN DE FILTROS ---
    with st.expander("🔍 Filtros Globales", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_desde = st.date_input("Desde", datetime.now() - timedelta(days=7))
        with col2:
            fecha_hasta = st.date_input("Hasta", datetime.now())
        with col3:
            usuario_sel = st.selectbox("Filtrar por Usuario", options=lista_usuarios)

    # --- PESTAÑAS DE BITÁCORA ---
    tab_sesiones, tab_datos, tab_modulos, tab_sistema = st.tabs([
        "🔑 Inicios de Sesión", 
        "💾 Operaciones de Datos", 
        "📂 Acceso a Módulos",
        "⚙️ Eventos del Sistema"
    ])

    # Función auxiliar para renderizar cada pestaña
    def render_bitacora_tab(acciones_list, key_suffix):
        # Escapamos los caracteres '%' como '%%' para evitar errores de psycopg2
        query = """
            SELECT u.email as Usuario, b.accion as Acción, b.modulo as Módulo, 
                   b.detalle as Descripción, b.fecha_hora as Fecha, 
                   CASE WHEN b.detalle ILIKE '%%error%%' THEN 'Error' ELSE 'Correcto' END as Resultado
            FROM bitacora_auditoria b
            LEFT JOIN usuarios u ON b.usuario_id = u.id
            WHERE b.fecha_hora::date BETWEEN %s AND %s
        """
        params = [fecha_desde, fecha_hasta]

        if acciones_list:
            query += " AND b.accion IN %s"
            params.append(tuple(acciones_list))
        
        if usuario_sel != "Todos":
            query += " AND u.email = %s"
            params.append(usuario_sel)

        query += " ORDER BY b.fecha_hora DESC LIMIT 500"

        with get_db_cursor() as cur:
            cur.execute(query, params)
            data = cur.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=['Usuario', 'Acción', 'Módulo', 'Descripción', 'Fecha', 'Resultado'])
                st.dataframe(df, use_container_width=True)
                
                # --- EXPORTACIÓN ---
                st.markdown("---")
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"bitacora_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime='text/csv',
                        key=f"csv_btn_{key_suffix}"
                    )
                
                with col_exp2:
                    pdf = generar_pdf_bitacora(df, f"Reporte de {st.session_state.get('current_tab', 'Bitácora')}")
                    st.download_button(
                        label="📄 Descargar PDF",
                        data=pdf,
                        file_name=f"bitacora_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime='application/pdf',
                        key=f"pdf_btn_{key_suffix}"
                    )
            else:
                st.info("No se encontraron registros para esta sección.")

    with tab_sesiones:
        st.session_state.current_tab = "Inicios de Sesión"
        render_bitacora_tab(["LOGIN", "LOGOUT", "LOGIN_FALLIDO"], "sesiones")

    with tab_datos:
        st.session_state.current_tab = "Operaciones de Datos"
        render_bitacora_tab(["CREACION", "MODIFICACION", "ELIMINACION"], "datos")

    with tab_modulos:
        st.session_state.current_tab = "Acceso a Módulos"
        render_bitacora_tab(["ACCESO_MODULO", "CONSULTA"], "modulos")

    with tab_sistema:
        st.session_state.current_tab = "Eventos del Sistema"
        render_bitacora_tab(["SISTEMA", "ERROR", "NOTIFICACION"], "sistema")
