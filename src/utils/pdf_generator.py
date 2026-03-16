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
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from datetime import datetime
import io

UNT_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/6/6e/Universidad_Nacional_de_Trujillo_-_Per%C3%BA_vector_logo.png"


def _dibujar_marca_agua_unt(c, width, height):
    """
    Dibuja el logo de la UNT como marca de agua semitransparente.
    Si no se puede cargar el logo, simplemente no dibuja nada.
    """
    try:
        logo = ImageReader(UNT_LOGO_URL)
        c.saveState()
        # Colocar centrado horizontal y ligeramente más abajo,
        # para que no invada tanto el encabezado ni el texto principal.
        c.translate(width / 2, height / 2 - 2*cm)
        try:
            c.setFillAlpha(0.06)
        except AttributeError:
            # Algunas versiones de reportlab no soportan alpha; continuamos sin transparencia explícita
            pass
        # Un poco más pequeño para que se vea más sutil y ordenado
        size = 11 * cm
        c.drawImage(logo, -size / 2, -size / 2, width=size, height=size, mask="auto")
        c.restoreState()
    except Exception:
        # Fallo silencioso: el PDF sigue siendo válido aunque no haya logo
        return


def generar_pdf_voucher_pago(voucher_data, qr_bytes=None):
    """Genera un PDF de voucher de pago."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    _dibujar_marca_agua_unt(c, width, height)

    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Voucher {voucher_data.get('codigo_voucher', '')}")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.5 * cm, "Sistema de Gestión de Egresados y Empleabilidad")
    c.setLineWidth(1)
    c.line(2 * cm, height - 3 * cm, width - 2 * cm, height - 3 * cm)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 4 * cm, "VOUCHER DE PAGO")

    fecha_pago = voucher_data.get("fecha_pago")
    if hasattr(fecha_pago, "strftime"):
        fecha_str = fecha_pago.strftime("%d/%m/%Y %H:%M")
    else:
        fecha_str = str(fecha_pago or datetime.now().strftime("%d/%m/%Y %H:%M"))

    y = height - 5 * cm
    c.setFont("Helvetica", 11)
    filas = [
        ("Código voucher:", voucher_data.get("codigo_voucher", "")),
        ("Usuario:", voucher_data.get("nombre", "")),
        ("Email:", voucher_data.get("email", "")),
        ("Concepto:", str(voucher_data.get("concepto", "")).upper()),
        ("Monto:", f"S/. {float(voucher_data.get('monto', 0) or 0):.2f}"),
        ("Fecha pago:", fecha_str),
        ("Estado:", "VALIDADO" if voucher_data.get("validado") else "PENDIENTE DE VALIDACIÓN"),
    ]

    for label, value in filas:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(6.5 * cm, y, str(value))
        y -= 0.7 * cm

    if qr_bytes:
        qr_buffer = io.BytesIO(qr_bytes)
        qr_image = ImageReader(qr_buffer)
        c.drawImage(qr_image, width - 7 * cm, height - 11.5 * cm, width=4.5 * cm, height=4.5 * cm, mask="auto")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.8 * cm, "Documento generado automáticamente por el Sistema de Egresados UNT")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_bitacora(df, titulo_reporte="Reporte de Bitácora"):
    """Genera un PDF con los registros de la bitácora en formato tabla."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Marca de agua
    _dibujar_marca_agua_unt(c, width, height)

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

def generar_pdf_postulaciones_lista(postulaciones):
    """Genera un PDF tabular con el listado de postulaciones."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Marca de agua
    _dibujar_marca_agua_unt(c, width, height)

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 3*cm, "Listado de Postulaciones")
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        width/2,
        height - 3.5*cm,
        f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

    # Preparar datos para tabla
    data = [["Oferta", "Empresa", "Egresado", "Fecha", "Estado"]]
    for p in postulaciones:
        data.append(
            [
                str(p.get("oferta", ""))[:40],
                str(p.get("empresa", ""))[:30],
                str(p.get("egresado", ""))[:30],
                p.get("fecha_postulacion").strftime("%d/%m/%Y %H:%M")
                if p.get("fecha_postulacion")
                else "",
                str(p.get("estado", "")),
            ]
        )

    table = Table(
        data,
        colWidths=[7*cm, 5*cm, 5*cm, 4*cm, 3*cm],
    )
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(style)

    table.wrapOn(c, width, height)
    table_height = 1.2 * cm * len(data)
    y_position = max(2*cm, height - 5*cm - table_height)
    table.drawOn(c, 1*cm, y_position)

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_ofertas_lista(ofertas, titulo="Listado de Ofertas Laborales"):
    """Genera un PDF tabular con un listado de ofertas laborales."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 3 * cm, titulo)
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        width / 2,
        height - 3.5 * cm,
        f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

    data = [["Título", "Empresa", "Tipo", "Modalidad", "Límite", "Estado", "Postulaciones"]]
    for o in ofertas:
        fecha_limite = o.get("fecha_limite_postulacion")
        if hasattr(fecha_limite, "strftime"):
            fecha_limite = fecha_limite.strftime("%d/%m/%Y")
        data.append(
            [
                str(o.get("titulo", ""))[:40],
                str(o.get("empresa", ""))[:28],
                str(o.get("tipo", ""))[:14],
                str(o.get("modalidad", ""))[:14],
                str(fecha_limite or ""),
                "Activa" if o.get("activa") else "Cerrada",
                str(o.get("postulaciones", 0)),
            ]
        )

    table = Table(
        data,
        colWidths=[8.5 * cm, 5.5 * cm, 3 * cm, 3.2 * cm, 3.2 * cm, 2.7 * cm, 2.8 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    table.wrapOn(c, width, height)
    table_height = 0.6 * cm * len(data)
    y_position = max(2 * cm, height - 5 * cm - table_height)
    table.drawOn(c, 1 * cm, y_position)

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1 * cm, 1.5 * cm, "Documento generado automáticamente por el Sistema de Egresados UNT")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generar_pdf_postulacion(postulacion_data):
    """Genera un PDF resumen de una postulación individual."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle("Reporte de Postulación")

    # Marca de agua
    _dibujar_marca_agua_unt(c, width, height)

    # Encabezado UNT
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.5*cm, "Sistema de Gestión de Egresados y Empleabilidad")

    c.setLineWidth(1)
    c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm)

    # Título del reporte
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 4*cm, "REPORTE DE POSTULACIÓN")

    y = height - 5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Información de la Oferta")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    datos_oferta = [
        ["Oferta:", postulacion_data.get("oferta", "N/A")],
        ["Empresa:", postulacion_data.get("empresa", "N/A")],
    ]
    for label, value in datos_oferta:
        c.drawString(2.5*cm, y, label)
        c.drawString(6*cm, y, str(value))
        y -= 0.5*cm

    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Datos del Egresado")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    datos_egresado = [
        ["Nombre:", postulacion_data.get("nombre_egresado", "N/A")],
        ["Carrera:", postulacion_data.get("carrera", "N/A")],
        ["Facultad:", postulacion_data.get("facultad", "N/A")],
    ]
    for label, value in datos_egresado:
        c.drawString(2.5*cm, y, label)
        c.drawString(6*cm, y, str(value))
        y -= 0.5*cm

    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Detalle de la Postulación")
    y -= 0.6*cm

    fecha_post = postulacion_data.get("fecha_postulacion")
    fecha_str = (
        fecha_post.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_post, "strftime") else str(fecha_post)
    )
    estado = postulacion_data.get("estado", "N/A")
    comentario = postulacion_data.get("comentario", "") or "Sin comentarios registrados."

    c.setFont("Helvetica", 10)
    c.drawString(2.5*cm, y, "Fecha de postulación:")
    c.drawString(6*cm, y, fecha_str)
    y -= 0.5*cm

    c.drawString(2.5*cm, y, "Estado actual:")
    c.drawString(6*cm, y, str(estado))
    y -= 0.8*cm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.5*cm, y, "Comentarios del empleador:")
    y -= 0.6*cm

    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(
        "ComentarioBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
    )
    comentario_paragraph = Paragraph(str(comentario), style_body)
    comentario_paragraph.wrapOn(c, width - 4*cm, height / 3)
    comentario_paragraph.drawOn(c, 2.5*cm, y - (height / 3) + 2*cm)

    # Pie de página
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(
        width - 2*cm,
        1.5*cm,
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generar_pdf_empresa(empresa_data):
    """Genera un PDF profesional con el perfil de la empresa."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Perfil empresarial - {empresa_data.get('razon_social', '')}")
    
    # Encabezado UNT
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.5*cm, "Sistema de Gestión de Egresados y Empleabilidad")
    
    c.setLineWidth(1)
    c.line(2*cm, height - 3*cm, width - 2*cm, height - 3*cm)
    
    # Título del reporte
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 4*cm, f"REPORTE DE PERFIL EMPRESARIAL")
    
    # Datos de la Empresa
    y = height - 5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Información General")
    y -= 0.6*cm
    
    c.setFont("Helvetica", 10)
    datos = [
        ["Razón Social:", empresa_data.get('razon_social', 'N/A')],
        ["RUC:", empresa_data.get('ruc', 'N/A')],
        ["Sector:", empresa_data.get('sector_economico', 'N/A')],
        ["Tamaño:", empresa_data.get('tamano_empresa', 'N/A')],
        ["Dirección:", empresa_data.get('direccion', 'N/A')],
        ["Email:", empresa_data.get('email_contacto', 'N/A')],
        ["Teléfono:", empresa_data.get('telefono_contacto', 'N/A')],
        ["Sitio Web:", empresa_data.get('sitio_web', 'N/A')],
        ["Estado:", empresa_data.get('estado', 'N/A').upper()]
    ]
    
    for label, value in datos:
        c.drawString(2.5*cm, y, label)
        c.drawString(6*cm, y, str(value))
        y -= 0.5*cm
        
    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_ficha_empresa(empresa_data, estadisticas, ofertas_resumen, public_url=None):
    """Genera una ficha oficial (PDF) del perfil de empresa con QR opcional."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Ficha de empresa - {empresa_data.get('razon_social', '')}")

    _dibujar_marca_agua_unt(c, width, height)

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.5 * cm, "Sistema de Gestión de Egresados y Empleabilidad")
    c.setLineWidth(1)
    c.line(2 * cm, height - 3 * cm, width - 2 * cm, height - 3 * cm)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 4 * cm, "FICHA DE EMPRESA")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 2 * cm, height - 4 * cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Datos de la Empresa")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    datos = [
        ("Razón Social:", empresa_data.get("razon_social", "N/A")),
        ("Nombre Comercial:", empresa_data.get("nombre_comercial", "N/A")),
        ("RUC:", empresa_data.get("ruc", "N/A")),
        ("Sector:", empresa_data.get("sector_economico", "N/A")),
        ("Tamaño:", empresa_data.get("tamano_empresa", "N/A")),
        ("Dirección:", empresa_data.get("direccion", "N/A")),
        ("Email:", empresa_data.get("email_contacto", "N/A")),
        ("Teléfono:", empresa_data.get("telefono_contacto", "N/A")),
        ("Sitio Web:", empresa_data.get("sitio_web", "N/A")),
    ]
    for label, value in datos:
        c.drawString(2.5 * cm, y, label)
        c.drawString(7.0 * cm, y, str(value))
        y -= 0.45 * cm

    y -= 0.2 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Estado de Validación")
    y -= 0.6 * cm

    estado = (empresa_data.get("estado") or "N/A").upper()
    fecha_ap = empresa_data.get("fecha_aprobacion")
    if hasattr(fecha_ap, "strftime"):
        fecha_ap_str = fecha_ap.strftime("%d/%m/%Y %H:%M")
    else:
        fecha_ap_str = str(fecha_ap) if fecha_ap else "—"

    c.setFont("Helvetica", 10)
    c.drawString(2.5 * cm, y, "Estado:")
    c.drawString(7.0 * cm, y, estado)
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, "Fecha aprobación:")
    c.drawString(7.0 * cm, y, fecha_ap_str)

    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Resumen de Actividad")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2.5 * cm, y, f"Ofertas publicadas: {ofertas_resumen.get('total_ofertas', 0)}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Ofertas activas: {ofertas_resumen.get('ofertas_activas', 0)}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Postulaciones recibidas: {estadisticas.get('total_postulaciones', 0)}")

    # QR opcional (perfil público)
    if public_url:
        try:
            size = 3.6 * cm
            qr_widget = qr.QrCodeWidget(public_url)
            bounds = qr_widget.getBounds()
            w = bounds[2] - bounds[0]
            h = bounds[3] - bounds[1]
            d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
            d.add(qr_widget)
            renderPDF.draw(d, c, width - 2 * cm - size, 2.2 * cm)
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 2 * cm, 2.0 * cm, "Escanee para ver el sitio web")
        except Exception:
            pass

    # Pie
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.5 * cm, "Documento generado automáticamente por el Sistema de Egresados UNT")
    c.drawRightString(width - 2 * cm, 1.5 * cm, f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_ofertas_empresa(empresa_data, ofertas, fecha_inicio, fecha_fin):
    """Genera un reporte PDF de ofertas de una empresa en un periodo."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Reporte de ofertas - {empresa_data.get('razon_social', '')}")

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.6 * cm, "Reporte de Ofertas Laborales por Empresa")
    c.setLineWidth(1)
    c.line(1.5 * cm, height - 3.1 * cm, width - 1.5 * cm, height - 3.1 * cm)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, height - 4 * cm, empresa_data.get("razon_social", "Empresa"))
    c.setFont("Helvetica", 9)
    c.drawString(1.5 * cm, height - 4.6 * cm, f"RUC: {empresa_data.get('ruc', '')}")
    c.drawRightString(
        width - 1.5 * cm,
        height - 4 * cm,
        f"Periodo: {fecha_inicio} a {fecha_fin}",
    )

    data = [["Título", "Tipo", "Modalidad", "Publicación", "Límite", "Activa", "Postulaciones"]]
    for o in ofertas:
        data.append(
            [
                str(o.get("titulo", ""))[:45],
                str(o.get("tipo", "")),
                str(o.get("modalidad", "")),
                o.get("fecha_publicacion").strftime("%d/%m/%Y") if o.get("fecha_publicacion") else "",
                o.get("fecha_limite_postulacion").strftime("%d/%m/%Y") if o.get("fecha_limite_postulacion") else "",
                "Sí" if o.get("activa") else "No",
                str(o.get("total_postulaciones", 0)),
            ]
        )

    table = Table(
        data,
        colWidths=[10 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm, 2 * cm, 3 * cm],
    )
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table_height = 0.55 * cm * len(data)
    y = height - 6 * cm - table_height
    table.drawOn(c, 1.5 * cm, max(1.5 * cm, y))

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1.5 * cm, 1.3 * cm, "Sistema de Egresados UNT")
    c.drawRightString(width - 1.5 * cm, 1.3 * cm, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_empresas_seleccionadas(empresas_data, kpis, titulo="Reporte de Empresas Seleccionadas"):
    """Genera un PDF con tabla resumen + KPIs de empresas seleccionadas."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(titulo)

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.5 * cm, "Sistema de Gestión de Egresados y Empleabilidad")
    c.setLineWidth(1)
    c.line(2 * cm, height - 3 * cm, width - 2 * cm, height - 3 * cm)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 4 * cm, titulo)
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 2 * cm, height - 4 * cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "KPIs del grupo seleccionado")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2.5 * cm, y, f"Total empresas: {kpis.get('total', 0)}")
    y -= 0.45 * cm
    c.drawString(
        2.5 * cm,
        y,
        f"Activas: {kpis.get('activas', 0)}  |  Pendientes: {kpis.get('pendientes', 0)}  |  Rechazadas: {kpis.get('rechazadas', 0)}",
    )
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Sectores (top): {kpis.get('top_sectores', '—')}")

    y -= 0.9 * cm
    data = [["RUC", "Razón Social", "Sector", "Tamaño", "Estado"]]
    for e in empresas_data:
        data.append(
            [
                str(e.get("ruc", "")),
                str(e.get("razon_social", ""))[:40],
                str(e.get("sector_economico", ""))[:20],
                str(e.get("tamano_empresa", ""))[:15],
                str(e.get("estado", ""))[:12],
            ]
        )

    table = Table(data, colWidths=[3 * cm, 7.5 * cm, 4 * cm, 3 * cm, 3 * cm])
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table_height = 0.55 * cm * len(data)
    table.drawOn(c, 2 * cm, max(2 * cm, y - table_height))

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.5 * cm, "Documento generado automáticamente por el Sistema de Egresados UNT")
    c.drawRightString(width - 2 * cm, 1.5 * cm, f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_empleadores_empresa(empresa_data, empleadores):
    """Genera un PDF con el listado de empleadores de una empresa."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Reporte de empleadores - {empresa_data.get('razon_social', '')}")

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.6 * cm, "Reporte de Empleadores por Empresa")
    c.setLineWidth(1)
    c.line(1.5 * cm, height - 3.1 * cm, width - 1.5 * cm, height - 3.1 * cm)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, height - 4 * cm, empresa_data.get("razon_social", "Empresa"))
    c.setFont("Helvetica", 9)
    c.drawString(1.5 * cm, height - 4.6 * cm, f"RUC: {empresa_data.get('ruc', '')}")
    c.drawRightString(width - 1.5 * cm, height - 4 * cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    data = [["Nombre", "Cargo", "Email", "Fecha registro", "Admin empresa"]]
    for emp in empleadores:
        fecha_reg = emp.get("fecha_registro")
        fecha_str = fecha_reg.strftime("%d/%m/%Y") if hasattr(fecha_reg, "strftime") else (str(fecha_reg) if fecha_reg else "")
        data.append(
            [
                str(emp.get("nombre", ""))[:35],
                str(emp.get("cargo", ""))[:20],
                str(emp.get("email", ""))[:35],
                fecha_str,
                "Sí" if emp.get("es_administrador_empresa") else "No",
            ]
        )

    table = Table(data, colWidths=[7 * cm, 4 * cm, 7 * cm, 4 * cm, 3.5 * cm])
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table_height = 0.55 * cm * len(data)
    y = height - 6 * cm - table_height
    table.drawOn(c, 1.5 * cm, max(1.5 * cm, y))

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1.5 * cm, 1.3 * cm, "Sistema de Egresados UNT")
    c.drawRightString(width - 1.5 * cm, 1.3 * cm, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_dashboard_empresa(empresa_data, stats, ofertas_recientes):
    """
    Genera un PDF con el resumen del dashboard de una empresa:
    - Datos básicos
    - KPIs
    - Actividad reciente (tabla)
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Dashboard empresa - {empresa_data.get('razon_social', '')}")

    _dibujar_marca_agua_unt(c, width, height)

    # Encabezado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.5 * cm, "Sistema de Gestión de Egresados y Empleabilidad")
    c.setLineWidth(1)
    c.line(2 * cm, height - 3 * cm, width - 2 * cm, height - 3 * cm)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 4 * cm, "RESUMEN DASHBOARD DE EMPRESA")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 2 * cm, height - 4 * cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Datos de la Empresa")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    datos = [
        ("Razón Social:", empresa_data.get("razon_social", "N/A")),
        ("RUC:", empresa_data.get("ruc", "N/A")),
        ("Sector:", empresa_data.get("sector_economico", "N/A")),
        ("Estado:", (empresa_data.get("estado") or "N/A").upper()),
    ]
    for label, value in datos:
        c.drawString(2.5 * cm, y, label)
        c.drawString(6.8 * cm, y, str(value))
        y -= 0.45 * cm

    y -= 0.2 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "KPIs")
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2.5 * cm, y, f"Ofertas totales: {stats.get('total_ofertas', 0)}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Ofertas activas: {stats.get('ofertas_activas', 0)}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Postulaciones: {stats.get('total_postulaciones', 0)}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Empleadores: {stats.get('total_empleadores', 0)}")

    y -= 0.9 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Actividad reciente (últimas ofertas)")
    y -= 0.6 * cm

    data = [["Oferta", "Publicación", "Estado", "Postulaciones"]]
    for r in ofertas_recientes or []:
        fecha_pub = r.get("fecha_publicacion")
        fecha_str = fecha_pub.strftime("%d/%m/%Y") if hasattr(fecha_pub, "strftime") else ""
        data.append(
            [
                str(r.get("titulo", ""))[:50],
                fecha_str,
                "Activa" if r.get("activa") else "Cerrada",
                str(r.get("postulaciones", 0)),
            ]
        )

    table = Table(data, colWidths=[10 * cm, 3 * cm, 3 * cm, 3 * cm])
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table_height = 0.55 * cm * len(data)
    table.drawOn(c, 2 * cm, max(2 * cm, y - table_height))

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.5 * cm, "Documento generado automáticamente por el Sistema de Egresados UNT")
    c.drawRightString(width - 2 * cm, 1.5 * cm, f"{datetime.now().strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_oferta_detalle(empresa_data, oferta_data, estadisticas_postulaciones=None, public_url=None):
    """Genera un PDF con el detalle de una oferta laboral de una empresa."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setAuthor("Sistema de Egresados UNT")
    c.setTitle(f"Oferta - {oferta_data.get('titulo', '')}")

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 2.5 * cm, "Sistema de Gestión de Egresados y Empleabilidad")
    c.setLineWidth(1)
    c.line(2 * cm, height - 3 * cm, width - 2 * cm, height - 3 * cm)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 4 * cm, "FICHA DE OFERTA LABORAL")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 2 * cm, height - 4 * cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 5 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, str(oferta_data.get("titulo", "Oferta")))
    y -= 0.6 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Empresa: {empresa_data.get('razon_social', 'N/A')}  |  RUC: {empresa_data.get('ruc', 'N/A')}")
    y -= 0.6 * cm

    datos = [
        ("Tipo:", oferta_data.get("tipo", "N/A")),
        ("Modalidad:", oferta_data.get("modalidad", "N/A")),
        ("Ubicación:", oferta_data.get("ubicacion", "N/A")),
        ("Salario:", oferta_data.get("salario", "N/A")),
        ("Publicación:", oferta_data.get("fecha_publicacion", "N/A")),
        ("Límite:", oferta_data.get("fecha_limite", "N/A")),
        ("Activa:", "Sí" if oferta_data.get("activa") else "No"),
    ]
    for label, value in datos:
        c.drawString(2.5 * cm, y, label)
        c.drawString(6.2 * cm, y, str(value))
        y -= 0.45 * cm

    # Descripción / requisitos (parrafos)
    y -= 0.2 * cm
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14)

    def _draw_paragraph(title, text, y_pos):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y_pos, title)
        y_pos -= 0.5 * cm
        para = Paragraph(str(text or "—"), style_body)
        para.wrapOn(c, width - 4 * cm, 6 * cm)
        para.drawOn(c, 2 * cm, y_pos - 4.7 * cm)
        return y_pos - 5.2 * cm

    y = _draw_paragraph("Descripción", oferta_data.get("descripcion"), y)
    y = _draw_paragraph("Requisitos", oferta_data.get("requisitos"), y)

    # Estadísticas de postulaciones (si existen)
    if estadisticas_postulaciones:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, max(2.8 * cm, y), "Resumen de postulaciones")
        y2 = max(2.2 * cm, y - 0.6 * cm)
        c.setFont("Helvetica", 10)
        resumen = [
            ("Total:", estadisticas_postulaciones.get("total", 0)),
            ("Recibidos:", estadisticas_postulaciones.get("recibidos", 0)),
            ("En revisión:", estadisticas_postulaciones.get("en_revision", 0)),
            ("Entrevista:", estadisticas_postulaciones.get("entrevista", 0)),
            ("Seleccionados:", estadisticas_postulaciones.get("seleccionado", 0)),
            ("Descartados:", estadisticas_postulaciones.get("descartado", 0)),
        ]
        for label, value in resumen:
            c.drawString(2.5 * cm, y2, f"{label} {value}")
            y2 -= 0.42 * cm

    # QR opcional (sitio web empresa)
    if public_url:
        try:
            size = 3.2 * cm
            qr_widget = qr.QrCodeWidget(public_url)
            bounds = qr_widget.getBounds()
            w = bounds[2] - bounds[0]
            h = bounds[3] - bounds[1]
            d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
            d.add(qr_widget)
            renderPDF.draw(d, c, width - 2 * cm - size, 2.1 * cm)
            c.setFont("Helvetica", 8)
            c.drawRightString(width - 2 * cm, 1.9 * cm, "QR: Sitio web de la empresa")
        except Exception:
            pass

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.5 * cm, "Sistema de Egresados UNT")
    c.drawRightString(width - 2 * cm, 1.5 * cm, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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


def generar_pdf_reporte_pagos(pagos_data):
    """Genera un PDF tabular profesional con reporte de pagos."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 3*cm, "REPORTE DE PAGOS Y VOUCHERS")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 3.5*cm, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    data = [["Código Voucher", "Usuario", "Concepto", "Monto (S/.)", "Fecha", "Pagado", "Validado"]]
    for pago in pagos_data:
        data.append([
            str(pago.get("codigo_voucher", ""))[:20],
            str(pago.get("email", ""))[:30],
            str(pago.get("concepto", "")).upper(),
            f"S/. {pago.get('monto', 0):.2f}",
            pago.get("fecha_pago").strftime("%d/%m/%Y %H:%M") if hasattr(pago.get("fecha_pago"), "strftime") else str(pago.get("fecha_pago", "")),
            "Sí" if pago.get("pagado") else "No",
            "Sí" if pago.get("validado") else "No",
        ])

    table = Table(data, colWidths=[4*cm, 5*cm, 3.5*cm, 3*cm, 4*cm, 2*cm, 2*cm])
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
    table.setStyle(style)

    table.wrapOn(c, width, height)
    table_height = 0.5 * cm * len(data)
    table.drawOn(c, 1*cm, max(2*cm, height - 5*cm - table_height))

    total_monto = sum(float(p.get("monto", 0)) for p in pagos_data)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*cm, 1.8*cm, f"Total Ingresos: S/. {total_monto:,.2f}")
    c.drawString(1*cm, 1.3*cm, f"Total Registros: {len(pagos_data)}")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1*cm, 0.8*cm, "Documento generado automáticamente por el Sistema de Egresados UNT")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_resultados_encuestas(resultados_data, titulo_encuesta="Resultados de Encuesta"):
    """Genera un PDF tabular profesional con resultados de encuestas."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 3*cm, f"RESULTADOS: {titulo_encuesta.upper()}")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 3.5*cm, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    data = [["Pregunta", "Tipo", "Respuesta", "Cantidad", "Porcentaje"]]
    for item in resultados_data:
        data.append([
            str(item.get("texto_pregunta", ""))[:40],
            str(item.get("tipo_respuesta", "")),
            str(item.get("respuesta", ""))[:30],
            str(int(item.get("cantidad", 0))),
            f"{float(item.get('porcentaje', 0)):.1f}%",
        ])

    table = Table(data, colWidths=[8*cm, 3*cm, 6*cm, 2.5*cm, 2.5*cm])
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
    table.setStyle(style)

    table.wrapOn(c, width, height)
    table_height = 0.5 * cm * len(data)
    table.drawOn(c, 1*cm, max(2*cm, height - 5*cm - table_height))

    total_respuestas = sum(int(item.get("cantidad", 0)) for item in resultados_data)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*cm, 1.8*cm, f"Total Respuestas: {total_respuestas}")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1*cm, 0.8*cm, "Documento generado automáticamente por el Sistema de Egresados UNT")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_reporte_generico(datos_list, titulo_reporte="Reporte de Búsqueda"):
    """Genera un PDF tabular profesional para cualquier tipo de reporte."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _dibujar_marca_agua_unt(c, width, height)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 3*cm, titulo_reporte.upper())
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, height - 3.5*cm, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    if not datos_list:
        c.setFont("Helvetica", 11)
        c.drawString(2*cm, height - 5*cm, "No hay datos para mostrar")
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # Obtener columnas del primer registro
    columnas = list(datos_list[0].keys()) if datos_list else []
    
    # Limitar cantidad de columnas para que quepa en página landscape
    if len(columnas) > 7:
        columnas = columnas[:7]

    data = [columnas]
    for item in datos_list:
        fila = []
        for col in columnas:
            valor = item.get(col, "")
            # Convertir a string y truncar si es muy largo
            valor_str = str(valor)[:40] if valor else ""
            fila.append(valor_str)
        data.append(fila)

    # Calcular ancho de columnas dinámicamente
    col_widths = [width / len(columnas) - 0.5*cm for _ in columnas]
    
    table = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
    table.setStyle(style)

    table.wrapOn(c, width, height)
    table_height = 0.4 * cm * len(data)
    table.drawOn(c, 0.5*cm, max(2*cm, height - 5*cm - table_height))

    c.setFont("Helvetica-Bold", 10)
    c.drawString(1*cm, 1.8*cm, f"Total Registros: {len(datos_list)}")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1*cm, 0.8*cm, "Documento generado automáticamente por el Sistema de Egresados UNT")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

