#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rutas de transporte público para app.py
Migradas desde app_metro_ligero.py
"""

from flask import render_template, jsonify
from transport_functions import *
import os
import json
import requests

# Funciones para añadir a app.py

def add_transport_routes(app):
    """Añade las rutas de transporte público a la aplicación Flask"""
    
    # ============================================================================
    # APIS DE TRANSPORTE PÚBLICO
    # ============================================================================

    @app.route('/api/transport/metro_ligero')
    def transport_metro_ligero():
        """Devuelve todas las líneas (tramos) y estaciones del Metro Ligero en un solo GeoJSON"""
        try:
            base_url = 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/Lineas_MetroLigero/FeatureServer'
            # IDs de capas de tramos (líneas) - AÑADIDAS CAPAS DE LÍNEA 3
            tramo_layers = [4, 8, 13, 17, 22, 26]  # Añadidas L3_S1_TRAMO (22) y L3_S2_TRAMO (26)
            # IDs de capas de estaciones - AÑADIDAS CAPAS DE LÍNEA 3
            estacion_layers = [2, 6, 11, 15, 20, 24]  # Añadidas L3_S1_ESTACION (20) y L3_S2_ESTACION (24)

            # Obtener features de tramos
            tramo_features = fetch_arcgis_data_multiple_layers(base_url, tramo_layers)
            # Obtener features de estaciones
            estacion_features = fetch_arcgis_data_multiple_layers(base_url, estacion_layers)

            # Añadir tipo de capa a las propiedades
            for f in tramo_features:
                f['properties']['layer_type'] = 'tramo'
            for f in estacion_features:
                f['properties']['layer_type'] = 'estacion'

            # Unir todo en un solo FeatureCollection
            all_features = tramo_features + estacion_features
            geojson = {
                'type': 'FeatureCollection',
                'features': all_features,
                'properties': {
                    'layer_type': 'metro_ligero',
                    'color': '#0099CC',
                    'total_features': len(all_features)
                }
            }
            
            # Devolver en el formato que espera el frontend
            return jsonify({
                'success': True,
                'data': geojson
            })
        except Exception as e:
            print(f"Error en transport_metro_ligero: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/transport/<layer_type>')
    def transport_layer(layer_type):
        """Endpoint genérico para obtener datos de cualquier capa de transporte"""
        try:
            # Configuración de servicios por tipo
            services_config = {
                'metro_ligero': {
                    'url': 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/Lineas_MetroLigero/FeatureServer',
                    'layer_ids': [4, 8, 13, 17, 22, 26],  # TODAS las capas de tramos (L1, L2, L3)
                    'estacion_layer_ids': [2, 6, 11, 15, 20, 24],  # TODAS las capas de estaciones (L1, L2, L3)
                    'color': '#0099CC',
                    'name': 'Metro Ligero',
                    'use_multiple_layers': True
                },
                'metro': {
                    'url': 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/Lineas_Metro/FeatureServer',
                    'layer_ids': [2, 6, 11, 15, 20, 24, 29, 33, 38, 42, 47, 51, 56, 59, 63, 66, 71, 75, 80, 83, 87, 90, 95, 98, 102, 105, 110],  # TODAS las capas de estaciones
                    'tramo_layer_ids': [4, 8, 13, 17, 22, 26, 31, 35, 40, 44, 49, 53, 58, 61, 65, 68, 73, 77, 82, 85, 89, 92, 97, 100, 104, 107, 112, 134],  # TODAS las capas de tramos
                    'color': '#FF6600',
                    'name': 'Metro de Madrid',
                    'use_multiple_layers': True
                },
                'cercanias': {
                    'url': 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/M5_Lineas/FeatureServer',
                    'layer_ids': [2, 6, 10, 14],  # Reducido de 8 a 4 capas para optimizar
                    'tramo_layer_ids': [4, 8, 12, 16],  # Reducido de 8 a 4 capas para optimizar
                    'color': '#99CC00',
                    'name': 'Cercanías Renfe',
                    'use_multiple_layers': True
                }
            }

            if layer_type not in services_config:
                return jsonify({'error': f'Tipo de capa no soportado: {layer_type}'}), 400

            config = services_config[layer_type]
            
            if config['use_multiple_layers']:
                # Obtener datos de múltiples capas
                features = fetch_arcgis_data_multiple_layers(config['url'], config['layer_ids'])
                if 'tramo_layer_ids' in config:
                    tramo_features = fetch_arcgis_data_multiple_layers(config['url'], config['tramo_layer_ids'])
                    features.extend(tramo_features)
            else:
                # Obtener datos de una sola capa
                data = fetch_arcgis_data(config['url'], config['layer_id'])
                features = data.get('features', [])

            # Crear GeoJSON
            geojson = {
                'type': 'FeatureCollection',
                'features': features,
                'properties': {
                    'layer_type': layer_type,
                    'color': config['color'],
                    'name': config['name'],
                    'total_features': len(features)
                }
            }

            return jsonify({
                'success': True,
                'data': geojson
            })

        except Exception as e:
            print(f"Error en transport_layer ({layer_type}): {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/transport/metro_optimized')
    def transport_metro_optimized():
        """Devuelve los datos del metro en formato optimizado para el frontend"""
        try:
            # Cargar datos desde el archivo JSON
            json_path = 'static/data/metro_madrid_completo.json'
            if not os.path.exists(json_path):
                return jsonify({'error': 'Datos no disponibles'}), 404
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            print(f"Error en transport_metro_optimized: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/transport/local/<transport_type>')
    def transport_local(transport_type):
        """Devuelve datos locales de transporte público"""
        try:
            # Mapeo de tipos a archivos JSON
            json_files = {
                'metro': 'metro_madrid_completo.json',
                'metro_ligero': 'metro_ligero_completo.json',
                'cercanias': 'cercanias_completo.json',
                'resumen': 'transporte_resumen.json'
            }
            
            if transport_type not in json_files:
                return jsonify({'error': f'Tipo de transporte no soportado: {transport_type}'}), 400
            
            json_path = f'static/data/{json_files[transport_type]}'
            if not os.path.exists(json_path):
                return jsonify({'error': 'Datos no disponibles'}), 404
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            print(f"Error en transport_local ({transport_type}): {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/transport/bicimad')
    def transport_bicimad():
        """Devuelve las estaciones de BiciMAD desde la API oficial de EMT Madrid"""
        try:
            # URL oficial de BiciMAD de EMT Madrid
            url = "https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.json"
            
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return jsonify({
                    "success": False,
                    "error": f"Error al obtener datos: Status {response.status_code}"
                }), 500
            
            data = response.json()
            
            if not data or 'features' not in data:
                return jsonify({
                    "success": False,
                    "error": "Formato de datos inválido"
                }), 500
            
            # Procesar los datos
            stations = []
            for feature in data.get('features', []):
                if feature.get('geometry') and feature.get('properties'):
                    coords = feature['geometry']['coordinates']
                    props = feature['properties']
                    
                    # Determinar estado y color basado en los datos
                    activate = props.get('Activate', 1)
                    dock_bikes = props.get('DockBikes', 0)
                    free_bases = props.get('FreeBases', 0)
                    total_bases = props.get('TotalBases', 0)
                    
                    # Determinar estado y color
                    if activate == 0:
                        fill_color = '#FF0000'  # Rojo - Desactivada
                        status_text = 'Desactivada'
                        status = 'desactivada'
                    elif free_bases == 0:
                        fill_color = '#8B008B'  # Púrpura - Sin anclajes
                        status_text = 'Sin anclajes disponibles'
                        status = 'sin_anclajes'
                    elif dock_bikes == 0:
                        fill_color = '#FF0000'  # Rojo - Sin bicicletas
                        status_text = 'Sin bicicletas disponibles'
                        status = 'sin_bicicletas'
                    else:
                        fill_color = '#00A859'  # Verde - Operativa
                        status_text = 'Operativa'
                        status = 'operativa'
                    
                    station = {
                        'lat': coords[1],
                        'lon': coords[0],
                        'name': props.get('Name', ''),
                        'number': props.get('number', ''),
                        'id_station': props.get('IdStation', ''),
                        'address': props.get('Address', ''),
                        'dock_bikes': dock_bikes,
                        'free_bases': free_bases,
                        'total_bases': total_bases,
                        'activate': activate,
                        'light': props.get('Ligth', 0),
                        'status': status,
                        'status_text': status_text,
                        'fill_color': fill_color,
                        'no_available': props.get('NoAvailabl', 0)
                    }
                    stations.append(station)
            
            return jsonify({
                "success": True,
                "data": {'stations': stations}
            })
            
        except Exception as e:
            print(f"Error en transport_bicimad: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return "✅ Funcionalidades de transporte público migradas correctamente" 