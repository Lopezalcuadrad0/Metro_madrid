#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de rutas de Cercanías desde datos GTFS
Extrae las rutas reales de Cercanías desde los archivos GTFS
"""

import csv
import json
import os
from typing import Dict, List, Tuple

def load_gtfs_data(gtfs_dir: str) -> Dict:
    """Cargar datos GTFS de Cercanías"""
    data = {
        'routes': [],
        'stops': [],
        'trips': [],
        'stop_times': []
    }
    
    # Cargar routes.txt
    routes_file = os.path.join(gtfs_dir, 'routes.txt')
    if os.path.exists(routes_file):
        with open(routes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data['routes'] = list(reader)
        print(f"✅ Rutas cargadas: {len(data['routes'])}")
    
    # Cargar stops.txt
    stops_file = os.path.join(gtfs_dir, 'stops.txt')
    if os.path.exists(stops_file):
        with open(stops_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data['stops'] = list(reader)
        print(f"✅ Paradas cargadas: {len(data['stops'])}")
    
    # Cargar trips.txt
    trips_file = os.path.join(gtfs_dir, 'trips.txt')
    if os.path.exists(trips_file):
        with open(trips_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data['trips'] = list(reader)
        print(f"✅ Viajes cargados: {len(data['trips'])}")
    
    # Cargar stop_times.txt
    stop_times_file = os.path.join(gtfs_dir, 'stop_times.txt')
    if os.path.exists(stop_times_file):
        with open(stop_times_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data['stop_times'] = list(reader)
        print(f"✅ Horarios cargados: {len(data['stop_times'])}")
    
    return data

def get_stop_coordinates(stop_id: str, stops: List[Dict]) -> Tuple[float, float]:
    """Obtener coordenadas de una parada"""
    for stop in stops:
        if stop['stop_id'] == stop_id:
            return float(stop['stop_lat']), float(stop['stop_lon'])
    return None, None

def get_route_stops(route_id: str, trips: List[Dict], stop_times: List[Dict]) -> List[str]:
    """Obtener las paradas de una ruta en orden"""
    # Encontrar un viaje de esta ruta
    route_trip = None
    for trip in trips:
        if trip['route_id'] == route_id:
            route_trip = trip['trip_id']
            break
    
    if not route_trip:
        return []
    
    # Obtener las paradas de este viaje en orden
    trip_stops = []
    for stop_time in stop_times:
        if stop_time['trip_id'] == route_trip:
            trip_stops.append({
                'stop_id': stop_time['stop_id'],
                'sequence': int(stop_time['stop_sequence'])
            })
    
    # Ordenar por secuencia
    trip_stops.sort(key=lambda x: x['sequence'])
    return [stop['stop_id'] for stop in trip_stops]

def generate_route_path(route_id: str, gtfs_data: Dict) -> List[List[float]]:
    """Generar ruta para una línea de Cercanías"""
    stops = gtfs_data['stops']
    trips = gtfs_data['trips']
    stop_times = gtfs_data['stop_times']
    
    # Obtener paradas de la ruta
    route_stops = get_route_stops(route_id, trips, stop_times)
    
    if not route_stops:
        print(f"⚠️ No se encontraron paradas para la ruta {route_id}")
        return []
    
    # Generar ruta conectando las paradas
    path = []
    for stop_id in route_stops:
        lat, lon = get_stop_coordinates(stop_id, stops)
        if lat is not None and lon is not None:
            path.append([lat, lon])
    
    return path

def extract_cercanias_routes(gtfs_dir: str) -> Dict:
    """Extraer todas las rutas de Cercanías"""
    print("🚂 Extrayendo rutas de Cercanías desde GTFS...")
    
    # Cargar datos GTFS
    gtfs_data = load_gtfs_data(gtfs_dir)
    
    if not gtfs_data['routes']:
        print("❌ No se encontraron rutas en el GTFS")
        return {}
    
    # Cargar datos de Cercanías existentes para obtener las estaciones por línea
    cercanias_file = 'static/data/cercanias_con_capas.json'
    if not os.path.exists(cercanias_file):
        print(f"❌ No se encontró el archivo: {cercanias_file}")
        return {}
    
    with open(cercanias_file, 'r', encoding='utf-8') as f:
        cercanias_data = json.load(f)
    
    # Colores oficiales de Cercanías
    cercanias_colors = {
        '5__C1___': '#70C5E8',  # C-1
        '5__C2___': '#008B45',  # C-2
        '5__C3___': '#9F2E86',  # C-3
        '5__C4_A__': '#004E98', # C-4A
        '5__C4_B__': '#004E98', # C-4B
        '5__C5___': '#F9BA13',  # C-5
        '5__C7___': '#ED1C24',  # C-7
        '5__C8___': '#008B45',  # C-8
        '5__C9___': '#F95900',  # C-9
        '5__C10___': '#90B70E'  # C-10
    }
    
    # Mapear rutas GTFS a capas existentes
    route_mapping = {
        '5__C1___': 'C-1',
        '5__C2___': 'C-2', 
        '5__C3___': 'C-3',
        '5__C4_A__': 'C-4a',
        '5__C4_B__': 'C-4b',
        '5__C5___': 'C-5',
        '5__C7___': 'C-7a',
        '5__C8___': 'C-8',
        '5__C9___': 'C-9',
        '5__C10___': 'C-10'
    }
    
    # Crear diccionario de coordenadas GTFS por nombre de estación
    gtfs_coords = {}
    for stop in gtfs_data['stops']:
        stop_name = stop['stop_name'].upper().strip()
        gtfs_coords[stop_name] = (float(stop['stop_lat']), float(stop['stop_lon']))
    
    routes_data = {}
    
    for route in gtfs_data['routes']:
        route_id = route['route_id']
        route_name = route['route_short_name']
        line_type = route_mapping.get(route_id)
        
        if not line_type:
            print(f"⚠️ Ruta {route_name} no mapeada, saltando...")
            continue
        
        print(f"🔧 Procesando ruta {route_name} ({line_type})...")
        
        # Buscar la capa correspondiente en los datos existentes
        layer_stations = []
        for layer_id, layer_info in cercanias_data['layers'].items():
            if layer_info.get('line_type') == line_type:
                layer_stations = layer_info.get('stations', [])
                break
        
        if not layer_stations:
            print(f"⚠️ No se encontraron estaciones para {line_type}")
            continue
        
        # Generar ruta usando coordenadas GTFS cuando estén disponibles
        path = []
        for station in layer_stations:
            station_name = station.get('name', '').upper().strip()
            
            # Buscar coordenadas en GTFS
            if station_name in gtfs_coords:
                lat, lon = gtfs_coords[station_name]
                path.append([lat, lon])
            else:
                # Usar coordenadas existentes si no están en GTFS
                lat = station.get('lat')
                lon = station.get('lon')
                if lat is not None and lon is not None:
                    path.append([lat, lon])
        
        if path:
            routes_data[route_id] = {
                'name': route_name,
                'long_name': route['route_long_name'],
                'color': cercanias_colors.get(route_id, '#808080'),
                'path': path,
                'stops_count': len(path),
                'line_type': line_type
            }
            print(f"✅ Ruta {route_name} generada: {len(path)} puntos")
        else:
            print(f"⚠️ No se pudo generar ruta para {route_name}")
    
    return routes_data

def save_routes_to_json(routes_data: Dict, output_file: str):
    """Guardar rutas en formato JSON"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(routes_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Rutas guardadas en: {output_file}")
    except Exception as e:
        print(f"❌ Error guardando rutas: {e}")

def update_cercanias_layers(routes_data: Dict):
    """Actualizar el archivo cercanias_con_capas.json con las rutas reales"""
    cercanias_file = 'static/data/cercanias_con_capas.json'
    
    if not os.path.exists(cercanias_file):
        print(f"❌ No se encontró el archivo: {cercanias_file}")
        return
    
    try:
        # Cargar datos actuales
        with open(cercanias_file, 'r', encoding='utf-8') as f:
            cercanias_data = json.load(f)
        
        # Mapear rutas GTFS a capas existentes
        route_mapping = {
            '5__C1___': 'C-1',
            '5__C2___': 'C-2', 
            '5__C3___': 'C-3',
            '5__C4_A__': 'C-4a',
            '5__C4_B__': 'C-4b',
            '5__C5___': 'C-5',
            '5__C7___': 'C-7a',
            '5__C8___': 'C-8',
            '5__C9___': 'C-9',
            '5__C10___': 'C-10'
        }
        
        # Actualizar capas con rutas reales
        layers_updated = 0
        for route_id, route_info in routes_data.items():
            line_type = route_mapping.get(route_id)
            if line_type:
                # Buscar la capa correspondiente
                for layer_id, layer_info in cercanias_data['layers'].items():
                    if layer_info.get('line_type') == line_type:
                        layer_info['paths'] = [route_info['path']]
                        layer_info['color'] = route_info['color']
                        layers_updated += 1
                        print(f"✅ Capa {line_type} actualizada con ruta real")
                        break
        
        # Guardar datos actualizados
        with open(cercanias_file, 'w', encoding='utf-8') as f:
            json.dump(cercanias_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Archivo actualizado: {layers_updated} capas con rutas reales")
        
    except Exception as e:
        print(f"❌ Error actualizando archivo: {e}")

def main():
    print("🚂 Extractor de rutas de Cercanías desde GTFS")
    print("=" * 60)
    
    # Directorio GTFS
    gtfs_dir = 'google_transit_M5'
    
    if not os.path.exists(gtfs_dir):
        print(f"❌ No se encontró el directorio GTFS: {gtfs_dir}")
        return
    
    # Extraer rutas
    routes_data = extract_cercanias_routes(gtfs_dir)
    
    if not routes_data:
        print("❌ No se pudieron extraer rutas")
        return
    
    # Guardar rutas en archivo separado
    routes_file = 'static/data/cercanias_rutas_gtfs.json'
    save_routes_to_json(routes_data, routes_file)
    
    # Actualizar archivo principal
    update_cercanias_layers(routes_data)
    
    # Estadísticas
    print("\n📊 Estadísticas:")
    print(f"   - Total de rutas extraídas: {len(routes_data)}")
    total_points = sum(len(route['path']) for route in routes_data.values())
    print(f"   - Total de puntos de ruta: {total_points}")
    
    print("\n✅ Proceso completado")

if __name__ == "__main__":
    main() 