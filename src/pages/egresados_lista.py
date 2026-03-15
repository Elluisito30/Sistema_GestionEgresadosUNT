import streamlit as st
import pandas as pd
from src.utils.database import get_db_cursor

def show():
    """Muestra la lista de egresados para los administradores."""
    st.title("👥 Gestión de Egresados")
    
    st.markdown("""
        En esta sección puedes revisar todos los egresados registrados en la plataforma.
        Utiliza los controles de la tabla para ordenar o buscar un alumno en específico.
    """)
    
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    e.nombres || ' ' || e.apellido_paterno || ' ' || COALESCE(e.apellido_materno, '') as nombre_completo,
                    e.dni,
                    e.carrera_principal,
                    e.anio_egreso,
                    u.email,
                    CASE WHEN u.activo THEN 'Activo' ELSE 'Inactivo' END as estado_cuenta
                FROM egresados e
                JOIN usuarios u ON e.usuario_id = u.id
                ORDER BY e.apellido_paterno ASC
            """)
            resultados = cur.fetchall()
            
            if resultados:
                df = pd.DataFrame(resultados, columns=[
                    'Nombre Completo', 'DNI', 'Carrera', 
                    'Año de Egreso', 'Email', 'Estado'
                ])
                
                # Mostrar métricas rápidas
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Registrados", len(df))
                col2.metric("Perfiles Activos", len(df[df['Estado'] == 'Activo']))
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Contenedor estético
                with st.container(border=True):
                    # Añadir columna de acción (Ver Detalle)
                    # Usamos st.data_editor o simplemente una lista con botones
                    for i, row in df.iterrows():
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.write(f"**{row['Nombre Completo']}** ({row['Carrera']}) - {row['Email']}")
                        with col_btn:
                            if st.button("👁️ Ver Detalle", key=f"btn_{row['DNI']}"):
                                # Obtener el egresado_id real desde la base de datos usando el DNI
                                from src.models.egresado import Egresado
                                eg = Egresado.get_by_dni(row['DNI'])
                                if eg:
                                    st.session_state.detalle_egresado_id = eg.id
                                    st.session_state.current_page = 'egresados_detalle'
                                    st.rerun()
            else:
                st.info("No hay egresados registrados en el sistema por el momento.")
                
    except Exception as e:
        st.error(f"Error cargando la lista de egresados: {e}")
