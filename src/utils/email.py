"""
Utilidades para envío de correos electrónicos.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional
import streamlit as st
from src.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

def send_email(to_email: str, subject: str, body: str, is_html: bool = False, attachments: Optional[List[dict]] = None):
    """
    Envía un correo electrónico.
    attachments: Lista de diccionarios con {'filename': str, 'content': bytes}
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"SMTP no configurado. Correo para {to_email} no enviado.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        # Cuerpo del mensaje
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        # Adjuntos
        if attachments:
            for att in attachments:
                part = MIMEApplication(att['content'], Name=att['filename'])
                part['Content-Disposition'] = f'attachment; filename="{att["filename"]}"'
                msg.attach(part)

        # Conexión al servidor
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error al enviar email a {to_email}: {e}")
        return False

def enviar_notificacion_evento(to_email: str, evento_titulo: str, fecha: str):
    """Envía un correo informativo sobre un evento."""
    subject = f"Confirmación de inscripción: {evento_titulo}"
    body = f"""
    <html>
        <body>
            <h2>¡Hola!</h2>
            <p>Te has inscrito exitosamente al evento: <strong>{evento_titulo}</strong>.</p>
            <p><strong>Fecha:</strong> {fecha}</p>
            <p>¡Te esperamos!</p>
            <hr>
            <p><small>Sistema de Gestión de Egresados UNT</small></p>
        </body>
    </html>
    """
    return send_email(to_email, subject, body, is_html=True)
