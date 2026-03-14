"""
Pruebas para los modelos de datos.
"""
import pytest
from datetime import datetime, date, timedelta
from src.models.user import User
from src.models.egresado import Egresado
from src.models.empresa import Empresa
from src.models.oferta import Oferta
from src.models.postulacion import Postulacion

class TestEgresado:
    """Pruebas para el modelo Egresado."""
    
    def test_crear_egresado(self, test_user):
        """Prueba la creación de un egresado."""
        egresado = Egresado(
            usuario_id=test_user.id,
            nombres="Juan",
            apellido_paterno="Pérez",
            dni="87654321",
            carrera_principal="Ingeniería Civil",
            facultad="Ingeniería",
            anio_egreso=2021
        )
        egresado_id = egresado.save()
        
        assert egresado_id is not None
        
        # Recuperar y verificar
        retrieved = Egresado.get_by_id(egresado_id)
        assert retrieved.nombre_completo == "Juan Pérez"
        assert retrieved.carrera_principal == "Ingeniería Civil"
    
    def test_completitud_perfil(self, test_egresado):
        """Prueba el cálculo de completitud del perfil."""
        completitud = test_egresado.calcular_completitud_perfil()
        assert 0 <= completitud <= 100
    
    def test_get_postulaciones(self, test_egresado):
        """Prueba obtener postulaciones."""
        postulaciones = test_egresado.get_postulaciones()
        assert isinstance(postulaciones, list)

class TestEmpresa:
    """Pruebas para el modelo Empresa."""
    
    def test_crear_empresa(self):
        """Prueba la creación de una empresa."""
        empresa = Empresa(
            ruc="20123456789",
            razon_social="Empresa Test S.A.C.",
            sector_economico="Tecnología",
            tamano_empresa="pequeña",
            estado="pendiente"
        )
        empresa_id = empresa.save()
        
        assert empresa_id is not None
        
        # Recuperar y verificar
        retrieved = Empresa.get_by_id(empresa_id)
        assert retrieved.ruc == "20123456789"
        assert retrieved.estado == "pendiente"
    
    def test_aprobar_empresa(self, test_empresa, test_admin):
        """Prueba la aprobación de una empresa."""
        test_empresa.aprobar(test_admin.id)
        
        assert test_empresa.estado == "activa"
        assert test_empresa.fecha_aprobacion is not None

class TestOferta:
    """Pruebas para el modelo Oferta."""
    
    def test_crear_oferta(self, test_empresa, test_empleador):
        """Prueba la creación de una oferta."""
        oferta = Oferta(
            empresa_id=test_empresa.id,
            publicado_por=test_empleador.id,
            titulo="Desarrollador Python",
            descripcion="Buscamos desarrollador Python",
            tipo="empleo",
            modalidad="remoto",
            fecha_limite_postulacion=date.today() + timedelta(days=30)
        )
        oferta_id = oferta.save()
        
        assert oferta_id is not None
        
        # Recuperar y verificar
        retrieved = Oferta.get_by_id(oferta_id)
        assert retrieved.titulo == "Desarrollador Python"
        assert retrieved.activa == True
    
    def test_dias_restantes(self, test_oferta):
        """Prueba el cálculo de días restantes."""
        dias = test_oferta.dias_restantes()
        assert dias >= 0

class TestPostulacion:
    """Pruebas para el modelo Postulacion."""
    
    def test_crear_postulacion(self, test_oferta, test_egresado):
        """Prueba la creación de una postulación."""
        postulacion = Postulacion(
            oferta_id=test_oferta.id,
            egresado_id=test_egresado.id
        )
        postulacion_id = postulacion.save()
        
        assert postulacion_id is not None
        
        # Recuperar y verificar
        retrieved = Postulacion.get_by_id(postulacion_id)
        assert retrieved.estado == "recibido"
    
    def test_cambiar_estado(self, test_postulacion):
        """Prueba cambiar estado de postulación."""
        success, message = test_postulacion.cambiar_estado("en_revision")
        
        assert success
        assert test_postulacion.estado == "en_revision"