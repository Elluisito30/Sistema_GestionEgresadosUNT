"""
Pruebas para el modelo Evento.
"""
import pytest
from datetime import datetime, timedelta
from src.models.evento import Evento

def test_crear_evento(test_db, test_user):
    evento = Evento(
        publicado_por=test_user.id,
        titulo="Feria Laboral 2024",
        descripcion="Gran feria del trabajo para egresados",
        tipo="feria_laboral",
        fecha_inicio=datetime.now() + timedelta(days=10),
        fecha_fin=datetime.now() + timedelta(days=12),
        lugar="Campus Universitario",
        capacidad_maxima=500,
        es_gratuito=True,
        activo=True
    )
    
    evento_id = evento.save()
    assert evento_id is not None
    
    retrieved = Evento.get_by_id(evento_id)
    assert retrieved.titulo == "Feria Laboral 2024"
    assert retrieved.lugar == "Campus Universitario"
    assert retrieved.capacidad_maxima == 500

def test_inscribir_usuario(test_db, test_user):
    evento = Evento(
        publicado_por=test_user.id,
        titulo="Seminario de Python",
        descripcion="Aprende Python",
        tipo="seminario",
        fecha_inicio=datetime.now() + timedelta(days=5),
        fecha_fin=datetime.now() + timedelta(days=6),
        lugar="Auditorio Virtual",
        capacidad_maxima=2,
        es_gratuito=True,
        activo=True
    )
    evento_id = evento.save()
    
    # Inscribir usuario
    success, message = evento.inscribir_usuario(test_user.id)
    assert success is True
    assert message == "Inscripción exitosa"
    
    # Inscribir usuario de nuevo debería fallar
    success2, msg2 = evento.inscribir_usuario(test_user.id)
    assert success2 is False
    assert "Ya estás inscrito" in msg2

def test_cupo_disponible(test_db, test_user):
    evento = Evento(
        publicado_por=test_user.id,
        titulo="Charla VIP",
        descripcion="Solo 1 cupo",
        tipo="charla",
        fecha_inicio=datetime.now() + timedelta(days=1),
        fecha_fin=datetime.now() + timedelta(days=2),
        lugar="Sala de Juntas",
        capacidad_maxima=1,
        es_gratuito=True,
        activo=True
    )
    evento.save()
    
    assert evento.cupo_disponible() is True
    
    # Inscribir 1 persona
    evento.inscribir_usuario(test_user.id)
    
    # No deberia haber cupo
    assert evento.cupo_disponible() is False
