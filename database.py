import sqlite3
from datetime import datetime, timedelta
from config import DB_NAME

def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def inicializar_bd():
    """Crea la base de datos y las tablas si no existen."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        
        # Tabla de Empresas para Facturación Electrónica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nit VARCHAR(20) UNIQUE NOT NULL,
                dv VARCHAR(2),
                razon_social TEXT NOT NULL,
                regimen_fiscal TEXT,
                direccion TEXT NOT NULL,
                ciudad TEXT NOT NULL,
                correo_fe TEXT NOT NULL,
                telefono TEXT NOT NULL
            )
        ''')

        # Tabla de Trabajadores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trabajadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_documento TEXT NOT NULL,
                numero_documento VARCHAR(20) UNIQUE NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                correo TEXT NOT NULL,
                telefono_whatsapp TEXT NOT NULL,
                empresa_id INTEGER,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id)
            )
        ''')

        # Tabla de Certificados de Cursos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajador_id INTEGER NOT NULL,
                nivel_curso TEXT NOT NULL,
                fecha_emision DATE NOT NULL,
                fecha_vencimiento DATE NOT NULL,
                alerta_30d_enviada INTEGER DEFAULT 0,
                alerta_15d_enviada INTEGER DEFAULT 0,
                alerta_5d_enviada INTEGER DEFAULT 0,
                FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id)
            )
        ''')
        conn.commit()

def registrar_cliente_completo(datos_empresa, datos_trabajador, datos_curso):
    """Guarda empresa, trabajador y calcula el vencimiento a 1 año."""
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        empresa_id = None

        # 1. Guardar o actualizar empresa
        if datos_empresa:
            cursor.execute('''
                INSERT INTO empresas (nit, dv, razon_social, regimen_fiscal, direccion, ciudad, correo_fe, telefono)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(nit) DO UPDATE SET razon_social=excluded.razon_social
            ''', (
                datos_empresa['nit'], datos_empresa['dv'], datos_empresa['razon_social'],
                datos_empresa['regimen_fiscal'], datos_empresa['direccion'],
                datos_empresa['ciudad'], datos_empresa['correo_fe'], datos_empresa['telefono']
            ))
            cursor.execute('SELECT id FROM empresas WHERE nit = ?', (datos_empresa['nit'],))
            empresa_id = cursor.fetchone()[0]

        # 2. Guardar o actualizar trabajador
        cursor.execute('''
            INSERT INTO trabajadores (tipo_documento, numero_documento, nombres, apellidos, correo, telefono_whatsapp, empresa_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(numero_documento) DO UPDATE SET 
                correo=excluded.correo,
                telefono_whatsapp=excluded.telefono_whatsapp,
                empresa_id=excluded.empresa_id
        ''', (
            datos_trabajador['tipo_doc'], datos_trabajador['num_doc'],
            datos_trabajador['nombres'], datos_trabajador['apellidos'],
            datos_trabajador['correo'], datos_trabajador['whatsapp'], empresa_id
        ))
        
        cursor.execute('SELECT id FROM trabajadores WHERE numero_documento = ?', (datos_trabajador['num_doc'],))
        trabajador_id = cursor.fetchone()[0]

        # 3. Guardar certificado (vence a los 365 días)
        f_emision = datetime.strptime(datos_curso['fecha_emision'], "%Y-%m-%d").date()
        f_vencimiento = f_emision + timedelta(days=365)

        cursor.execute('''
            INSERT INTO certificados (trabajador_id, nivel_curso, fecha_emision, fecha_vencimiento)
            VALUES (?, ?, ?, ?)
        ''', (trabajador_id, datos_curso['nivel'], f_emision, f_vencimiento))

        conn.commit()
        print("✅ Registro guardado con éxito en la base de datos.")