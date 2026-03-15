"""
Generador de constancias en formato PDF.
Utiliza reportlab para crear un diseño formal y profesional.
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from datetime import datetime
import io

def generar_pdf_bitacora(df, titulo_reporte="Reporte de Bitácora"):
    """Genera un PDF con los registros de la bitácora en formato tabla."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 3*cm, titulo_reporte)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 3.5*cm, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Preparar datos para la tabla
    data = [["Usuario", "Acción", "Módulo", "Descripción", "Fecha/Hora", "Resultado"]]
    for _, row in df.iterrows():
        # Truncar descripción si es muy larga
        desc = str(row['Descripción'])
        if len(desc) > 50: desc = desc[:47] + "..."
        
        data.append([
            str(row['Usuario']),
            str(row['Acción']),
            str(row['Módulo']),
            desc,
            str(row['Fecha']),
            str(row['Resultado'])
        ])

    # Estilo de tabla
    table = Table(data, colWidths=[5*cm, 3*cm, 3*cm, 8*cm, 4*cm, 3*cm])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0056b3")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    table.setStyle(style)

    # Dibujar tabla
    table.wrapOn(c, width, height)
    table.drawOn(c, 1*cm, height - 5*cm - (len(data)*0.5*cm)) # Ajuste simple de posición

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generar_pdf_constancia(nombre_usuario, nombre_evento, fecha_evento):
    """Genera un buffer de bytes con el PDF de la constancia."""
    buffer = io.BytesIO()
    
    # Configurar página en horizontal
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # --- Diseño de fondo / Bordes ---
    c.setStrokeColor(colors.HexColor("#0056b3"))
    c.setLineWidth(5)
    c.rect(1*cm, 1*cm, width-2*cm, height-2*cm) # Borde exterior
    
    c.setLineWidth(1)
    c.rect(1.2*cm, 1.2*cm, width-2.4*cm, height-2.4*cm) # Borde interior fino

    # --- Encabezado ---
    # Intentar cargar logo si existe, si no, texto
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#0056b3"))
    c.drawCentredString(width/2, height - 4*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height - 5*cm, "Dirección de Seguimiento del Egresado y Empleabilidad")

    # --- Título Central ---
    c.setFont("Times-BoldItalic", 48)
    c.drawCentredString(width/2, height/2 + 2*cm, "Constancia de Participación")

    # --- Cuerpo del texto ---
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height/2 - 0.5*cm, "Se otorga la presente a:")
    
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height/2 - 2*cm, nombre_usuario.upper())

    # Texto descriptivo
    c.setFont("Helvetica", 16)
    texto = f"Por haber participado satisfactoriamente en el evento <b>'{nombre_evento}'</b>, realizado el día {fecha_evento}."
    
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=20,
        alignment=1 # Center
    )
    
    p = Paragraph(texto, style_body)
    p.wrapOn(c, width-6*cm, 4*cm)
    p.drawOn(c, 3*cm, height/2 - 5*cm)

    # --- Firmas ---
    c.setDash(1, 2)
    c.line(4*cm, 4*cm, 10*cm, 4*cm)
    c.line(width-10*cm, 4*cm, width-4*cm, 4*cm)
    c.setDash()

    c.setFont("Helvetica", 10)
    c.drawCentredString(7*cm, 3.5*cm, "Director de Seguimiento del Egresado")
    c.drawCentredString(width-7*cm, 3.5*cm, "Secretario Académico - UNT")

    # --- Fecha de emisión ---
    fecha_emision = datetime.now().strftime("%d de %B de %Y")
    c.setFont("Helvetica-Oblique", 10)
    c.drawRightString(width-2*cm, 1.5*cm, f"Emitido el: {fecha_emision}")

    c.showPage()
    c.save()
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
