"""
Generador de PDFs - Diseño moderno, colorido y dinámico.
Universidad Nacional de Trujillo - Sistema de Egresados y Empleabilidad.
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from datetime import datetime
import io
import math

# ─────────────────────────────────────────────
#  PALETA DE COLORES
# ─────────────────────────────────────────────
C_PRIMARIO   = colors.HexColor("#1A237E")   # Azul profundo
C_ACENTO     = colors.HexColor("#283593")   # Azul medio
C_GRAD_MID   = colors.HexColor("#3949AB")   # Azul brillante
C_GRAD_END   = colors.HexColor("#5C6BC0")   # Azul suave
C_NARANJA    = colors.HexColor("#FF6F00")   # Naranja energético
C_AMARILLO   = colors.HexColor("#FFC107")   # Amarillo dorado
C_VERDE      = colors.HexColor("#00897B")   # Verde esmeralda
C_ROJO       = colors.HexColor("#E53935")   # Rojo vivo
C_CYAN       = colors.HexColor("#00ACC1")   # Cyan
C_PURPURA    = colors.HexColor("#8E24AA")   # Púrpura
C_BLANCO     = colors.white
C_FONDO      = colors.HexColor("#F5F7FF")   # Fondo muy suave
C_FONDO2     = colors.HexColor("#EEF2FF")   # Fondo alternado
C_TEXTO      = colors.HexColor("#1A1A2E")   # Texto oscuro
C_GRIS_CLARO = colors.HexColor("#B0BEC5")
C_SOMBRA     = colors.HexColor("#E8EAF6")

UNT_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/6/6e/Universidad_Nacional_de_Trujillo_-_Per%C3%BA_vector_logo.png"

# Colores para los KPIs rotativos
KPI_COLORS = [C_ACENTO, C_NARANJA, C_VERDE, C_PURPURA, C_CYAN, C_ROJO]


# ─────────────────────────────────────────────
#  UTILIDADES DE DIBUJO
# ─────────────────────────────────────────────

def _gradiente_horizontal(c, x, y, w, h, color_inicio, color_fin, pasos=60):
    """Simula un gradiente horizontal rellenando rectángulos delgados."""
    r1, g1, b1 = color_inicio.red, color_inicio.green, color_inicio.blue
    r2, g2, b2 = color_fin.red,   color_fin.green,   color_fin.blue
    step_w = w / pasos
    for i in range(pasos):
        t = i / pasos
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        c.setFillColorRGB(r, g, b)
        c.rect(x + i * step_w, y, step_w + 0.5, h, fill=1, stroke=0)


def _rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None, line_width=0):
    """Dibuja un rectángulo con esquinas redondeadas."""
    c.saveState()
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke_color else 0)
    c.restoreState()


def _draw_logo(c, x, y, size=1.8*cm):
    """Intenta cargar el logo UNT; si falla, dibuja un círculo placeholder."""
    try:
        logo = ImageReader(UNT_LOGO_URL)
        c.drawImage(logo, x, y, width=size, height=size, mask="auto")
    except Exception:
        c.saveState()
        c.setFillColor(C_BLANCO)
        c.circle(x + size/2, y + size/2, size/2, fill=1, stroke=0)
        c.restoreState()


def _marca_agua(c, width, height):
    """Logo semitransparente centrado como marca de agua."""
    try:
        logo = ImageReader(UNT_LOGO_URL)
        c.saveState()
        c.translate(width / 2, height / 2)
        try:
            c.setFillAlpha(0.04)
        except AttributeError:
            pass
        size = 13 * cm
        c.drawImage(logo, -size/2, -size/2, width=size, height=size, mask="auto")
        c.restoreState()
    except Exception:
        pass


def _encabezado(c, width, height, titulo_doc, subtitulo=None):
    """
    Encabezado moderno con gradiente completo, logo, título y banda decorativa.
    Retorna la coordenada Y donde termina el encabezado.
    """
    header_h = 3.6 * cm
    # Gradiente de fondo del encabezado
    _gradiente_horizontal(c, 0, height - header_h, width, header_h, C_PRIMARIO, C_GRAD_END)

    # Banda inferior decorativa (naranja)
    c.setFillColor(C_NARANJA)
    c.rect(0, height - header_h - 0.22*cm, width, 0.22*cm, fill=1, stroke=0)

    # Logo
    _draw_logo(c, 0.7*cm, height - header_h + 0.45*cm, size=2.6*cm)

    # Texto institucional
    c.setFillColor(C_BLANCO)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(4.0*cm, height - 1.35*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")
    c.setFont("Helvetica", 8.5)
    c.drawString(4.0*cm, height - 1.9*cm, "Dirección de Seguimiento del Egresado y Empleabilidad")

    # Título del documento (derecha)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 0.8*cm, height - 1.4*cm, titulo_doc.upper())
    c.setFont("Helvetica", 7.5)
    c.drawRightString(width - 0.8*cm, height - 1.95*cm,
                      f"Generado: {datetime.now().strftime('%d/%m/%Y  %H:%M')}")

    # Subtítulo (banda gris debajo del header)
    base_y = height - header_h - 0.22*cm
    if subtitulo:
        c.setFillColor(C_SOMBRA)
        c.rect(0, base_y - 0.7*cm, width, 0.7*cm, fill=1, stroke=0)
        c.setFillColor(C_PRIMARIO)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(0.8*cm, base_y - 0.5*cm, subtitulo)
        base_y -= 0.7*cm

    return base_y  # Coordenada Y libre para continuar


def _pie_pagina(c, width, numero_pagina=None):
    """Pie de página con gradiente y número de página."""
    pie_h = 0.9*cm
    _gradiente_horizontal(c, 0, 0, width, pie_h, C_GRAD_END, C_PRIMARIO)
    c.setFillColor(C_BLANCO)
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(0.8*cm, 0.3*cm, "Sistema de Egresados UNT — Documento generado automáticamente")
    if numero_pagina:
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(width - 0.8*cm, 0.3*cm, f"Pág. {numero_pagina}")


def _kpi_box(c, x, y, w, h, valor, label, color, icono="●"):
    """Dibuja una caja KPI con color, valor grande y etiqueta."""
    # Sombra suave
    c.setFillColor(colors.HexColor("#CCCCCC"))
    c.roundRect(x + 0.08*cm, y - 0.08*cm, w, h, 0.3*cm, fill=1, stroke=0)
    # Fondo blanco
    _rounded_rect(c, x, y, w, h, 0.3*cm, C_BLANCO)
    # Barra lateral de color
    _rounded_rect(c, x, y, 0.35*cm, h, 0.18*cm, color)
    # Círculo icono
    c.setFillColor(color)
    c.circle(x + w - 1.1*cm, y + h/2, 0.4*cm, fill=1, stroke=0)
    c.setFillColor(C_BLANCO)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + w - 1.1*cm, y + h/2 - 0.13*cm, icono)
    # Valor
    c.setFillColor(C_TEXTO)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 0.7*cm, y + h/2 + 0.1*cm, str(valor))
    # Label
    c.setFillColor(C_GRIS_CLARO)
    c.setFont("Helvetica", 7.5)
    c.drawString(x + 0.7*cm, y + 0.22*cm, label.upper())


def _seccion_titulo(c, x, y, w, texto, color=None):
    """Barra de sección con acento de color."""
    color = color or C_ACENTO
    # Fondo degradado suave
    c.setFillColor(C_SOMBRA)
    c.rect(x, y - 0.05*cm, w, 0.6*cm, fill=1, stroke=0)
    # Acento izquierdo
    c.setFillColor(color)
    c.rect(x, y - 0.05*cm, 0.25*cm, 0.6*cm, fill=1, stroke=0)
    # Texto
    c.setFillColor(C_PRIMARIO)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 0.45*cm, y + 0.1*cm, texto.upper())
    return y - 0.05*cm - 0.35*cm  # Y para continuar


def _tabla_moderna(data, col_widths, col_colors=None):
    """Crea una tabla con estilo moderno colorido."""
    n_cols = len(data[0]) if data else 1
    col_colors = col_colors or [C_ACENTO] * n_cols

    estilo = [
        # Encabezado
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8.5),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING',    (0, 0), (-1, 0), 7),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        # Cuerpo
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 7.5),
        ('TEXTCOLOR',     (0, 1), (-1, -1), C_TEXTO),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING',    (0, 1), (-1, -1), 5),
        ('ALIGN',         (0, 1), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 1), (0, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        # Líneas
        ('LINEBELOW',     (0, 0), (-1, -1), 0.4, colors.HexColor("#C5CAE9")),
        ('LINEAFTER',     (0, 0), (-1, -1), 0, colors.white),
        ('BOX',           (0, 0), (-1, -1), 0.8, colors.HexColor("#9FA8DA")),
    ]

    # Colores de fondo encabezado por columna
    for col_i, col_color in enumerate(col_colors[:n_cols]):
        estilo.append(('BACKGROUND', (col_i, 0), (col_i, 0), col_color))

    # Filas alternas
    for row_i in range(1, len(data)):
        bg = C_FONDO if row_i % 2 == 0 else C_BLANCO
        estilo.append(('BACKGROUND', (0, row_i), (-1, row_i), bg))

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(estilo))
    return t


# ─────────────────────────────────────────────
#  FUNCIONES PÚBLICAS
# ─────────────────────────────────────────────


def _dibujar_tabla_paginada(cv, width, height, data, col_widths, col_colors,
                             y_inicio, pie_h=1.4*cm, margen_x=0.8*cm,
                             titulo_reporte="", subtitulo_reporte=""):
    """
    Dibuja una tabla con paginación automática.
    - y_inicio: coordenada Y justo debajo del encabezado de la primera página
                (lo que devuelve _encabezado).
    - pie_h:    altura reservada para el pie de página (no se pisa).
    La función llama showPage() automáticamente entre páginas pero NO en la última;
    el llamador debe hacer showPage() + save() al final.
    """
    HEADER_ROW   = [data[0]]          # primera fila = encabezado de columnas
    data_rows    = data[1:]           # filas de datos
    MARGIN_TOP   = 0.5*cm            # respiro entre encabezado y tabla
    MARGIN_BOT   = pie_h + 0.3*cm    # espacio mínimo sobre el pie

    # Medir altura real de UNA fila de encabezado para estimar ROW_H
    sample = _tabla_moderna(HEADER_ROW + data_rows[:1], col_widths, col_colors)
    _sw, sample_h = sample.wrapOn(cv, width - margen_x * 2, height)
    row_h = sample_h / 2 if len(data_rows) >= 1 else 0.6 * cm
    row_h = max(row_h, 0.55 * cm)

    page_rows = []      # filas acumuladas para la página actual
    y_top     = y_inicio  # Y disponible en la página actual

    def _flush(rows, y_top, is_last=False):
        """Dibuja las filas acumuladas y hace showPage si no es la última."""
        if not rows:
            return
        t = _tabla_moderna(HEADER_ROW + rows, col_widths, col_colors)
        _tw, t_h = t.wrapOn(cv, width - margen_x * 2, height)
        y_draw = y_top - MARGIN_TOP - t_h
        t.drawOn(cv, margen_x, y_draw)
        if not is_last:
            cv.showPage()

    page_num   = 1
    total_est  = max(1, len(data_rows))   # para el encabezado compacto

    for i, row in enumerate(data_rows):
        # Espacio que ocuparía añadir esta fila
        prospective_h = row_h * (len(page_rows) + 2)  # +1 header +1 nueva fila
        available     = y_top - MARGIN_TOP - MARGIN_BOT

        if prospective_h > available and page_rows:
            # No cabe — vaciar página actual
            _flush(page_rows, y_top, is_last=False)
            page_num += 1
            page_rows = []

            # Encabezado compacto para la nueva página
            _marca_agua(cv, width, height)
            _gradiente_horizontal(cv, 0, height - 1.4*cm, width, 1.4*cm,
                                  C_PRIMARIO, C_GRAD_END)
            cv.setFillColor(C_BLANCO)
            cv.setFont("Helvetica-Bold", 9)
            cv.drawString(0.8*cm, height - 0.9*cm, titulo_reporte.upper())
            cv.setFont("Helvetica", 7.5)
            cv.drawRightString(width - 0.8*cm, height - 0.9*cm,
                               f"Pág. {page_num}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            cv.setFillColor(C_NARANJA)
            cv.rect(0, height - 1.4*cm - 0.18*cm, width, 0.18*cm, fill=1, stroke=0)
            _pie_pagina(cv, width, str(page_num))
            y_top = height - 1.4*cm - 0.18*cm

        page_rows.append(row)

    # Última página
    _flush(page_rows, y_top, is_last=True)


def generar_pdf_voucher_pago(voucher_data, qr_bytes=None):
    """Genera un PDF de voucher de pago con diseño moderno."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")
    cv.setTitle(f"Voucher {voucher_data.get('codigo_voucher', '')}")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "VOUCHER DE PAGO")
    _pie_pagina(cv, width, 1)

    # Fondo tarjeta principal
    card_y = y_libre - 0.5*cm - 9.5*cm
    _rounded_rect(cv, 1.2*cm, card_y, width - 2.4*cm, 9.5*cm, 0.4*cm, C_FONDO,
                  stroke_color=colors.HexColor("#9FA8DA"), line_width=0.8)

    # Banda superior de la tarjeta
    _gradiente_horizontal(cv, 1.2*cm, card_y + 8.8*cm, width - 2.4*cm, 0.7*cm, C_ACENTO, C_GRAD_END)
    cv.setFillColor(C_BLANCO)
    cv.setFont("Helvetica-Bold", 11)
    cv.drawString(1.8*cm, card_y + 9.0*cm, f"  Código: {voucher_data.get('codigo_voucher', '')}")

    estado = "VALIDADO ✓" if voucher_data.get("validado") else "PENDIENTE DE VALIDACIÓN"
    color_estado = C_VERDE if voucher_data.get("validado") else C_NARANJA
    cv.setFont("Helvetica-Bold", 10)
    cv.setFillColor(color_estado)
    cv.drawRightString(width - 1.8*cm, card_y + 9.0*cm, estado)

    # Datos del voucher en dos columnas
    fecha_pago = voucher_data.get("fecha_pago")
    fecha_str = fecha_pago.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_pago, "strftime") else str(fecha_pago or "—")

    filas_izq = [
        ("👤 Usuario",   voucher_data.get("nombre", "—")),
        ("✉  Email",     voucher_data.get("email", "—")),
        ("📋 Concepto",  str(voucher_data.get("concepto", "—")).upper()),
    ]
    filas_der = [
        ("💰 Monto",    f"S/. {float(voucher_data.get('monto', 0) or 0):.2f}"),
        ("📅 Fecha",    fecha_str),
        ("🔖 Estado",   estado),
    ]

    y_data = card_y + 7.8*cm
    for label, value in filas_izq:
        cv.setFont("Helvetica-Bold", 8.5)
        cv.setFillColor(C_ACENTO)
        cv.drawString(1.8*cm, y_data, label)
        cv.setFont("Helvetica", 9)
        cv.setFillColor(C_TEXTO)
        cv.drawString(4.5*cm, y_data, str(value))
        y_data -= 0.9*cm

    y_data = card_y + 7.8*cm
    for label, value in filas_der:
        cv.setFont("Helvetica-Bold", 8.5)
        cv.setFillColor(C_NARANJA)
        cv.drawString(10.0*cm, y_data, label)
        cv.setFont("Helvetica", 9)
        cv.setFillColor(C_TEXTO)
        cv.drawString(12.5*cm, y_data, str(value))
        y_data -= 0.9*cm

    # Línea divisoria
    cv.setStrokeColor(colors.HexColor("#C5CAE9"))
    cv.setLineWidth(0.5)
    cv.line(1.8*cm, card_y + 5.1*cm, width - 1.8*cm, card_y + 5.1*cm)

    # Monto destacado
    cv.setFillColor(C_SOMBRA)
    cv.roundRect(1.8*cm, card_y + 3.6*cm, 8*cm, 1.2*cm, 0.3*cm, fill=1, stroke=0)
    cv.setFillColor(C_PRIMARIO)
    cv.setFont("Helvetica-Bold", 9)
    cv.drawString(2.2*cm, card_y + 4.35*cm, "TOTAL PAGADO")
    cv.setFont("Helvetica-Bold", 20)
    cv.setFillColor(C_VERDE)
    cv.drawString(2.2*cm, card_y + 3.8*cm, f"S/. {float(voucher_data.get('monto', 0) or 0):.2f}")

    # QR
    if qr_bytes:
        try:
            qr_buffer = io.BytesIO(qr_bytes)
            qr_image = ImageReader(qr_buffer)
            cv.drawImage(qr_image, width - 5.8*cm, card_y + 3.2*cm,
                         width=4*cm, height=4*cm, mask="auto")
            cv.setFont("Helvetica", 7)
            cv.setFillColor(C_GRIS_CLARO)
            cv.drawCentredString(width - 3.8*cm, card_y + 2.9*cm, "Verificar pago")
        except Exception:
            pass

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_bitacora(df, titulo_reporte="Reporte de Bitácora"):
    """Genera PDF de bitácora con diseño moderno y paginación automática."""
    import re as _re
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    col_widths = [5.2*cm, 3.2*cm, 3.2*cm, 7.8*cm, 5.8*cm, 2.6*cm]
    col_colors = [C_PRIMARIO, C_NARANJA, C_VERDE, C_ACENTO, C_CYAN, C_PURPURA]
    HEADER_ROW = [["USUARIO", "ACCIÓN", "MÓDULO", "DESCRIPCIÓN", "FECHA/HORA", "RESULTADO"]]
    ROW_H      = 0.6*cm
    MARGIN_BOT = 1.4*cm

    # ── Preparar filas limpiando timestamps ───────────────────────────────
    all_rows = []
    for _, row in df.iterrows():
        fecha_raw = str(row.get('Fecha', row.get('Fecha/Hora', '')))
        fecha_str = _re.sub(r'\.\d+', '', fecha_raw)
        fecha_str = _re.sub(r'\+\d{2}:\d{2}$', '', fecha_str).strip()
        desc = str(row.get('Descripción', ''))
        if len(desc) > 52:
            desc = desc[:49] + "…"
        all_rows.append([
            str(row.get('Usuario', '')),
            str(row.get('Acción', '')),
            str(row.get('Módulo', '')),
            desc, fecha_str,
            str(row.get('Resultado', '')),
        ])

    # ── Espacio disponible por página ─────────────────────────────────────
    # Página 1: encabezado (3.6 + 0.22 + 0.7 cm) + 0.5cm margen superior tabla
    TOP_P1 = (3.6 + 0.22 + 0.7 + 0.5) * cm
    # Páginas 2+: encabezado compacto (1.4 + 0.18 cm) + 0.5cm margen
    TOP_PN = (1.4 + 0.18 + 0.5) * cm

    rows_p1 = max(1, int((height - TOP_P1 - MARGIN_BOT) / ROW_H) - 1)
    rows_pn = max(1, int((height - TOP_PN  - MARGIN_BOT) / ROW_H) - 1)

    # ── Dividir en páginas ────────────────────────────────────────────────
    pages     = []
    remaining = list(all_rows)
    pages.append(remaining[:rows_p1]); remaining = remaining[rows_p1:]
    while remaining:
        pages.append(remaining[:rows_pn]); remaining = remaining[rows_pn:]
    total_pages = len(pages)

    # ── Dibujar cada página ───────────────────────────────────────────────
    for page_num, page_rows in enumerate(pages, start=1):
        if page_num == 1:
            _marca_agua(cv, width, height)
            # y_top = coordenada Y justo debajo del encabezado completo
            y_top = _encabezado(cv, width, height, titulo_reporte, subtitulo=titulo_reporte)
        else:
            _marca_agua(cv, width, height)
            _gradiente_horizontal(cv, 0, height - 1.4*cm, width, 1.4*cm, C_PRIMARIO, C_GRAD_END)
            cv.setFillColor(C_BLANCO)
            cv.setFont("Helvetica-Bold", 9)
            cv.drawString(0.8*cm, height - 0.9*cm, titulo_reporte.upper())
            cv.setFont("Helvetica", 7.5)
            cv.drawRightString(width - 0.8*cm, height - 0.9*cm,
                               f"Pág. {page_num}/{total_pages}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            cv.setFillColor(C_NARANJA)
            cv.rect(0, height - 1.4*cm - 0.18*cm, width, 0.18*cm, fill=1, stroke=0)
            y_top = height - 1.4*cm - 0.18*cm

        _pie_pagina(cv, width, f"{page_num}/{total_pages}")

        # Construir tabla — wrapOn devuelve la altura REAL
        data       = HEADER_ROW + page_rows
        t          = _tabla_moderna(data, col_widths, col_colors)
        _tw, t_h   = t.wrapOn(cv, width - 1.6*cm, height)

        # Anclar la tabla justo bajo el encabezado con 0.5cm de respiro
        y_draw = y_top - 0.5*cm - t_h
        t.drawOn(cv, 0.8*cm, y_draw)

        cv.showPage()

    cv.save()
    return buffer.getvalue()


def generar_pdf_postulaciones_lista(postulaciones):
    """Genera PDF tabular de postulaciones con diseño moderno."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "LISTADO DE POSTULACIONES", "Listado de Postulaciones")
    _pie_pagina(cv, width, 1)

    data = [["OFERTA", "EMPRESA", "EGRESADO", "FECHA", "ESTADO"]]
    for p in postulaciones:
        fecha = p.get("fecha_postulacion")
        fecha_str = fecha.strftime("%d/%m/%Y %H:%M") if hasattr(fecha, "strftime") else ""
        data.append([
            str(p.get("oferta", ""))[:40], str(p.get("empresa", ""))[:28],
            str(p.get("egresado", ""))[:28], fecha_str, str(p.get("estado", ""))
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [8*cm, 5.5*cm, 5.5*cm, 4*cm, 3.5*cm],
                            [C_PRIMARIO, C_ACENTO, C_VERDE, C_CYAN, C_NARANJA],
                            y_inicio=y_libre)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_ofertas_lista(ofertas, titulo="Listado de Ofertas Laborales"):
    """Genera PDF de listado de ofertas con diseño moderno."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, titulo, subtitulo=titulo)
    _pie_pagina(cv, width, 1)

    # KPIs rápidos
    total    = len(ofertas)
    activas  = sum(1 for o in ofertas if o.get("activa"))
    cerradas = total - activas
    posts    = sum(int(o.get("postulaciones", 0)) for o in ofertas)

    kpi_w = (width - 1.6*cm) / 4 - 0.3*cm
    kpi_h = 1.4*cm
    kpi_y = y_libre - 0.4*cm - kpi_h
    for i, (val, lbl, color) in enumerate([
        (total,    "Total Ofertas",   C_ACENTO),
        (activas,  "Activas",         C_VERDE),
        (cerradas, "Cerradas",        C_ROJO),
        (posts,    "Postulaciones",   C_NARANJA),
    ]):
        _kpi_box(cv, 0.8*cm + i*(kpi_w + 0.3*cm), kpi_y, kpi_w, kpi_h, val, lbl, color)

    y_tabla = kpi_y - 0.5*cm
    data = [["TÍTULO", "EMPRESA", "TIPO", "MODALIDAD", "LÍMITE", "ESTADO", "POST."]]
    for o in ofertas:
        fecha_limite = o.get("fecha_limite_postulacion")
        if hasattr(fecha_limite, "strftime"): fecha_limite = fecha_limite.strftime("%d/%m/%Y")
        data.append([
            str(o.get("titulo", ""))[:42], str(o.get("empresa", ""))[:26],
            str(o.get("tipo", "")), str(o.get("modalidad", "")),
            str(fecha_limite or ""), "Activa" if o.get("activa") else "Cerrada",
            str(o.get("postulaciones", 0)),
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [9*cm, 5.5*cm, 3*cm, 3.2*cm, 3*cm, 2.6*cm, 2*cm],
                            [C_PRIMARIO, C_ACENTO, C_NARANJA, C_CYAN, C_VERDE, C_PURPURA, C_ROJO],
                            y_inicio=y_tabla)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_postulacion(postulacion_data):
    """Genera PDF detalle de una postulación individual."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "REPORTE DE POSTULACIÓN")
    _pie_pagina(cv, width, 1)

    y = y_libre - 0.6*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Información de la Oferta", C_ACENTO)
    y -= 0.3*cm

    pares = [
        ("Oferta:",   postulacion_data.get("oferta", "N/A"), C_ACENTO),
        ("Empresa:",  postulacion_data.get("empresa", "N/A"), C_NARANJA),
    ]
    for label, value, color in pares:
        cv.setFont("Helvetica-Bold", 9); cv.setFillColor(color)
        cv.drawString(1.2*cm, y, label)
        cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
        cv.drawString(4.5*cm, y, str(value))
        y -= 0.6*cm

    y -= 0.3*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Datos del Egresado", C_VERDE)
    y -= 0.3*cm

    datos_egr = [
        ("Nombre:",   postulacion_data.get("nombre_egresado", "N/A"), C_VERDE),
        ("Carrera:",  postulacion_data.get("carrera", "N/A"), C_CYAN),
        ("Facultad:", postulacion_data.get("facultad", "N/A"), C_PURPURA),
    ]
    for label, value, color in datos_egr:
        cv.setFont("Helvetica-Bold", 9); cv.setFillColor(color)
        cv.drawString(1.2*cm, y, label)
        cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
        cv.drawString(4.5*cm, y, str(value))
        y -= 0.6*cm

    y -= 0.3*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Detalle de la Postulación", C_NARANJA)
    y -= 0.3*cm

    fecha_post = postulacion_data.get("fecha_postulacion")
    fecha_str = fecha_post.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_post, "strftime") else str(fecha_post)

    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_NARANJA)
    cv.drawString(1.2*cm, y, "Fecha de postulación:")
    cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
    cv.drawString(6*cm, y, fecha_str)
    y -= 0.6*cm

    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_ROJO)
    cv.drawString(1.2*cm, y, "Estado actual:")
    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_PRIMARIO)
    cv.drawString(6*cm, y, str(postulacion_data.get("estado", "N/A")).upper())
    y -= 0.8*cm

    # Caja de comentarios
    comentario = postulacion_data.get("comentario") or "Sin comentarios registrados."
    _rounded_rect(cv, 0.8*cm, y - 3.5*cm, width - 1.6*cm, 3.8*cm, 0.3*cm,
                  C_FONDO2, stroke_color=colors.HexColor("#9FA8DA"), line_width=0.5)
    cv.setFillColor(C_ACENTO)
    cv.setFont("Helvetica-Bold", 9)
    cv.drawString(1.2*cm, y - 0.3*cm, "Comentarios del empleador:")

    styles = getSampleStyleSheet()
    style_body = ParagraphStyle("Coment", parent=styles["Normal"],
                                fontName="Helvetica", fontSize=9, leading=13,
                                textColor=C_TEXTO)
    para = Paragraph(str(comentario), style_body)
    para.wrapOn(cv, width - 2.4*cm, 3*cm)
    para.drawOn(cv, 1.2*cm, y - 3.3*cm)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_empresa(empresa_data):
    """Genera PDF con perfil de empresa."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "PERFIL EMPRESARIAL",
                          subtitulo=empresa_data.get("razon_social", ""))
    _pie_pagina(cv, width, 1)

    y = y_libre - 0.6*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Información General", C_ACENTO)
    y -= 0.3*cm

    datos = [
        ("Razón Social:", empresa_data.get('razon_social', 'N/A'), C_ACENTO),
        ("RUC:",          empresa_data.get('ruc', 'N/A'), C_PRIMARIO),
        ("Sector:",       empresa_data.get('sector_economico', 'N/A'), C_NARANJA),
        ("Tamaño:",       empresa_data.get('tamano_empresa', 'N/A'), C_VERDE),
        ("Dirección:",    empresa_data.get('direccion', 'N/A'), C_CYAN),
        ("Email:",        empresa_data.get('email_contacto', 'N/A'), C_PURPURA),
        ("Teléfono:",     empresa_data.get('telefono_contacto', 'N/A'), C_ROJO),
        ("Sitio Web:",    empresa_data.get('sitio_web', 'N/A'), C_VERDE),
        ("Estado:",       (empresa_data.get('estado', 'N/A') or '').upper(), C_ACENTO),
    ]
    for label, value, color in datos:
        cv.setFont("Helvetica-Bold", 9); cv.setFillColor(color)
        cv.drawString(1.2*cm, y, label)
        cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
        cv.drawString(5.5*cm, y, str(value))
        y -= 0.6*cm

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_ficha_empresa(empresa_data, estadisticas, ofertas_resumen, public_url=None):
    """Genera ficha oficial de empresa con QR, KPIs y diseño moderno."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "FICHA DE EMPRESA",
                          subtitulo=empresa_data.get("razon_social", ""))
    _pie_pagina(cv, width, 1)

    # KPIs actividad
    kpi_w = (width - 1.6*cm) / 3 - 0.3*cm
    kpi_h = 1.4*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    for i, (val, lbl, color) in enumerate([
        (ofertas_resumen.get('total_ofertas', 0),    "Ofertas publicadas",   C_ACENTO),
        (ofertas_resumen.get('ofertas_activas', 0),  "Ofertas activas",      C_VERDE),
        (estadisticas.get('total_postulaciones', 0), "Postulaciones",        C_NARANJA),
    ]):
        _kpi_box(cv, 0.8*cm + i*(kpi_w + 0.3*cm), kpi_y, kpi_w, kpi_h, val, lbl, color)

    y = kpi_y - 0.6*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Datos de la Empresa", C_ACENTO)
    y -= 0.3*cm

    datos = [
        ("Razón Social:",    empresa_data.get("razon_social", "N/A"), C_PRIMARIO),
        ("Nombre Comercial:",empresa_data.get("nombre_comercial", "N/A"), C_ACENTO),
        ("RUC:",             empresa_data.get("ruc", "N/A"), C_NARANJA),
        ("Sector:",          empresa_data.get("sector_economico", "N/A"), C_VERDE),
        ("Tamaño:",          empresa_data.get("tamano_empresa", "N/A"), C_CYAN),
        ("Dirección:",       empresa_data.get("direccion", "N/A"), C_PURPURA),
        ("Email:",           empresa_data.get("email_contacto", "N/A"), C_ROJO),
        ("Teléfono:",        empresa_data.get("telefono_contacto", "N/A"), C_VERDE),
        ("Sitio Web:",       empresa_data.get("sitio_web", "N/A"), C_CYAN),
    ]
    col_w = (width - 2*cm) / 2 - 0.5*cm
    for idx, (label, value, color) in enumerate(datos):
        col = idx % 2
        row = idx // 2
        x_pos = 0.8*cm + col * (col_w + 0.5*cm)
        y_pos = y - row * 0.65*cm
        cv.setFont("Helvetica-Bold", 8.5); cv.setFillColor(color)
        cv.drawString(x_pos, y_pos, label)
        cv.setFont("Helvetica", 8.5); cv.setFillColor(C_TEXTO)
        cv.drawString(x_pos + 3.8*cm, y_pos, str(value)[:30])

    rows = math.ceil(len(datos) / 2)
    y -= rows * 0.65*cm + 0.5*cm

    y = _seccion_titulo(cv, 0.8*cm, y, width - (5*cm if public_url else 1.6*cm),
                        "Estado de Validación", C_VERDE)
    y -= 0.3*cm

    estado = (empresa_data.get("estado") or "N/A").upper()
    fecha_ap = empresa_data.get("fecha_aprobacion")
    fecha_ap_str = fecha_ap.strftime("%d/%m/%Y %H:%M") if hasattr(fecha_ap, "strftime") else str(fecha_ap or "—")

    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_VERDE)
    cv.drawString(1.2*cm, y, "Estado:")
    cv.setFont("Helvetica-Bold", 11); cv.setFillColor(C_PRIMARIO)
    cv.drawString(4.5*cm, y, estado)
    y -= 0.65*cm
    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_CYAN)
    cv.drawString(1.2*cm, y, "Fecha aprobación:")
    cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
    cv.drawString(5.5*cm, y, fecha_ap_str)

    # QR
    if public_url:
        try:
            size = 3.8*cm
            qr_widget = qr.QrCodeWidget(public_url)
            bounds = qr_widget.getBounds()
            qw = bounds[2] - bounds[0]; qh = bounds[3] - bounds[1]
            d = Drawing(size, size, transform=[size/qw, 0, 0, size/qh, 0, 0])
            d.add(qr_widget)
            qr_x = width - 0.8*cm - size
            qr_y = 1.2*cm
            _rounded_rect(cv, qr_x - 0.2*cm, qr_y - 0.2*cm, size + 0.4*cm, size + 0.8*cm,
                          0.2*cm, C_FONDO, stroke_color=colors.HexColor("#9FA8DA"), line_width=0.5)
            renderPDF.draw(d, cv, qr_x, qr_y + 0.2*cm)
            cv.setFont("Helvetica", 7); cv.setFillColor(C_GRIS_CLARO)
            cv.drawCentredString(qr_x + size/2, qr_y - 0.05*cm, "Perfil público")
        except Exception:
            pass

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_ofertas_empresa(empresa_data, ofertas, fecha_inicio, fecha_fin):
    """Genera PDF de ofertas de una empresa."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "OFERTAS LABORALES POR EMPRESA",
                          subtitulo=f"{empresa_data.get('razon_social','')}  |  RUC: {empresa_data.get('ruc','')}  |  Período: {fecha_inicio} – {fecha_fin}")
    _pie_pagina(cv, width, 1)

    data = [["TÍTULO", "TIPO", "MODALIDAD", "PUBLICACIÓN", "LÍMITE", "ACTIVA", "POST."]]
    for o in ofertas:
        data.append([
            str(o.get("titulo", ""))[:48],
            str(o.get("tipo", "")), str(o.get("modalidad", "")),
            o.get("fecha_publicacion").strftime("%d/%m/%Y") if o.get("fecha_publicacion") else "",
            o.get("fecha_limite_postulacion").strftime("%d/%m/%Y") if o.get("fecha_limite_postulacion") else "",
            "Sí" if o.get("activa") else "No",
            str(o.get("total_postulaciones", 0)),
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [10*cm, 3*cm, 3*cm, 3.2*cm, 3.2*cm, 2.2*cm, 2.5*cm],
                            [C_PRIMARIO, C_NARANJA, C_CYAN, C_VERDE, C_PURPURA, C_VERDE, C_ROJO],
                            y_inicio=y_libre)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_empresas_seleccionadas(empresas_data, kpis, titulo="Reporte de Empresas Seleccionadas"):
    """Genera PDF con tabla + KPIs de empresas filtradas."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, titulo, subtitulo=titulo)
    _pie_pagina(cv, width, 1)

    # KPIs
    kpi_w = (width - 1.6*cm) / 4 - 0.3*cm
    kpi_h = 1.5*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    for i, (val, lbl, color) in enumerate([
        (kpis.get('total', 0),      "Total empresas",  C_ACENTO),
        (kpis.get('activas', 0),    "Activas",         C_VERDE),
        (kpis.get('pendientes', 0), "Pendientes",      C_NARANJA),
        (kpis.get('rechazadas', 0), "Rechazadas",      C_ROJO),
    ]):
        _kpi_box(cv, 0.8*cm + i*(kpi_w + 0.3*cm), kpi_y, kpi_w, kpi_h, val, lbl, color)

    y = kpi_y - 0.5*cm
    # Top sectores
    _rounded_rect(cv, 0.8*cm, y - 0.7*cm, width - 1.6*cm, 0.65*cm, 0.2*cm, C_FONDO2)
    cv.setFont("Helvetica-Bold", 8); cv.setFillColor(C_PRIMARIO)
    cv.drawString(1.2*cm, y - 0.45*cm, f"Top sectores: {kpis.get('top_sectores', '—')}")
    y -= 1.0*cm

    data = [["RUC", "RAZÓN SOCIAL", "SECTOR", "TAMAÑO", "ESTADO"]]
    for e in empresas_data:
        data.append([
            str(e.get("ruc", "")),
            str(e.get("razon_social", ""))[:38],
            str(e.get("sector_economico", ""))[:22],
            str(e.get("tamano_empresa", ""))[:15],
            str(e.get("estado", ""))[:12],
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [3.2*cm, 7.8*cm, 4.2*cm, 3*cm, 2.8*cm],
                            [C_PRIMARIO, C_ACENTO, C_NARANJA, C_CYAN, C_VERDE],
                            y_inicio=y)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_empleadores_empresa(empresa_data, empleadores):
    """Genera PDF con listado de empleadores de una empresa."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "REPORTE DE EMPLEADORES",
                          subtitulo=f"{empresa_data.get('razon_social','')}  |  RUC: {empresa_data.get('ruc','')}")
    _pie_pagina(cv, width, 1)

    data = [["NOMBRE", "CARGO", "EMAIL", "FECHA REGISTRO", "ADMIN"]]
    for emp in empleadores:
        fecha_reg = emp.get("fecha_registro")
        fecha_str = fecha_reg.strftime("%d/%m/%Y") if hasattr(fecha_reg, "strftime") else str(fecha_reg or "")
        data.append([
            str(emp.get("nombre", ""))[:35], str(emp.get("cargo", ""))[:22],
            str(emp.get("email", ""))[:35], fecha_str,
            "Sí" if emp.get("es_administrador_empresa") else "No",
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [7*cm, 4.5*cm, 7*cm, 4*cm, 2.5*cm],
                            [C_PRIMARIO, C_ACENTO, C_CYAN, C_VERDE, C_NARANJA],
                            y_inicio=y_libre)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_dashboard_empresa(empresa_data, stats, ofertas_recientes):
    """Genera PDF resumen del dashboard de empresa con KPIs y tabla de actividad."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "DASHBOARD DE EMPRESA",
                          subtitulo=empresa_data.get("razon_social", ""))
    _pie_pagina(cv, width, 1)

    # KPIs
    kpi_w = (width - 1.6*cm) / 4 - 0.3*cm
    kpi_h = 1.5*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    for i, (val, lbl, color) in enumerate([
        (stats.get('total_ofertas', 0),       "Ofertas totales",  C_ACENTO),
        (stats.get('ofertas_activas', 0),     "Activas",          C_VERDE),
        (stats.get('total_postulaciones', 0), "Postulaciones",    C_NARANJA),
        (stats.get('total_empleadores', 0),   "Empleadores",      C_PURPURA),
    ]):
        _kpi_box(cv, 0.8*cm + i*(kpi_w + 0.3*cm), kpi_y, kpi_w, kpi_h, val, lbl, color)

    y = kpi_y - 0.6*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Datos de la Empresa", C_ACENTO)
    y -= 0.3*cm

    datos = [
        ("Razón Social:", empresa_data.get("razon_social", "N/A"), C_PRIMARIO),
        ("RUC:",          empresa_data.get("ruc", "N/A"), C_NARANJA),
        ("Sector:",       empresa_data.get("sector_economico", "N/A"), C_CYAN),
        ("Estado:",       (empresa_data.get("estado") or "N/A").upper(), C_VERDE),
    ]
    for label, value, color in datos:
        cv.setFont("Helvetica-Bold", 9); cv.setFillColor(color)
        cv.drawString(1.2*cm, y, label)
        cv.setFont("Helvetica", 9); cv.setFillColor(C_TEXTO)
        cv.drawString(5.5*cm, y, str(value))
        y -= 0.6*cm

    y -= 0.3*cm
    y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Actividad reciente (últimas ofertas)", C_NARANJA)
    y -= 0.3*cm

    data = [["OFERTA", "PUBLICACIÓN", "ESTADO", "POST."]]
    for r in (ofertas_recientes or []):
        fecha_pub = r.get("fecha_publicacion")
        fecha_str = fecha_pub.strftime("%d/%m/%Y") if hasattr(fecha_pub, "strftime") else ""
        data.append([
            str(r.get("titulo", ""))[:52], fecha_str,
            "Activa" if r.get("activa") else "Cerrada",
            str(r.get("postulaciones", 0)),
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [10.5*cm, 3*cm, 3*cm, 2.5*cm],
                            [C_PRIMARIO, C_CYAN, C_VERDE, C_NARANJA],
                            y_inicio=y)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_oferta_detalle(empresa_data, oferta_data, estadisticas_postulaciones=None, public_url=None):
    """Genera PDF detalle de una oferta laboral."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    cv.setAuthor("Sistema de Egresados UNT")

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "FICHA DE OFERTA LABORAL",
                          subtitulo=oferta_data.get("titulo", ""))
    _pie_pagina(cv, width, 1)

    # Empresa info
    cv.setFont("Helvetica-Bold", 9); cv.setFillColor(C_ACENTO)
    cv.drawString(0.8*cm, y_libre - 0.5*cm,
                  f"Empresa: {empresa_data.get('razon_social','N/A')}   |   RUC: {empresa_data.get('ruc','N/A')}")
    y = y_libre - 1.2*cm

    # Datos clave en dos columnas con cajas
    info = [
        ("Tipo",         oferta_data.get("tipo", "N/A"),       C_NARANJA),
        ("Modalidad",    oferta_data.get("modalidad", "N/A"),   C_CYAN),
        ("Ubicación",    oferta_data.get("ubicacion", "N/A"),   C_VERDE),
        ("Salario",      oferta_data.get("salario", "N/A"),     C_PURPURA),
        ("Publicación",  oferta_data.get("fecha_publicacion", "N/A"), C_ACENTO),
        ("Límite",       oferta_data.get("fecha_limite", "N/A"), C_ROJO),
    ]
    box_w = (width - 2.4*cm) / 3 - 0.2*cm
    box_h = 1.1*cm
    cols = 3
    for idx, (lbl, val, color) in enumerate(info):
        col = idx % cols
        row = idx // cols
        bx = 0.8*cm + col * (box_w + 0.2*cm)
        by = y - row * (box_h + 0.25*cm) - box_h
        _rounded_rect(cv, bx, by, box_w, box_h, 0.2*cm, C_FONDO2)
        cv.setFillColor(color); cv.setFont("Helvetica-Bold", 7.5)
        cv.drawString(bx + 0.25*cm, by + box_h - 0.35*cm, lbl.upper())
        cv.setFillColor(C_TEXTO); cv.setFont("Helvetica-Bold", 9)
        cv.drawString(bx + 0.25*cm, by + 0.18*cm, str(val)[:28])

    rows_data = math.ceil(len(info) / cols)
    y -= rows_data * (box_h + 0.25*cm) + 0.4*cm

    # Descripción y requisitos
    styles = getSampleStyleSheet()
    style_body = ParagraphStyle("Body2", parent=styles["Normal"],
                                fontName="Helvetica", fontSize=8.5, leading=13, textColor=C_TEXTO)

    for titulo_sec, key, color_sec in [
        ("Descripción", "descripcion", C_ACENTO),
        ("Requisitos",  "requisitos",  C_VERDE),
    ]:
        if y < 3*cm:
            break
        y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, titulo_sec, color_sec)
        y -= 0.2*cm
        texto = str(oferta_data.get(key) or "—")
        _rounded_rect(cv, 0.8*cm, y - 2.5*cm, width - 1.6*cm, 2.5*cm, 0.2*cm, C_FONDO2)
        para = Paragraph(texto, style_body)
        para.wrapOn(cv, width - 2.4*cm, 2.3*cm)
        para.drawOn(cv, 1.0*cm, y - 2.3*cm)
        y -= 2.9*cm

    # Resumen de postulaciones
    if estadisticas_postulaciones and y > 3*cm:
        y = _seccion_titulo(cv, 0.8*cm, y, width - 1.6*cm, "Resumen de Postulaciones", C_NARANJA)
        y -= 0.3*cm
        items = [
            ("Total",        estadisticas_postulaciones.get("total", 0), C_PRIMARIO),
            ("Recibidos",    estadisticas_postulaciones.get("recibidos", 0), C_CYAN),
            ("En revisión",  estadisticas_postulaciones.get("en_revision", 0), C_NARANJA),
            ("Entrevista",   estadisticas_postulaciones.get("entrevista", 0), C_AMARILLO),
            ("Seleccionados",estadisticas_postulaciones.get("seleccionado", 0), C_VERDE),
            ("Descartados",  estadisticas_postulaciones.get("descartado", 0), C_ROJO),
        ]
        mini_w = (width - 2.4*cm) / len(items) - 0.15*cm
        for idx, (lbl, val, color) in enumerate(items):
            bx = 0.8*cm + idx * (mini_w + 0.15*cm)
            _kpi_box(cv, bx, y - 1.4*cm, mini_w, 1.3*cm, val, lbl, color)

    # QR
    if public_url:
        try:
            size = 3*cm
            qr_widget = qr.QrCodeWidget(public_url)
            bounds = qr_widget.getBounds()
            qw = bounds[2] - bounds[0]; qh = bounds[3] - bounds[1]
            d = Drawing(size, size, transform=[size/qw, 0, 0, size/qh, 0, 0])
            d.add(qr_widget)
            renderPDF.draw(d, cv, width - 0.8*cm - size, 1.1*cm)
            cv.setFont("Helvetica", 7); cv.setFillColor(C_GRIS_CLARO)
            cv.drawCentredString(width - 0.8*cm - size/2, 1.0*cm, "Sitio web empresa")
        except Exception:
            pass

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_constancia(nombre_usuario, nombre_evento, fecha_evento):
    """Genera un buffer de bytes con el PDF de la constancia."""
    buffer = io.BytesIO()

    # Configurar página en horizontal
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # --- Diseño de fondo / Bordes ---
    cv.setStrokeColor(colors.HexColor("#0056b3"))
    cv.setLineWidth(5)
    cv.rect(1*cm, 1*cm, width-2*cm, height-2*cm)  # Borde exterior

    cv.setLineWidth(1)
    cv.rect(1.2*cm, 1.2*cm, width-2.4*cm, height-2.4*cm)  # Borde interior fino

    # --- Encabezado ---
    cv.setFont("Helvetica-Bold", 24)
    cv.setFillColor(colors.HexColor("#0056b3"))
    cv.drawCentredString(width/2, height - 4*cm, "UNIVERSIDAD NACIONAL DE TRUJILLO")

    cv.setFont("Helvetica", 14)
    cv.setFillColor(colors.black)
    cv.drawCentredString(width/2, height - 5*cm, "Dirección de Seguimiento del Egresado y Empleabilidad")

    # --- Título Central ---
    cv.setFont("Times-BoldItalic", 48)
    cv.drawCentredString(width/2, height/2 + 2*cm, "Constancia de Participación")

    # --- Cuerpo del texto ---
    cv.setFont("Helvetica", 18)
    cv.drawCentredString(width/2, height/2 - 0.5*cm, "Se otorga la presente a:")

    cv.setFont("Helvetica-Bold", 26)
    cv.drawCentredString(width/2, height/2 - 2*cm, nombre_usuario.upper())

    # Texto descriptivo
    cv.setFont("Helvetica", 16)
    texto = f"Por haber participado satisfactoriamente en el evento <b>'{nombre_evento}'</b>, realizado el día {fecha_evento}."

    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=20,
        alignment=1  # Center
    )

    p = Paragraph(texto, style_body)
    p.wrapOn(cv, width-6*cm, 4*cm)
    p.drawOn(cv, 3*cm, height/2 - 5*cm)

    # --- Firmas ---
    cv.setDash(1, 2)
    cv.line(4*cm, 4*cm, 10*cm, 4*cm)
    cv.line(width-10*cm, 4*cm, width-4*cm, 4*cm)
    cv.setDash()

    cv.setFont("Helvetica", 10)
    cv.drawCentredString(7*cm, 3.5*cm, "Director de Seguimiento del Egresado")
    cv.drawCentredString(width-7*cm, 3.5*cm, "Secretario Académico - UNT")

    # --- Fecha de emisión ---
    fecha_emision = datetime.now().strftime("%d de %B de %Y")
    cv.setFont("Helvetica-Oblique", 10)
    cv.drawRightString(width-2*cm, 1.5*cm, f"Emitido el: {fecha_emision}")

    cv.showPage()
    cv.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generar_pdf_reporte_pagos(pagos_data):
    """Genera PDF de reporte de pagos con KPIs y tabla moderna."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "REPORTE DE PAGOS Y VOUCHERS",
                          subtitulo="Reporte de Pagos y Vouchers")
    _pie_pagina(cv, width, 1)

    total_monto  = sum(float(p.get("monto", 0)) for p in pagos_data)
    total_pagos  = len(pagos_data)
    pagados      = sum(1 for p in pagos_data if p.get("pagado"))
    validados    = sum(1 for p in pagos_data if p.get("validado"))

    kpi_w = (width - 1.6*cm) / 4 - 0.3*cm
    kpi_h = 1.4*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    for i, (val, lbl, color) in enumerate([
        (f"S/.{total_monto:,.0f}", "Total ingresos",  C_VERDE),
        (total_pagos,              "Registros",        C_ACENTO),
        (pagados,                  "Pagados",          C_CYAN),
        (validados,                "Validados",        C_NARANJA),
    ]):
        _kpi_box(cv, 0.8*cm + i*(kpi_w + 0.3*cm), kpi_y, kpi_w, kpi_h, val, lbl, color)

    y_tabla = kpi_y - 0.5*cm
    data = [["VOUCHER", "USUARIO", "CONCEPTO", "MONTO (S/.)", "FECHA", "PAGADO", "VALIDADO"]]
    for p in pagos_data:
        data.append([
            str(p.get("codigo_voucher", ""))[:20],
            str(p.get("email", ""))[:28],
            str(p.get("concepto", "")).upper()[:18],
            f"{float(p.get('monto', 0)):.2f}",
            p.get("fecha_pago").strftime("%d/%m/%Y %H:%M") if hasattr(p.get("fecha_pago"), "strftime") else str(p.get("fecha_pago", "")),
            "Sí" if p.get("pagado") else "No",
            "Sí" if p.get("validado") else "No",
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [4*cm, 5.5*cm, 3.5*cm, 3*cm, 4.5*cm, 2*cm, 2*cm],
                            [C_PRIMARIO, C_ACENTO, C_NARANJA, C_VERDE, C_CYAN, C_PURPURA, C_ROJO],
                            y_inicio=y_tabla)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_resultados_encuestas(resultados_data, titulo_encuesta="Resultados de Encuesta"):
    """Genera PDF de resultados de encuestas con diseño moderno."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, "RESULTADOS DE ENCUESTA",
                          subtitulo=titulo_encuesta)
    _pie_pagina(cv, width, 1)

    total_resp = sum(int(r.get("cantidad", 0)) for r in resultados_data)

    kpi_w = (width - 1.6*cm) / 2 - 0.3*cm
    kpi_h = 1.3*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    _kpi_box(cv, 0.8*cm, kpi_y, kpi_w, kpi_h, total_resp, "Total Respuestas", C_ACENTO)
    _kpi_box(cv, 0.8*cm + kpi_w + 0.3*cm, kpi_y, kpi_w, kpi_h,
             len(set(r.get("texto_pregunta") for r in resultados_data)),
             "Preguntas", C_NARANJA)

    y_tabla = kpi_y - 0.5*cm
    data = [["PREGUNTA", "TIPO", "RESPUESTA", "CANTIDAD", "PORCENTAJE"]]
    for item in resultados_data:
        data.append([
            str(item.get("texto_pregunta", ""))[:45],
            str(item.get("tipo_respuesta", "")),
            str(item.get("respuesta", ""))[:32],
            str(int(item.get("cantidad", 0))),
            f"{float(item.get('porcentaje', 0)):.1f}%",
        ])

    _dibujar_tabla_paginada(cv, width, height, data,
                            [9*cm, 3.5*cm, 6.5*cm, 2.5*cm, 2.5*cm],
                            [C_PRIMARIO, C_NARANJA, C_ACENTO, C_VERDE, C_CYAN],
                            y_inicio=y_tabla)

    cv.showPage()
    cv.save()
    return buffer.getvalue()


def generar_pdf_reporte_generico(datos_list, titulo_reporte="Reporte"):
    """Genera PDF genérico para cualquier conjunto de datos."""
    buffer = io.BytesIO()
    cv = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    _marca_agua(cv, width, height)
    y_libre = _encabezado(cv, width, height, titulo_reporte.upper(), subtitulo=titulo_reporte)
    _pie_pagina(cv, width, 1)

    if not datos_list:
        cv.setFont("Helvetica-Bold", 12); cv.setFillColor(C_GRIS_CLARO)
        cv.drawCentredString(width/2, height/2, "No hay datos para mostrar")
        cv.showPage(); cv.save()
        return buffer.getvalue()

    columnas = list(datos_list[0].keys())[:7]
    n = len(columnas)
    col_colors_cycle = KPI_COLORS[:n]

    kpi_h = 1.3*cm
    kpi_w = (width - 1.6*cm) / 2 - 0.3*cm
    kpi_y = y_libre - 0.5*cm - kpi_h
    _kpi_box(cv, 0.8*cm, kpi_y, kpi_w, kpi_h, len(datos_list), "Total Registros", C_ACENTO)

    y_tabla = kpi_y - 0.5*cm
    data = [[c.upper() for c in columnas]]
    for item in datos_list:
        fila = [str(item.get(c, ""))[:38] for c in columnas]
        data.append(fila)

    col_w = (width - 1.6*cm) / n
    _dibujar_tabla_paginada(cv, width, height, data,
                            [col_w] * n, col_colors_cycle,
                            y_inicio=y_tabla)

    cv.showPage()
    cv.save()
    return buffer.getvalue()