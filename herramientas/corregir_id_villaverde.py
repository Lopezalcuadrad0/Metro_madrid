import sqlite3
import os

def corregir_id_villaverde():
    """
    Corrige el id_fijo incorrecto de la estación Villaverde Alto en la tabla linea_3.
    """
    db_path = os.path.join('db', 'estaciones_fijas_v2.db')
    print(f"Conectando a la base de datos: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        id_incorrecto = 307
        id_correcto = 357
        nombre_estacion = 'Villaverde Alto'
        tabla = 'linea_3'

        # 1. Verificar el id_fijo actual en linea_3 para Villaverde Alto
        cursor.execute(f"SELECT id_fijo FROM {tabla} WHERE nombre = ?", (nombre_estacion,))
        result_actual = cursor.fetchone()
        
        if not result_actual:
            print(f"❌ Error: No se pudo encontrar '{nombre_estacion}' en {tabla}.")
            return
            
        id_actual = result_actual[0]
        print(f"ℹ️ ID fijo actual de '{nombre_estacion}' en {tabla} es: {id_actual}")

        if id_actual == id_correcto:
            print(f"✅ El ID fijo de '{nombre_estacion}' ya es el correcto ({id_correcto}). No se necesita hacer nada.")
        elif id_actual != id_incorrecto:
            print(f"⚠️  El ID actual ({id_actual}) no es el esperado ({id_incorrecto}), pero tampoco es el correcto. Se actualizará de todas formas.")
            print(f"🔄 Actualizando ID fijo de '{nombre_estacion}' en {tabla} de {id_actual} a {id_correcto}...")
            cursor.execute(f"UPDATE {tabla} SET id_fijo = ? WHERE nombre = ?", (id_correcto, nombre_estacion))
            conn.commit()
            print("✅ ¡Actualización completada!")
        else:
            # 2. Actualizar el id_fijo en linea_3
            print(f"🔄 Actualizando ID fijo de '{nombre_estacion}' en {tabla} de {id_incorrecto} a {id_correcto}...")
            cursor.execute(f"UPDATE {tabla} SET id_fijo = ? WHERE nombre = ?", (id_correcto, nombre_estacion))
            conn.commit()
            print("✅ ¡Actualización completada!")

        # 3. Verificar la actualización
        cursor.execute(f"SELECT id_fijo FROM {tabla} WHERE nombre = ?", (nombre_estacion,))
        id_verificado = cursor.fetchone()[0]
        print(f"🔍 Verificación post-actualización: ID en {tabla} es ahora {id_verificado}")


    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión cerrada.")

if __name__ == '__main__':
    corregir_id_villaverde() 