import sqlite3
import os

def crear_tablas_favoritos():
    """
    Crea las tablas 'favorite_lines' y 'favorite_stations' en la base de datos si no existen.
    """
    db_path = os.path.join('db', 'estaciones_fijas_v2.db')
    print(f"Conectando a la base de datos en: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear tabla de líneas favoritas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                line_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, line_id)
            )
        """)
        print("✅ Tabla 'favorite_lines' verificada/creada correctamente.")

        # Crear tabla de estaciones favoritas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                station_id INTEGER NOT NULL,
                line_id TEXT NOT NULL,
                station_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, station_id, line_id)
            )
        """)
        print("✅ Tabla 'favorite_stations' verificada/creada correctamente.")

        conn.commit()
        print("🎯 Tablas de favoritos creadas y confirmadas en la base de datos.")

        # Verificar las tablas creadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'favorite_%'")
        tables = cursor.fetchall()
        print(f"📊 Tablas de favoritos disponibles: {[table[0] for table in tables]}")

    except sqlite3.Error as e:
        print(f"❌ Error al crear las tablas de favoritos: {e}")
    finally:
        if conn:
            conn.close()
            print("🔒 Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    print("🚀 Iniciando la creación de tablas de favoritos...")
    crear_tablas_favoritos()
    print("✨ Proceso finalizado.") 