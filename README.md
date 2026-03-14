# Sistema de Gestión de Egresados y Oferta Laboral - UNT
 
Este proyecto es un sistema integral para conectar a la Universidad Nacional de Trujillo (UNT) con sus egresados y el sector empleador. Desarrollado con Python (Streamlit) y PostgreSQL, y empaquetado con Docker.
 
---
 
## Tecnologías Utilizadas
 
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** [PostgreSQL](https://www.postgresql.org/)
- **Contenedorización:** [Docker](https://www.docker.com/) y Docker Compose
- **Lenguaje:** Python 3.10+
 
---
 
## Requisitos Previos
 
- Tener instalado [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/) (incluido en Docker Desktop).
- (Opcional) Git para clonar el repositorio.
 
---
 
## Cómo Ejecutar el Sistema Localmente
 
Sigue estos pasos para levantar el entorno completo:
 
### 1. Clona el repositorio (o descarga los archivos)
 
```bash
git clone <url-del-repositorio>
cd egresados_unt_app
```
 
### 2. Inicia los servicios con Docker Compose
 
```bash
docker-compose up -d
```
 
> Este comando descargará las imágenes necesarias (PostgreSQL, pgAdmin) y construirá la imagen de la aplicación Streamlit. La primera vez puede tomar varios minutos.
 
### 3. Accede a la aplicación
 
| Servicio | URL |
|---|---|
| Aplicación Web | http://localhost:8501 |
| pgAdmin (Gestor BD) | http://localhost:5050 |
 
**Credenciales de pgAdmin:**
- Email: `admin@admin.com`
- Contraseña: `admin`
 
**Para conectar al servidor de BD desde pgAdmin:**
 
| Campo | Valor |
|---|---|
| Host | `db` |
| Port | `5432` |
| Database | `egresados_unt_db` |
| User | `postgres` |
| Password | `postgres` |
 
---
 
## Credenciales de Prueba (Base de Datos Inicial)
 
Después de ejecutar el script `database/init.sql`, se pueden usar los siguientes usuarios de prueba:
 
| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin@unitru.edu.pe` | `admin123` |
| Egresado | `juan.perez@unitru.edu.pe` | `egresado123` |
| Empleador | `contacto@techcorp.com` | `empresa123` |
 
> **Nota:** La empresa empleadora debe estar activa en el sistema. En un entorno real, las contraseñas deben ser mucho más seguras.
 
---
 
## Estructura del Proyecto
 
```
egresados_unt_app/
├── app.py                  # Punto de entrada de la aplicación
├── src/                    # Lógica de la aplicación (autenticación, páginas, utilidades)
├── database/
│   └── init.sql            # Script SQL para crear el esquema de la base de datos
├── docker-compose.yml      # Orquestación de servicios (app, db, pgadmin)
└── Dockerfile              # Definición de la imagen de la aplicación
```
 
---
 
## Detener el Sistema
 
Para detener y eliminar los contenedores:
 
```bash
docker-compose down
```
 
Para también eliminar los volúmenes de la base de datos (**¡esto borrará todos los datos!**):
 
```bash
docker-compose down -v
```
 
---
 
## Advertencias y Buenas Prácticas
 
1. **Seguridad de Contraseñas:** Las contraseñas usadas en el `docker-compose.yml` son débiles (`postgres`, `admin`). Esto es **inaceptable en producción**. Usa variables de entorno o un sistema de secretos (Docker Swarm secrets, HashiCorp Vault, etc.) para gestionar credenciales.
 
2. **Validación de Entradas:** Es crucial implementar una validación robusta en **todos** los formularios para prevenir inyección SQL y XSS. Psycopg2, usado correctamente con `%s`, ya protege contra inyección SQL, pero se deben validar los tipos de datos.
 
3. **Manejo de Sesiones:** `st.session_state` es seguro dentro de una sesión de usuario, pero no es un sustituto de una gestión de sesiones backend robusta si la aplicación escalara a múltiples réplicas.
 
4. **Rendimiento:** El dashboard del administrador puede ralentizarse si la base de datos crece. Las vistas materializadas y el decorador `st.cache_data` son aliados clave para mejorar el rendimiento de consultas pesadas.
 
5. **Manejo de Errores:** Cada llamada a la base de datos debe estar envuelta en bloques `try...except` para mostrar mensajes amigables al usuario y registrar errores técnicos en un archivo de log.
 
6. **Código QR en Vouchers:** La generación de QR debe incluir un identificador único y una URL de validación (ej. `https://tudominio.com/validar?code=UUID`) para verificar autenticidad sin necesidad de buscar por texto completo.
 