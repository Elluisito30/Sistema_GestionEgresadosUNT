-- =====================================================
-- SCRIPT DE DATOS INICIALES (SEED) - SISTEMA DE EGRESADOS UNT
-- =====================================================
-- Limpiar tablas antes de insertar
TRUNCATE TABLE
    usuarios, egresados, empresas, empleadores, ofertas, postulaciones, 
    eventos, pagos, inscripciones_eventos, historial_laboral, educacion_continua, 
    encuestas, preguntas_encuesta, respuestas_encuesta, notificaciones, 
    chat_eventos, bitacora_auditoria
RESTART IDENTITY CASCADE;

-- =====================================================
--  USUARIOS (8)
-- =====================================================
-- Esquema de Passwords: <primer_nombre>123
INSERT INTO usuarios (id, email, password_hash, rol, email_confirmado, activo) VALUES
(1, 'admin@unitru.edu.pe', '$2b$12$C9Wxp7hoLkohW8NPQnsEae6BjvJKtCf7p4.vGw9C0H/.GJRyOaRxm', 'administrador', TRUE, TRUE),
(2, 'juan.perez@unitru.edu.pe', '$2b$12$uK7qG4ZYvzZPgHKYHgLIDevRfcuKrSMstFpgoQxTI6scWg9Oamqgy', 'egresado', TRUE, TRUE),
(3, 'rrhh@techandina.com', '$2b$12$IyOnKPfcu9OQjhvqQMMSWuRE09Z2jmb4jzR.HwzNYiXi3QCbf1EZ6', 'empleador', TRUE, TRUE),
(4, 'ana.garcia@unitru.edu.pe', '$2b$12$BCdlYhWdLP4Cn9eDU5KO3OuzT/r52dIvydlxt5CDTyDcH295bQHt.', 'egresado', TRUE, TRUE),
(5, 'luis.rojas@unitru.edu.pe', '$2b$12$fc4XxLzM9bga6erd09DBeOJq1llj7BkdyxZ/YWOmo4lfGFzQfKTAG', 'egresado', TRUE, TRUE),
(6, 'maria.lopez@unitru.edu.pe', '$2b$12$UwqQhWD9j6ZQ.C3/1u3lFOsnEvev482q.jtGz9/rPypNOZ5OMf4QK', 'egresado', TRUE, TRUE),
(7, 'pedro.sanchez@unitru.edu.pe', '$2b$12$kIu0zJwP6T2eHGL0wFlPHOExqRmW/iuqCvcVY3x/YFfRz.8eQ9LhK', 'egresado', TRUE, TRUE),
(8, 'contacto@minerals.pe', '$2b$12$xMZDCjbdlYdW7uYf6fHW3e.ffEX2BqZQU6EKvUZcxY.0Lz6jpFoqy', 'empleador', TRUE, TRUE);

-- =====================================================
--  EMPRESAS (5)
-- =====================================================
INSERT INTO empresas (id, ruc, razon_social, nombre_comercial, sector_economico, tamano_empresa, estado, aprobado_por) VALUES
(1, '20123456789', 'Tech Andina S.A.C.', 'TechAndina', 'Tecnología', 'mediana', 'activa', 1),
(2, '20987654321', 'Minerals Corp Perú S.A.', 'Minerals Corp', 'Minería', 'grande', 'activa', 1),
(3, '20555444333', 'Agroindustrias del Norte S.R.L.', 'AgroNorte', 'Agroindustria', 'grande', 'activa', 1),
(4, '20111222333', 'Consultores Financieros Asociados', 'ConFin', 'Finanzas', 'pequeña', 'pendiente', NULL),
(5, '20777888999', 'SaludTotal Clínica Internacional', 'SaludTotal', 'Salud', 'grande', 'rechazada', 1);

-- =====================================================
--  PERFILES (5 Egresados, 2 Empleadores)
-- =====================================================
INSERT INTO egresados (id, usuario_id, nombres, apellido_paterno, apellido_materno, dni, carrera_principal, facultad, anio_egreso) VALUES
(1, 2, 'Juan', 'Perez', 'Garcia', '12345678', 'Ingeniería de Sistemas', 'Facultad de Ingeniería', 2023),
(2, 4, 'Ana', 'Garcia', 'Torres', '87654321', 'Administración', 'Facultad de Ciencias Económicas', 2022),
(3, 5, 'Luis', 'Rojas', 'Mendoza', '11223344', 'Ingeniería Industrial', 'Facultad de Ingeniería', 2021),
(4, 6, 'Maria', 'Lopez', 'Silva', '44332211', 'Contabilidad', 'Facultad de Ciencias Económicas', 2023),
(5, 7, 'Pedro', 'Sanchez', 'Quispe', '55667788', 'Ingeniería de Sistemas', 'Facultad de Ingeniería', 2022);

INSERT INTO empleadores (id, usuario_id, empresa_id, nombres, apellidos, cargo, es_administrador_empresa) VALUES
(1, 3, 1, 'Carlos', 'Rodriguez', 'Gerente de RRHH', TRUE),
(2, 8, 2, 'Elena', 'Casas', 'Jefe de Reclutamiento', TRUE);

-- =====================================================
--  OFERTAS LABORALES (10)
-- =====================================================
INSERT INTO ofertas (empresa_id, publicado_por, titulo, descripcion, tipo, modalidad, salario_min, salario_max, fecha_limite_postulacion, activa, carrera_objetivo) VALUES
(1, 1, 'Desarrollador Backend Jr (Python)', 'Buscamos un desarrollador Python para nuestro equipo de microservicios.', 'empleo', 'remoto', 2500, 3500, '2026-04-15', TRUE, '{"Ingeniería de Sistemas", "Ingeniería de Software"}'),
(1, 1, 'Analista de Datos Power BI', 'Creación de dashboards y reportes para el área comercial.', 'practicas', 'hibrido', 1200, 1500, '2026-03-30', TRUE, '{"Estadística", "Ingeniería Industrial"}'),
(2, 1, 'Ingeniero de Seguridad Minera', 'Supervisión de protocolos de seguridad en operaciones.', 'empleo', 'presencial', 5000, 7000, '2026-05-01', TRUE, '{"Ingeniería de Minas", "Ingeniería Geológica"}'),
(3, 1, 'Jefe de Control de Calidad', 'Asegurar la calidad de nuestros productos de exportación.', 'empleo', 'presencial', 4500, 6000, '2026-04-20', TRUE, '{"Ingeniería Agroindustrial", "Ingeniería Química"}'),
(1, 1, 'Diseñador UX/UI Senior', 'Liderar el diseño de nuestra nueva app móvil.', 'empleo', 'remoto', 6000, 8000, '2026-03-25', FALSE, '{"Ciencias de la Comunicación"}'),
(2, 1, 'Practicante de Geología', 'Apoyo en el mapeo y análisis de muestras.', 'pasantia', 'presencial', 1500, 1800, '2026-04-10', TRUE, '{"Ingeniería Geológica"}'),
(3, 1, 'Asistente Contable', 'Registro de facturas y apoyo en declaraciones.', 'practicas', 'presencial', 1025, 1300, '2026-04-05', TRUE, '{"Contabilidad y Finanzas"}'),
(1, 1, 'DevOps Engineer', 'Mantenimiento de infraestructura en AWS y CI/CD.', 'empleo', 'remoto', 7000, 9000, '2026-04-18', TRUE, '{"Ingeniería de Sistemas"}'),
(2, 1, 'Supervisor de Medio Ambiente', 'Monitoreo de impacto ambiental en la unidad minera.', 'empleo', 'presencial', 5500, 7500, '2026-05-10', TRUE, '{"Ingeniería Ambiental"}'),
(3, 1, 'Analista de Logística', 'Optimización de la cadena de suministro y exportaciones.', 'practicas', 'hibrido', 1300, 1600, '2026-04-01', FALSE, '{"Ingeniería Industrial"}');

-- =====================================================
--  POSTULACIONES (13)
-- =====================================================
INSERT INTO postulaciones (oferta_id, egresado_id, estado) VALUES
(1, 1, 'recibido'), (2, 1, 'en_revision'), (7, 1, 'entrevista'), (5, 1, 'descartado'), (10, 1, 'recibido'),
(1, 2, 'en_revision'), (8, 2, 'recibido'),
(3, 3, 'recibido'), (9, 3, 'entrevista'),
(4, 4, 'seleccionado'), (7, 4, 'en_revision'),
(8, 5, 'recibido'), (1, 5, 'descartado');

-- =====================================================
--  EVENTOS (4)
-- =====================================================
INSERT INTO eventos (publicado_por, titulo, descripcion, tipo, fecha_inicio, fecha_fin, lugar, es_gratuito, precio) VALUES
(1, 'Feria Laboral de Ingeniería 2026', 'Conecta con las mejores empresas de la región.', 'feria_laboral', '2026-04-25 09:00', '2026-04-26 18:00', 'Ciudad Universitaria UNT', TRUE, 0),
(1, 'Webinar: Tu CV en la era de la IA', 'Aprende a optimizar tu CV con inteligencia artificial.', 'webinar', '2026-03-28 19:00', '2026-03-28 21:00', 'Online - Zoom', TRUE, 0),
(1, 'Curso: Finanzas para Emprendedores', 'Conceptos clave para iniciar tu propio negocio.', 'curso', '2026-05-05 18:00', '2026-05-26 20:00', 'Online - Plataforma UNT', FALSE, 150.00),
(1, 'Charla: El Futuro de la Minería Sostenible', 'Expertos de Minerals Corp comparten su visión.', 'charla', '2026-04-08 16:00', '2026-04-08 18:00', 'Auditorio de Geología', TRUE, 0),
(1, 'Workshop: Liderazgo y Trabajo en Equipo', 'Desarrolla habilidades blandas críticas para el éxito laboral.', 'curso', '2026-06-15 09:00', '2026-06-15 13:00', 'Centro de Idiomas UNT', FALSE, 80.00),
(1, 'Seminario: Innovación Tecnológica 2025', 'Tendencias emergentes en IA y computación cuántica.', 'charla', '2025-10-15 09:00', '2025-10-15 18:00', 'Auditorio Copérnico - UNT', TRUE, 0);

-- =====================================================
--  INSCRIPCIONES A EVENTOS (4)
-- =====================================================
INSERT INTO inscripciones_eventos (evento_id, usuario_id, asistio) VALUES
(1, 2, FALSE), (2, 2, FALSE), (4, 2, FALSE), (6, 2, TRUE);

-- =====================================================
--  HISTORIAL LABORAL Y ACADÉMICO
-- =====================================================
-- Juan Perez (ID 1)
INSERT INTO historial_laboral (egresado_id, empresa_nombre, puesto, fecha_inicio, fecha_fin, es_trabajo_actual) VALUES
(1, 'Bodega Don Pepe', 'Asistente de Caja', '2021-01-15', '2022-12-20', FALSE),
(1, 'Tech Solutions S.R.L.', 'Practicante de Desarrollo Web', '2023-03-01', '2023-08-31', FALSE);

INSERT INTO educacion_continua (egresado_id, institucion, titulo_curso, nivel, fecha_fin) VALUES
(1, 'Platzi', 'Curso de Python Profesional', 'curso', '2023-11-10'),
(1, 'Coderhouse', 'Diplomado en Data Science', 'diplomado', '2024-02-20');

-- Ana Garcia (ID 2)
INSERT INTO historial_laboral (egresado_id, empresa_nombre, puesto, fecha_inicio, fecha_fin, es_trabajo_actual) VALUES
(2, 'Banco de la Nación', 'Asistente Administrativo', '2022-05-01', NULL, TRUE);

INSERT INTO educacion_continua (egresado_id, institucion, titulo_curso, nivel, fecha_fin) VALUES
(2, 'ESAN', 'Gestión Pública Moderna', 'curso', '2023-08-15');

-- Luis Rojas (ID 3)
INSERT INTO historial_laboral (egresado_id, empresa_nombre, puesto, fecha_inicio, fecha_fin, es_trabajo_actual) VALUES
(3, 'Cervecería Backus', 'Analista de Procesos', '2021-02-10', '2023-12-30', FALSE);

INSERT INTO educacion_continua (egresado_id, institucion, titulo_curso, nivel, fecha_fin) VALUES
(3, 'PUCP', 'Lean Six Sigma Green Belt', 'diplomado', '2022-11-20');

-- Maria Lopez (ID 4)
INSERT INTO historial_laboral (egresado_id, empresa_nombre, puesto, fecha_inicio, fecha_fin, es_trabajo_actual) VALUES
(4, 'Estudio Contable ABC', 'Auxiliar Contable', '2023-01-15', NULL, TRUE);

-- Pedro Sanchez (ID 5)
INSERT INTO historial_laboral (egresado_id, empresa_nombre, puesto, fecha_inicio, fecha_fin, es_trabajo_actual) VALUES
(5, 'Siderperu', 'Desarrollador Jr', '2022-08-01', NULL, TRUE);

-- =====================================================
--  ENCUESTAS Y PREGUNTAS (2)
-- =====================================================
INSERT INTO encuestas (id, titulo, descripcion, fecha_inicio, fecha_fin, creada_por) VALUES
(1, 'Encuesta de Satisfacción Anual 2025', 'Mide la satisfacción de los egresados con los servicios de la bolsa de trabajo.', '2025-12-01', '2025-12-31', 1);

INSERT INTO preguntas_encuesta (encuesta_id, texto_pregunta, tipo_respuesta, opciones) VALUES
(1, 'En una escala del 1 al 5, ¿qué tan útil ha sido la plataforma para tu desarrollo profesional?', 'escala', '["1", "2", "3", "4", "5"]'),
(1, '¿Qué nueva funcionalidad te gustaría ver en el sistema?', 'texto', NULL);

-- =====================================================
--  REAJUSTE DE SECUENCIAS
-- =====================================================
SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));
SELECT setval('egresados_id_seq', (SELECT MAX(id) FROM egresados));
SELECT setval('empresas_id_seq', (SELECT MAX(id) FROM empresas));
SELECT setval('empleadores_id_seq', (SELECT MAX(id) FROM empleadores));
SELECT setval('ofertas_id_seq', (SELECT MAX(id) FROM ofertas));
SELECT setval('postulaciones_id_seq', (SELECT MAX(id) FROM postulaciones));
SELECT setval('eventos_id_seq', (SELECT MAX(id) FROM eventos));
SELECT setval('inscripciones_eventos_id_seq', (SELECT MAX(id) FROM inscripciones_eventos));
SELECT setval('historial_laboral_id_seq', (SELECT MAX(id) FROM historial_laboral));
SELECT setval('educacion_continua_id_seq', (SELECT MAX(id) FROM educacion_continua));
SELECT setval('encuestas_id_seq', (SELECT MAX(id) FROM encuestas));
SELECT setval('preguntas_encuesta_id_seq', (SELECT MAX(id) FROM preguntas_encuesta));
