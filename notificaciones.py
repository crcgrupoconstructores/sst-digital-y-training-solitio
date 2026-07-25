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
        conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por su nombre exacto
        cursor = conn.cursor()
        
        # Consultar la tabla de registros
        cursor.execute("SELECT * FROM clientes")
        registros = cursor.fetchall()

        alertas_enviadas = 0
        hoy = datetime.now().date()

        for row in registros:
            # Obtener datos de forma segura sin importar variaciones de nombre
            nombre = row["nombre"] if "nombre" in row.keys() else "Cliente"
            correo = row["correo"] if "correo" in row.keys() else row.get("email", None)
            telefono = row["telefono"] if "telefono" in row.keys() else row.get("celular", None)
            curso = row["nivel_curso"] if "nivel_curso" in row.keys() else row.get("curso", "Curso de Alturas")
            fecha_str = row["fecha_vencimiento"] if "fecha_vencimiento" in row.keys() else None

            if not fecha_str:
                continue
            
            fecha_str = str(fecha_str).replace("/", "-").strip()
            
            try:
                fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            dias_restantes = (fecha_venc - hoy).days

            # Disparar si faltan 30 días o menos para el 2026-08-01 (faltan 7 días)
            if dias_restantes <= 30:
                asunto = f"⚠️ Alerta Vencimiento de Curso: {curso}"
                mensaje_html = f"""
                <h3>Hola {nombre},</h3>
                <p>Te recordamos que tu curso de <b>{curso}</b> {'ya se encuentra vencido' if dias_restantes < 0 else f'vence en {dias_restantes} días'}.</p>
                <p>Por favor ponte en contacto con nosotros para gestionar tu renovación.</p>
                """
                
                if correo:
                    enviar_email(correo, asunto, mensaje_html)
                
                if telefono:
                    msg_wa = f"Hola {nombre}, tu curso de {curso} {'ya venció' if dias_restantes < 0 else f'vence en {dias_restantes} días'}. ¡Comunícate con nosotros para renovarlo!"
                    enviar_whatsapp(str(telefono), msg_wa)

                # Marcar en la base de datos que ya se envió la alerta de 30 días
                if "id" in row.keys():
                    cursor.execute("UPDATE clientes SET alerta_30d_enviada = 1 WHERE id = ?", (row["id"],))
                
                alertas_enviadas += 1

        conn.commit()
        conn.close()

        return True, f"Proceso completado. Se enviaron {alertas_enviadas} alertas."
        
    except Exception as e:
        print(f"Error procesando alertas: {e}")
        return False, str(e)
