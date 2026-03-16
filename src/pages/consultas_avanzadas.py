"""
Módulo de consultas avanzadas.
Permite realizar búsquedas complejas con múltiples filtros.
"""
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from src.utils.database import get_db_cursor
from src.utils.session import add_notification

def show():
    """Muestra la página de consultas avanzadas."""
    
    st.title("🔍 Consultas Avanzadas")
    
    user = st.session_state.user
    
    if user['rol'] != 'administrador':
        st.error("Acceso restringido a administradores")
        return
    
    # Tipo de consulta
    tipo_consulta = st.selectbox(
        "Seleccionar tipo de consulta",
        options=[
            'Egresados por filtros',
            'Empresas por sector y ubicación',
            'Ofertas por rango salarial',
            'Postulaciones por período',
            'Análisis de compatibilidad',
            'Tendencia de contratación',
            'Consulta personalizada SQL'
        ]
    )
    
    st.markdown("---")
    
    if tipo_consulta == 'Egresados por filtros':
        consulta_egresados_avanzada()
    elif tipo_consulta == 'Empresas por sector y ubicación':
        consulta_empresas_avanzada()
    elif tipo_consulta == 'Ofertas por rango salarial':
        consulta_ofertas_avanzada()
    elif tipo_consulta == 'Postulaciones por período':
        consulta_postulaciones_avanzada()
    elif tipo_consulta == 'Análisis de compatibilidad':
        consulta_compatibilidad()
    elif tipo_consulta == 'Tendencia de contratación':
        consulta_tendencia()
    elif tipo_consulta == 'Consulta personalizada SQL':
        consulta_sql_personalizada()

def consulta_egresados_avanzada():
    """Consulta avanzada de egresados con múltiples filtros."""
    
    st.subheader("Filtros de Búsqueda - Egresados")
    
    with st.form("filtros_egresados"):
        col1, col2 = st.columns(2)
        
        with col1:
            carrera = st.text_input("Carrera", placeholder="Ej: Ingeniería de Sistemas")
            facultad = st.text_input("Facultad", placeholder="Ej: Ingeniería")
            año_desde = st.number_input("Año de egreso desde", min_value=1950, max_value=date.today().year, value=2000)
        
        with col2:
            año_hasta = st.number_input("Año de egreso hasta", min_value=1950, max_value=date.today().year, value=date.today().year)
            tiene_cv = st.checkbox("Tiene CV subido")
            perfil_publico = st.checkbox("Perfil público")
        
        st.subheader("Historial Laboral")
        tiene_experiencia = st.checkbox("Tiene experiencia laboral")
        
        if tiene_experiencia:
            col3, col4 = st.columns(2)
            with col3:
                años_exp = st.number_input("Mínimo años de experiencia", min_value=0, max_value=50, value=1)
            with col4:
                cargo = st.text_input("Cargo", placeholder="Ej: Desarrollador")
        
        submitted = st.form_submit_button("Buscar Egresados", type="primary", use_container_width=True)
    
    if submitted:
        ejecutar_consulta_egresados(
            carrera, facultad, año_desde, año_hasta,
            tiene_cv, perfil_publico, tiene_experiencia,
            años_exp if tiene_experiencia else None, cargo if tiene_experiencia else None
        )

def ejecutar_consulta_egresados(carrera, facultad, año_desde, año_hasta,
                               tiene_cv, perfil_publico, tiene_experiencia,
                               años_exp, cargo):
    """Ejecuta la consulta de egresados con los filtros."""
    
    query = """
        SELECT 
            u.email,
            e.nombres,
            e.apellido_paterno,
            e.apellido_materno,
            e.carrera_principal,
            e.facultad,
            e.anio_egreso,
            CASE WHEN e.url_cv IS NOT NULL THEN 'Sí' ELSE 'No' END as tiene_cv,
            CASE WHEN e.perfil_publico THEN 'Sí' ELSE 'No' END as perfil_publico,
            COUNT(DISTINCT h.id) as num_experiencias
        FROM egresados e
        JOIN usuarios u ON e.usuario_id = u.id
        LEFT JOIN historial_laboral h ON e.id = h.egresado_id
        WHERE 1=1
    """
    params = []
    
    if carrera:
        query += " AND e.carrera_principal ILIKE %s"
        params.append(f"%{carrera}%")
    
    if facultad:
        query += " AND e.facultad ILIKE %s"
        params.append(f"%{facultad}%")
    
    query += " AND e.anio_egreso BETWEEN %s AND %s"
    params.extend([año_desde, año_hasta])
    
    if tiene_cv:
        query += " AND e.url_cv IS NOT NULL"
    
    if perfil_publico:
        query += " AND e.perfil_publico = true"
    
    if tiene_experiencia and años_exp:
        query += """ AND e.id IN (
            SELECT egresado_id 
            FROM historial_laboral 
            WHERE (EXTRACT(YEAR FROM age(COALESCE(fecha_fin, CURRENT_DATE), fecha_inicio)) >= %s)
        )"""
        params.append(años_exp)
        
        if cargo:
            query += """ AND e.id IN (
                SELECT egresado_id 
                FROM historial_laboral 
                WHERE puesto ILIKE %s
            )"""
            params.append(f"%{cargo}%")
    
    query += " GROUP BY u.email, e.nombres, e.apellido_paterno, e.apellido_materno, e.carrera_principal, e.facultad, e.anio_egreso, e.url_cv, e.perfil_publico"
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        resultados = cur.fetchall()
        
        if not resultados:
            st.info("No se encontraron egresados con los filtros especificados")
            return
        
        df = pd.DataFrame(
            resultados,
            columns=['Email', 'Nombres', 'Apellido Paterno', 'Apellido Materno',
                    'Carrera', 'Facultad', 'Año Egreso', 'Tiene CV',
                    'Perfil Público', 'Experiencias']
        )
        
        st.success(f"Se encontraron {len(resultados)} egresados")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botón de exportación
        if st.button("📥 Exportar Resultados"):
            exportar_resultados(df, "egresados_consulta")

def consulta_empresas_avanzada():
    """Consulta avanzada de empresas."""
    
    st.subheader("Filtros de Búsqueda - Empresas")
    
    with st.form("filtros_empresas"):
        col1, col2 = st.columns(2)
        
        with col1:
            sector = st.selectbox(
                "Sector económico",
                options=['Todos', 'Tecnología', 'Salud', 'Educación', 'Finanzas', 'Construcción', 'Otros']
            )
            tamano = st.selectbox(
                "Tamaño de empresa",
                options=['Todos', 'pequeña', 'mediana', 'grande']
            )
        
        with col2:
            ubicacion = st.text_input("Ubicación", placeholder="Ej: Trujillo")
            estado = st.selectbox(
                "Estado",
                options=['Todos', 'activa', 'pendiente', 'rechazada']
            )
        
        tiene_ofertas = st.checkbox("Tiene ofertas publicadas")
        ofertas_activas = st.checkbox("Tiene ofertas activas")
        
        submitted = st.form_submit_button("Buscar Empresas", type="primary", use_container_width=True)
    
    if submitted:
        ejecutar_consulta_empresas(
            sector, tamano, ubicacion, estado,
            tiene_ofertas, ofertas_activas
        )

def ejecutar_consulta_empresas(sector, tamano, ubicacion, estado,
                              tiene_ofertas, ofertas_activas):
    """Ejecuta la consulta de empresas."""
    
    query = """
        SELECT 
            e.ruc,
            e.razon_social,
            e.sector_economico,
            e.tamano_empresa,
            e.direccion,
            e.email_contacto,
            e.telefono_contacto,
            e.estado,
            COUNT(DISTINCT o.id) as total_ofertas,
            COUNT(DISTINCT o.id) FILTER (WHERE o.activa) ofertas_activas
        FROM empresas e
        LEFT JOIN ofertas o ON e.id = o.empresa_id
        WHERE 1=1
    """
    params = []
    
    if sector != 'Todos':
        query += " AND e.sector_economico = %s"
        params.append(sector)
    
    if tamano != 'Todos':
        query += " AND e.tamano_empresa = %s"
        params.append(tamano)
    
    if ubicacion:
        query += " AND e.direccion ILIKE %s"
        params.append(f"%{ubicacion}%")
    
    if estado != 'Todos':
        query += " AND e.estado = %s"
        params.append(estado)
    
    if tiene_ofertas:
        query += " AND EXISTS (SELECT 1 FROM ofertas WHERE empresa_id = e.id)"
    
    if ofertas_activas:
        query += " AND EXISTS (SELECT 1 FROM ofertas WHERE empresa_id = e.id AND activa = true)"
    
    query += " GROUP BY e.ruc, e.razon_social, e.sector_economico, e.tamano_empresa, e.direccion, e.email_contacto, e.telefono_contacto, e.estado"
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        resultados = cur.fetchall()
        
        if not resultados:
            st.info("No se encontraron empresas con los filtros especificados")
            return
        
        df = pd.DataFrame(
            resultados,
            columns=['RUC', 'Razón Social', 'Sector', 'Tamaño',
                    'Dirección', 'Email', 'Teléfono', 'Estado',
                    'Total Ofertas', 'Ofertas Activas']
        )
        
        st.success(f"Se encontraron {len(resultados)} empresas")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("📥 Exportar Resultados", key="exp_emp"):
            exportar_resultados(df, "empresas_consulta")

def consulta_ofertas_avanzada():
    """Consulta avanzada de ofertas."""
    
    st.subheader("Filtros de Búsqueda - Ofertas")
    
    with st.form("filtros_ofertas"):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo = st.selectbox(
                "Tipo de oferta",
                options=['Todos', 'empleo', 'pasantia', 'practicas']
            )
            modalidad = st.selectbox(
                "Modalidad",
                options=['Todos', 'presencial', 'remoto', 'hibrido']
            )
        
        with col2:
            salario_min = st.number_input("Salario mínimo (S/.)", min_value=0, value=0, step=500)
            salario_max = st.number_input("Salario máximo (S/.)", min_value=0, value=10000, step=500)
        
        sector = st.text_input("Sector de empresa", placeholder="Ej: Tecnología")
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Trujillo")
        
        solo_activas = st.checkbox("Solo ofertas activas", value=True)
        
        submitted = st.form_submit_button("Buscar Ofertas", type="primary", use_container_width=True)
    
    if submitted:
        ejecutar_consulta_ofertas(
            tipo, modalidad, salario_min, salario_max,
            sector, ubicacion, solo_activas
        )

def ejecutar_consulta_ofertas(tipo, modalidad, salario_min, salario_max,
                            sector, ubicacion, solo_activas):
    """Ejecuta la consulta de ofertas."""
    
    query = """
        SELECT 
            o.titulo,
            e.razon_social,
            o.tipo,
            o.modalidad,
            o.ubicacion,
            o.salario_min,
            o.salario_max,
            o.fecha_publicacion,
            o.fecha_limite_postulacion,
            o.activa,
            COUNT(p.id) as postulaciones
        FROM ofertas o
        JOIN empresas e ON o.empresa_id = e.id
        LEFT JOIN postulaciones p ON o.id = p.oferta_id
        WHERE 1=1
    """
    params = []
    
    if tipo != 'Todos':
        query += " AND o.tipo = %s"
        params.append(tipo)
    
    if modalidad != 'Todos':
        query += " AND o.modalidad = %s"
        params.append(modalidad)
    
    if salario_min > 0:
        query += " AND o.salario_max >= %s"
        params.append(salario_min)
    
    if salario_max < 10000:
        query += " AND o.salario_min <= %s"
        params.append(salario_max)
    
    if sector:
        query += " AND e.sector_economico ILIKE %s"
        params.append(f"%{sector}%")
    
    if ubicacion:
        query += " AND o.ubicacion ILIKE %s"
        params.append(f"%{ubicacion}%")
    
    if solo_activas:
        query += " AND o.activa = true"
    
    query += " GROUP BY o.id, e.razon_social ORDER BY o.fecha_publicacion DESC"
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        resultados = cur.fetchall()
        
        if not resultados:
            st.info("No se encontraron ofertas con los filtros especificados")
            return
        
        df = pd.DataFrame(
            resultados,
            columns=['Título', 'Empresa', 'Tipo', 'Modalidad', 'Ubicación',
                    'Salario Mínimo', 'Salario Máximo', 'Publicación',
                    'Límite', 'Activa', 'Postulaciones']
        )
        
        st.success(f"Se encontraron {len(resultados)} ofertas")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("📥 Exportar Resultados", key="exp_of"):
            exportar_resultados(df, "ofertas_consulta")

def consulta_postulaciones_avanzada():
    """Consulta avanzada de postulaciones."""
    
    st.subheader("Filtros de Búsqueda - Postulaciones")
    
    with st.form("filtros_postulaciones"):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_desde = st.date_input("Fecha desde", value=date.today() - timedelta(days=30))
            estado = st.selectbox(
                "Estado",
                options=['Todos', 'recibido', 'en_revision', 'entrevista', 'seleccionado', 'descartado']
            )
        
        with col2:
            fecha_hasta = st.date_input("Fecha hasta", value=date.today())
            empresa = st.text_input("Empresa", placeholder="Ej: TechAndina")
        
        submitted = st.form_submit_button("Buscar Postulaciones", type="primary", use_container_width=True)
    
    if submitted:
        ejecutar_consulta_postulaciones(fecha_desde, fecha_hasta, estado, empresa)

def ejecutar_consulta_postulaciones(fecha_desde, fecha_hasta, estado, empresa):
    """Ejecuta la consulta de postulaciones."""
    
    query = """
        SELECT 
            o.titulo as oferta,
            e.razon_social as empresa,
            eg.nombres || ' ' || eg.apellido_paterno as egresado,
            p.estado,
            p.fecha_postulacion,
            p.fecha_estado_actual,
            EXTRACT(DAY FROM (p.fecha_estado_actual - p.fecha_postulacion))::int as dias_en_proceso
        FROM postulaciones p
        JOIN ofertas o ON p.oferta_id = o.id
        JOIN empresas e ON o.empresa_id = e.id
        JOIN egresados eg ON p.egresado_id = eg.id
        WHERE p.fecha_postulacion::date BETWEEN %s AND %s
    """
    params = [fecha_desde, fecha_hasta]
    
    if estado != 'Todos':
        query += " AND p.estado = %s"
        params.append(estado)
    
    if empresa:
        query += " AND e.razon_social ILIKE %s"
        params.append(f"%{empresa}%")
    
    query += " ORDER BY p.fecha_postulacion DESC"
    
    with get_db_cursor() as cur:
        cur.execute(query, params)
        resultados = cur.fetchall()
        
        if not resultados:
            st.info("No se encontraron postulaciones con los filtros especificados")
            return
        
        df = pd.DataFrame(
            resultados,
            columns=['Oferta', 'Empresa', 'Egresado', 'Estado',
                    'Fecha Postulación', 'Última Actualización', 'Días en Proceso']
        )
        
        st.success(f"Se encontraron {len(resultados)} postulaciones")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("📥 Exportar Resultados", key="exp_post"):
            exportar_resultados(df, "postulaciones_consulta")

def consulta_compatibilidad():
    """Análisis de compatibilidad entre egresados y ofertas."""
    
    st.subheader("Análisis de Compatibilidad")
    
    st.info("""
    Este análisis muestra los egresados más compatibles con ofertas específicas
    basado en su perfil académico y experiencia.
    """)
    
    with get_db_cursor() as cur:
        # Seleccionar oferta
        cur.execute("""
            SELECT id, titulo, empresa_id
            FROM ofertas
            WHERE activa = true
            ORDER BY fecha_publicacion DESC
            LIMIT 20
        """)
        
        ofertas = cur.fetchall()
        
        if not ofertas:
            st.warning("No hay ofertas activas para analizar")
            return
        
        oferta_opciones = {f"{o[1]}": o[0] for o in ofertas}
        oferta_seleccionada = st.selectbox("Seleccionar oferta", options=list(oferta_opciones.keys()))
        
        if oferta_seleccionada:
            oferta_id = oferta_opciones[oferta_seleccionada]
            
            # Obtener detalles de la oferta
            cur.execute("""
                SELECT carrera_objetivo, requisitos
                FROM ofertas
                WHERE id = %s
            """, (oferta_id,))
            
            carrera_objetivo, requisitos = cur.fetchone()
            
            st.subheader("Egresados compatibles")
            
            # Buscar egresados compatibles
            query = """
                SELECT 
                    eg.nombres || ' ' || eg.apellido_paterno as egresado,
                    eg.carrera_principal,
                    eg.anio_egreso,
                    COUNT(DISTINCT h.id) as experiencias,
                    CASE 
                        WHEN eg.carrera_principal = ANY(%s) THEN 30
                        ELSE 0
                    END + 
                    COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, MIN(h.fecha_inicio)))::int * 10, 0) as puntaje
                FROM egresados eg
                LEFT JOIN historial_laboral h ON eg.id = h.egresado_id
                WHERE NOT EXISTS (
                    SELECT 1 FROM postulaciones p 
                    WHERE p.egresado_id = eg.id AND p.oferta_id = %s
                )
                GROUP BY eg.id, eg.nombres, eg.apellido_paterno, eg.carrera_principal, eg.anio_egreso
                HAVING 
                    eg.carrera_principal = ANY(%s) OR
                    EXISTS (SELECT 1 FROM historial_laboral WHERE egresado_id = eg.id)
                ORDER BY puntaje DESC
                LIMIT 20
            """
            
            cur.execute(query, (carrera_objetivo, oferta_id, carrera_objetivo))
            
            compatibles = cur.fetchall()
            
            if compatibles:
                df = pd.DataFrame(
                    compatibles,
                    columns=['Egresado', 'Carrera', 'Año Egreso', 'Experiencias', 'Puntaje']
                )
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Opción para invitar a postular
                if st.button("📧 Invitar a postular a los top 5"):
                    add_notification("Invitaciones enviadas a los 5 mejores candidatos", "success")
            else:
                st.info("No se encontraron egresados compatibles")

def consulta_tendencia():
    """Análisis de tendencias de contratación."""
    
    st.subheader("Tendencias de Contratación")
    
    periodo = st.selectbox(
        "Período de análisis",
        options=['Últimos 6 meses', 'Último año', 'Últimos 2 años']
    )
    
    meses = {
        'Últimos 6 meses': 6,
        'Último año': 12,
        'Últimos 2 años': 24
    }[periodo]
    
    with get_db_cursor() as cur:
        # Ofertas por mes
        cur.execute("""
            SELECT 
                DATE_TRUNC('month', fecha_publicacion)::date as mes,
                COUNT(*) as ofertas,
                COUNT(*) FILTER (WHERE activa = false) as cerradas
            FROM ofertas
            WHERE fecha_publicacion > NOW() - (%s || ' months')::interval
            GROUP BY mes
            ORDER BY mes
        """, (meses,))
        
        ofertas_mes = cur.fetchall()
        
        if ofertas_mes:
            df_ofertas = pd.DataFrame(ofertas_mes, columns=['Mes', 'Ofertas', 'Cerradas'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ofertas por Mes")
                st.line_chart(df_ofertas.set_index('Mes')[['Ofertas', 'Cerradas']])
        
        # Contrataciones por carrera
        cur.execute("""
            SELECT 
                eg.carrera_principal,
                COUNT(*) as contrataciones
            FROM postulaciones p
            JOIN egresados eg ON p.egresado_id = eg.id
            WHERE p.estado = 'seleccionado'
            AND p.fecha_estado_actual > NOW() - (%s || ' months')::interval
            GROUP BY eg.carrera_principal
            ORDER BY contrataciones DESC
            LIMIT 10
        """, (meses,))
        
        contrataciones = cur.fetchall()
        
        if contrataciones:
            st.subheader("Top Carreras con más Contrataciones")
            df_contrataciones = pd.DataFrame(contrataciones, columns=['Carrera', 'Contrataciones'])
            st.bar_chart(df_contrataciones.set_index('Carrera'))
        
        # Tiempo promedio de contratación
        cur.execute("""
            SELECT 
                AVG(EXTRACT(DAY FROM (fecha_estado_actual - fecha_postulacion)))::int as tiempo_promedio
            FROM postulaciones
            WHERE estado = 'seleccionado'
            AND fecha_estado_actual > NOW() - (%s || ' months')::interval
        """, (meses,))
        
        tiempo_promedio = cur.fetchone()[0]
        
        if tiempo_promedio:
            st.metric("Tiempo promedio de contratación", f"{tiempo_promedio} días")

def consulta_sql_personalizada():
    """Permite ejecutar consultas SQL personalizadas."""
    
    st.subheader("Consulta SQL Personalizada")
    
    st.warning("""
    ⚠️ **Precaución**: Esta herramienta permite ejecutar consultas SQL directamente.
    Solo use SELECT para consultas de lectura. No modifique datos.
    """)
    
    sql_query = st.text_area(
        "Ingrese su consulta SQL",
        height=150,
        placeholder="SELECT * FROM egresados LIMIT 10;"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        ejecutar = st.button("▶️ Ejecutar Consulta", type="primary", use_container_width=True)
    
    with col2:
        limpiar = st.button("🗑️ Limpiar", use_container_width=True)
    
    if limpiar:
        st.rerun()
    
    if ejecutar and sql_query:
        if sql_query.strip().upper().startswith('SELECT'):
            try:
                with get_db_cursor() as cur:
                    cur.execute(sql_query)
                    
                    # Obtener resultados
                    resultados = cur.fetchall()
                    columnas = [desc[0] for desc in cur.description]
                    
                    if resultados:
                        df = pd.DataFrame(resultados, columns=columnas)
                        
                        st.success(f"Consulta ejecutada exitosamente. {len(resultados)} filas obtenidas.")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        if st.button("📥 Exportar Resultados", key="exp_sql"):
                            exportar_resultados(df, "consulta_sql")
                    else:
                        st.info("La consulta no devolvió resultados")
                        
            except Exception as e:
                st.error(f"Error en la consulta: {str(e)}")
        else:
            st.error("Solo se permiten consultas SELECT")

def exportar_resultados(df, nombre_base):
    """Exporta resultados a CSV."""
    
    import io
    import base64
    
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:text/csv;base64,{b64}" download="{nombre_base}_{date.today()}.csv">Descargar CSV</a>'
    st.markdown(href, unsafe_allow_html=True)