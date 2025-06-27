#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de rutas para Cercanías Madrid
Genera las rutas (paths) para cada línea de Cercanías basándose en las estaciones
"""

import json
import os
from typing import List, Dict, Tuple

def load_cercanias_data() -> Dict:
    """Cargar datos de Cercanías con capas"""
    cercanias_file = 'static/data/cercanias_con_capas.json'
    
    if not os.path.exists(cercanias_file):
        print(f"❌ No se encontró el archivo: {cercanias_file}")
        return None
    
    try:
        with open(cercanias_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Datos de Cercanías cargados: {len(data.get('stations', []))} estaciones")
        return data
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return None

def get_station_coordinates(station_id: str, stations: List[Dict]) -> Tuple[float, float]:
    """Obtener coordenadas de una estación por su código"""
    for station in stations:
        if station.get('codigo') == station_id:
            return station.get('latitud'), station.get('longitud')
    return None, None

def generate_line_path(station_ids: List[str], stations: List[Dict]) -> List[List[float]]:
    """Generar ruta para una línea basándose en las estaciones"""
    path = []
    
    for station_id in station_ids:
        lat, lon = get_station_coordinates(station_id, stations)
        if lat is not None and lon is not None:
            path.append([lat, lon])
    
    return path

def generate_all_routes(cercanias_data: Dict) -> Dict:
    """Generar rutas para todas las líneas de Cercanías"""
    stations = cercanias_data.get('stations', [])
    layers = cercanias_data.get('layers', {})
    
    print("🔧 Generando rutas para cada línea...")
    
    for layer_id, layer_info in layers.items():
        line_type = layer_info.get('line_type')
        station_ids = layer_info.get('stations', [])
        
        if station_ids:
            path = generate_line_path(station_ids, stations)
            if path:
                layer_info['paths'] = [path]  # Añadir la ruta a la capa
                print(f"✅ Ruta generada para {line_type}: {len(path)} puntos")
            else:
                print(f"⚠️ No se pudo generar ruta para {line_type}")
        else:
            print(f"⚠️ No hay estaciones para {line_type}")
    
    return cercanias_data

def save_updated_data(data: Dict, output_file: str):
    """Guardar datos actualizados"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Datos guardados en: {output_file}")
    except Exception as e:
        print(f"❌ Error guardando datos: {e}")

def main():
    print("🚂 Generador de rutas de Cercanías Madrid")
    print("=" * 50)
    
    # Cargar datos
    cercanias_data = load_cercanias_data()
    if not cercanias_data:
        return
    
    # Generar rutas
    updated_data = generate_all_routes(cercanias_data)
    
    # Guardar datos actualizados
    output_file = 'static/data/cercanias_con_capas.json'
    save_updated_data(updated_data, output_file)
    
    # Estadísticas
    layers = updated_data.get('layers', {})
    total_routes = sum(1 for layer in layers.values() if layer.get('paths'))
    
    print("\n📊 Estadísticas:")
    print(f"   - Total de líneas: {len(layers)}")
    print(f"   - Líneas con rutas: {total_routes}")
    print(f"   - Total de estaciones: {len(updated_data.get('stations', []))}")
    
    print("\n✅ Proceso completado")

if __name__ == "__main__":
    main() 