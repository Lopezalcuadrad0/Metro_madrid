#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERADOR DE DATOS COMPLETOS DE CERCANÍAS
=========================================

Descarga todos los datos de Cercanías desde el servicio ArcGIS y genera
un archivo JSON completo con todas las líneas (C-1 a C-10).

Basado en el servicio: https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/M5_Lineas/FeatureServer
"""

import requests
import json
import os
from datetime import datetime
from math import sqrt
from collections import defaultdict
from typing import Dict, List, Tuple, Any

# Datos oficiales de estaciones por línea de Cercanías Madrid
ESTACIONES_OFICIALES_CERCANIAS = {
    "C-1": [
        "Chamartín-Clara Campoamor", "Fuente de la Mora", "Valdebebas", "Aeropuerto T4"
    ],
    "C-2": [
        "Guadalajara", "Azuqueca", "Meco", "Alcalá de Henares-Universidad", 
        "Alcalá de Henares", "La Garena", "Soto del Henares", "Torrejón de Ardoz", 
        "San Fernando", "Coslada", "Vicálvaro", "Santa Eugenia", "Vallecas", 
        "El Pozo", "Asamblea de Madrid-Entrevías", "Atocha", "Recoletos", 
        "Nuevos Ministerios", "Chamartín-Clara Campoamor"
    ],
    "C-3": [
        "Aranjuez", "Ciempozuelos", "Valdemoro", "Pinto", "Getafe Industrial", 
        "El Casar", "San Cristóbal Industrial", "San Cristóbal de los Ángeles", 
        "Villaverde Bajo", "Atocha", "Sol", "Nuevos Ministerios", "Chamartín-Clara Campoamor"
    ],
    "C-4a": [
        "Parla", "Getafe Sector 3", "Getafe Centro", "Las Margaritas-Universidad", 
        "Villaverde Alto", "Villaverde Bajo", "Atocha", "Sol", "Nuevos Ministerios", 
        "Chamartín-Clara Campoamor", "Fuencarral", "Cantoblanco-Universidad", 
        "Valdelasfuentes", "Alcobendas-San Sebastián de los Reyes"
    ],
    "C-4b": [
        "Parla", "Getafe Sector 3", "Getafe Centro", "Las Margaritas-Universidad", 
        "Villaverde Alto", "Villaverde Bajo", "Atocha", "Sol", "Nuevos Ministerios", 
        "Chamartín-Clara Campoamor", "Fuencarral", "Cantoblanco-Universidad", 
        "El Goloso", "Tres Cantos", "Colmenar Viejo"
    ],
    "C-5": [
        "Humanes", "Fuenlabrada", "La Serna", "Parque Polvoranca", "Leganés", 
        "Zarzaquemada", "Villaverde Alto", "Puente Alcocer", "Orcasitas", 
        "Doce de Octubre", "Méndez Álvaro", "Atocha", "Embajadores", "Laguna", 
        "Aluche", "Maestra Justa Freire-Polideportivo Aluche", "Las Águilas", 
        "Cuatro Vientos", "San José de Valderas", "Alcorcón", "Las Retamas", 
        "Móstoles", "Móstoles-El Soto"
    ],
    "C-7": [
        "Príncipe Pío", "Aravaca", "Pozuelo", "El Barrial-Centro Comercial Pozuelo", 
        "Majadahonda", "Las Rozas", "Pitis", "Mirasierra-Paco de Lucía", 
        "Ramón y Cajal", "Chamartín-Clara Campoamor", "Nuevos Ministerios", 
        "Recoletos", "Atocha", "Asamblea de Madrid-Entrevías", "El Pozo", 
        "Vallecas", "Santa Eugenia", "Vicálvaro", "Coslada", "San Fernando", 
        "Torrejón de Ardoz", "Soto del Henares", "La Garena", "Alcalá de Henares"
    ],
    "C-8a": [
        "Guadalajara", "Azuqueca", "Meco", "Alcalá de Henares-Universidad", 
        "Alcalá de Henares", "La Garena", "Soto del Henares", "Torrejón de Ardoz", 
        "San Fernando", "Coslada", "Vicálvaro", "Santa Eugenia", "Vallecas", 
        "El Pozo", "Asamblea de Madrid-Entrevías", "Atocha", "Recoletos", 
        "Nuevos Ministerios", "Chamartín-Clara Campoamor", "Ramón y Cajal", 
        "Mirasierra-Paco de Lucía", "Pitis", "Pinar", "Las Matas", "Torrelodones", 
        "Galapagar-La Navata", "Villalba", "San Yago", "Las Zorreras", "El Escorial", 
        "Robledo de Chavela", "Zarzalejo", "Santa María de la Alameda-Peguerinos"
    ],
    "C-8b": [
        "Guadalajara", "Azuqueca", "Meco", "Alcalá de Henares-Universidad", 
        "Alcalá de Henares", "La Garena", "Soto del Henares", "Torrejón de Ardoz", 
        "San Fernando", "Coslada", "Vicálvaro", "Santa Eugenia", "Vallecas", 
        "El Pozo", "Asamblea de Madrid-Entrevías", "Atocha", "Recoletos", 
        "Nuevos Ministerios", "Chamartín-Clara Campoamor", "Ramón y Cajal", 
        "Mirasierra-Paco de Lucía", "Pitis", "Pinar", "Las Matas", "Torrelodones", 
        "Galapagar-La Navata", "Villalba", "Los Negrales", "Alpedrete", 
        "Collado Mediano", "Los Molinos", "Cercedilla"
    ],
    "C-9": [
        "Cercedilla", "Puerto de Navacerrada", "Cotos"
    ],
    "C-10": [
        "Villalba", "Galapagar-La Navata", "Torrelodones", "Las Matas", "Pinar", 
        "Las Rozas", "Majadahonda", "El Barrial-Centro Comercial Pozuelo", 
        "Pozuelo", "Aravaca", "Príncipe Pío", "Pirámides", "Delicias", 
        "Méndez Álvaro", "Atocha", "Recoletos", "Nuevos Ministerios", "Chamartín-Clara Campoamor"
    ]
}

def fetch_arcgis_data(url, layer_id=0, out_srs=4326):
    """Función para obtener datos de servicios ArcGIS"""
    try:
        query_url = f"{url}/{layer_id}/query"
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'outSR': str(out_srs),
            'f': 'json',
            'returnGeometry': 'true'
        }
        
        print(f"🔍 Consultando capa {layer_id}: {query_url}")
        response = requests.get(query_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Error en respuesta ArcGIS: {data['error']}")
            return None
            
        if 'features' not in data:
            print(f"⚠️ No se encontraron features en capa {layer_id}")
            return None
            
        print(f"✅ Capa {layer_id}: {len(data['features'])} features obtenidas")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red al consultar capa {layer_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado en capa {layer_id}: {e}")
        return None

def convert_arcgis_geometry_to_geojson(geometry, geometry_type):
    """Convierte geometría de ArcGIS al formato GeoJSON estándar"""
    if not geometry:
        return None
    
    try:
        if geometry_type == "esriGeometryPoint":
            if 'x' in geometry and 'y' in geometry:
                return {
                    "type": "Point",
                    "coordinates": [geometry['x'], geometry['y']]
                }
        
        elif geometry_type == "esriGeometryPolyline":
            if 'paths' in geometry and geometry['paths']:
                path = geometry['paths'][0]
                return {
                    "type": "LineString",
                    "coordinates": path
                }
        
        elif geometry_type == "esriGeometryPolygon":
            if 'rings' in geometry and geometry['rings']:
                return {
                    "type": "Polygon",
                    "coordinates": geometry['rings']
                }
        
        return None
    except Exception as e:
        print(f"⚠️ Error convirtiendo geometría: {e}")
        return None

def normalizar_nombre_estacion(nombre):
    """
    Normaliza nombres de estaciones para comparación.
    """
    return nombre.upper().replace('-', ' ').replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')

def associate_stations_to_lines_by_name_and_proximity(estaciones_data, tramos_data, max_distance_meters=500):
    """
    Asocia estaciones a líneas usando primero coincidencia de nombres con datos oficiales,
    y luego proximidad geográfica como respaldo.
    """
    print("🔍 Asociando estaciones a líneas...")
    print("   1️⃣ Por nombre usando datos oficiales")
    print("   2️⃣ Por proximidad geográfica como respaldo")
    
    def calculate_distance(coord1, coord2):
        """Calcula distancia euclidiana aproximada entre dos coordenadas"""
        try:
            x1, y1 = coord1
            x2, y2 = coord2
            return sqrt((x2 - x1)**2 + (y2 - y1)**2)
        except:
            return float('inf')
    
    def get_coordinates_from_geometry(geometry):
        """Extrae coordenadas del geometry"""
        try:
            if geometry.get('type') == 'Point':
                return geometry['coordinates']
            elif geometry.get('type') == 'LineString':
                # Para líneas, usar el punto medio
                coords = geometry['coordinates']
                if coords:
                    mid_idx = len(coords) // 2
                    return coords[mid_idx]
            return None
        except:
            return None
    
    # Crear índice normalizado de estaciones oficiales
    estaciones_oficiales_normalizadas = {}
    for linea, nombres in ESTACIONES_OFICIALES_CERCANIAS.items():
        for nombre in nombres:
            nombre_norm = normalizar_nombre_estacion(nombre)
            estaciones_oficiales_normalizadas[nombre_norm] = linea
    
    print(f"📊 Estaciones oficiales cargadas: {len(estaciones_oficiales_normalizadas)}")
    
    # Organizar tramos por línea con sus coordenadas
    tramos_por_linea = {}
    for linea, tramos in tramos_data.items():
        if linea != 'unknown' and tramos:
            tramos_por_linea[linea] = []
            for tramo in tramos:
                coords = get_coordinates_from_geometry(tramo.get('geometry', {}))
                if coords:
                    tramos_por_linea[linea].append(coords)
    
    print(f"📊 Líneas con tramos disponibles: {list(tramos_por_linea.keys())}")
    
    # Procesar estaciones
    estaciones_por_linea = {}
    estaciones_sin_linea = []
    estaciones_asignadas_por_nombre = 0
    estaciones_asignadas_por_proximidad = 0
    
    if 'unknown' in estaciones_data:
        for estacion in estaciones_data['unknown']:
            props = estacion.get('properties', {})
            nombre_estacion = props.get('DENOMINACION', '').strip()
            
            if not nombre_estacion:
                estaciones_sin_linea.append(estacion)
                continue
            
            # Fase 1: Asignación por nombre
            nombre_norm = normalizar_nombre_estacion(nombre_estacion)
            
            if nombre_norm in estaciones_oficiales_normalizadas:
                linea = estaciones_oficiales_normalizadas[nombre_norm]
                if linea not in estaciones_por_linea:
                    estaciones_por_linea[linea] = []
                estaciones_por_linea[linea].append(estacion)
                estaciones_asignadas_por_nombre += 1
                print(f"   ✓ {nombre_estacion} → {linea} (nombre oficial)")
                continue
            
            # Fase 2: Asignación por proximidad
            estacion_coords = get_coordinates_from_geometry(estacion.get('geometry', {}))
            
            if not estacion_coords:
                estaciones_sin_linea.append(estacion)
                continue
            
            mejor_linea = None
            menor_distancia = float('inf')
            
            # Buscar la línea más cercana
            for linea, coords_tramos in tramos_por_linea.items():
                for coords_tramo in coords_tramos:
                    distancia = calculate_distance(estacion_coords, coords_tramo)
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        mejor_linea = linea
            
            # Si está dentro del rango, asignar a esa línea
            if mejor_linea and menor_distancia <= max_distance_meters:
                if mejor_linea not in estaciones_por_linea:
                    estaciones_por_linea[mejor_linea] = []
                estaciones_por_linea[mejor_linea].append(estacion)
                estaciones_asignadas_por_proximidad += 1
                print(f"   ✓ {nombre_estacion} → {mejor_linea} (proximidad: {menor_distancia:.1f}m)")
            else:
                estaciones_sin_linea.append(estacion)
                print(f"   ⚠️ {nombre_estacion} → No asignada (distancia mínima: {menor_distancia:.1f}m)")
    
    # Estadísticas
    total_asociadas = sum(len(estaciones) for estaciones in estaciones_por_linea.values())
    print(f"\n📊 RESUMEN DE ASIGNACIÓN:")
    print(f"   ✅ Por nombre oficial: {estaciones_asignadas_por_nombre}")
    print(f"   ✅ Por proximidad: {estaciones_asignadas_por_proximidad}")
    print(f"   ✅ Total asociadas: {total_asociadas}")
    print(f"   ❌ Sin línea asignada: {len(estaciones_sin_linea)}")
    
    for linea in sorted(estaciones_por_linea.keys()):
        estaciones = estaciones_por_linea[linea]
        print(f"   📍 {linea}: {len(estaciones)} estaciones")
    
    # Si quedan estaciones sin asignar, mantenerlas en unknown
    if estaciones_sin_linea:
        estaciones_por_linea['unknown'] = estaciones_sin_linea
    
    return estaciones_por_linea

def fetch_all_cercanias_data():
    """Descarga todos los datos de Cercanías desde ArcGIS"""
    
    print("🚆 DESCARGANDO DATOS COMPLETOS DE CERCANÍAS")
    print("=" * 60)
    
    # URL del servicio de Cercanías
    base_url = "https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/M5_Lineas/FeatureServer"
    
    # Mapeo de capas a tipos de datos y líneas
    layer_mapping = {
        # Estaciones
        2: ('estaciones', 'C-1', 'S1'), 6: ('estaciones', 'C-1', 'S2'),
        11: ('estaciones', 'C-2', 'S1'), 15: ('estaciones', 'C-2', 'S2'),
        20: ('estaciones', 'C-3', 'S1'), 24: ('estaciones', 'C-3', 'S2'),
        29: ('estaciones', 'C-4a', 'S1'), 32: ('estaciones', 'C-4b', 'S1'),
        36: ('estaciones', 'C-4a', 'S2'), 39: ('estaciones', 'C-4b', 'S2'),
        44: ('estaciones', 'C-5', 'S1'), 48: ('estaciones', 'C-5', 'S2'),
        53: ('estaciones', 'C-7a', 'S1'), 56: ('estaciones', 'C-7b', 'S1'),
        60: ('estaciones', 'C-7a', 'S2'), 63: ('estaciones', 'C-7b', 'S2'),
        68: ('estaciones', 'C-8', 'S1'), 72: ('estaciones', 'C-8', 'S2'),
        77: ('estaciones', 'C-9', 'S1'), 81: ('estaciones', 'C-9', 'S2'),
        86: ('estaciones', 'C-10', 'S1'), 89: ('estaciones', 'C-10', 'S2'),
        
        # Tramos  
        4: ('tramos', 'C-1', 'S1'), 8: ('tramos', 'C-1', 'S2'),
        13: ('tramos', 'C-2', 'S1'), 17: ('tramos', 'C-2', 'S2'),
        22: ('tramos', 'C-3', 'S1'), 26: ('tramos', 'C-3', 'S2'),
        31: ('tramos', 'C-4a', 'S1'), 34: ('tramos', 'C-4b', 'S1'),
        38: ('tramos', 'C-4a', 'S2'), 41: ('tramos', 'C-4b', 'S2'),
        46: ('tramos', 'C-5', 'S1'), 50: ('tramos', 'C-5', 'S2'),
        55: ('tramos', 'C-7a', 'S1'), 58: ('tramos', 'C-7b', 'S1'),
        62: ('tramos', 'C-7a', 'S2'), 65: ('tramos', 'C-7b', 'S2'),
        70: ('tramos', 'C-8', 'S1'), 74: ('tramos', 'C-8', 'S2'),
        79: ('tramos', 'C-9', 'S1'), 83: ('tramos', 'C-9', 'S2'),
        87: ('tramos', 'C-10', 'S1'), 91: ('tramos', 'C-10', 'S2'),
    }
    
    # Descargar todas las capas
    all_estaciones = []
    all_tramos = []
    
    print("\n📥 Descargando capas...")
    for layer_id, (data_type, line, direction) in layer_mapping.items():
        try:
            print(f"   Capa {layer_id}: {line} {direction} ({data_type})")
            features = fetch_arcgis_data(base_url, layer_id)
            
            if features and 'features' in features:
                for feature in features['features']:
                    # Convertir geometría ArcGIS a GeoJSON
                    geometry_type = features.get('geometryType', '')
                    geojson_geometry = convert_arcgis_geometry_to_geojson(
                        feature.get('geometry', {}), geometry_type
                    )
                    
                    # Crear feature GeoJSON estándar
                    geojson_feature = {
                        'type': 'Feature',
                        'properties': feature.get('attributes', {}),
                        'geometry': geojson_geometry
                    }
                    
                    # Añadir metadatos de línea
                    geojson_feature['properties']['_LINEA_INFERIDA'] = line
                    geojson_feature['properties']['_SENTIDO'] = direction
                    geojson_feature['properties']['_TIPO_DATOS'] = data_type
                    
                    if data_type == 'estaciones':
                        all_estaciones.append(geojson_feature)
                    elif data_type == 'tramos':
                        all_tramos.append(geojson_feature)
                        
        except Exception as e:
            print(f"   ❌ Error en capa {layer_id}: {e}")
            continue
    
    print(f"\n📊 Descarga completada:")
    print(f"   Estaciones: {len(all_estaciones)}")
    print(f"   Tramos: {len(all_tramos)}")
    
    # Organizar tramos por línea (estos SÍ tienen información de línea)
    tramos_by_line = {}
    for feature in all_tramos:
        props = feature.get('properties', {})
        
        # Intentar obtener línea de varios campos
        line_num = None
        for field in ['NUMEROLINEAUSUARIO', 'CODIGOGESTIONLINEA', '_LINEA_INFERIDA']:
            if field in props and props[field]:
                line_num = str(props[field]).strip()
                if line_num and line_num != '0':
                    break
        
        if not line_num or line_num == '0':
            line_num = 'unknown'
        
        if line_num not in tramos_by_line:
            tramos_by_line[line_num] = []
        tramos_by_line[line_num].append(feature)
    
    # Organizar estaciones inicialmente en 'unknown'
    estaciones_by_line = {'unknown': all_estaciones}
    
    # Asociar estaciones a líneas usando nombres oficiales y proximidad
    estaciones_by_line = associate_stations_to_lines_by_name_and_proximity(
        estaciones_by_line, tramos_by_line
    )
    
    # Generar resumen
    lineas_estaciones = list(estaciones_by_line.keys())
    lineas_tramos = list(tramos_by_line.keys())
    
    # Datos finales
    datos_completos = {
        'metadatos': {
            'fecha_generacion': datetime.now().isoformat(),
            'fuente': base_url,
            'total_estaciones': len(all_estaciones),
            'total_tramos': len(all_tramos),
            'lineas_con_estaciones': len([l for l in lineas_estaciones if l != 'unknown']),
            'lineas_con_tramos': len([l for l in lineas_tramos if l != 'unknown']),
            'descripcion': 'Datos completos de Cercanías Madrid con asociación por proximidad'
        },
        'lineas_estaciones': sorted([l for l in lineas_estaciones if l != 'unknown']),
        'lineas_tramos': sorted([l for l in lineas_tramos if l != 'unknown']),
        'estaciones': estaciones_by_line,
        'tramos': tramos_by_line
    }
    
    # Guardar archivo
    output_file = 'static/data/cercanias_completo.json'
    print(f"\n💾 Guardando en {output_file}...")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo generado exitosamente!")
    print(f"📁 Tamaño: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
    
    return datos_completos

def save_json_file(data, filename):
    """Guarda los datos en un archivo JSON"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Archivo guardado: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando archivo {filename}: {e}")
        return False

def main():
    """Función principal"""
    print("🚆 GENERADOR DE DATOS COMPLETOS DE CERCANÍAS")
    print("=" * 60)
    print("Este script descarga todos los datos de Cercanías desde ArcGIS")
    print("y genera un archivo JSON completo con todas las líneas.\n")
    
    # Descargar datos
    data = fetch_all_cercanias_data()
    
    if not data:
        print("❌ No se pudieron obtener datos de Cercanías")
        return False
    
    # Guardar archivo
    output_file = "static/data/cercanias_completo.json"
    success = save_json_file(data, output_file)
    
    if success:
        print(f"\n📊 RESUMEN FINAL")
        print("-" * 40)
        print(f"Total estaciones: {data['metadatos']['total_estaciones']}")
        print(f"Total tramos: {data['metadatos']['total_tramos']}")
        print(f"Líneas encontradas: {', '.join(data['lineas_estaciones'])}")
        print(f"Archivo generado: {output_file}")
        
        # Mostrar desglose por línea
        print(f"\n📋 DESGLOSE POR LÍNEA:")
        for linea in sorted(data['lineas_estaciones']):
            estaciones = len(data['estaciones'].get(linea, []))
            tramos = len(data['tramos'].get(linea, []))
            print(f"  {linea}: {estaciones} estaciones, {tramos} tramos")
        
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ¡Datos de Cercanías generados exitosamente!")
    else:
        print("\n❌ Error generando datos de Cercanías") 