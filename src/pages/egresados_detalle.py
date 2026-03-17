import streamlit as st
import pandas as pd
from src.models.egresado import Egresado

def show():
    """Muestra el detalle y las analíticas individuales de un egresado."""
    
    st.title("📄 Detalle de Egresado")
    
    # Validar si accedió a esta vista desde una lista previa de manera correcta
    egresado_id = st.session_state.get('detalle_egresado_id', None)
    
    if not egresado_id:
        st.warning("No se ha seleccionado ningún egresado para inspeccionar.")
        if st.button("Volver a Lista"):
            from src.utils.session import set_current_page
            set_current_page('egresados_lista')
            st.rerun()
        return
        
    try:
        egresado = Egresado.get_by_id(egresado_id)
        if not egresado:
            st.error("No se encontró el registro en la base de datos.")
            return

        # Botón volver
        if st.button("⬅ Volver a Lista"):
            st.session_state.pop('detalle_egresado_id', None)
            st.session_state.current_page = 'egresados_lista'
            st.rerun()
            
        st.markdown("---")
        
        # Resumen Rápido (Top)
        col1, col2 = st.columns([1, 2])
        with col1:
            if egresado.foto_perfil_url:
                st.image(egresado.foto_perfil_url, width=150)
            else:
                st.markdown("👨‍🎓 **(Sin Foto de Perfil)**")
            st.subheader(egresado.nombre_completo)
            st.caption(f"DNI: {egresado.dni}")
            st.caption(f"Estado de Perfil Público: {'Activo' if egresado.perfil_publico else 'Privado'}")
            
        with col2:
            st.markdown("#### Datos de la Carrera")
            st.markdown(f"- **Carrera Principal:** {egresado.carrera_principal}")
            st.markdown(f"- **Facultad:** {egresado.facultad}")
            st.markdown(f"- **Año de Egreso:** {egresado.anio_egreso}")
            
            st.markdown("#### Información de Contacto")
            st.markdown(f"- **Teléfono:** {egresado.telefono or 'No registrado'}")
            st.markdown(f"- **Dirección:** {egresado.direccion or 'No registrada'}")
            if egresado.url_cv:
               st.markdown(f"📄 [Descargar CV Aquí]({egresado.url_cv})")
               
        st.markdown("---")
        
        # Tabs de analítica e historial
        tab1, tab2, tab3 = st.tabs(["Estadísticas de Postulación", "Historial Laboral", "Educación Continua"])
        
        with tab1:
            stats = egresado.get_estadisticas()
            if stats:
                st_col1, st_col2, st_col3 = st.columns(3)
                st_col1.metric("Postulaciones Totales", stats['total_postulaciones'])
                st_col2.metric("En Entrevista", stats['entrevistas'])
                st_col3.metric("Seleccionado", f"{stats['seleccionados']} (Tasa: {stats['tasa_exito']}%)")
            
            # Postulaciones List
            postulaciones = egresado.get_postulaciones(limit=10)
            if postulaciones:
                df_post = pd.DataFrame(postulaciones)[['oferta_titulo', 'empresa', 'estado', 'fecha_postulacion']]
                st.dataframe(df_post, hide_index=True)
            else:
                st.info("No tiene historial de postulaciones.")
                
        with tab2:
            historial = egresado.get_historial_laboral()
            if historial:
                st.dataframe(pd.DataFrame(historial), hide_index=True)
            else:
                st.info("No hay registros de historial laboral previo.")
                
        with tab3:
            edu = egresado.get_educacion_continua()
            if edu:
                st.dataframe(pd.DataFrame(edu), hide_index=True)
            else:
                st.info("No hay registros de educación continua.")

    except Exception as e:
        st.error(f"Ocurrió un error construyendo la vista de detalle: {str(e)}")
