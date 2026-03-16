"""
Utilidades para generación de códigos QR.
"""
import qrcode
import io
import base64
from typing import Optional

class QRGenerator:
    """Generador de códigos QR."""
    
    @staticmethod
    def generate_qr(data: str, box_size: int = 10, border: int = 4) -> bytes:
        """
        Genera un código QR y retorna los bytes de la imagen.
        
        Args:
            data: Datos a codificar en el QR
            box_size: Tamaño de cada caja del QR
            border: Tamaño del borde
        
        Returns:
            bytes: Imagen PNG del QR
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    @staticmethod
    def build_voucher_validation_url(codigo_voucher: str, base_url: str = "https://sistema.unitru.edu.pe") -> str:
        """Construye la URL de validación para un voucher."""
        return f"{base_url}/validar/{codigo_voucher}"

    @staticmethod
    def generate_voucher_qr(codigo_voucher: str, base_url: str = "https://sistema.unitru.edu.pe") -> bytes:
        """
        Genera un QR específico para voucher.
        
        Args:
            codigo_voucher: Código único del voucher
            base_url: URL base para validación
        
        Returns:
            bytes: Imagen PNG del QR
        """
        url = QRGenerator.build_voucher_validation_url(codigo_voucher, base_url)
        return QRGenerator.generate_qr(url)
    
    @staticmethod
    def generate_event_qr(evento_id: str, evento_titulo: str, base_url: str = "https://sistema.unitru.edu.pe") -> bytes:
        """
        Genera un QR para evento.
        
        Args:
            evento_id: ID del evento
            evento_titulo: Título del evento
            base_url: URL base
        
        Returns:
            bytes: Imagen PNG del QR
        """
        data = f"{base_url}/evento/{evento_id}\n{evento_titulo}"
        return QRGenerator.generate_qr(data)
    
    @staticmethod
    def generate_profile_qr(usuario_id: str, nombre: str, base_url: str = "https://sistema.unitru.edu.pe") -> bytes:
        """
        Genera un QR para perfil de egresado.
        
        Args:
            usuario_id: ID del usuario
            nombre: Nombre del egresado
            base_url: URL base
        
        Returns:
            bytes: Imagen PNG del QR
        """
        data = f"{base_url}/perfil/{usuario_id}\n{nombre}"
        return QRGenerator.generate_qr(data)
    
    @staticmethod
    def qr_to_base64(qr_bytes: bytes) -> str:
        """
        Convierte un QR en bytes a base64 para incrustar en HTML.
        
        Args:
            qr_bytes: Bytes de la imagen QR
        
        Returns:
            str: Imagen en base64
        """
        return base64.b64encode(qr_bytes).decode('utf-8')
    
    @staticmethod
    def generate_qr_data_url(data: str) -> str:
        """
        Genera un QR y lo retorna como data URL para HTML.
        
        Args:
            data: Datos a codificar
        
        Returns:
            str: Data URL de la imagen
        """
        qr_bytes = QRGenerator.generate_qr(data)
        b64 = QRGenerator.qr_to_base64(qr_bytes)
        return f"data:image/png;base64,{b64}"

# Instancia global
qr_generator = QRGenerator()