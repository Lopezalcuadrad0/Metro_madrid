import os
import zipfile
import re
from xml.etree import ElementTree as ET
import json

# Diccionario de configuración de líneas (colores y nombres)
LINEAS_CONFIG = {
    '1':  {'name': 'Línea 1',  'color': '#00AEEF'},
    '2':  {'name': 'Línea 2',  'color': '#FF0000'},
    '3':  {'name': 'Línea 3',  'color': '#FFD700'},
    '4':  {'name': 'Línea 4',  'color': '#B25400'},
    '5':  {'name': 'Línea 5',  'color': '#39B54A'},
    '6':  {'name': 'Línea 6',  'color': '#9E9E9E'},
    '7':  {'name': 'Línea 7',  'color': '#FF9800'},
    '8':  {'name': 'Línea 8',  'color': '#FF69B4'},
    '9':  {'name': 'Línea 9',  'color': '#9C27B0'},
    '10': {'name': 'Línea 10', 'color': '#0D47A1'},
    '11': {'name': 'Línea 11', 'color': '#006400'},
    '12': {'name': 'Línea 12', 'color': '#a49a00'},
    'R':  {'name': 'Ramal',    'color': '#FFFFFF'}
}

def extraer_coordenadas_de_kml(kml_content):
    """Parsea el contenido de un archivo KML y extrae las coordenadas."""
    # Eliminar el namespace de XML para simplificar el parseo
    kml_content = re.sub(' xmlns="[^"]+"', '', kml_content, count=1)
    
    root = ET.fromstring(kml_content)
    
    # Buscar todas las coordenadas en el archivo
    all_coords_str = []
    for coordinates_tag in root.findall('.//coordinates'):
        all_coords_str.append(coordinates_tag.text.strip())
        
    # Unir todas las coordenadas encontradas
    full_coords_str = " ".join(all_coords_str)
    
    # Procesar el string de coordenadas
    coordinates = []
    for coord_set in full_coords_str.split():
        parts = coord_set.split(',')
        if len(parts) >= 2:
            try:
                lon, lat = float(parts[0]), float(parts[1])
                coordinates.append([lat, lon])
            except ValueError:
                continue
        
    return coordinates

def generar_json_desde_kmz(kmz_dir, output_path):
    """
    Genera el archivo metro_routes.json a partir de archivos KMZ.
    """
    print(f"Iniciando generación de JSON desde la carpeta '{kmz_dir}'...")
    
    rutas_data = {"lines": []}
    
    for filename in os.listdir(kmz_dir):
        if not filename.endswith('.kmz'):
            continue
            
        # Extraer el número de línea del nombre del archivo (ej. 'M4_L10A.kmz' -> '10')
        match = re.search(r'_L(\d+)', filename)
        if not match:
            continue
        
        line_num = match.group(1)
        config = LINEAS_CONFIG.get(line_num)
        
        if not config:
            print(f"  -> Advertencia: No se encontró configuración para la línea {line_num} en el archivo {filename}")
            continue

        try:
            kmz_path = os.path.join(kmz_dir, filename)
            with zipfile.ZipFile(kmz_path, 'r') as kmz:
                # Buscar archivos de tramo dentro de la carpeta files/
                tramo_files = [f for f in kmz.namelist() if f.endswith('_TRAMO.kml') and 'files/' in f]
                
                if not tramo_files:
                    print(f"  -> Error: No se encontraron archivos de tramo en '{filename}'")
                    continue
                
                # Extraer coordenadas de cada tramo
                paths = []
                total_points = 0
                
                for tramo_file in sorted(tramo_files):
                    with kmz.open(tramo_file) as kml_file:
                        kml_content = kml_file.read().decode('utf-8')
                        coordinates = extraer_coordenadas_de_kml(kml_content)
                        
                        if coordinates:
                            paths.append(coordinates)
                            total_points += len(coordinates)
                            print(f"    -> Tramo {tramo_file}: {len(coordinates)} puntos")
                        else:
                            print(f"    -> Advertencia: No se extrajeron coordenadas de {tramo_file}")
                
                if paths:
                    # Añadir el trazado al JSON con estructura paths
                    rutas_data["lines"].append({
                        "line": line_num,
                        "name": config['name'],
                        "color": config['color'],
                        "paths": paths
                    })
                    print(f"  -> Procesado '{filename}' para la Línea {line_num} ({len(paths)} tramos, {total_points} puntos total)")
                else:
                    print(f"  -> Advertencia: No se extrajeron coordenadas de '{filename}'")

        except Exception as e:
            print(f"  -> Error procesando el archivo '{filename}': {e}")
            
    # Guardar el archivo JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rutas_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Archivo '{output_path}' generado exitosamente con {len(rutas_data['lines'])} líneas.")
    except IOError as e:
        print(f"\n❌ Error al escribir el archivo JSON: {e}")


if __name__ == '__main__':
    KMZ_DIRECTORY = 'LINESM4'
    OUTPUT_JSON_PATH = 'static/data/metro_routes.json'
    
    if not os.path.isdir(KMZ_DIRECTORY):
        print(f"Error: El directorio '{KMZ_DIRECTORY}' no se encuentra.")
    else:
        generar_json_desde_kmz(KMZ_DIRECTORY, OUTPUT_JSON_PATH) 