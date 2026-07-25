import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
from datetime import datetime
import config
import streamlit as st

def enviar_email(destinatario, asunto, html_content):
    """Envía correos electrónicos automatizados."""
    msg = MIMEMultipart()
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, destinatario, msg.as_string())
        return True, "Correo enviado con éxito"
    except Exception as e:
        error_msg = f"Error SMTP de Gmail: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def enviar_whatsapp(numero, texto):
    """Envía mensajes a WhatsApp usando la API."""
    if not numero.startswith("+"):
        numero = "+57" + numero

    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json"
    payload = {
        'From': config.TWILIO_WHATSAPP_NUMBER,
        'To': f'whatsapp:{numero}',
        'Body': texto
    }

    try:
        res = requests.post(url, data=payload, auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN))
        if res.status_code in [200, 201]:
            return True, "WhatsApp enviado con éxito"
        else:
            error_msg = f"Error Twilio (Código {res.status_code}): {res.text}"
            print(f"⚠️ {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"Error de red con WhatsApp: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def enviar_alerta_individual(certificado_id):
    """Envía correo y WhatsApp de forma manual para un certificado y reporta el estado exacto."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                t.nombres, t.apellidos, t.correo, t.telefono, 
                c.nivel_curso, c.fecha_vencimiento
            FROM certificados c
            JOIN trabajadores t ON c.trabajador_id = t.id
            WHERE c.id = ?
        """, (certificado_id,))
        
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, "Certificado no encontrado en la base de datos."

        nombre = f"{row['nombres']} {row['apellidos']}"
        correo = row['correo']
        telefono = row['telefono']
        curso = row['nivel_curso']
        fecha_str = row['fecha_vencimiento']

        hoy = datetime.now().date()
        fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dias_restantes = (fecha_venc - hoy).days

        asunto = f"⚠️ Alerta Vencimiento de Curso: {curso}"
        mensaje_html = f"""
        <h3>Hola {nombre},</h3>
        <p>Te recordamos que tu curso de <b>{curso}</b> {'ya se encuentra vencido' if dias_restantes < 0 else f'vence en {dias_restantes} días'}.</p>
        <p>Por favor ponte en contacto con nosotros para gestionar tu renovación.</p>
        """

        resultados = []

        if correo:
            exito_c, msg_c = enviar_email(correo, asunto, mensaje_html)
            resultados.append(f"Correo: {msg_c}")
        else:
            resultados.append("Correo: No tiene correo registrado")

        if telefono:
            msg_wa = f"Hola {nombre}, tu curso de {curso} {'ya venció' if dias_restantes < 0 else f'vence en {dias_restantes} días'}. ¡Comunícate con nosotros para renovarlo!"
            exito_w, msg_w = enviar_whatsapp(str(telefono), msg_wa)
            resultados.append(f"WhatsApp: {msg_w}")
        else:
            resultados.append("WhatsApp: No tiene teléfono registrado")

        return True, " | ".join(resultados)
    except Exception as e:
        return False, f"Excepción general: {str(e)}"
        
    except Exception as e:
        print(f"Error procesando alertas: {e}")
        return False, str(e)
