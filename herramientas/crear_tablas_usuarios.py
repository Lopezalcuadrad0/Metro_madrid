import sqlite3
import os

def crear_tablas_usuarios():
    """
    Crea las tablas 'users' y 'favorite_lines' en la base de datos si no existen.
    """
    db_path = os.path.join('db', 'estaciones_fijas_v2.db')
    print(f"Conectando a la base de datos en: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabla 'users' verificada/creada correctamente.")

        # Crear tabla de líneas favoritas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                line_id TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, line_id)
            )
        """)
        print("Tabla 'favorite_lines' verificada/creada correctamente.")

        conn.commit()
        print("Tablas de usuario creadas y confirmadas en la base de datos.")

    except sqlite3.Error as e:
        print(f"Error al crear las tablas de usuario: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    print("Iniciando la creación de tablas de base de datos para usuarios...")
    crear_tablas_usuarios()
    print("Proceso finalizado.") 