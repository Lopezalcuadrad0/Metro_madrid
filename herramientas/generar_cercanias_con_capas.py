#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERADOR DE CERCANÍAS CON CAPAS POR LÍNEA
==========================================

Genera un archivo de Cercanías con capas separadas por línea usando los colores oficiales.
"""

import json
import os

def generar_cercanias_con_capas():
    """Genera el archivo de Cercanías con capas por línea"""
    
    # Cargar datos de Cercanías
    with open('static/data/cercanias_completo.json', 'r', encoding='utf-8') as f:
        cercanias_data = json.load(f)
    
    # Cargar colores oficiales
    with open('static/data/line_colors.json', 'r', encoding='utf-8') as f:
        colores_data = json.load(f)
    
    # Configuración de colores por línea desde line_colors.json
    colores_lineas = colores_data.get('cercanias', {})
    
    # Agrupar estaciones por línea
    estaciones_por_linea = {}
    for estacion in cercanias_data.get('estaciones', []):
        linea = estacion.get('linea', '')
        if linea:
            if linea not in estaciones_por_linea:
                estaciones_por_linea[linea] = []
            estaciones_por_linea[linea].append(estacion)
    
    # Crear capas por línea
    layers = {}
    for linea, estaciones in estaciones_por_linea.items():
        layer_id = f'cercanias_linea_{linea.replace("-", "_")}'
        layer_name = f'Cercanías {linea}'
        
        # Obtener color de la línea
        color = colores_lineas.get(linea, '#E20714')
        
        layers[layer_id] = {
            'id': layer_id,
            'name': layer_name,
            'type': 'cercanias',
            'line_type': linea,
            'visible': False,  # Por defecto no visible
            'stations': [est.get('codigo', '') for est in estaciones if est.get('codigo')],
            'color': color,
            'icon': f'/static/logos/Cercanias/Cercanías_{linea}.svg.png'
        }
    
    # Crear estructura final
    cercanias_con_capas = {
        'stations': cercanias_data.get('estaciones', []),
        'lines': [],  # Las rutas se pueden agregar después
        'layers': layers,
        'colors': colores_lineas,
        'metadata': {
            'name': 'Cercanías Madrid',
            'version': '2.0',
            'total_stations': len(cercanias_data.get('estaciones', [])),
            'total_lines': len(estaciones_por_linea),
            'description': 'Datos completos de Cercanías Madrid con estaciones y capas por línea'
        }
    }
    
    # Guardar archivo final
    output_path = 'static/data/cercanias_con_capas.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cercanias_con_capas, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo generado: {output_path}")
    print(f"📊 Estadísticas:")
    print(f"   - Estaciones: {len(cercanias_data.get('estaciones', []))}")
    print(f"   - Líneas: {len(estaciones_por_linea)}")
    print(f"   - Colores: {len(colores_lineas)}")
    print(f"   - Líneas encontradas: {list(estaciones_por_linea.keys())}")
    
    return cercanias_con_capas

if __name__ == '__main__':
    generar_cercanias_con_capas() 