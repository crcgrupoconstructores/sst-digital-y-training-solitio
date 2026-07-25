import streamlit as st
import database
import notificaciones
import config
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Alertas - Cursos de Alturas",
    page_icon="👷",
    layout="wide"
)

# Inicializar la base de datos al abrir la app
database.inicializar_bd()

st.title("👷 Sistema de Alertas para Cursos de Alturas")
st.markdown("---")

# Menú lateral
opcion = st.sidebar.radio("Navegación", ["Registrar Cliente", "Ver Clientes Registrados", "Revisar y Enviar Alertas"])

if opcion == "Registrar Cliente":
    st.header("📝 Registro de Nuevo Cliente")
    
    with st.form("form_registro_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datos de la Empresa")
            nit = st.text_input("NIT")
            dv = st.text_input("Dígito de Verificación (DV)", max_chars=1, value="0")
            razon_social = st.text_input("Razón Social")
            regimen = st.selectbox("Régimen Fiscal", ["Simplificado", "Común", "Especial"])
            direccion = st.text_input("Dirección")
            ciudad = st.text_input("Ciudad", value="Fusagasugá")
            correo_fe = st.text_input("Correo Facturación Electrónica")
            telefono_empresa = st.text_input("Teléfono Empresa")

        with col2:
            st.subheader("Datos del Trabajador y Curso")
            tipo_doc = st.selectbox("Tipo Documento", ["CC", "CE", "PASAPORTE"])
            num_doc = st.text_input("Número de Documento")
            nombres = st.text_input("Nombres")
            apellidos = st.text_input("Apellidos")
            correo_trabajador = st.text_input("Correo Personal")
            whatsapp = st.text_input("Número de WhatsApp (Ej: 3197259806)")
            
            nivel_curso = st.selectbox("Nivel de Curso", [
                "Reentrenamiento Avanzado",
                "Trabajador Autorizado",
                "Coordinador de Trabajo en Alturas",
                "Jefe de Área"
            ])
            fecha_emision = st.date_input("Fecha de Emisión del Curso")

        btn_guardar = st.form_submit_button("💾 Guardar y Registrar", type="primary")

    if btn_guardar:
        nit_val = nit.strip()
        doc_val = num_doc.strip()
        nombres_val = nombres.strip()
        correo_fe_val = correo_fe.strip()

        faltantes = []
        if not nit_val: faltantes.append("NIT")
        if not doc_val: faltantes.append("Número de Documento")
        if not nombres_val: faltantes.append("Nombres")
        if not correo_fe_val: faltantes.append("Correo FE")

        if faltantes:
            st.error(f"⚠️ Por favor completa los siguientes campos obligatorios: {', '.join(faltantes)}")
        else:
            try:
                f_emision_str = fecha_emision.strftime("%Y-%m-%d")
                f_venc_obj = fecha_emision.replace(year=fecha_emision.year + 1)
                f_vencimiento_str = f_venc_obj.strftime("%Y-%m-%d")

                conn = sqlite3.connect(config.DB_NAME)
                cursor = conn.cursor()
                
                # Asegurar que las tablas tengan la estructura correcta si ya existían mal creadas
                cursor.execute("DROP TABLE IF EXISTS certificados")
                cursor.execute("DROP TABLE IF EXISTS trabajadores")
                cursor.execute("DROP TABLE IF EXISTS empresas")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS empresas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nit TEXT UNIQUE,
                        dv TEXT,
                        razon_social TEXT,
                        direccion TEXT,
                        ciudad TEXT,
                        correo_fe TEXT,
                        telefono TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trabajadores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        empresa_id INTEGER,
                        tipo_doc TEXT,
                        numero_doc TEXT,
                        nombres TEXT,
                        apellidos TEXT,
                        correo TEXT,
                        telefono TEXT,
                        FOREIGN KEY(empresa_id) REFERENCES empresas(id)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS certificados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trabajador_id INTEGER,
                        nivel_curso TEXT,
                        fecha_emision TEXT,
                        fecha_vencimiento TEXT,
                        alerta_30d_enviada INTEGER,
                        alerta_15d_enviada INTEGER,
                        alerta_5d_enviada INTEGER,
                        FOREIGN KEY(trabajador_id) REFERENCES trabajadores(id)
                    )
                """)

                # 1. Insertar o recuperar Empresa
                cursor.execute("""
                    INSERT OR IGNORE INTO empresas (nit, dv, razon_social, direccion, ciudad, correo_fe, telefono)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nit_val, dv, razon_social, direccion, ciudad, correo_fe_val, telefono_empresa))
                
                cursor.execute("SELECT id FROM empresas WHERE nit = ?", (nit_val,))
                empresa_id = cursor.fetchone()[0]

                # 2. Insertar Trabajador
                cursor.execute("""
                    INSERT INTO trabajadores (empresa_id, tipo_doc, numero_doc, nombres, apellidos, correo, telefono)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (empresa_id, tipo_doc, doc_val, nombres_val, apellidos, correo_trabajador, whatsapp))
                
                trabajador_id = cursor.lastrowid

                # 3. Insertar Certificado/Curso
                cursor.execute("""
                    INSERT INTO certificados (trabajador_id, nivel_curso, fecha_emision, fecha_vencimiento, alerta_30d_enviada, alerta_15d_enviada, alerta_5d_enviada)
                    VALUES (?, ?, ?, ?, 0, 0, 0)
                """, (trabajador_id, nivel_curso, f_emision_str, f_vencimiento_str))

                conn.commit()
                conn.close()
                st.success("🎉 ¡Cliente y Curso registrados exitosamente!")
            except Exception as e:
                st.error(f"Error guardando en la base de datos: {e}")

elif opcion == "Ver Clientes Registrados":
    st.header("📋 Lista de Clientes y Cursos en la Base de Datos")
    
    conn = sqlite3.connect(config.DB_NAME)
    query = """
    SELECT 
        e.razon_social AS Empresa,
        e.nit AS NIT,
        t.numero_doc AS Documento,
        (t.nombres || ' ' || t.apellidos) AS Trabajador,
        t.correo AS Correo_Trabajador,
        t.telefono AS Whatsapp,
        c.nivel_curso AS Curso,
        c.fecha_emision AS Emision,
        c.fecha_vencimiento AS Vencimiento
    FROM certificados c
    JOIN trabajadores t ON c.trabajador_id = t.id
    JOIN empresas e ON t.empresa_id = e.id
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aún no hay clientes registrados en la base de datos.")
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")

elif opcion == "Revisar y Enviar Alertas":
    st.header("🔔 Control y Envío de Alertas Diarias")
    
    st.info("Presiona el botón para consultar los cursos próximos a vencer y disparar los correos y mensajes de WhatsApp.")
    
    if st.button("🚀 Ejecutar Alertas de Hoy", type="primary"):
        with st.spinner("Enviando notificaciones..."):
            notificaciones.ejecutar_alertas_diarias()
        st.success("🎉 ¡Proceso finalizado! Revisa la terminal para confirmar los envíos.")
