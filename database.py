import sqlite3
import config

def inicializar_bd():
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    
    # Crear tabla empresas
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
    
    # Crear tabla trabajadores con los nombres de columnas correctos
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

    # Crear tabla certificados
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
    
    conn.commit()
    conn.close()
