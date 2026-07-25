import os
import streamlit as st

# Nombre de la Base de Datos
DB_NAME = "centro_entrenamiento_v2.db"

# Configuración para enviar correos (SMTP) leyendo de los Secrets de Streamlit o valores por defecto
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = st.secrets.get("EMAIL_SENDER", "crcgrupoconstructores@gmail.com")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "oxjoijddedeivfuf")

# Configuración para enviar WhatsApp (Twilio / API) leyendo de los Secrets de Streamlit
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "AC6c9066fb9f72dc1f2896b1dafca4ef0")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "0c258ac69aa849866ad992e5e0201050")
TWILIO_WHATSAPP_NUMBER = st.secrets.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
