"""
Configuración de pytest para pruebas.
"""
import os
import uuid
from pathlib import Path

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

@pytest.fixture(scope="session")
def test_db():
    """Configura una base de datos de prueba."""
    db_name = "test_egresados_unt_db"

    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cur.execute(f"CREATE DATABASE {db_name}")
    cur.close()
    conn.close()

    conn = psycopg2.connect(
        host="localhost",
        database=db_name,
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    schema_path = Path("database/create_bd.sql")
    with schema_path.open("r", encoding="utf-8") as f:
        cur.execute(f.read())

    conn.commit()
    cur.close()
    conn.close()

    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_NAME"] = db_name
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_PASSWORD"] = "postgres"
    os.environ["DB_PORT"] = "5432"

    import src.config as config_module
    import src.utils.database as database_module

    config_module.DB_CONFIG = {
        "host": "localhost",
        "database": db_name,
        "user": "postgres",
        "password": "postgres",
        "port": "5432",
    }
    database_module.DB_CONFIG = config_module.DB_CONFIG

    if getattr(database_module.DatabasePool, "_pool", None):
        try:
            database_module.DatabasePool._pool.closeall()
        except Exception:
            pass
    database_module.DatabasePool._instance = None
    database_module.DatabasePool._pool = None
    database_module.db_pool = database_module.DatabasePool()

    yield

    if getattr(database_module.DatabasePool, "_pool", None):
        try:
            database_module.DatabasePool._pool.closeall()
        except Exception:
            pass
    database_module.DatabasePool._instance = None
    database_module.DatabasePool._pool = None

    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid()
        """,
        (db_name,),
    )
    cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cur.close()
    conn.close()

@pytest.fixture
def test_user(test_db):
    """Crea un usuario de prueba."""
    from src.auth import hash_password
    from src.models.user import User
    from src.utils.database import get_db_cursor

    email = f"test_{uuid.uuid4().hex[:8]}@unitru.edu.pe"

    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO usuarios (email, password_hash, rol, email_confirmado, activo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (email, hash_password("test123"), "egresado", True, True),
        )
        user_id = cur.fetchone()[0]

    return User.get_by_id(user_id)

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