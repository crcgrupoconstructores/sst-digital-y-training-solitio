import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import psycopg2
from datetime import datetime
import config
import streamlit as st

from email.header import Header

def enviar_email(destinatario, asunto, texto_plano):
    """Envía correos electrónicos automatizados con cabeceras codificadas en UTF-8."""
    msg = MIMEMultipart()
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = destinatario
    
    # Forzar la codificación UTF-8 en el asunto para que soporte cualquier carácter especial o tilde
    msg['Subject'] = Header(asunto, 'utf-8')
    
    msg.attach(MIMEText(texto_plano, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, destinatario, msg.as_string())
        return True, "Correo enviado con exito"
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
            return True, "WhatsApp enviado con exito"
        else:
            error_msg = f"Error Twilio (Codigo {res.status_code}): {res.text}"
            print(f"⚠️ {error_msg}")
            return False, error_msg
    except Exception as e:
        error_msg = f"Error de red con WhatsApp: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

def enviar_alerta_individual(certificado_id):
    """Envía correo y WhatsApp de forma manual para un certificado y reporta el estado exacto."""
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                t.nombres, t.apellidos, t.correo, t.telefono, 
                c.nivel_curso, c.fecha_vencimiento
            FROM certificados c
            JOIN trabajadores t ON c.trabajador_id = t.id
            WHERE c.id = %s
        """, (certificado_id,))
        
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, "Certificado no encontrado en la base de datos."

        nombre = f"{row[0]} {row[1]}"
        correo = row[2]
        telefono = row[3]
        curso = row[4]
        fecha_str = str(row[5])

        hoy = datetime.now().date()
        fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dias_restantes = (fecha_venc - hoy).days

        # Asunto sin tildes ni caracteres especiales problemáticos
        asunto = f"Alerta Vencimiento de Curso: {curso}"
        
        # Mensaje en texto plano limpio
        cuerpo_correo = f"""Hola {nombre},

Te recordamos que tu curso de {curso} {'ya se encuentra vencido' if dias_restantes < 0 else f'vence en {dias_restantes} dias'}.

Por favor ponte en contacto con nosotros para gestionar tu renovacion."""

        resultados = []

        if correo:
            exito_c, msg_c = enviar_email(correo, asunto, cuerpo_correo)
            resultados.append(f"Correo: {msg_c}")
        else:
            resultados.append("Correo: No tiene correo registrado")

        if telefono:
            msg_wa = f"Hola {nombre}, tu curso de {curso} {'ya vencio' if dias_restantes < 0 else f'vence en {dias_restantes} dias'}. ¡Comunícate con nosotros para renovarlo!"
            exito_w, msg_w = enviar_whatsapp(str(telefono), msg_wa)
            resultados.append(f"WhatsApp: {msg_w}")
        else:
            resultados.append("WhatsApp: No tiene telefono registrado")

        return True, " | ".join(resultados)
    except Exception as e:
        return False, f"Excepcion general: {str(e)}"

def ejecutar_alertas_diarias():
    """Recorre todos los certificados y envía alertas automáticas según su vencimiento."""
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM certificados")
        certificados = cursor.fetchall()
        conn.close()

        resultados_totales = []
        for cert in certificados:
            exito, mensaje = enviar_alerta_individual(cert[0])
            resultados_totales.append(f"ID {cert[0]}: {mensaje}")
            
        return True, " | ".join(resultados_totales)
    except Exception as e:
        return False, f"Error en alertas diarias: {str(e)}"
