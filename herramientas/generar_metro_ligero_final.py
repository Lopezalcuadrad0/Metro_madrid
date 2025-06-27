#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERADOR DE METRO LIGERO FINAL
===============================

Combina las estaciones de metro_ligero_completo.json con las rutas de 
metro_ligero_rutas_gtfs.json para crear un archivo final con todo integrado.
"""

import json
import os

def generar_metro_ligero_final():
    """Genera el archivo final de Metro Ligero con estaciones y rutas"""
    
    # Cargar estaciones
    with open('static/data/metro_ligero_completo.json', 'r', encoding='utf-8') as f:
        estaciones_data = json.load(f)
    
    # Cargar rutas
    with open('static/data/metro_ligero_rutas_gtfs.json', 'r', encoding='utf-8') as f:
        rutas_data = json.load(f)
    
    # Cargar colores oficiales
    with open('static/data/line_colors.json', 'r', encoding='utf-8') as f:
        colores_data = json.load(f)
    
    # Configuración de colores por línea desde line_colors.json
    colores_lineas = colores_data.get('metro_ligero', {})
    
    # Agrupar estaciones por línea
    estaciones_por_linea = {"ML1": [], "ML2": [], "ML3": []}
    for est in estaciones_data['stations']:
        for linea in est.get('lines', []):
            if linea in estaciones_por_linea:
                estaciones_por_linea[linea].append(est)
    
    # Procesar rutas y asignar colores
    lines = []
    for feature in rutas_data['features']:
        if feature['geometry']['type'] == 'LineString':
            props = feature.get('properties', {})
            linea_id = props.get('linea', 'ML1')  # ML1, ML2, ML3
            # Filtrar solo ML1, ML2 y ML3
            if linea_id in ['ML1', 'ML2', 'ML3']:
                linea_numero = linea_id[-1] if linea_id.endswith(('1', '2', '3')) else '1'
                color = colores_lineas.get(linea_numero, '#70C5E8')
                coordinates = [[coord[1], coord[0]] for coord in feature['geometry']['coordinates']]
                line_data = {
                    'id': f'linea_{linea_id}',
                    'name': f'Metro Ligero {linea_numero}',
                    'line': linea_id,
                    'coordinates': coordinates,
                    'color': color,
                    'type': 'metro_ligero',
                    'active': True
                }
                lines.append(line_data)
    
    # Crear capas por línea
    layers = {}
    for linea_id, estaciones in estaciones_por_linea.items():
        linea_numero = linea_id[-1]
        color = colores_lineas.get(linea_numero, '#70C5E8')
        layers[f'metro_ligero_{linea_id.lower()}'] = {
            'id': f'metro_ligero_{linea_id.lower()}',
            'name': f'Metro Ligero {linea_numero}',
            'type': 'metro_ligero',
            'line_type': linea_id,
            'visible': False,
            'stations': [est['id'] for est in estaciones],
            'color': color,
            'icon': f'/static/logos/lineas/ml{linea_numero}.svg'
        }
    
    # Estructura final
    metro_ligero_final = {
        'stations': estaciones_data['stations'],
        'lines': lines,
        'layers': layers,
        'colors': colores_lineas,
        'metadata': {
            'name': 'Metro Ligero de Madrid',
            'version': '2.1',
            'total_stations': len(estaciones_data['stations']),
            'total_lines': len(lines),
            'description': 'Datos completos del Metro Ligero de Madrid con estaciones, rutas, colores y capas'
        }
    }
    
    # Guardar archivo final
    output_path = 'static/data/metro_ligero_final.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metro_ligero_final, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo generado: {output_path}")
    print(f"📊 Estadísticas:")
    print(f"   - Estaciones: {len(estaciones_data['stations'])}")
    print(f"   - Líneas: {len(lines)}")
    print(f"   - Colores: {len(colores_lineas)}")
    print(f"   - Colores usados: {colores_lineas}")
    
    return metro_ligero_final

if __name__ == '__main__':
    generar_metro_ligero_final() 