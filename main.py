from datetime import datetime
import sqlite3
import database
import notificaciones
from config import DB_NAME

def ejecutar_alertas_diarias():
    """Revisa los certificados y dispara alertas a los 30, 15 y 5 días antes del vencimiento."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hoy = datetime.now().date()

    query = '''
        SELECT 
            c.id, c.nivel_curso, c.fecha_vencimiento, 
            c.alerta_30d_enviada, c.alerta_15d_enviada, c.alerta_5d_enviada,
            t.nombres, t.apellidos, t.correo, t.telefono_whatsapp,
            e.razon_social, e.correo_fe
        FROM certificados c
        JOIN trabajadores t ON c.trabajador_id = t.id
        LEFT JOIN empresas e ON t.empresa_id = e.id
        WHERE c.fecha_vencimiento >= ?
    '''

    cursor.execute(query, (str(hoy),))
    registros = cursor.fetchall()

    for reg in registros:
        (cert_id, nivel, f_venc, a30, a15, a5, 
         nombres, apellidos, correo_trab, tel_wa, empresa, correo_emp) = reg
        
        fecha_venc = datetime.strptime(f_venc, "%Y-%m-%d").date()
        dias = (fecha_venc - hoy).days

        alerta_campo = None

        if dias <= 30 and not a30:
            alerta_campo = "alerta_30d_enviada"
        elif dias <= 15 and not a15:
            alerta_campo = "alerta_15d_enviada"
        elif dias <= 5 and not a5:
            alerta_campo = "alerta_5d_enviada"

        if alerta_campo:
            asunto = f"⏰ Recordatorio: Vencimiento de Curso de Alturas ({dias} días)"
            
            body_email = f"""
            <h3>Centro de Entrenamiento en Trabajo en Alturas</h3>
            <p>Estimado(a) <strong>{nombres} {apellidos}</strong>,</p>
            <p>Le informamos que su curso de <strong>{nivel}</strong> vence el día <strong>{fecha_venc}</strong> (quedan {dias} días).</p>
            <p>Agende su reentrenamiento a tiempo para mantener al día su certificación laboral.</p>
            """

            msg_wa = f"Hola {nombres}, tu certificado de {nivel} vence en {dias} días ({fecha_venc}). ¡Escríbenos para agendar tu cupo!"
            # Notificar al trabajador
            notificaciones.enviar_email(correo_trab, asunto, body_email)
            notificaciones.enviar_whatsapp(tel_wa, msg_wa)

            # Notificar a la empresa si aplica
            if correo_emp:
                notificaciones.enviar_email(correo_emp, f"Vencimiento Alturas - {nombres} {apellidos}", body_email)

            # Marcar como enviado en la base de datos
            cursor.execute(f"UPDATE certificados SET {alerta_campo} = 1 WHERE id = ?", (cert_id,))
            conn.commit()

    conn.close()

if __name__ == "__main__":
    # 1. Inicializar la base de datos
    database.inicializar_bd()
    
    # 2. Datos de prueba
    empresa_demo = {
        'nit': '900996881',
        'dv': '0',
        'razon_social': 'San Felipe Construcciones S.A.S.',
        'regimen_fiscal': 'Simplificado',
        'direccion': 'Carrera 51#20A-01',
        'ciudad': 'Fusagasugá',
        'correo_fe': 'dianita2907_@hotmail.com',
        'telefono': '3213848590'
    }

    trabajador_demo = {
        'tipo_doc': 'CC',
        'num_doc': '1007664772',
        'nombres': 'Juan Camilo',
        'apellidos': 'Camacho Velandia',
        'correo': 'camachocamilo09@gmail.com',
        'whatsapp': '3197259806'
    }

    curso_demo = {
        'nivel': 'Reentrenamiento Avanzado',
        'fecha_emision': '2025-08-01'
    }

    # 3. Guardar en base de datos
    database.registrar_cliente_completo(empresa_demo, trabajador_demo, curso_demo)

    # 4. Revisar alertas del día
    print("🔍 Revisando vencimientos del día...")
    ejecutar_alertas_diarias()
    print("🏁 Proceso finalizado.")