import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
from datetime import datetime, timedelta
import config

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
        print(f"📧 Correo enviado a: {destinatario}")
        return True
    except Exception as e:
        print(f"❌ Error al enviar correo a {destinatario}: {e}")
        return False

def enviar_whatsapp(numero, texto):
    """Envía mensajes a WhatsApp usando la API."""
    if not numero.startswith("+"):
        numero = "+57" + numero  # Indicativo del país (ej. Colombia +57)

    url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json"
    payload = {
        'From': config.TWILIO_WHATSAPP_NUMBER,
        'To': f'whatsapp:{numero}',
        'Body': texto
    }

    try:
        res = requests.post(url, data=payload, auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN))
        if res.status_code in [200, 201]:
            print(f"📱 WhatsApp enviado a: {numero}")
            return True
        else:
            print(f"⚠️ Error enviando WhatsApp: {res.text}")
            return False
    except Exception as e:
        print(f"❌ Error de red con WhatsApp: {e}")
        return False

def ejecutar_alertas_diarias():
    """Consulta la BD y envía las alertas de cursos vencidos o próximos a vencer."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Consultar clientes/alumnos con sus fechas de vencimiento
        cursor.execute("SELECT nombre, correo, telefono, curso, fecha_vencimiento FROM clientes")
        registros = cursor.fetchall()
        conn.close()

        alertas_enviadas = 0
        hoy = datetime.now().date()

        for nombre, correo, telefono, curso, fecha_str in registros:
            if not fecha_str:
                continue
            
            try:
                fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            dias_restantes = (fecha_venc - hoy).days

            # Alerta para cursos por vencer (30 días o menos) o ya vencidos
            if dias_restantes <= 30:
                asunto = f"⚠️ Alerta Vencimiento de Curso: {curso}"
                mensaje_html = f"""
                <h3>Hola {nombre},</h3>
                <p>Te recordamos que tu curso de <b>{curso}</b> {'ya se encuentra vencido' if dias_restantes < 0 else f'vence en {dias_restantes} días'}.</p>
                <p>Por favor ponte en contacto con nosotros para gestionar tu renovación.</p>
                """
                
                # Intentar enviar correo si existe
                if correo:
                    enviar_email(correo, asunto, mensaje_html)
                
                # Intentar enviar WhatsApp si existe
                if telefono:
                    msg_wa = f"Hola {nombre}, tu curso de {curso} {'ya venció' if dias_restantes < 0 else f'vence en {dias_restantes} días'}. ¡Comunícate con nosotros para renovarlo!"
                    enviar_whatsapp(telefono, msg_wa)

                alertas_enviadas += 1

        return True, f"Proceso completado. Se procesaron {alertas_enviadas} alertas."
        
    except Exception as e:
        print(f"Error procesando alertas: {e}")
        return False, str(e)
