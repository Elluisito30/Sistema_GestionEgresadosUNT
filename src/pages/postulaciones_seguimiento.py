"""
Módulo de seguimiento de postulaciones para egresados.
Permite ver el estado de las postulaciones realizadas.
"""
import streamlit as st
import pandas as pd
from src.utils.database import get_db_cursor

def show():
    st.title("📋 Seguimiento de Mis Postulaciones")
    
    usuario_id = st.session_state.user['id']
    
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    o.titulo as oferta,
                    e.razon_social as empresa,
                    p.fecha_postulacion,
                    p.estado,
                    p.comentarios_empleador
                FROM postulaciones p
                JOIN ofertas o ON p.oferta_id = o.id
                JOIN empresas e ON o.empresa_id = e.id
                WHERE p.egresado_id = (SELECT id FROM egresados WHERE usuario_id = %s)
                ORDER BY p.fecha_postulacion DESC
            """, (usuario_id,))
            
            columns = [desc[0] for desc in cur.description]
            postulaciones = [dict(zip(columns, row)) for row in cur.fetchall()]
            
        if not postulaciones:
            st.info("Aún no has realizado ninguna postulación.")
            if st.button("Buscar Ofertas"):
                st.session_state.current_page = "ofertas_buscar"
                st.rerun()
            return

        # Mostrar resumen en métricas
        col1, col2, col3 = st.columns(3)
        total = len(postulaciones)
        en_proceso = sum(1 for p in postulaciones if p['estado'] in ['recibido', 'en_revision'])
        col1.metric("Total Postulaciones", total)
        col2.metric("En Proceso", en_proceso)
        col3.metric("Finalizadas", total - en_proceso)

        st.markdown("---")

        # Tabla de postulaciones
        df = pd.DataFrame(postulaciones)
        df['fecha_postulacion'] = pd.to_datetime(df['fecha_postulacion']).dt.strftime('%d/%m/%Y %H:%M')
        
        # Mapeo de estados para mejor visualización
        estado_map = {
            'recibido': '📩 Recibido',
            'en_revision': '🔍 En Revisión',
            'entrevista': '📅 Entrevista',
            'seleccionado': '✅ Seleccionado',
            'no_seleccionado': '❌ No Seleccionado',
            'cancelado': '🚫 Cancelado'
        }
        df['Estado'] = df['estado'].map(lambda x: estado_map.get(x, x))
        
        st.dataframe(
            df[['fecha_postulacion', 'oferta', 'empresa', 'Estado']],
            use_container_width=True,
            hide_index=True
        )

        # Detalles individuales
        st.subheader("Detalles y Comentarios")
        for p in postulaciones:
            with st.expander(f"{p['oferta']} - {p['empresa']} ({p['fecha_postulacion']})"):
                st.write(f"**Estado actual:** {estado_map.get(p['estado'], p['estado'])}")
                if p['comentarios_empleador']:
                    st.info(f"**Comentarios de la empresa:**\n\n{p['comentarios_empleador']}")
                else:
                    st.write("Aún no hay comentarios del empleador.")

    except Exception as e:
        st.error(f"Error al cargar las postulaciones: {e}")
