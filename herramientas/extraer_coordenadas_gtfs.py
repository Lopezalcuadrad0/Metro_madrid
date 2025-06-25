import sqlite3
import unicodedata

def normalizar_nombre(nombre):
    """Normaliza el nombre de la estación para facilitar la coincidencia."""
    # Transliterar a una forma sin acentos
    nombre = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
    # Convertir a mayúsculas y quitar espacios extra
    return nombre.upper().strip()

def extraer_y_actualizar_coordenadas():
    """
    Extrae las coordenadas de la base de datos GTFS y las carga en la
    base de datos relacional.
    """
    # --- 1. Conexión a las bases de datos ---
    try:
        conn_gtfs = sqlite3.connect('M4/metro_madrid.db')
        cursor_gtfs = conn_gtfs.cursor()
        
        conn_relacional = sqlite3.connect('db/estaciones_relacional.db')
        cursor_relacional = conn_relacional.cursor()
        print("Conexión a las bases de datos establecida.")
    except sqlite3.Error as e:
        print(f"Error al conectar con las bases de datos: {e}")
        return

    # --- 2. Asegurar que las columnas de coordenadas existan ---
    try:
        cursor_relacional.execute("ALTER TABLE estaciones ADD COLUMN latitud REAL;")
        print("Columna 'latitud' añadida a 'estaciones'.")
    except sqlite3.OperationalError:
        print("La columna 'latitud' ya existe.")
        
    try:
        cursor_relacional.execute("ALTER TABLE estaciones ADD COLUMN longitud REAL;")
        print("Columna 'longitud' añadida a 'estaciones'.")
    except sqlite3.OperationalError:
        print("La columna 'longitud' ya existe.")

    # --- 3. Extraer coordenadas de GTFS ---
    try:
        cursor_gtfs.execute('SELECT stop_name, stop_lat, stop_lon FROM stops')
        estaciones_gtfs = cursor_gtfs.fetchall()
        
        # Usar un diccionario para manejar múltiples paradas por estación (mismo nombre)
        # y promediar sus coordenadas para obtener un punto central.
        coordenadas = {}
        for nombre, lat, lon in estaciones_gtfs:
            nombre_norm = normalizar_nombre(nombre)
            if nombre_norm not in coordenadas:
                coordenadas[nombre_norm] = {'lats': [], 'lons': []}
            coordenadas[nombre_norm]['lats'].append(lat)
            coordenadas[nombre_norm]['lons'].append(lon)
            
        print(f"Se extrajeron {len(estaciones_gtfs)} paradas de GTFS.")
    except sqlite3.Error as e:
        print(f"Error al extraer datos de GTFS: {e}")
        conn_gtfs.close()
        conn_relacional.close()
        return

    # --- 4. Actualizar la base de datos relacional ---
    estaciones_actualizadas = 0
    estaciones_no_encontradas = set()

    cursor_relacional.execute('SELECT id_fijo, nombre FROM estaciones')
    estaciones_relacional = cursor_relacional.fetchall()

    for id_fijo, nombre_relacional in estaciones_relacional:
        nombre_norm_relacional = normalizar_nombre(nombre_relacional)
        
        if nombre_norm_relacional in coordenadas:
            # Calcular el promedio de las coordenadas para la estación
            avg_lat = sum(coordenadas[nombre_norm_relacional]['lats']) / len(coordenadas[nombre_norm_relacional]['lats'])
            avg_lon = sum(coordenadas[nombre_norm_relacional]['lons']) / len(coordenadas[nombre_norm_relacional]['lons'])
            
            cursor_relacional.execute(
                'UPDATE estaciones SET latitud = ?, longitud = ? WHERE id_fijo = ?',
                (avg_lat, avg_lon, id_fijo)
            )
            estaciones_actualizadas += 1
        else:
            estaciones_no_encontradas.add(nombre_relacional)

    # --- 5. Confirmar cambios y cerrar conexiones ---
    conn_relacional.commit()
    print(f"Actualización completada. Se actualizaron {estaciones_actualizadas} estaciones.")
    if estaciones_no_encontradas:
        print("\nADVERTENCIA: No se encontraron coordenadas para las siguientes estaciones:")
        for nombre in sorted(list(estaciones_no_encontradas)):
            print(f"- {nombre}")

    conn_gtfs.close()
    conn_relacional.close()
    print("Conexiones a las bases de datos cerradas.")

if __name__ == '__main__':
    extraer_y_actualizar_coordenadas() 