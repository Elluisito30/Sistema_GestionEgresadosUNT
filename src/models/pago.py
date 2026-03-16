"""
Modelo de Pago para el sistema.
Representa un pago realizado por un usuario.
"""
from datetime import datetime
import io
import uuid

from src.utils.database import get_db_cursor
from src.utils.qr_generator import QRGenerator

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
            """, (usuario_id, limit))
            
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
    def obtener_historial_usuario(cls, usuario_id):
        """Obtiene el historial de pagos de un usuario con descripción."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    p.concepto,
                    p.referencia_id,
                    p.monto,
                    p.fecha_pago,
                    p.codigo_voucher,
                    p.pagado,
                    p.validado,
                    CASE
                        WHEN p.concepto = 'evento' THEN COALESCE((SELECT titulo FROM eventos WHERE id = p.referencia_id::uuid), 'Evento')
                        WHEN p.concepto = 'certificado' THEN 'Certificado'
                        WHEN p.concepto = 'membresia' THEN 'Membresía'
                    END as descripcion
                FROM pagos p
                WHERE p.usuario_id = %s
                ORDER BY p.fecha_pago DESC
                """,
                (usuario_id,),
            )
            return cur.fetchall()

    @classmethod
    def obtener_todos(cls, limit=1000):
        """Obtiene todos los pagos para la vista administrativa."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    u.email,
                    p.concepto,
                    p.monto,
                    p.fecha_pago,
                    p.codigo_voucher,
                    p.pagado,
                    p.validado
                FROM pagos p
                JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.fecha_pago DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    @classmethod
    def obtener_pendientes_validacion(cls, limit=20):
        """Obtiene vouchers pagados que aún no fueron validados."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.codigo_voucher, u.email, p.concepto, p.monto, p.fecha_pago
                FROM pagos p
                JOIN usuarios u ON u.id = p.usuario_id
                WHERE p.pagado = true AND p.validado = false
                ORDER BY p.fecha_pago DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    @classmethod
    def obtener_ingresos_12_meses(cls):
        """Obtiene métricas mensuales de ingresos y cantidad de pagos."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    DATE_TRUNC('month', fecha_pago)::date as mes,
                    SUM(monto) as total,
                    COUNT(*) as cantidad
                FROM pagos
                WHERE pagado = true
                AND fecha_pago > NOW() - INTERVAL '12 months'
                GROUP BY mes
                ORDER BY mes
                """
            )
            return cur.fetchall()

    @classmethod
    def obtener_distribucion_conceptos(cls):
        """Obtiene distribución de pagos por concepto."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT concepto, COUNT(*), SUM(monto)
                FROM pagos
                WHERE pagado = true
                GROUP BY concepto
                """
            )
            return cur.fetchall()

    @classmethod
    def obtener_detalle_voucher(cls, pago_id):
        """Obtiene detalle completo de un voucher para visualización/PDF."""
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    p.usuario_id,
                    p.concepto,
                    p.monto,
                    p.fecha_pago,
                    p.codigo_voucher,
                    p.qr_code_data,
                    p.validado,
                    p.pdf_voucher_url,
                    u.email,
                    CASE
                        WHEN e.id IS NOT NULL THEN TRIM(e.nombres || ' ' || e.apellido_paterno || ' ' || COALESCE(e.apellido_materno, ''))
                        WHEN em.id IS NOT NULL THEN TRIM(em.nombres || ' ' || em.apellidos)
                        ELSE 'Administrador'
                    END as nombre
                FROM pagos p
                JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN egresados e ON u.id = e.usuario_id
                LEFT JOIN empleadores em ON u.id = em.usuario_id
                WHERE p.id = %s
                """,
                (pago_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "usuario_id": row[1],
            "concepto": row[2],
            "monto": row[3],
            "fecha_pago": row[4],
            "codigo_voucher": row[5],
            "qr_code_data": row[6],
            "validado": row[7],
            "pdf_voucher_url": row[8],
            "email": row[9],
            "nombre": row[10],
        }

    @classmethod
    def validar_por_id(cls, pago_id):
        """Valida un voucher por su ID y retorna su código."""
        with get_db_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE pagos
                SET validado = true
                WHERE id = %s
                RETURNING codigo_voucher
                """,
                (pago_id,),
            )
            row = cur.fetchone()

        return row[0] if row else None
    
    @classmethod
    def crear_pago(cls, usuario_id, concepto, monto, referencia_id=None):
        """Crea un nuevo pago y genera voucher."""
        # Generar código único
        codigo_voucher = f"VCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Generar datos para QR
        qr_data = QRGenerator.build_voucher_validation_url(codigo_voucher)
        
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO pagos (
                    usuario_id, concepto, referencia_id, monto,
                    codigo_voucher, qr_code_data, pagado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario_id, concepto, referencia_id, monto,
                 codigo_voucher, qr_data, True))
            
            pago_id = cur.fetchone()[0]
        
        return cls.get_by_id(pago_id)
    
    def generar_qr(self):
        """Genera la imagen QR para el voucher."""
        qr_source = self.codigo_voucher or ""
        qr_bytes = QRGenerator.generate_voucher_qr(qr_source)
        return io.BytesIO(qr_bytes)
    
    def validar(self):
        """Valida el voucher (marca como usado)."""
        codigo = self.validar_por_id(self.id)
        if codigo:
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
                """, (self.pagado, self.validado, self.pdf_voucher_url, self.id))
        else:
            with get_db_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO pagos (
                        usuario_id, concepto, referencia_id, monto,
                        codigo_voucher, qr_code_data, pagado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
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