import streamlit as st
import database
import notificaciones
import config
import sqlite3
import pandas as pd
from datetime import datetime

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

# Opción de emergencia en la barra lateral para limpiar base de datos si es necesario
if st.sidebar.button("🧹 Reiniciar Base de Datos"):
    try:
        import os
        if os.path.exists(config.DB_NAME):
            os.remove(config.DB_NAME)
        database.inicializar_bd()
        st.sidebar.success("¡Base de datos reiniciada con éxito!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al reiniciar: {e}")

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

        if not all([nit_val, doc_val, nombres_val, correo_fe_val]):
            st.error("⚠️ Por favor completa los campos obligatorios (NIT, Documento, Nombres y Correo FE).")
        else:
            try:
              from dateutil.relativedelta import relativedelta

f_emision_str = fecha_emision.strftime("%Y-%m-%d")
f_venc_obj = fecha_emision + relativedelta(months=18) # <-- Suma exacta de 18 meses
f_vencimiento_str = f_venc_obj.strftime("%Y-%m-%d")

                conn = sqlite3.connect(config.DB_NAME)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO empresas (nit, dv, razon_social, direccion, ciudad, correo_fe, telefono)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nit_val, dv, razon_social, direccion, ciudad, correo_fe_val, telefono_empresa))
                
                cursor.execute("SELECT id FROM empresas WHERE nit = ?", (nit_val,))
                empresa_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO trabajadores (empresa_id, tipo_doc, numero_doc, nombres, apellidos, correo, telefono)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (empresa_id, tipo_doc, doc_val, nombres_val, apellidos, correo_trabajador, whatsapp))
                
                trabajador_id = cursor.lastrowid

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
    st.header("🔔 Control y Envío de Alertas")
    
    st.info("Aquí puedes ver el estado actual de los cursos, los días restantes para su vencimiento y enviar notificaciones manuales.")
    
    # Botón global para barrido automático
    if st.button("🚀 Ejecutar Automatización General de Alertas", type="primary"):
        with st.spinner("Revisando y enviando notificaciones pendientes..."):
            notificaciones.ejecutar_alertas_diarias()
        st.success("🎉 ¡Proceso automático finalizado!")

    st.markdown("---")
    st.subheader("📊 Panel de Vencimientos y Envío Manual")

    conn = sqlite3.connect(config.DB_NAME)
    query = """
    SELECT 
        c.id AS certificado_id,
        e.razon_social AS Empresa,
        (t.nombres || ' ' || t.apellidos) AS Trabajador,
        t.correo AS Correo,
        t.telefono AS Whatsapp,
        c.nivel_curso AS Curso,
        c.fecha_vencimiento AS Vencimiento
    FROM certificados c
    JOIN trabajadores t ON c.trabajador_id = t.id
    JOIN empresas e ON t.empresa_id = e.id
    """
    try:
        df_alertas = pd.read_sql_query(query, conn)
        conn.close()

        if not df_alertas.empty:
            hoy = datetime.now().date()
            
            for index, row in df_alertas.iterrows():
                f_venc = datetime.strptime(row["Vencimiento"], "%Y-%m-%d").date()
                dias_restantes = (f_venc - hoy).days
                
                with st.container():
                    col_info, col_btn = st.columns([4, 1])
                    
                    with col_info:
                        if dias_restantes < 0:
                            estado_txt = f"🔴 **VENCIDO** hace {abs(dias_restantes)} días"
                        elif dias_restantes == 0:
                            estado_txt = "⚠️ **VENCE HOY**"
                        else:
                            estado_txt = f"🟢 Vence en **{dias_restantes} días**"
                        
                        st.markdown(f"**Empresa:** {row['Empresa']} | **Trabajador:** {row['Trabajador']} | **Curso:** {row['Curso']}")
                        st.markdown(f"📅 Fecha Vencimiento: `{row['Vencimiento']}` | {estado_txt} | ✉️ `{row['Correo']}` | 📱 `{row['Whatsapp']}`")
                    
                    with col_btn:
                        if st.button("📨 Enviar Alerta", key=f"btn_alerta_{row['certificado_id']}"):
                            with st.spinner("Enviando..."):
                                exito, mensaje = notificaciones.enviar_alerta_individual(row['certificado_id'])
                                if exito:
                                    st.success(mensaje)
                                else:
                                    st.error(mensaje)
                    st.markdown("---")
        else:
            st.info("No hay registros en la base de datos para evaluar alertas.")
    except Exception as e:
        st.error(f"Error cargando el panel de alertas: {e}")
