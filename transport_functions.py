#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones de transporte público para app.py
Migradas desde app_metro_ligero.py
"""

import requests
import json
from datetime import datetime, timedelta

# Cache simple para los datos de transporte
transport_cache = {}
CACHE_DURATION = 300  # 5 minutos de cache

def get_cached_data(key):
    """Obtiene datos del cache si no han expirado"""
    if key in transport_cache:
        data, timestamp = transport_cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
            print(f"📦 Usando cache para {key}")
            return data
    return None

def set_cached_data(key, data):
    """Guarda datos en el cache"""
    transport_cache[key] = (data, datetime.now())
    print(f"💾 Guardando en cache: {key}")

def transform_coordinates(x, y, from_srs=25830, to_srs=4326):
    """Transforma coordenadas entre sistemas de referencia"""
    try:
        # Para transformación simple de EPSG:25830 a EPSG:4326 (aproximada)
        # Esta es una aproximación básica - en producción usar una librería como pyproj
        if from_srs == 25830 and to_srs == 4326:
            # Transformación aproximada de UTM ETRS89 a WGS84
            # Madrid está en zona 30N
            lon = (x - 500000) / (0.9996 * 6378137) * 180 / 3.14159 + 3
            lat = y / (0.9996 * 6378137) * 180 / 3.14159 + 40.4
            return lon, lat
        return x, y
    except Exception as e:
        print(f"Error transformando coordenadas: {e}")
        return x, y

def convert_arcgis_geometry_to_geojson(geometry, geometry_type):
    """Convierte geometría de ArcGIS al formato GeoJSON estándar"""
    if not geometry:
        return None
    
    try:
        if geometry_type == "esriGeometryPoint":
            # Punto: {x, y} -> {"type": "Point", "coordinates": [x, y]}
            if 'x' in geometry and 'y' in geometry:
                return {
                    "type": "Point",
                    "coordinates": [geometry['x'], geometry['y']]
                }
        
        elif geometry_type == "esriGeometryPolyline":
            # Línea: {paths: [[[x1,y1], [x2,y2], ...]]} -> {"type": "LineString", "coordinates": [[x1,y1], [x2,y2], ...]}
            if 'paths' in geometry and geometry['paths']:
                # Tomar el primer path (la primera línea)
                path = geometry['paths'][0]
                return {
                    "type": "LineString",
                    "coordinates": path
                }
        
        elif geometry_type == "esriGeometryPolygon":
            # Polígono: {rings: [[[x1,y1], [x2,y2], ...]]} -> {"type": "Polygon", "coordinates": [[[x1,y1], [x2,y2], ...]]}
            if 'rings' in geometry and geometry['rings']:
                return {
                    "type": "Polygon",
                    "coordinates": geometry['rings']
                }
        
        return None
    except Exception as e:
        print(f"Error convirtiendo geometría: {e}")
        return None

def fetch_arcgis_data(url, layer_id=0, out_srs=4326):
    """Función genérica para obtener datos de servicios ArcGIS"""
    try:
        # Construir URL de consulta
        query_url = f"{url}/{layer_id}/query"
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'outSR': str(out_srs),
            'f': 'json',
            'returnGeometry': 'true'
        }
        
        print(f"Consultando: {query_url}")
        response = requests.get(query_url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Validar respuesta
        if 'error' in data:
            print(f"Error en respuesta ArcGIS: {data['error']}")
            return None
            
        if 'features' not in data:
            print("No se encontraron features en la respuesta")
            return None
            
        # Transformar coordenadas si es necesario
        if out_srs == 4326 and data.get('spatialReference', {}).get('wkid') == 25830:
            for feature in data['features']:
                if 'geometry' in feature and 'x' in feature['geometry'] and 'y' in feature['geometry']:
                    x, y = transform_coordinates(
                        feature['geometry']['x'], 
                        feature['geometry']['y']
                    )
                    feature['geometry']['x'] = x
                    feature['geometry']['y'] = y
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error de red al consultar {url}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al consultar {url}: {e}")
        return None

def fetch_arcgis_data_multiple_layers(url, layer_ids, out_srs=4326):
    """Obtiene y concatena features de varias capas de un servicio ArcGIS"""
    # Crear clave de cache única
    cache_key = f"arcgis_{url}_{'_'.join(map(str, layer_ids))}_{out_srs}"
    
    # Verificar cache primero
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data
    
    all_features = []
    successful_layers = 0
    
    for layer_id in layer_ids:
        try:
            print(f"Consultando capa {layer_id} de {url}")
            data = fetch_arcgis_data(url, layer_id, out_srs)
            if data and 'features' in data:
                # Obtener el tipo de geometría de la capa
                geometry_type = data.get('geometryType', 'esriGeometryPoint')
                
                for feature in data['features']:
                    # Convertir geometría ArcGIS a GeoJSON estándar
                    geojson_geometry = convert_arcgis_geometry_to_geojson(feature.get('geometry', {}), geometry_type)
                    
                    # Fusionar attributes y properties en uno solo
                    properties = {}
                    if 'attributes' in feature and feature['attributes']:
                        properties.update(feature['attributes'])
                    if 'properties' in feature and feature['properties']:
                        properties.update(feature['properties'])
                    # Siempre incluir layer_type si existe
                    if 'layer_type' in feature:
                        properties['layer_type'] = feature['layer_type']
                    
                    # Crear feature GeoJSON válido
                    geojson_feature = {
                        'type': 'Feature',
                        'geometry': geojson_geometry,
                        'properties': properties
                    }
                    all_features.append(geojson_feature)
                
                successful_layers += 1
                print(f"✅ Capa {layer_id}: {len(data['features'])} features")
            else:
                print(f"⚠️ Capa {layer_id}: Sin datos válidos")
                
        except Exception as e:
            print(f"❌ Error en capa {layer_id}: {e}")
    
    # Guardar en cache
    set_cached_data(cache_key, all_features)
    
    print(f"Total: {successful_layers}/{len(layer_ids)} capas exitosas, {len(all_features)} features")
    return all_features 