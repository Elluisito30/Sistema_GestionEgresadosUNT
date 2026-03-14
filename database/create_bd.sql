-- =====================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS - SISTEMA DE EGRESADOS UNT
-- =====================================================
-- Crear la base de datos (ejecutar como superusuario)
-- CREATE DATABASE bd_egresadosUNT;
-- =====================================================

-- Habilitar extensión para UUIDs (recomendado para claves primarias)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ENUMS (Tipos de datos personalizados)
-- =====================================================
CREATE TYPE rol_usuario AS ENUM ('administrador', 'egresado', 'empleador');
CREATE TYPE estado_postulacion AS ENUM ('recibido', 'en_revision', 'entrevista', 'seleccionado', 'descartado');
CREATE TYPE tipo_oferta AS ENUM ('empleo', 'pasantia', 'practicas');
CREATE TYPE modalidad_trabajo AS ENUM ('presencial', 'remoto', 'hibrido');
CREATE TYPE estado_empresa AS ENUM ('pendiente', 'activa', 'rechazada');
CREATE TYPE tipo_evento AS ENUM ('feria_laboral', 'webinar', 'charla', 'curso');
CREATE TYPE tipo_pago AS ENUM ('certificado', 'membresia', 'evento');

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- 1. TABLA USUARIOS (Base para autenticación y control)
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    -- Hash de la contraseña (NUNCA guardar en texto plano)
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL,
    -- Validar correo institucional (ej. @unitru.edu.pe) se hará en aplicación
    email_confirmado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    -- Para recuperación de contraseña
    reset_password_token VARCHAR(255),
    reset_password_expira TIMESTAMP WITH TIME ZONE
);

-- 2. TABLA EGRESADOS (Datos específicos del perfil Egresado)
CREATE TABLE egresados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombres VARCHAR(255) NOT NULL,
    apellido_paterno VARCHAR(255) NOT NULL,
    apellido_materno VARCHAR(255),
    dni CHAR(8) UNIQUE NOT NULL,
    fecha_nacimiento DATE,
    telefono VARCHAR(20),
    direccion TEXT,
    -- Datos académicos principales (se podrían normalizar más)
    carrera_principal VARCHAR(255) NOT NULL,
    facultad VARCHAR(255) NOT NULL,
    anio_egreso INTEGER,
    -- URL o ruta al archivo del CV
    url_cv TEXT,
    -- Perfil público para networking
    perfil_publico BOOLEAN DEFAULT FALSE,
    foto_perfil_url TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABLA EMPRESAS
CREATE TABLE empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ruc CHAR(11) UNIQUE NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    nombre_comercial VARCHAR(255),
    sector_economico VARCHAR(100),
    tamano_empresa VARCHAR(50), -- Ej: 'pequeña', 'mediana', 'grande'
    direccion TEXT,
    telefono_contacto VARCHAR(20),
    email_contacto VARCHAR(255),
    sitio_web VARCHAR(255),
    estado estado_empresa DEFAULT 'pendiente',
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    aprobado_por UUID REFERENCES usuarios(id), -- Administrador que aprobó
    logo_url TEXT
);

-- 4. TABLA EMPLEADORES (Usuarios que representan a una empresa)
CREATE TABLE empleadores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    cargo_en_empresa VARCHAR(100) NOT NULL,
    es_administrador_empresa BOOLEAN DEFAULT FALSE -- Si puede gestionar otros usuarios de la misma empresa
);

-- 5. TABLA OFERTAS LABORALES
CREATE TABLE ofertas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    publicado_por UUID NOT NULL REFERENCES empleadores(id), -- Quién la creó
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    requisitos TEXT,
    tipo tipo_oferta NOT NULL,
    modalidad modalidad_trabajo NOT NULL,
    ubicacion VARCHAR(255),
    salario_min NUMERIC(10,2),
    salario_max NUMERIC(10,2),
    -- Fechas de la oferta
    fecha_publicacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_limite_postulacion DATE NOT NULL,
    -- Estado de la oferta (activa, cerrada, en pausa...)
    activa BOOLEAN DEFAULT TRUE,
    -- Para filtros
    carrera_objetivo VARCHAR(255)[] -- Array de carreras a las que va dirigida
);

-- 6. TABLA POSTULACIONES (Núcleo del proceso de selección)
CREATE TABLE postulaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    oferta_id UUID NOT NULL REFERENCES ofertas(id) ON DELETE CASCADE,
    egresado_id UUID NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    fecha_postulacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    estado estado_postulacion DEFAULT 'recibido',
    -- Mensajes internos de la postulación (simplificado, para un chat se necesitaría otra tabla)
    -- Se puede añadir un campo para la última comunicación o crear tabla mensajes_postulacion
    cv_usado_url TEXT, -- Copia del CV al momento de postular
    -- Campos para seguimiento
    fecha_estado_actual TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    comentario_revision TEXT, -- Comentario del empleador
    UNIQUE(oferta_id, egresado_id) -- Un egresado no puede postular dos veces a la misma oferta
);

-- 7. TABLA EVENTOS
CREATE TABLE eventos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publicado_por UUID NOT NULL REFERENCES usuarios(id), -- Puede ser admin o empleador
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo tipo_evento NOT NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    lugar VARCHAR(255), -- Puede ser virtual (link) o físico
    capacidad_maxima INTEGER,
    es_gratuito BOOLEAN DEFAULT TRUE,
    precio NUMERIC(10,2),
    imagen_promocional_url TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- 8. TABLA INSCRIPCIONES EVENTOS
CREATE TABLE inscripciones_eventos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE, -- Puede ser egresado o empleador
    fecha_inscripcion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    asistio BOOLEAN DEFAULT FALSE,
    -- Relación con pago si el evento es pagado
    pago_id UUID NULL, -- Se agregará la FK después de crear tabla pagos
    UNIQUE(evento_id, usuario_id)
);

-- 9. TABLA PAGOS Y VOUCHERS
CREATE TABLE pagos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    concepto tipo_pago NOT NULL,
    referencia_id UUID, -- ID del evento, certificado, etc. (No es FK estricta por ser polimórfico)
    monto NUMERIC(10,2) NOT NULL,
    fecha_pago TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Datos del voucher
    codigo_voucher VARCHAR(100) UNIQUE, -- Código único legible
    qr_code_data TEXT, -- Texto que irá en el QR (ej. URL de validación + codigo_voucher)
    pdf_voucher_url TEXT, -- Ruta al PDF generado
    pagado BOOLEAN DEFAULT TRUE,
    validado BOOLEAN DEFAULT FALSE -- Si ya se usó para el servicio
);

-- Agregar FK de inscripciones_eventos a pagos
ALTER TABLE inscripciones_eventos ADD CONSTRAINT fk_inscripcion_pago
    FOREIGN KEY (pago_id) REFERENCES pagos(id) ON DELETE SET NULL;

-- 10. TABLA HISTORIAL LABORAL (Egresados)
CREATE TABLE historial_laboral (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    egresado_id UUID NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    empresa_nombre VARCHAR(255) NOT NULL,
    puesto VARCHAR(255) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    es_trabajo_actual BOOLEAN DEFAULT FALSE,
    descripcion TEXT
);

-- 11. TABLA EDUCACION CONTINUA (Egresados)
CREATE TABLE educacion_continua (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    egresado_id UUID NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    institucion VARCHAR(255) NOT NULL,
    titulo_curso VARCHAR(255) NOT NULL,
    nivel VARCHAR(50), -- Ej: 'diplomado', 'maestria', 'curso'
    fecha_inicio DATE,
    fecha_fin DATE,
    documento_url TEXT -- Ruta al certificado
);

-- 12. TABLA ENCUESTAS
CREATE TABLE encuestas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    creada_por UUID REFERENCES usuarios(id) -- El admin que la creó
);

-- 13. TABLA PREGUNTAS (de una encuesta)
CREATE TABLE preguntas_encuesta (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encuesta_id UUID NOT NULL REFERENCES encuestas(id) ON DELETE CASCADE,
    texto_pregunta TEXT NOT NULL,
    tipo_respuesta VARCHAR(50), -- Ej: 'texto', 'opcion_multiple', 'escala'
    opciones JSONB -- Guardar opciones como JSON para preguntas de opción múltiple
);

-- 14. TABLA RESPUESTAS ENCUESTA
CREATE TABLE respuestas_encuesta (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encuesta_id UUID NOT NULL REFERENCES encuestas(id) ON DELETE CASCADE,
    pregunta_id UUID NOT NULL REFERENCES preguntas_encuesta(id) ON DELETE CASCADE,
    egresado_id UUID NOT NULL REFERENCES egresados(id) ON DELETE CASCADE,
    respuesta TEXT, -- La respuesta en texto o el valor seleccionado
    fecha_respuesta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pregunta_id, egresado_id) -- Un egresado responde una vez por pregunta
);

-- 15. TABLA NOTIFICACIONES (Sistema y Email)
CREATE TABLE notificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50), -- 'email', 'sistema'
    asunto VARCHAR(255),
    mensaje TEXT NOT NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_envio TIMESTAMP WITH TIME ZONE,
    metadata JSONB -- Datos adicionales (ej. id de la oferta que generó la notificación)
);

-- 16. TABLA BITACORA DE AUDITORIA (SEGURIDAD)
CREATE TABLE bitacora_auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    perfil_utilizado rol_usuario,
    accion VARCHAR(50) NOT NULL, -- Ej: 'LOGIN', 'CREATE', 'UPDATE', 'DELETE', 'LOGOUT'
    modulo VARCHAR(100), -- Ej: 'ofertas', 'egresados'
    detalle TEXT, -- Descripción de la acción (ej. "Se creó la oferta con ID X")
    direccion_ip INET, -- Dirección IP del usuario
    user_agent TEXT, -- Navegador/cliente usado
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);
CREATE INDEX idx_egresados_carrera ON egresados(carrera_principal);
CREATE INDEX idx_egresados_anio_egreso ON egresados(anio_egreso);
CREATE INDEX idx_ofertas_fecha_publicacion ON ofertas(fecha_publicacion);
CREATE INDEX idx_ofertas_empresa_id ON ofertas(empresa_id);
CREATE INDEX idx_ofertas_carrera_objetivo ON ofertas USING GIN (carrera_objetivo); -- Índice GIN para arrays
CREATE INDEX idx_postulaciones_estado ON postulaciones(estado);
CREATE INDEX idx_postulaciones_egresado_id ON postulaciones(egresado_id);
CREATE INDEX idx_postulaciones_oferta_id ON postulaciones(oferta_id);
CREATE INDEX idx_eventos_fecha_inicio ON eventos(fecha_inicio);
CREATE INDEX idx_pagos_usuario_id ON pagos(usuario_id);
CREATE INDEX idx_bitacora_fecha ON bitacora_auditoria(fecha_hora);
CREATE INDEX idx_bitacora_usuario ON bitacora_auditoria(usuario_id);

-- =====================================================
-- VISTAS ÚTILES (Ejemplos)
-- =====================================================
-- Vista para el dashboard del admin: Conteo de egresados por mes
CREATE VIEW v_egresados_por_mes AS
SELECT
    DATE_TRUNC('month', fecha_registro) AS mes,
    COUNT(*) AS total_egresados
FROM usuarios u
JOIN egresados e ON u.id = e.usuario_id
GROUP BY mes
ORDER BY mes DESC;

-- Vista para ofertas activas con postulaciones
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
