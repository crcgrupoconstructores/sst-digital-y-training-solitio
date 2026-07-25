import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
from datetime import datetime
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
            print(f"📱 WhatsApp enviado a: {numero}")
            return True
        else:
            print(f"⚠️ Error enviando WhatsApp: {res.text}")
            return False
    except Exception as e:
        print(f"❌ Error de red con WhatsApp: {e}")
        return False

def enviar_alerta_individual(certificado_id):
    """Envía correo y WhatsApp de forma manual o individual para un certificado específico."""
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
            return False, "Certificado no encontrado."

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

        exito_correo = False
        exito_wa = False

        if correo:
            exito_correo = enviar_email(correo, asunto, mensaje_html)

        if telefono:
            msg_wa = f"Hola {nombre}, tu curso de {curso} {'ya venció' if dias_restantes < 0 else f'vence en {dias_restantes} días'}. ¡Comunícate con nosotros para renovarlo!"
            exito_wa = enviar_whatsapp(str(telefono), msg_wa)

        return True, "Notificación procesada correctamente."
    except Exception as e:
        return False, str(e)

def ejecutar_alertas_diarias():
    """Consulta la BD correcta uniendo tablas y envía alertas masivas."""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Consulta corregida usando las tablas reales de la app
        cursor.execute("""
            SELECT 
                c.id AS certificado_id,
                t.nombres, t.apellidos, t.correo, t.telefono,
                c.nivel_curso, c.fecha_vencimiento
            FROM certificados c
            JOIN trabajadores t ON c.trabajador_id = t.id
        """)
        registros = cursor.fetchall()

        alertas_enviadas = 0
        hoy = datetime.now().date()

        for row in registros:
            nombre = f"{row['nombres']} {row['apellidos']}"
            correo = row['correo']
            telefono = row['telefono']
            curso = row['nivel_curso']
            fecha_str = row['fecha_vencimiento']

            if not fecha_str:
                continue
            
            try:
                fecha_venc = datetime.strptime(str(fecha_str).strip(), "%Y-%m-%d").date()
            except ValueError:
                continue

            dias_restantes = (fecha_venc - hoy).days

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

                cursor.execute("UPDATE certificados SET alerta_30d_enviada = 1 WHERE id = ?", (row["certificado_id"],))
                alertas_enviadas += 1

        conn.commit()
        conn.close()

        return True, f"Proceso completado. Se enviaron {alertas_enviadas} alertas."
        
    except Exception as e:
        print(f"Error procesando alertas: {e}")
        return False, str(e)
