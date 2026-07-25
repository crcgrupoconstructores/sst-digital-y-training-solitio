import streamlit as st
import database
import notificaciones
import sqlite3
import pandas as pd

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Datos de la Empresa")
        nit = st.text_input("NIT")
        dv = st.text_input("Dígito de Verificación (DV)", max_chars=1)
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

    if st.button("💾 Guardar y Registrar", type="primary"):
        nit_val = nit.strip() if nit else ""
        doc_val = numero_doc.strip() if 'numero_doc' in locals() and numero_doc else ""
        nombres_val = nombres.strip() if nombres else ""
        correo_fe_val = correo_fe.strip() if 'correo_fe' in locals() and correo_fe else ""

        faltantes = []
        if not nit_val: faltantes.append("NIT")
        if not doc_val: faltantes.append("Número de Documento")
        if not nombres_val: faltantes.append("Nombres")
        if not correo_fe_val: faltantes.append("Correo FE")

        if faltantes:
            st.error(f"⚠️ Por favor completa los siguientes campos obligatorios: {', '.join(faltantes)}")
        else:
            try:
                conn = sqlite3.connect(config.DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clientes (
                        nit, dv, razon_social, regimen, direccion, ciudad, correo_fe, telefono_empresa,
                        tipo_doc, numero_doc, nombres, apellidos, correo, telefono, nivel_curso, fecha_emision, fecha_vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nit, dv, razon_social, regimen_fiscal, direccion, ciudad, correo_fe, telefono_empresa,
                    tipo_doc, numero_doc, nombres, apellidos, correo_personal, whatsapp, nivel_curso, fecha_emision, fecha_vencimiento
                ))
                conn.commit()
                conn.close()
                st.success("¡Cliente y Curso registrados exitosamente!")
            except Exception as e:
                st.error(f"Error guardando en la base de datos: {e}")
                
elif opcion == "Ver Clientes Registrados":
    st.header("📋 Lista de Clientes y Cursos en la Base de Datos")
    
    conn = sqlite3.connect("centro_entrenamiento.db")
    
    # Consulta directa de todas las columnas unidas
    query = """
    SELECT * 
    FROM certificados c
    JOIN trabajadores t ON c.trabajador_id = t.id
    JOIN empresas e ON t.empresa_id = e.id
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            # Eliminamos columnas repetidas de IDs para dejar la tabla limpia
            df = df.loc[:, ~df.columns.duplicated()]
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
