# Sistema de Gestión de Egresados y Oferta Laboral - UNT
 
Este proyecto es un sistema integral para conectar a la Universidad Nacional de Trujillo (UNT) con sus egresados y el sector empleador. Desarrollado con Python (Streamlit) y PostgreSQL, y empaquetado con Docker.
 
---
 
## Tecnologías Utilizadas
 
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** [PostgreSQL](https://www.postgresql.org/)
- **Contenedorización:** [Docker](https://www.docker.com/) y Docker Compose
- **Lenguaje:** Python 3.10+
- **Librerías Clave:** Pandas, Plotly, OpenPyXL, Bcrypt, Psycopg2
 
---
 
## Requisitos Previos
 
- Tener instalado [Docker Desktop](https://docs.docker.com/get-docker/) (incluye Docker Compose).
- Navegador web moderno (Chrome, Edge, Firefox).
 
---
 
## Cómo Ejecutar el Sistema Localmente
 
Sigue estos pasos para levantar el entorno completo:
 
### 1. Preparar el entorno
 
Clona el repositorio y crea tu archivo de configuración:
 
```powershell
# Clonar repositorio (o descargar archivos)
cd Sistema_GestionEgresadosUNT

# Crear archivo .env desde el ejemplo
Copy-Item .env.example .env
```
 
### 2. Iniciar los servicios con Docker Compose
 
```powershell
docker-compose up -d --build
```
 
> **Nota:** El flag `--build` asegura que se apliquen los últimos cambios realizados en el código Python. 
> 
> En el primer arranque, Docker ejecutará automáticamente los scripts en orden:
> 1. `database/create_bd.sql`: Crea las tablas, tipos ENUM e índices.
> 2. `database/seed_bd.sql`: Carga todos los datos de prueba (usuarios, egresados, empresas, ofertas).

### 3. Si necesitas reiniciar la base de datos (Limpieza Total)

Si has modificado la estructura de las tablas o quieres limpiar todos los datos para volver al estado inicial:

```powershell
docker-compose down -v
docker-compose up -d --build
```
*El parámetro `-v` es fundamental ya que elimina el volumen persistente de la base de datos.*

### 4. Actualizar solo los datos (Seed Manual)

Si el contenedor ya está corriendo y solo quieres refrescar los datos de prueba sin borrar las tablas:

```powershell
Get-Content database/seed_bd.sql | docker exec -i bd_egresadosUNT psql -U postgres -d bd_egresadosUNT
```
 
---

## Credenciales de Prueba (Actualizadas)
 
El sistema cuenta con un esquema de contraseñas unificado para las cuentas de prueba: `<primer_nombre>123` (todo en minúsculas).
 
| Rol | Usuario (Email) | Contraseña |
|---|---|---|
| **Administrador** | `admin@unitru.edu.pe` | `admin123` |
| **Egresado 1** | `juan.perez@unitru.edu.pe` | `juan123` |
| **Egresado 2** | `ana.garcia@unitru.edu.pe` | `ana123` |
| **Egresado 3** | `luis.rojas@unitru.edu.pe` | `luis123` |
| **Egresado 4** | `maria.lopez@unitru.edu.pe` | `maria123` |
| **Egresado 5** | `pedro.sanchez@unitru.edu.pe` | `pedro123` |
| **Empleador 1** | `rrhh@techandina.com` | `empleador123` |
| **Empleador 2** | `contacto@minerals.pe` | `elena123` |
 
---

## Módulos Principales Implementados
 
- **Navegación Dinámica**: Menú lateral persistente que carga módulos bajo demanda según el rol del usuario.
- **Gestión de Egresados (Admin)**: 
    - **Visualización**: Listado de solo lectura con métricas en tiempo real.
    - **Registro**: Formulario para dar de alta nuevos alumnos.
    - **Edición**: Formulario tradicional con validaciones y botones de guardar/cancelar.
- **Consultas Avanzadas**: Buscador multivariante con persistencia de resultados y exportación a **Excel** y **PDF** (corregido para zonas horarias).
- **Dashboard Estadístico**: Gráficos interactivos de tendencia de registros y métricas de impacto.
- **Gestión de Ofertas Laborales**:
    - **Postulación y Seguimiento**: Los egresados pueden postular a ofertas y ver su historial de postulaciones.
    - **Egresado Emprendedor**: Permite que los egresados publiquen sus propios emprendimientos u ofertas laborales.
- **Sistema de Encuestas de Seguimiento**:
    - **Diseño Dinámico (Admin)**: Creación de encuestas con múltiples tipos de preguntas (Texto, Opción Múltiple, Escala 1-10).
    - **Plantillas Predefinidas**: Generación rápida de encuestas laborales, académicas y de satisfacción.
    - **Módulo de Respuesta (Egresado)**: Interfaz interactiva con barra de progreso, guardado de borradores y validación de campos obligatorios.
- **Pagos y Certificados**:
    - **Generación de Vouchers**: Formato estándar simplificado con **Código QR** para validación institucional.
    - **Certificados Automáticos**: Emisión de certificados PDF tras la finalización y asistencia confirmada a eventos.
 
---
 
## Estructura del Proyecto
 
```
Sistema_GestionEgresadosUNT/
├── app.py                  # Punto de entrada y Enrutador Dinámico
├── src/                    # Lógica central
│   ├── pages/              # Módulos de la aplicación (Egresados, Empresas, etc.)
│   ├── utils/              # Generadores de Excel/PDF, Gestión de Sesión y BD
│   ├── models/             # Modelos de datos (Egresado, Empresa, etc.)
│   └── auth.py             # Lógica de autenticación y hashing
├── database/
│   ├── create_bd.sql       # Esquema de base de datos (Tablas/Vistas)
│   └── seed_bd.sql         # Datos de prueba (Seed completo)
├── docker-compose.yml      # Orquestación (App + PostgreSQL + pgAdmin)
└── Dockerfile              # Configuración del entorno Python
```
 
---
 
## Soporte y Mantenimiento
 
Para ver los registros de errores en tiempo real:
```bash
docker logs -f Sistema_GestionEgresadosUNT
```

Para acceder a la base de datos visualmente (pgAdmin): [http://localhost:5050](http://localhost:5050)
- Usuario: `admin@admin.com` | Clave: `postgres`
