-- =====================================================
-- SCRIPT DE DATOS DE PRUEBA - SISTEMA DE EGRESADOS UNT
-- =====================================================

-- Insertar roles de usuario (si no se usan ENUMs)
-- INSERT INTO roles (nombre) VALUES ('administrador'), ('egresado'), ('empleador');

-- Insertar usuarios de prueba
-- Nota: Las contraseñas están hasheadas con bcrypt. La contraseña es el nombre + '123'
-- Ejemplo: admin123, juan123, etc.

-- Administrador
INSERT INTO usuarios (id, email, password_hash, rol, email_confirmado, activo) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'admin@unitru.edu.pe',
    '$2b$12$mz4oGy4BEI9iDs3o5vwrO.A0R9Y1H.nx9GczuRZYAW6Nm46vnqUry', -- admin123
    'administrador',
    TRUE,
    TRUE
);

-- Egresados
INSERT INTO usuarios (id, email, password_hash, rol, email_confirmado, activo) VALUES
(
    '22222222-2222-2222-2222-222222222222',
    'juan.perez@unitru.edu.pe',
    '$2b$12$GzyTAxacPo/ZRvTadyeyD.JkinOyFb0jQXIcE96GRT9TA8zSLPeLK', -- juan123
    'egresado',
    TRUE,
    TRUE
),
(
    '33333333-3333-3333-3333-333333333333',
    'maria.lopez@unitru.edu.pe',
    '$2b$12$iI7I9ky8y.GJ/gz16jf8UOXQZmVx1bM43KU5XcslRg0wnsGg/caAC', -- maria123
    'egresado',
    TRUE,
    TRUE
),
(
    '44444444-4444-4444-4444-444444444444',
    'carlos.rodriguez@unitru.edu.pe',
    '$2b$12$vO18vjQfG3/r1HKBCRaDke/BwjsZxZ7VGPGTZ.bAqOyD3y8MD2jE2', -- carlos123
    'egresado',
    TRUE,
    TRUE
);

-- Empresas
INSERT INTO empresas (id, ruc, razon_social, nombre_comercial, sector_economico, 
                      tamano_empresa, direccion, telefono_contacto, email_contacto, 
                      sitio_web, estado) VALUES
(
    '55555555-5555-5555-5555-555555555555',
    '20123456789',
    'Tecnología Andina S.A.C.',
    'TechAndina',
    'Tecnología',
    'mediana',
    'Av. España 123, Trujillo',
    '044-123456',
    'contacto@techandina.com',
    'www.techandina.com',
    'activa'
),
(
    '66666666-6666-6666-6666-666666666666',
    '20456789012',
    'Clínica San Pablo S.A.C.',
    'San Pablo Salud',
    'Salud',
    'grande',
    'Av. América Sur 456, Trujillo',
    '044-789012',
    'rrhh@sanpablo.com',
    'www.sanpablo.com',
    'activa'
),
(
    '77777777-7777-7777-7777-777777777777',
    '20567890123',
    'Constructora Norte S.A.C.',
    'Conorte',
    'Construcción',
    'pequeña',
    'Calle Bolívar 789, Trujillo',
    '044-345678',
    'info@conorte.com',
    'www.conorte.com',
    'pendiente'
);

-- Empleadores (usuarios de empresas)
INSERT INTO empleadores (id, usuario_id, empresa_id, nombres, apellidos, cargo, es_administrador_empresa) VALUES
(
    '88888888-8888-8888-8888-888888888888',
    '11111111-1111-1111-1111-111111111111', -- Este es el admin, pero también podría ser empleador
    '55555555-5555-5555-5555-555555555555',
    'Roberto',
    'García Mendoza',
    'Gerente de RRHH',
    TRUE
);

-- Crear usuarios para empleadores (primero insertar en usuarios)
INSERT INTO usuarios (id, email, password_hash, rol, email_confirmado, activo) VALUES
(
    '99999999-9999-9999-9999-999999999999',
    'rrhh@techandina.com',
    '$2b$12$K.xAfE5ns1vq2yADPfLnZuE4TnFS0ugcK.s78E0tTHRLAOSB23NKG', -- empleador123
    'empleador',
    TRUE,
    TRUE
),
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'seleccion@sanpablo.com',
    '$2b$12$K.xAfE5ns1vq2yADPfLnZuE4TnFS0ugcK.s78E0tTHRLAOSB23NKG', -- empleador123
    'empleador',
    TRUE,
    TRUE
);

-- Agregar los empleadores restantes
INSERT INTO empleadores (id, usuario_id, empresa_id, nombres, apellidos, cargo, es_administrador_empresa) VALUES
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '99999999-9999-9999-9999-999999999999',
    '55555555-5555-5555-5555-555555555555',
    'Ana',
    'Martínez López',
    'Coordinadora de Selección',
    FALSE
),
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '66666666-6666-6666-6666-666666666666',
    'Pedro',
    'Sánchez Torres',
    'Jefe de Personal',
    TRUE
);

-- Datos de egresados
INSERT INTO egresados (id, usuario_id, nombres, apellido_paterno, apellido_materno,
                      dni, fecha_nacimiento, telefono, direccion, carrera_principal,
                      facultad, anio_egreso, perfil_publico) VALUES
(
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    '22222222-2222-2222-2222-222222222222',
    'Juan Carlos',
    'Pérez',
    'Gutiérrez',
    '12345678',
    '1995-05-15',
    '987654321',
    'Urb. Primavera Mz A Lt 12, Trujillo',
    'Ingeniería de Sistemas',
    'Ingeniería',
    2018,
    TRUE
),
(
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    '33333333-3333-3333-3333-333333333333',
    'María Isabel',
    'López',
    'Fernández',
    '23456789',
    '1996-08-22',
    '976543210',
    'Av. Larco 456, Trujillo',
    'Administración de Empresas',
    'Ciencias Económicas',
    2019,
    TRUE
),
(
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '44444444-4444-4444-4444-444444444444',
    'Carlos Alberto',
    'Rodríguez',
    'Mendoza',
    '34567890',
    '1994-11-30',
    '965432109',
    'Calle San Martín 789, Trujillo',
    'Contabilidad',
    'Ciencias Económicas',
    2017,
    FALSE
);

-- Ofertas laborales
INSERT INTO ofertas (id, empresa_id, publicado_por, titulo, descripcion, requisitos,
                    tipo, modalidad, ubicacion, salario_min, salario_max,
                    fecha_publicacion, fecha_limite_postulacion, activa, carrera_objetivo) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    '55555555-5555-5555-5555-555555555555',
    '88888888-8888-8888-8888-888888888888',
    'Desarrollador Python Senior',
    'Buscamos un desarrollador Python con experiencia en desarrollo web y análisis de datos para unirse a nuestro equipo de innovación.',
    'Requisitos:
    - Mínimo 3 años de experiencia con Python
    - Conocimientos de Django/Flask
    - Experiencia con bases de datos SQL
    - Inglés intermedio
    - Deseable conocimiento en Machine Learning',
    'empleo',
    'hibrido',
    'Trujillo',
    3500,
    5000,
    CURRENT_DATE - INTERVAL '5 days',
    CURRENT_DATE + INTERVAL '25 days',
    TRUE,
    ARRAY['Ingeniería de Sistemas', 'Ingeniería Informática']
),
(
    '22222222-2222-2222-2222-222222222222',
    '66666666-6666-6666-6666-666666666666',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'Asistente Administrativo',
    'Importante clínica busca asistente administrativo para área de admisión y archivo.',
    'Requisitos:
    - Egresado de Administración o carreras afines
    - Conocimiento de Office
    - Experiencia en atención al cliente
    - Disponibilidad para trabajar en horarios rotativos',
    'pasantia',
    'presencial',
    'Trujillo',
    1025,
    1200,
    CURRENT_DATE - INTERVAL '2 days',
    CURRENT_DATE + INTERVAL '15 days',
    TRUE,
    ARRAY['Administración de Empresas', 'Contabilidad']
),
(
    '33333333-3333-3333-3333-333333333333',
    '55555555-5555-5555-5555-555555555555',
    '88888888-8888-8888-8888-888888888888',
    'Prácticas en Desarrollo Web',
    'Buscamos practicante de sistemas para apoyo en desarrollo de aplicaciones web.',
    'Requisitos:
    - Estudiante de últimos ciclos de Sistemas o Informática
    - Conocimientos básicos de HTML, CSS, JavaScript
    - Interés en aprender Django
    - Horario flexible',
    'practicas',
    'remoto',
    'Remoto',
    800,
    1000,
    CURRENT_DATE - INTERVAL '10 days',
    CURRENT_DATE + INTERVAL '10 days',
    TRUE,
    ARRAY['Ingeniería de Sistemas', 'Ingeniería Informática', 'Ciencias de la Computación']
);

-- Postulaciones
INSERT INTO postulaciones (id, oferta_id, egresado_id, estado, fecha_postulacion) VALUES
(
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'en_revision',
    CURRENT_DATE - INTERVAL '4 days'
),
(
    '55555555-5555-5555-5555-555555555555',
    '11111111-1111-1111-1111-111111111111',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'recibido',
    CURRENT_DATE - INTERVAL '2 days'
),
(
    '66666666-6666-6666-6666-666666666666',
    '22222222-2222-2222-2222-222222222222',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'entrevista',
    CURRENT_DATE - INTERVAL '6 days'
);

-- Eventos (Fechas actualizadas a 2026 para pruebas)
INSERT INTO eventos (id, publicado_por, titulo, descripcion, tipo,
                    fecha_inicio, fecha_fin, lugar, capacidad_maxima,
                    es_gratuito, precio, activo) VALUES
(
    '99999999-9999-9999-9999-999999999999',
    '11111111-1111-1111-1111-111111111111',
    'Seminario de Liderazgo y Empleabilidad 2026',
    'Un evento magistral enfocado en las nuevas tendencias del mercado laboral y el desarrollo de habilidades blandas para egresados de la UNT.',
    'webinar',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day',
    'Plataforma Zoom Institucional',
    100,
    TRUE,
    NULL,
    TRUE
),
(
    '88888888-8888-8888-8888-888888888888',
    '11111111-1111-1111-1111-111111111111',
    'Feria Laboral de Ingeniería 2026',
    'Conecta con las mejores empresas del sector tecnológico e industrial. Trae tu CV actualizado.',
    'feria_laboral',
    NOW() + INTERVAL '7 days',
    NOW() + INTERVAL '7 days' + INTERVAL '8 hours',
    'Coliseo Multiusos UNT',
    500,
    TRUE,
    NULL,
    TRUE
),
(
    '77777777-7777-7777-7777-777777777777',
    '11111111-1111-1111-1111-111111111111',
    'Taller: Estrategias de Networking en LinkedIn',
    'Aprende a potenciar tu perfil profesional y generar contactos de valor en la red profesional más grande del mundo.',
    'curso',
    NOW() - INTERVAL '1 hour',
    NOW() + INTERVAL '2 hours',
    'Plataforma Microsoft Teams',
    50,
    FALSE,
    50.00,
    TRUE
);

-- Inscripciones a eventos
INSERT INTO inscripciones_eventos (id, evento_id, usuario_id, fecha_inscripcion, asistio) VALUES
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '99999999-9999-9999-9999-999999999999',
    '22222222-2222-2222-2222-222222222222',
    NOW() - INTERVAL '3 days',
    TRUE
),
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '77777777-7777-7777-7777-777777777777',
    '22222222-2222-2222-2222-222222222222',
    NOW() - INTERVAL '2 days',
    FALSE
);

-- Historial laboral
INSERT INTO historial_laboral (id, egresado_id, empresa_nombre, puesto,
                              fecha_inicio, fecha_fin, es_trabajo_actual,
                              descripcion) VALUES
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'TechSolutions S.A.C.',
    'Desarrollador Junior',
    '2019-01-15',
    '2021-03-30',
    FALSE,
    'Desarrollo de aplicaciones web con Python y Django'
),
(
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Innovación Digital S.A.C.',
    'Desarrollador Semi-Senior',
    '2021-04-01',
    NULL,
    TRUE,
    'Líder de equipo de desarrollo backend'
);

-- Educación continua
INSERT INTO educacion_continua (id, egresado_id, institucion, titulo_curso,
                               nivel, fecha_inicio, fecha_fin) VALUES
(
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'Universidad Nacional de Ingeniería',
    'Diplomado en Ciencia de Datos',
    'diplomado',
    '2022-01-10',
    '2022-07-15'
),
(
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'ESAN',
    'Maestría en Administración de Empresas',
    'maestria',
    '2021-03-01',
    NULL
);

-- Encuestas
INSERT INTO encuestas (id, titulo, descripcion, fecha_inicio, fecha_fin, activa, creada_por) VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'Encuesta de Seguimiento a Graduados 2024',
    'Encuesta para conocer la situación laboral actual de nuestros egresados.',
    CURRENT_DATE - INTERVAL '10 days',
    CURRENT_DATE + INTERVAL '20 days',
    TRUE,
    '11111111-1111-1111-1111-111111111111'
);

-- Preguntas de encuesta
INSERT INTO preguntas_encuesta (id, encuesta_id, texto_pregunta, tipo_respuesta, opciones) VALUES
(
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    '¿Cuál es su situación laboral actual?',
    'opcion_multiple',
    '["Trabajando tiempo completo", "Trabajando medio tiempo", "Buscando empleo", "Estudiando", "Independiente"]'
),
(
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    '¿Su trabajo actual está relacionado con su carrera?',
    'opcion_multiple',
    '["Sí, directamente relacionado", "Sí, parcialmente relacionado", "No está relacionado"]'
),
(
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    'Rango salarial mensual (en soles)',
    'opcion_multiple',
    '["Menos de 1000", "1000 - 2000", "2001 - 3000", "3001 - 5000", "Más de 5000"]'
);

-- Notificaciones
INSERT INTO notificaciones (id, usuario_id, tipo, asunto, mensaje, leida, fecha_creacion) VALUES
(
    '55555555-5555-5555-5555-555555555555',
    '22222222-2222-2222-2222-222222222222',
    'sistema',
    'Nueva oferta recomendada',
    'Hay nuevas ofertas de trabajo que coinciden con tu perfil',
    FALSE,
    NOW() - INTERVAL '1 day'
),
(
    'aaaaaaaa-1111-2222-3333-444444444444',
    '22222222-2222-2222-2222-222222222222',
    'sistema',
    'Actualización de postulación',
    'Tu postulación a "Desarrollador Python Senior" ha pasado a estado "En revisión"',
    TRUE,
    NOW() - INTERVAL '2 days'
);

-- Chat de Eventos (Networking)
INSERT INTO chat_eventos (evento_id, usuario_id, mensaje, fecha_envio) VALUES
('77777777-7777-7777-7777-777777777777', '11111111-1111-1111-1111-111111111111', 'Bienvenidos al taller de LinkedIn!', NOW() - INTERVAL '45 minutes'),
('77777777-7777-7777-7777-777777777777', '22222222-2222-2222-2222-222222222222', 'Hola! Muchas gracias por el evento.', NOW() - INTERVAL '30 minutes');

-- Insertar registros en bitácora (Auditoría)
INSERT INTO bitacora_auditoria (usuario_id, perfil_utilizado, accion, modulo, detalle, fecha_hora) VALUES
('11111111-1111-1111-1111-111111111111', 'administrador', 'LOGIN', 'autenticacion', 'Login exitoso', NOW() - INTERVAL '1 day'),
('22222222-2222-2222-2222-222222222222', 'egresado', 'LOGIN', 'autenticacion', 'Login exitoso', NOW() - INTERVAL '12 hours'),
('22222222-2222-2222-2222-222222222222', 'egresado', 'ACCESO_MODULO', 'eventos', 'Usuario consultó el calendario de eventos', NOW() - INTERVAL '1 hour'),
('11111111-1111-1111-1111-111111111111', 'administrador', 'CREACION', 'eventos', 'Se creó el evento: Seminario de Liderazgo', NOW() - INTERVAL '2 days');

-- =====================================================
-- FIN DEL SCRIPT DE DATOS DE PRUEBA
-- =====================================================