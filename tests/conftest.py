"""
Configuración de pytest para pruebas.
"""
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.utils.database import get_db_cursor

@pytest.fixture(scope="session")
def test_db():
    """Configura una base de datos de prueba."""
    # Crear base de datos de prueba
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Eliminar si existe
    cur.execute("DROP DATABASE IF EXISTS test_egresados_unt_db")
    cur.execute("CREATE DATABASE test_egresados_unt_db")
    
    cur.close()
    conn.close()
    
    # Conectar a la nueva base de datos y ejecutar schema
    conn = psycopg2.connect(
        host="localhost",
        database="test_egresados_unt_db",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    
    # Leer y ejecutar schema.sql
    with open('database/init.sql', 'r') as f:
        cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()
    
    yield
    
    # Limpiar después de las pruebas
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("DROP DATABASE IF EXISTS test_egresados_unt_db")
    cur.close()
    conn.close()

@pytest.fixture
def test_user():
    """Crea un usuario de prueba."""
    from src.models.user import User
    user = User(
        email="test@unitru.edu.pe",
        rol="egresado",
        email_confirmado=True,
        activo=True
    )
    user.save()
    return user

@pytest.fixture
def test_egresado(test_user):
    """Crea un egresado de prueba."""
    from src.models.egresado import Egresado
    egresado = Egresado(
        usuario_id=test_user.id,
        nombres="Test",
        apellido_paterno="Usuario",
        dni="12345678",
        carrera_principal="Ingeniería de Sistemas",
        facultad="Ingeniería",
        anio_egreso=2020
    )
    egresado.save()
    return egresado