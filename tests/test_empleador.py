"""
Pruebas para el modelo Empleador.
"""
import pytest
from src.models.empleador import Empleador
from src.models.empresa import Empresa
from src.models.user import User

def test_crear_empleador(test_db):
    user = User(
        email="empleador_test@techcorp.com",
        rol="empleador"
    )
    user_id = user.save()

    empresa = Empresa(
        ruc="20987654321",
        razon_social="TechCorp Test",
        sector_economico="Tecnología",
        tamano_empresa="mediana",
        estado="activa"
    )
    empresa_id = empresa.save()

    empleador = Empleador(
        usuario_id=user_id,
        empresa_id=empresa_id,
        nombres="Carlos",
        apellidos="López",
        cargo="Gerente de RRHH",
        telefono="999888777",
        es_administrador_empresa=True
    )
    empleador_id = empleador.save()

    assert empleador_id is not None
    
    retrieved = Empleador.get_by_id(empleador_id)
    assert retrieved.nombre_completo == "Carlos López"
    assert retrieved.cargo == "Gerente de RRHH"
    assert retrieved.puede_publicar_ofertas() is True
