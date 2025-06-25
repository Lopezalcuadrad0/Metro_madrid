import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Ver tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📋 Tablas en la base de datos:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Ver estructura de cada tabla
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 Estructura de tabla '{table_name}':")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Ver algunos datos de ejemplo
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            print(f"  📊 Datos de ejemplo:")
            for row in rows:
                print(f"    {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database() 