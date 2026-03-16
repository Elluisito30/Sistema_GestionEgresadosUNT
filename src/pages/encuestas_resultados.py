"""
Vista dedicada para resultados de encuestas.
"""
from datetime import datetime

import streamlit as st

from src.pages.encuestas_disenar import ver_resultados_encuestas
from src.utils.database import get_db_cursor
from src.utils.excel_generator import generar_excel_encuestas_resultados


def show():
    """Muestra la vista administrativa de resultados de encuestas."""
    user = st.session_state.user
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return

    st.title("📊 Resultados de Encuestas")
    st.caption("Consulta consolidada de respuestas y métricas de seguimiento.")
    
    # Agregar opción de descarga de reportes
    tab1, tab2 = st.tabs(["📋 Resultados Detallados", "📥 Descargar Reportes"])
    
    with tab1:
        ver_resultados_encuestas()
    
    with tab2:
        mostrar_opciones_descarga_encuestas()


def mostrar_opciones_descarga_encuestas():
    """Muestra opciones para descargar reportes de encuestas."""
    st.subheader("Descargar Reportes de Encuestas")
    
    with get_db_cursor() as cur:
        cur.execute("SELECT id, titulo FROM encuestas ORDER BY titulo DESC")
        encuestas = cur.fetchall()
    
    if not encuestas:
        st.info("No hay encuestas disponibles")
        return
    
    opciones_encuesta = {f"{e[1]}": e[0] for e in encuestas}
    encuesta_seleccionada = st.selectbox("Seleccionar Encuesta", options=list(opciones_encuesta.keys()), key="select_encuesta_download")
    
    if encuesta_seleccionada:
        encuesta_id = opciones_encuesta[encuesta_seleccionada]
        
        datos_reporte = _obtener_datos_reporte_encuesta(encuesta_id)
        
        if not datos_reporte:
            st.warning("No hay datos para descargar de esta encuesta")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            excel_bytes = generar_excel_encuestas_resultados(datos_reporte)
            st.download_button(
                "📊 Descargar Excel",
                data=excel_bytes,
                file_name=f"resultados_encuesta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        
        with col2:
            from src.utils.pdf_generator import generar_pdf_resultados_encuestas
            pdf_bytes = generar_pdf_resultados_encuestas(datos_reporte, encuesta_seleccionada)
            st.download_button(
                "📄 Descargar PDF",
                data=pdf_bytes,
                file_name=f"resultados_encuesta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


def _obtener_datos_reporte_encuesta(encuesta_id):
    """Obtiene datos de resultados de encuesta para reporte."""
    with get_db_cursor() as cur:
        cur.execute("SELECT titulo FROM encuestas WHERE id = %s", (encuesta_id,))
        resultado = cur.fetchone()
        titulo_encuesta = resultado[0] if resultado else "Encuesta Desconocida"
        
        cur.execute("""
            SELECT 
                p.texto_pregunta,
                p.tipo_respuesta,
                r.respuesta,
                COUNT(*) as cantidad
            FROM preguntas_encuesta p
            LEFT JOIN respuestas_encuesta r ON p.id = r.pregunta_id AND r.encuesta_id = %s
            WHERE p.encuesta_id = %s
            GROUP BY p.texto_pregunta, p.tipo_respuesta, r.respuesta
            ORDER BY p.id, r.respuesta
        """, (encuesta_id, encuesta_id))
        
        resultados = cur.fetchall()
    
    if not resultados:
        return None
    
    # Formatear datos para reporte
    datos = []
    for texto_pregunta, tipo_respuesta, respuesta, cantidad in resultados:
        # Calcular total de respuestas para porcentaje
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT COUNT(DISTINCT egresado_id)
                FROM respuestas_encuesta
                WHERE encuesta_id = %s AND pregunta_id = (
                    SELECT id FROM preguntas_encuesta WHERE texto_pregunta = %s LIMIT 1
                )
            """, (encuesta_id, texto_pregunta))
            total_respuestas = cur.fetchone()[0] or 1
        
        porcentaje = (cantidad / total_respuestas * 100) if total_respuestas > 0 else 0
        
        datos.append({
            "titulo_encuesta": titulo_encuesta,
            "texto_pregunta": texto_pregunta,
            "tipo_respuesta": tipo_respuesta or "indefinido",
            "respuesta": respuesta or "sin respuesta",
            "cantidad": cantidad or 0,
            "porcentaje": porcentaje,
        })
    
    return datos

