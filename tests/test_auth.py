"""
Pruebas para el módulo de autenticación.
"""
import pytest
from src.auth import hash_password, verify_password, login_usuario
from src.models.user import User

def test_password_hashing():
    """Prueba el hash y verificación de contraseñas."""
    password = "MiContraseña123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_user_creation():
    """Prueba la creación de usuarios."""
    user = User(
        email="nuevo@unitru.edu.pe",
        rol="egresado"
    )
    user_id = user.save()
    
    assert user_id is not None
    
    # Recuperar y verificar
    retrieved = User.get_by_id(user_id)
    assert retrieved.email == "nuevo@unitru.edu.pe"
    assert retrieved.rol == "egresado"

def test_login_success(test_user):
    """Prueba login exitoso."""
    # Primero establecer contraseña
    from src.auth import hash_password
    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE usuarios
            SET password_hash = %s
            WHERE id = %s
        ``, (hash_password("test123"), test_user.id))
    
    user, error = login_usuario("test@unitru.edu.pe", "test123")
    assert user is not None
    assert error is None
    assert user['email'] == "test@unitru.edu.pe"

def test_login_wrong_password(test_user):
    """Prueba login con contraseña incorrecta."""
    user, error = login_usuario("test@unitru.edu.pe", "wrongpass")
    assert user is None
    assert error is not None

def test_login_nonexistent_user():
    """Prueba login con usuario inexistente."""
    user, error = login_usuario("noexiste@unitru.edu.pe", "test123")
    assert user is None
    assert error is not None