-- =====================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS - SISTEMA DE EGRESADOS UNT
-- =====================================================
-- Estructura simplificada con IDs correlativos (SERIAL)
-- =====================================================

-- =====================================================
-- ENUMS (Tipos de datos personalizados)
-- =====================================================
DROP TYPE IF EXISTS rol_usuario CASCADE;
CREATE TYPE rol_usuario AS ENUM ('administrador', 'egresado', 'empleador');

DROP TYPE IF EXISTS estado_postulacion CASCADE;
CREATE TYPE estado_postulacion AS ENUM ('recibido', 'en_revision', 'entrevista', 'seleccionado', 'descartado');

DROP TYPE IF EXISTS tipo_oferta CASCADE;
CREATE TYPE tipo_oferta AS ENUM ('empleo', 'pasantia', 'practicas');

DROP TYPE IF EXISTS modalidad_trabajo CASCADE;
CREATE TYPE modalidad_trabajo AS ENUM ('presencial', 'remoto', 'hibrido');

DROP TYPE IF EXISTS estado_empresa CASCADE;
CREATE TYPE estado_empresa AS ENUM ('pendiente', 'activa', 'rechazada');

DROP TYPE IF EXISTS tipo_evento CASCADE;
CREATE TYPE tipo_evento AS ENUM ('feria_laboral', 'webinar', 'charla', 'curso');

DROP TYPE IF EXISTS tipo_pago CASCADE;
CREATE TYPE tipo_pago AS ENUM ('certificado', 'membresia', 'evento');

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- 1. TABLA USUARIOS
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL,
    email_confirmado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    reset_password_token VARCHAR(255),
    reset_password_expira TIMESTAMP WITH TIME ZONE
);

-- 2. TABLA EGRESADOS
CREATE TABLE egresados (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombres VARCHAR(255) NOT NULL,
    apellido_paterno VARCHAR(255) NOT NULL,
    apellido_materno VARCHAR(255),
    dni CHAR(8) UNIQUE NOT NULL,
    fecha_nacimiento DATE,
    telefono VARCHAR(20),
    direccion TEXT,
    carrera_principal VARCHAR(255) NOT NULL,
    facultad VARCHAR(255) NOT NULL,
    anio_egreso INTEGER,
    url_cv TEXT,
    perfil_publico BOOLEAN DEFAULT FALSE,
    foto_perfil_url TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLA EMPRESAS
CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    ruc CHAR(11) UNIQUE NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    nombre_comercial VARCHAR(255),
    sector_economico VARCHAR(100),
    tamano_empresa VARCHAR(50),
    direccion TEXT,
    telefono_contacto VARCHAR(20),
    email_contacto VARCHAR(255),
    sitio_web VARCHAR(255),
    estado estado_empresa DEFAULT 'pendiente',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    aprobado_por INTEGER REFERENCES usuarios(id),
    logo_url TEXT
);

-- 4. TABLA EMPLEADORES
CREATE TABLE empleadores (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    nombres VARCHAR(255) NOT NULL,
    apellidos VARCHAR(255) NOT NULL,
    cargo VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    es_administrador_empresa BOOLEAN DEFAULT FALSE
);

-- 5. TABLA OFERTAS LABORALES
CREATE TABLE ofertas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    publicado_por INTEGER NOT NULL REFERENCES empleadores(id),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    requisitos TEXT,
    tipo tipo_oferta NOT NULL,
    modalidad modalidad_trabajo NOT NULL,
    ubicacion VARCHAR(255),
    salario_min NUMERIC(10,2),
    salario_max NUMERIC(10,2),
    fecha_publicacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_limite_postulacion DATE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    carrera_objetivo VARCHAR(255)[]
);

-- 6. TABLA POSTULACIONES
CREATE TABLE postulaciones (
    id SERIAL PRIMARY KEY,
    oferta_id INTEGER NOT NULL REFERENCES ofertas(id) ON DELETE CASCADE,
    egresado_id INTEGER NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    fecha_postulacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estado estado_postulacion DEFAULT 'recibido',
    cv_usado_url TEXT,
    fecha_estado_actual TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    comentario_revision TEXT,
    UNIQUE(oferta_id, egresado_id)
);

-- 7. TABLA EVENTOS
CREATE TABLE eventos (
    id SERIAL PRIMARY KEY,
    publicado_por INTEGER NOT NULL REFERENCES usuarios(id),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo tipo_evento NOT NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    lugar VARCHAR(255),
    capacidad_maxima INTEGER,
    es_gratuito BOOLEAN DEFAULT TRUE,
    precio NUMERIC(10,2),
    imagen_promocional_url TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- 8. TABLA PAGOS Y VOUCHERS
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    concepto tipo_pago NOT NULL,
    referencia_id INTEGER,
    monto NUMERIC(10,2) NOT NULL,
    fecha_pago TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    codigo_voucher VARCHAR(100) UNIQUE,
    qr_code_data TEXT,
    pdf_voucher_url TEXT,
    pagado BOOLEAN DEFAULT TRUE,
    validado BOOLEAN DEFAULT FALSE
);

-- 9. TABLA INSCRIPCIONES EVENTOS
CREATE TABLE inscripciones_eventos (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha_inscripcion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    asistio BOOLEAN DEFAULT FALSE,
    pago_id INTEGER REFERENCES pagos(id) ON DELETE SET NULL,
    UNIQUE(evento_id, usuario_id)
);

-- 10. TABLA HISTORIAL LABORAL
CREATE TABLE historial_laboral (
    id SERIAL PRIMARY KEY,
    egresado_id INTEGER NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    empresa_nombre VARCHAR(255) NOT NULL,
    puesto VARCHAR(255) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    es_trabajo_actual BOOLEAN DEFAULT FALSE,
    descripcion TEXT
);

-- 11. TABLA EDUCACION CONTINUA
CREATE TABLE educacion_continua (
    id SERIAL PRIMARY KEY,
    egresado_id INTEGER NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    institucion VARCHAR(255) NOT NULL,
    titulo_curso VARCHAR(255) NOT NULL,
    nivel VARCHAR(50),
    fecha_inicio DATE,
    fecha_fin DATE,
    documento_url TEXT
);

-- 12. TABLA ENCUESTAS
CREATE TABLE encuestas (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    creada_por INTEGER REFERENCES usuarios(id)
);

-- 13. TABLA PREGUNTAS
CREATE TABLE preguntas_encuesta (
    id SERIAL PRIMARY KEY,
    encuesta_id INTEGER NOT NULL REFERENCES encuestas(id) ON DELETE CASCADE,
    texto_pregunta TEXT NOT NULL,
    tipo_respuesta VARCHAR(50),
    opciones JSONB
);

-- 14. TABLA RESPUESTAS ENCUESTA
CREATE TABLE respuestas_encuesta (
    id SERIAL PRIMARY KEY,
    encuesta_id INTEGER NOT NULL REFERENCES encuestas(id) ON DELETE CASCADE,
    pregunta_id INTEGER NOT NULL REFERENCES preguntas_encuesta(id) ON DELETE CASCADE,
    egresado_id INTEGER NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    respuesta TEXT,
    fecha_respuesta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pregunta_id, egresado_id)
);

-- 15. TABLA NOTIFICACIONES
CREATE TABLE notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50),
    asunto VARCHAR(255),
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_envio TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- 16. TABLA CHAT EVENTOS
CREATE TABLE chat_eventos (
    id SERIAL PRIMARY KEY,
    evento_id INTEGER NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    fecha_envio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. TABLA BITACORA DE AUDITORIA
CREATE TABLE bitacora_auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    perfil_utilizado rol_usuario,
    accion VARCHAR(50) NOT NULL,
    modulo VARCHAR(100),
    detalle TEXT,
    direccion_ip INET,
    user_agent TEXT,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_egresados_carrera ON egresados(carrera_principal);
CREATE INDEX idx_ofertas_fecha_publicacion ON ofertas(fecha_publicacion);
CREATE INDEX idx_postulaciones_estado ON postulaciones(estado);
CREATE INDEX idx_eventos_fecha_inicio ON eventos(fecha_inicio);
CREATE INDEX idx_pagos_usuario_id ON pagos(usuario_id);
CREATE INDEX idx_bitacora_fecha ON bitacora_auditoria(fecha_hora);

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================
CREATE VIEW v_egresados_por_mes AS
SELECT
    DATE_TRUNC('month', fecha_registro) AS mes,
    COUNT(*) AS total_egresados
FROM usuarios u
JOIN egresados e ON u.id = e.usuario_id
GROUP BY mes
ORDER BY mes DESC;

CREATE VIEW v_ofertas_con_postulaciones AS
SELECT
    o.id,
    o.titulo,
    e.razon_social,
    o.fecha_limite_postulacion,
    COUNT(p.id) AS total_postulaciones,
    SUM(CASE WHEN p.estado = 'recibido' THEN 1 ELSE 0 END) as pendientes_revision
FROM ofertas o
JOIN empresas e ON o.empresa_id = e.id
LEFT JOIN postulaciones p ON o.id = p.oferta_id
WHERE o.activa = TRUE
GROUP BY o.id, e.razon_social;
