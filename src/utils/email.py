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

class EmailSender:
    """Clase para enviar correos electrónicos."""
    
    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
    
    def send_email(self, to_emails: List[str], subject: str, 
                   body: str, html_body: Optional[str] = None,
                   attachments: Optional[List[dict]] = None):
        """
        Envía un correo electrónico.
        
        Args:
            to_emails: Lista de destinatarios
            subject: Asunto del correo
            body: Cuerpo del correo (texto plano)
            html_body: Cuerpo del correo en HTML (opcional)
            attachments: Lista de archivos adjuntos [{'filename':, 'content':, 'mime_type':}]
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = ', '.join(to_emails)
            
            # Adjuntar cuerpo en texto plano
            msg.attach(MIMEText(body, 'plain'))
            
            # Adjuntar cuerpo en HTML si existe
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Adjuntar archivos
            if attachments:
                for att in attachments:
                    part = MIMEApplication(att['content'], Name=att['filename'])
                    part['Content-Disposition'] = f'attachment; filename="{att["filename"]}"'
                    msg.attach(part)
            
            # Enviar correo
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            return True, "Correo enviado exitosamente"
            
        except Exception as e:
            return False, f"Error al enviar correo: {str(e)}"
    
    def send_welcome_email(self, to_email: str, nombre: str, rol: str):
        """Envía correo de bienvenida."""
        subject = "Bienvenido al Sistema de Egresados UNT"
        
        body = f"""
        Hola {nombre},
        
        Bienvenido al Sistema de Gestión de Egresados de la Universidad Nacional de Trujillo.
        
        Te has registrado como {rol}. Ya puedes acceder al sistema y comenzar a utilizar todas las funcionalidades.
        
        Para acceder, visita: https://sistema.unitru.edu.pe
        
        Saludos,
        Equipo UNT
        """
        
        html_body = f"""
        <html>
            <body>
                <h2>Bienvenido al Sistema de Egresados UNT</h2>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Bienvenido al Sistema de Gestión de Egresados de la Universidad Nacional de Trujillo.</p>
                <p>Te has registrado como <strong>{rol}</strong>. Ya puedes acceder al sistema y comenzar a utilizar todas las funcionalidades.</p>
                <p>Para acceder, visita: <a href="https://sistema.unitru.edu.pe">https://sistema.unitru.edu.pe</a></p>
                <br>
                <p>Saludos,<br>Equipo UNT</p>
            </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body, html_body)
    
    def send_password_reset(self, to_email: str, nombre: str, reset_link: str):
        """Envía correo para restablecer contraseña."""
        subject = "Restablecer tu contraseña - Sistema Egresados UNT"
        
        body = f"""
        Hola {nombre},
        
        Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva contraseña:
        
        {reset_link}
        
        Si no solicitaste este cambio, ignora este correo.
        
        El enlace expirará en 24 horas.
        
        Saludos,
        Equipo UNT
        """
        
        html_body = f"""
        <html>
            <body>
                <h2>Restablecer Contraseña</h2>
                <p>Hola <strong>{nombre}</strong>,</p>
                <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a></p>
                <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                <p>{reset_link}</p>
                <p>Si no solicitaste este cambio, ignora este correo.</p>
                <p>El enlace expirará en 24 horas.</p>
                <br>
                <p>Saludos,<br>Equipo UNT</p>
            </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body, html_body)
    
    def send_notification(self, to_email: str, subject: str, message: str):
        """Envía una notificación por correo."""
        body = f"""
        {message}
        
        ---
        Sistema de Gestión de Egresados - UNT
        """
        
        return self.send_email([to_email], subject, body)
    
    def send_voucher(self, to_email: str, nombre: str, voucher_data: dict, pdf_content: bytes):
        """Envía voucher de pago por correo."""
        subject = f"Voucher de Pago - {voucher_data['codigo']}"
        
        body = f"""
        Hola {nombre},
        
        Adjuntamos el voucher de tu pago con los siguientes detalles:
        
        Código: {voucher_data['codigo']}
        Concepto: {voucher_data['concepto']}
        Monto: S/. {voucher_data['monto']:.2f}
        Fecha: {voucher_data['fecha']}
        
        Puedes validar este voucher en: https://sistema.unitru.edu.pe/validar/{voucher_data['codigo']}
        
        Gracias por tu pago.
        
        Saludos,
        Equipo UNT
        """
        
        attachments = [{
            'filename': f"voucher_{voucher_data['codigo']}.pdf",
            'content': pdf_content,
            'mime_type': 'application/pdf'
        }]
        
        return self.send_email([to_email], subject, body, attachments=attachments)

# Instancia global
email_sender = EmailSender()