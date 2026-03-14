"""
Modelos de datos para el sistema de egresados UNT.
Exporta todas las clases de modelos para fácil importación.
"""
from .user import User
from .egresado import Egresado
from .empresa import Empresa
from .empleador import Empleador
from .oferta import Oferta
from .postulacion import Postulacion
from .evento import Evento
from .pago import Pago
from .encuesta import Encuesta

__all__ = [
    'User',
    'Egresado',
    'Empresa',
    'Empleador',
    'Oferta',
    'Postulacion',
    'Evento',
    'Pago',
    'Encuesta'
]