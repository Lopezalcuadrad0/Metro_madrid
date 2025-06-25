import sqlite3
import os

def corregir_ids_criticos():
    """
    Corrige los id_fijo incorrectos para Villaverde Alto y Callao.
    """
    db_path = os.path.join('db', 'estaciones_fijas_v2.db')
    print(f"Conectando a la base de datos: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- 1. Corregir Villaverde Alto (Línea 3) ---
        id_correcto_villaverde = 357
        nombre_villaverde = 'Villaverde Alto'
        cursor.execute("UPDATE linea_3 SET id_fijo = ? WHERE nombre = ?", (id_correcto_villaverde, nombre_villaverde))
        print(f"✅ Actualizado '{nombre_villaverde}' en linea_3 al id_fijo: {id_correcto_villaverde}")

        # --- 2. Corregir Callao (Línea 5 y 3) ---
        id_correcto_callao = 308
        nombre_callao = 'Callao'
        
        # Actualizar Callao en la linea_3
        cursor.execute("UPDATE linea_3 SET id_fijo = ? WHERE nombre = ?", (id_correcto_callao, nombre_callao))
        print(f"✅ Actualizado '{nombre_callao}' en linea_3 al id_fijo: {id_correcto_callao}")

        # Actualizar Callao en la linea_5
        cursor.execute("UPDATE linea_5 SET id_fijo = ? WHERE nombre = ?", (id_correcto_callao, nombre_callao))
        print(f"✅ Actualizado '{nombre_callao}' en linea_5 al id_fijo: {id_correcto_callao}")

        conn.commit()
        print("\n🎉 Correcciones aplicadas a la base de datos.")

    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión cerrada.")

if __name__ == '__main__':
    corregir_ids_criticos() 