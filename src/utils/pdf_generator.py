"""
Utilidades para generación de PDFs.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
import qrcode
from typing import Dict, Any, Optional

class PDFGenerator:
    """Generador de PDFs para constancias y vouchers."""
    
    @staticmethod
    def generar_voucher(datos_pago: Dict[str, Any], qr_data: Optional[bytes] = None) -> bytes:
        """
        Genera un PDF de voucher de pago.
        
        Args:
            datos_pago: Diccionario con datos del pago
            qr_data: Imagen QR en bytes (opcional)
        
        Returns:
            bytes: Contenido del PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003366'),
            alignment=1,  # Centro
            spaceAfter=30
        )
        story.append(Paragraph("VOUCHER DE PAGO", title_style))
        
        # Línea separadora
        story.append(Spacer(1, 0.5*cm))
        
        # Datos del voucher
        data = [
            ['Código:', datos_pago.get('codigo', '')],
            ['Fecha:', datos_pago.get('fecha', datetime.now().strftime('%d/%m/%Y %H:%M'))],
            ['Usuario:', datos_pago.get('usuario', '')],
            ['Email:', datos_pago.get('email', '')],
            ['Concepto:', datos_pago.get('concepto', '').upper()],
            ['Monto:', f"S/. {datos_pago.get('monto', 0):,.2f}"],
            ['Estado:', 'PAGADO']
        ]
        
        table = Table(data, colWidths=[100, 300])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003366')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 2*cm))
        
        # QR
        if qr_data:
            qr_buffer = io.BytesIO(qr_data)
            qr_buffer.seek(0)
            img = Image(qr_buffer, width=3*cm, height=3*cm)
            story.append(img)
        
        # Texto de validación
        story.append(Spacer(1, 1*cm))
        validation_text = f"Validar en: https://sistema.unitru.edu.pe/validar/{datos_pago.get('codigo', '')}"
        story.append(Paragraph(validation_text, styles['Normal']))
        
        story.append(Spacer(1, 0.5*cm))
        disclaimer = "Este voucher es válido solo con presentación de documento de identidad."
        story.append(Paragraph(disclaimer, styles['Italic']))
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generar_constancia(evento: Dict[str, Any], egresado: Dict[str, Any]) -> bytes:
        """
        Genera una constancia de participación en evento.
        
        Args:
            evento: Datos del evento
            egresado: Datos del egresado
        
        Returns:
            bytes: Contenido del PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Manejo de fechas
        fecha_inicio = evento.get('fecha_inicio')
        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            except ValueError:
                fecha_inicio = datetime.now()
        elif not isinstance(fecha_inicio, (datetime, date)):
            fecha_inicio = datetime.now()
        
        # Mapeo de meses en español
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        fecha_str = f"{fecha_inicio.day} de {meses[fecha_inicio.month-1]} de {fecha_inicio.year}"
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=28,
            textColor=colors.HexColor('#003366'),
            alignment=1,
            spaceAfter=20
        )
        story.append(Paragraph("UNIVERSIDAD NACIONAL DE TRUJILLO", title_style))
        
        story.append(Spacer(1, 1*cm))
        
        # Subtítulo
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=20,
            alignment=1,
            spaceAfter=30
        )
        story.append(Paragraph("CONSTANCIA DE PARTICIPACIÓN", subtitle_style))
        
        story.append(Spacer(1, 2*cm))
        
        # Texto
        text_style = ParagraphStyle(
            'Text',
            parent=styles['Normal'],
            fontSize=14,
            alignment=1,
            spaceAfter=20,
            leading=20
        )
        
        texto = f"""
        Otorgada a:
        
        <b>{egresado.get('nombre_completo', '')}</b>
        <b>DNI: {egresado.get('dni', '')}</b>
        
        Por su participación en el evento:
        
        <b>{evento.get('titulo', '')}</b>
        
        Realizado el {fecha_str}
        """
        
        story.append(Paragraph(texto.replace('\n', '<br/>'), text_style))
        
        story.append(Spacer(1, 4*cm))
        
        # Firma
        firma_style = ParagraphStyle(
            'Firma',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1
        )
        story.append(Paragraph("_________________________", firma_style))
        story.append(Paragraph("Director de Egresados UNT", firma_style))
        
        # Fecha de emisión
        hoy = datetime.now()
        fecha_emision = f"Trujillo, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"
        fecha_style = ParagraphStyle(
            'Fecha',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2,  # Derecha
            spaceBefore=30
        )
        story.append(Paragraph(fecha_emision, fecha_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generar_reporte(datos: Dict[str, Any], titulo: str) -> bytes:
        """
        Genera un reporte en PDF.
        
        Args:
            datos: Datos del reporte
            titulo: Título del reporte
        
        Returns:
            bytes: Contenido del PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.HexColor('#003366'),
            spaceAfter=20
        )
        story.append(Paragraph(titulo, title_style))
        
        # Fecha
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 1*cm))
        
        # Datos del reporte
        for key, value in datos.items():
            if isinstance(value, (list, tuple)):
                story.append(Paragraph(f"<b>{key}:</b>", styles['Heading3']))
                for item in value:
                    story.append(Paragraph(f"• {item}", styles['Normal']))
                story.append(Spacer(1, 0.5*cm))
            elif isinstance(value, dict):
                story.append(Paragraph(f"<b>{key}:</b>", styles['Heading3']))
                data_table = [[k, str(v)] for k, v in value.items()]
                table = Table(data_table, colWidths=[150, 300])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.5*cm))
            else:
                story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

# Instancia global
pdf_generator = PDFGenerator()