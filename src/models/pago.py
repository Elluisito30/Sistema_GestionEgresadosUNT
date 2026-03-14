"""
Modelo de Pago para el sistema.
Representa un pago realizado por un usuario.
"""
from datetime import datetime
from src.utils.database import get_db_cursor
import uuid
import qrcode
import io

class Pago:
    """Clase que representa un pago."""
    
    def __init__(self, id=None, usuario_id=None, concepto=None,
                 referencia_id=None, monto=None, fecha_pago=None,
                 codigo_voucher=None, qr_code_data=None,
                 pdf_voucher_url=None, pagado=True, validado=False):
        self.id = id
        self.usuario_id = usuario_id
        self.concepto = concepto
        self.referencia_id = referencia_id
        self.monto = monto
        self.fecha_pago = fecha_pago or datetime.now()
        self.codigo_voucher = codigo_voucher
        self.qr_code_data = qr_code_data
        self.pdf_voucher_url = pdf_voucher_url
        self.pagado = pagado
        self.validado = validado
    
    @classmethod
    def get_by_id(cls, pago_id):
        """Obtiene un pago por su ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM pagos WHERE id = %s", (pago_id,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def get_by_usuario(cls, usuario_id, limit=50):
        """Obtiene pagos de un usuario."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM pagos
                WHERE usuario_id = %s
                ORDER BY fecha_pago DESC
                LIMIT %s
            ``, (usuario_id, limit))
            
            columns = [desc[0] for desc in cur.description]
            return [cls(*row) for row in cur.fetchall()]
    
    @classmethod
    def get_by_voucher(cls, codigo_voucher):
        """Obtiene un pago por código de voucher."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM pagos WHERE codigo_voucher = %s", (codigo_voucher,))
            row = cur.fetchone()
            
            if row:
                return cls(*row)
            return None
    
    @classmethod
    def crear_pago(cls, usuario_id, concepto, monto, referencia_id=None):
        """Crea un nuevo pago y genera voucher."""
        # Generar código único
        codigo_voucher = f"VCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Generar datos para QR
        qr_data = f"https://tusitio.com/validar/{codigo_voucher}"
        
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO pagos (
                    usuario_id, concepto, referencia_id, monto,
                    codigo_voucher, qr_code_data, pagado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ``, (usuario_id, concepto, referencia_id, monto,
                 codigo_voucher, qr_data, True))
            
            pago_id = cur.fetchone()[0]
        
        return cls.get_by_id(pago_id)
    
    def generar_qr(self):
        """Genera la imagen QR para el voucher."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.qr_code_data or f"PAGO:{self.codigo_voucher}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
    
    def validar(self):
        """Valida el voucher (marca como usado)."""
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE pagos
                SET validado = true
                WHERE id = %s
                RETURNING id
            ``, (self.id,))
            
            if cur.fetchone():
                self.validado = True
                return True
            return False
    
    def get_descripcion_concepto(self):
        """Obtiene la descripción del concepto asociado."""
        with get_db_cursor() as cur:
            if self.concepto == 'evento' and self.referencia_id:
                cur.execute("SELECT titulo FROM eventos WHERE id = %s", (self.referencia_id,))
                row = cur.fetchone()
                return row[0] if row else "Evento"
            elif self.concepto == 'certificado':
                return "Certificado de Egresado"
            elif self.concepto == 'membresia':
                return "Membresía Anual"
            return self.concepto
    
    def save(self):
        """Guarda o actualiza el pago en la base de datos."""
        if self.id:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE pagos
                    SET pagado = %s,
                        validado = %s,
                        pdf_voucher_url = %s
                    WHERE id = %s
                ``, (self.pagado, self.validado, self.pdf_voucher_url, self.id))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO pagos (
                        usuario_id, concepto, referencia_id, monto,
                        codigo_voucher, qr_code_data, pagado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ``, (
                    self.usuario_id, self.concepto, self.referencia_id,
                    self.monto, self.codigo_voucher, self.qr_code_data,
                    self.pagado
                ))
                self.id = cur.fetchone()[0]
        
        return self.id
    
    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            'id': str(self.id) if self.id else None,
            'usuario_id': str(self.usuario_id) if self.usuario_id else None,
            'concepto': self.concepto,
            'descripcion': self.get_descripcion_concepto(),
            'monto': float(self.monto) if self.monto else None,
            'fecha_pago': self.fecha_pago.isoformat() if self.fecha_pago else None,
            'codigo_voucher': self.codigo_voucher,
            'pagado': self.pagado,
            'validado': self.validado,
            'pdf_voucher_url': self.pdf_voucher_url
        }