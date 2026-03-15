"""
Pruebas para el modelo Encuesta.
"""
import pytest
from datetime import datetime, timedelta
from src.models.encuesta import Encuesta

def test_crear_encuesta(test_db, test_user):
    encuesta = Encuesta(
        titulo="Satisfacción Laboral 2024",
        descripcion="Encuesta anual",
        fecha_inicio=datetime.now().date(),
        fecha_fin=(datetime.now() + timedelta(days=30)).date(),
        activa=True,
        creada_por=test_user.id
    )
    
    encuesta_id = encuesta.save()
    assert encuesta_id is not None
    
    retrieved = Encuesta.get_by_id(encuesta_id)
    assert retrieved.titulo == "Satisfacción Laboral 2024"
    assert retrieved.activa is True

def test_get_activas(test_db, test_user):
    # Crear una encuesta activa
    e1 = Encuesta(
        titulo="Activa",
        descripcion="Encuesta Activa",
        fecha_inicio=datetime.now().date() - timedelta(days=1),
        fecha_fin=(datetime.now() + timedelta(days=30)).date(),
        activa=True,
        creada_por=test_user.id
    )
    e1.save()
    
    activas = Encuesta.get_activas()
    assert len(activas) > 0
    assert any(e.titulo == "Activa" for e in activas)
