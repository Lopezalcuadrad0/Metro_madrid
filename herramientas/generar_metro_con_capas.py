#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERADOR DE METRO CON CAPAS POR LÍNEA
======================================

Genera un archivo de Metro con capas separadas por línea usando los colores oficiales.
"""

import json
import os

def generar_metro_con_capas():
    """Genera el archivo de Metro con capas por línea"""
    
    # Cargar datos de Metro
    with open('static/data/metro_madrid_completo.json', 'r', encoding='utf-8') as f:
        metro_data = json.load(f)
    
    # Cargar colores oficiales
    with open('static/data/line_colors.json', 'r', encoding='utf-8') as f:
        colores_data = json.load(f)
    
    # Configuración de colores por línea desde line_colors.json
    colores_lineas = colores_data.get('metro', {})
    
    # Procesar estaciones y extraer líneas correctamente
    stations = []
    estaciones_por_linea = {}
    
    for estacion in metro_data.get('stations', []):
        # Extraer línea del código de empresa
        codigo_empresa = estacion.get('codigo_empresa', '')
        linea = 'unknown'
        
        if codigo_empresa and len(codigo_empresa) >= 2:
            # Los primeros 2 dígitos son la línea
            linea_codigo = codigo_empresa[:2]
            if linea_codigo.startswith('0'):
                linea = linea_codigo[1]  # Quitar el 0 inicial
            else:
                linea = linea_codigo
        
        # Crear estación con línea corregida
        station = {
            'id': estacion.get('id', ''),
            'name': estacion.get('name', ''),
            'lat': estacion.get('lat', 0),
            'lon': estacion.get('lon', 0),
            'lines': [linea],
            'codigo_empresa': codigo_empresa,
            'id_estacion': estacion.get('id_estacion', ''),
            'id_modal': estacion.get('id_modal', ''),
            'tipo': 'metro'
        }
        
        stations.append(station)
        
        # Agrupar por línea
        if linea not in estaciones_por_linea:
            estaciones_por_linea[linea] = []
        estaciones_por_linea[linea].append(station)
    
    # Cargar rutas desde metro_routes.json
    lines = []
    try:
        with open('static/data/metro_routes.json', 'r', encoding='utf-8') as f:
            rutas_data = json.load(f)
            rutas_lines = rutas_data.get('lines', [])
            
            # Procesar cada ruta
            for line_data in rutas_lines:
                linea_id = line_data.get('line', '')
                
                # Solo incluir líneas válidas (1-12, R)
                if linea_id and linea_id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                    paths = line_data.get('paths', [])
                    color = colores_lineas.get(linea_id, '#0055A4')
                    
                    if paths:
                        # Tomar el primer path (ruta principal)
                        coordinates = paths[0] if paths else []
                        if coordinates:
                            line_info = {
                                'line': linea_id,
                                'coordinates': coordinates,
                                'color': color,
                                'name': f'Línea {linea_id}',
                                'type': 'metro'
                            }
                            lines.append(line_info)
                            print(f"✅ Ruta de Línea {linea_id} cargada con {len(coordinates)} puntos")
    except Exception as e:
        print(f"❌ Error cargando rutas: {e}")
        print("No se encontraron rutas de Metro")
    
    # Crear capas por línea
    layers = {}
    for linea, estaciones in estaciones_por_linea.items():
        if linea == 'unknown':
            continue  # Saltar líneas desconocidas
            
        layer_id = f'metro_linea_{linea}'
        layer_name = f'Línea {linea}'
        
        # Obtener color de la línea
        color = colores_lineas.get(linea, '#0099CC')
        
        layers[layer_id] = {
            'id': layer_id,
            'name': layer_name,
            'type': 'metro',
            'line_type': linea,
            'visible': False,  # Por defecto no visible
            'stations': [est['id'] for est in estaciones if est.get('id')],
            'color': color,
            'icon': f'/static/logos/lineas/linea-{linea}.svg'
        }
    
    # Crear estructura final
    metro_con_capas = {
        'stations': stations,
        'lines': lines,
        'layers': layers,
        'colors': colores_lineas,
        'metadata': {
            'name': 'Metro de Madrid',
            'version': '2.0',
            'total_stations': len(stations),
            'total_lines': len([l for l in estaciones_por_linea.keys() if l != 'unknown']),
            'total_routes': len(lines),
            'description': 'Datos completos del Metro de Madrid con estaciones, rutas y capas por línea'
        }
    }
    
    # Guardar archivo final
    output_path = 'static/data/metro_con_capas.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metro_con_capas, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo generado: {output_path}")
    print(f"📊 Estadísticas:")
    print(f"   - Estaciones: {len(stations)}")
    print(f"   - Líneas válidas: {len([l for l in estaciones_por_linea.keys() if l != 'unknown'])}")
    print(f"   - Rutas cargadas: {len(lines)}")
    print(f"   - Líneas encontradas: {sorted([l for l in estaciones_por_linea.keys() if l != 'unknown'])}")
    print(f"   - Estaciones con línea 'unknown': {len(estaciones_por_linea.get('unknown', []))}")
    print(f"   - Colores: {len(colores_lineas)}")
    
    return metro_con_capas

if __name__ == '__main__':
    generar_metro_con_capas() 