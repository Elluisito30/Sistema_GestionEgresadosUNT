"""
Pruebas para el modelo Pago.
"""
import pytest
from src.models.pago import Pago

def test_crear_pago(test_db, test_user):
    pago = Pago.crear_pago(
        usuario_id=test_user.id,
        concepto="membresia",
        monto=50.00
    )
    
    assert pago is not None
    assert pago.id is not None
    assert pago.codigo_voucher.startswith("VCH-")
    assert pago.concepto == "membresia"
    assert pago.monto == 50.00
    assert pago.pagado is True
    assert pago.validado is False
    assert pago.qr_code_data is not None

def test_validar_pago(test_db, test_user):
    pago = Pago.crear_pago(
        usuario_id=test_user.id,
        concepto="certificado",
        monto=20.00
    )
    
    assert pago.validado is False
    
    # Validar
    success = pago.validar()
    assert success is True
    
    # Comprobar en bd
    retrieved = Pago.get_by_id(pago.id)
    assert retrieved.validado is True

def test_generar_qr(test_db, test_user):
    pago = Pago.crear_pago(
        usuario_id=test_user.id,
        concepto="evento",
        monto=100.00,
        referencia_id="test_uuid" # En un caso real, seria el UUID del evento
    )
    
    qr_bytes = pago.generar_qr()
    assert qr_bytes is not None
    # Leer algo de png header o tamaño
    qr_bytes.seek(0)
    magic = qr_bytes.read(4)
    # Check PNG magic number \x89PNG
    assert magic == b'\x89PNG'
