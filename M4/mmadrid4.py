import pandas as pd
import svgwrite
import os
import re

# --- Configuración ---
# Directorio de datos GTFS
GTFS_DIR = os.path.dirname(__file__) # Esto usará la carpeta M4/ donde está el script

# Archivos GTFS
SHAPES_FILE = os.path.join(GTFS_DIR, 'shapes.txt')
TRIPS_FILE = os.path.join(GTFS_DIR, 'trips.txt')
ROUTES_FILE = os.path.join(GTFS_DIR, 'routes.txt')

# Colores oficiales (consistente con app.py)
LINEAS_CONFIG = {
    '1':  {'color': '#00AEEF'},
    '2':  {'color': '#FF0000'},
    '3':  {'color': '#FFD700'},
    '4':  {'color': '#B25400'},
    '5':  {'color': '#39B54A'},
    '6':  {'color': '#9E9E9E'},
    '7':  {'color': '#FF9800'},
    '8':  {'color': '#FF69B4'},
    '9':  {'color': '#9C27B0'},
    '10': {'color': '#0D47A1'},
    '11': {'color': '#006400'},
    '12': {'color': '#a49a00'},
    'R':  {'color': '#FFFFFF'}
}

# --- Carga de datos ---
print("Cargando datos GTFS...")
shapes = pd.read_csv(SHAPES_FILE)
trips = pd.read_csv(TRIPS_FILE)
routes = pd.read_csv(ROUTES_FILE)

# --- Procesamiento ---
# 1. Crear un mapeo de shape_id -> route_id -> line_number
# Usamos trips para conectar shapes con routes
shape_to_route = trips[['shape_id', 'route_id']].drop_duplicates().set_index('shape_id')
route_to_line = routes[['route_id', 'route_short_name']].set_index('route_id')

shape_to_line = shape_to_route.join(route_to_line, on='route_id')

def get_line_number(short_name):
    """
    Función mejorada para extraer el número de línea base de forma robusta.
    """
    if pd.isna(short_name):
        return None
    
    s_name = str(short_name)
    
    # 1. Intenta encontrar el número de línea al principio del nombre.
    match = re.match(r'^(\d+)', s_name)
    if match:
        return match.group(1)
        
    # 2. Maneja casos especiales como 'Ramal' o 'R'.
    if 'ramal' in s_name.lower() or 'r' == s_name.lower():
        return 'R'
        
    # 3. Como fallback, devuelve el nombre original.
    return s_name

shape_to_line['line_number'] = shape_to_line['route_short_name'].apply(get_line_number)
print("Mapeo de trazados a líneas creado.")

# 2. Normalización de coordenadas
print("Normalizando coordenadas...")
lat_min, lat_max = shapes['shape_pt_lat'].min(), shapes['shape_pt_lat'].max()
lon_min, lon_max = shapes['shape_pt_lon'].min(), shapes['shape_pt_lon'].max()

# Para evitar un mapa aplastado, calculamos un aspect ratio
width = lon_max - lon_min
height = lat_max - lat_min
aspect_ratio = height / width
svg_width = 1200
svg_height = svg_width * aspect_ratio

shapes['x'] = (shapes['shape_pt_lon'] - lon_min) / (lon_max - lon_min) * svg_width
shapes['y'] = (lat_max - shapes['shape_pt_lat']) / (lat_max - lat_min) * svg_height
print("Coordenadas normalizadas.")

# --- Creación de SVG ---
print("Creando archivo SVG...")
dwg = svgwrite.Drawing('plano_metro_oficial.svg', profile='full', size=(svg_width, svg_height))
dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='black')) # Fondo negro

# Dibuja cada shape_id con su color oficial
for shape_id, group in shapes.groupby("shape_id"):
    try:
        line_info = shape_to_line.loc[shape_id]
        line_number = line_info['line_number']
        color = LINEAS_CONFIG.get(line_number, {'color': '#808080'})['color']
    except (KeyError, TypeError):
        color = '#808080' # Color gris para trazados sin línea asignada

    points = list(zip(group['x'], group['y']))
    dwg.add(dwg.polyline(points, stroke=color, fill='none', stroke_width=2, opacity=0.8))

dwg.save()

print(f"✅ SVG mejorado generado: plano_metro_oficial.svg (Tamaño: {int(svg_width)}x{int(svg_height)})")
