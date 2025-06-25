import sqlite3
import json
import os
import re

# Diccionario centralizado con toda la información de las líneas
# (Copiado de app.py para consistencia)
LINEAS_CONFIG = {
    '1':  {'id': '1',  'name': 'Línea 1',  'color': '#00AEEF'},
    '2':  {'id': '2',  'name': 'Línea 2',  'color': '#FF0000'},
    '3':  {'id': '3',  'name': 'Línea 3',  'color': '#FFD700'},
    '4':  {'id': '4',  'name': 'Línea 4',  'color': '#B25400'},
    '5':  {'id': '5',  'name': 'Línea 5',  'color': '#39B54A'},
    '6':  {'id': '6',  'name': 'Línea 6',  'color': '#9E9E9E'},
    '7':  {'id': '7',  'name': 'Línea 7',  'color': '#FF9800'},
    '8':  {'id': '8',  'name': 'Línea 8',  'color': '#FF69B4'},
    '9':  {'id': '9',  'name': 'Línea 9',  'color': '#9C27B0'},
    '10': {'id': '10', 'name': 'Línea 10', 'color': '#0D47A1'},
    '11': {'id': '11', 'name': 'Línea 11', 'color': '#006400'},
    '12': {'id': '12', 'name': 'Línea 12', 'color': '#a49a00'}, # Color corregido
    'R':  {'id': 'R',  'name': 'Ramal',    'color': '#FFFFFF'}
}

def generar_json_rutas(db_path_gtfs, output_path_json):
    """
    Genera un archivo JSON con los trazados (shapes) de las líneas de metro
    y sus colores correctos a partir de la base de datos GTFS.
    """
    print(f"Iniciando la generación de '{output_path_json}' desde '{db_path_gtfs}'...")

    # --- 1. Conectar a la base de datos GTFS ---
    try:
        conn_gtfs = sqlite3.connect(db_path_gtfs)
        cursor_gtfs = conn_gtfs.cursor()
        print("Conexión a la base de datos GTFS establecida.")
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos GTFS: {e}")
        return

    # --- 2. Extraer rutas y shapes ---
    try:
        # Obtener mapeo de route_id a route_short_name
        cursor_gtfs.execute("SELECT route_id, route_short_name FROM routes")
        routes_map = {row[0]: row[1] for row in cursor_gtfs.fetchall()}

        # Obtener todos los shapes
        cursor_gtfs.execute("SELECT shape_id, shape_pt_lat, shape_pt_lon FROM shapes ORDER BY shape_id, shape_pt_sequence")
        shapes_data = cursor_gtfs.fetchall()
        
        # Obtener mapeo de route_id a shape_id (desde trips)
        cursor_gtfs.execute("SELECT DISTINCT route_id, shape_id FROM trips")
        route_to_shape_map = {row[0]: row[1] for row in cursor_gtfs.fetchall()}

        print(f"Se han extraído {len(shapes_data)} puntos de trazado.")

    except sqlite3.Error as e:
        print(f"Error al extraer datos de GTFS: {e}")
        conn_gtfs.close()
        return

    # --- 3. Procesar y agrupar datos ---
    rutas_agrupadas = {}
    
    # Agrupar los puntos por shape_id
    shapes_agrupados = {}
    for shape_id, lat, lon in shapes_data:
        if shape_id not in shapes_agrupados:
            shapes_agrupados[shape_id] = []
        shapes_agrupados[shape_id].append([lat, lon])

    # Usamos un mapeo de shape_id a route_id. Un shape pertenece a una sola ruta.
    cursor_gtfs.execute("SELECT shape_id, route_id FROM trips GROUP BY shape_id")
    shape_to_route_map = {row[0]: row[1] for row in cursor_gtfs.fetchall()}

    # Construir una estructura agrupada por línea base
    for shape_id, coordinates in shapes_agrupados.items():
        route_id = shape_to_route_map.get(shape_id)
        if not route_id: continue

        linea_short_name = routes_map.get(route_id)
        if not linea_short_name: continue
        
        # Lógica mejorada para obtener el número de línea base
        # Extrae el número del principio del nombre (e.j., '10' de '10A', '6' de '6')
        match = re.match(r'^(\d+)', linea_short_name)
        if match:
            linea_base = match.group(1)
        # Maneja casos como 'Ramal' o 'R'
        elif 'ramal' in linea_short_name.lower() or 'r' == linea_short_name.lower():
            linea_base = 'R'
        else:
            linea_base = linea_short_name

        if linea_base not in rutas_agrupadas:
            config = LINEAS_CONFIG.get(linea_base)
            if not config:
                print(f"Advertencia: No se encontró configuración para la línea base '{linea_base}' (de '{linea_short_name}'). Se omitirá.")
                continue
            rutas_agrupadas[linea_base] = {
                "line": linea_base,
                "name": config['name'],
                "color": config['color'],
                "paths": [] # Usaremos 'paths' para guardar múltiples trazados
            }
        
        # Cada shape es un path diferente
        rutas_agrupadas[linea_base]["paths"].append(coordinates)

    # Convertir el diccionario a la lista final para el JSON,
    # Aplanando las coordenadas de cada línea en una sola lista si es necesario.
    final_lines = []
    for line_data in rutas_agrupadas.values():
        # CORRECCIÓN: NO aplanar los paths. Guardarlos como una lista de trazados.
        if not line_data["paths"]:
            print(f"Advertencia: La línea {line_data['line']} no tiene trazados válidos. Se omitirá.")
            continue
            
        final_lines.append({
            "line": line_data["line"],
            "name": line_data["name"],
            "color": line_data["color"],
            "paths": line_data["paths"] # Guardar la lista de trazados, no 'coordinates'
        })

    rutas_json = {"lines": final_lines}

    # --- 4. Guardar el archivo JSON ---
    try:
        with open(output_path_json, 'w', encoding='utf-8') as f:
            json.dump(rutas_json, f, ensure_ascii=False, indent=2)
        print(f"Archivo '{output_path_json}' generado exitosamente con {len(rutas_json['lines'])} líneas y múltiples trazados.")
    except IOError as e:
        print(f"Error al escribir el archivo JSON: {e}")

if __name__ == '__main__':
    DB_GTFS = os.path.join('M4', 'metro_madrid.db')
    OUTPUT_JSON = os.path.join('static', 'data', 'metro_routes.json')
    
    if not os.path.exists(DB_GTFS):
        print(f"Error: La base de datos GTFS '{DB_GTFS}' no se encuentra.")
    else:
        generar_json_rutas(DB_GTFS, OUTPUT_JSON) 