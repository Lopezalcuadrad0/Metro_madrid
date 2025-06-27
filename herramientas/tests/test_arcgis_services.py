#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar servicios ArcGIS directamente
"""

import requests
import json

def test_arcgis_service(url, name):
    """Prueba un servicio ArcGIS específico"""
    try:
        print(f"🔍 Probando servicio ArcGIS: {name}")
        print(f"   URL: {url}")
        
        # Primero probar el endpoint de información del servicio
        response = requests.get(url, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Servicio accesible")
                print(f"   Nombre: {data.get('name', 'N/A')}")
                print(f"   Descripción: {data.get('description', 'N/A')}")
                print(f"   Capas disponibles: {len(data.get('layers', []))}")
                
                # Mostrar información de las primeras 5 capas
                for i, layer in enumerate(data.get('layers', [])[:5]):
                    print(f"   Capa {layer.get('id', 'N/A')}: {layer.get('name', 'N/A')} ({layer.get('geometryType', 'N/A')})")
                
                if len(data.get('layers', [])) > 5:
                    print(f"   ... y {len(data.get('layers', [])) - 5} capas más")
                
                # Probar la primera capa con datos
                for layer in data.get('layers', []):
                    if layer.get('geometryType') in ['esriGeometryPoint', 'esriGeometryPolyline']:
                        layer_id = layer.get('id')
                        test_url = f"{url.replace('?f=json', '')}/{layer_id}/query?where=1%3D1&outFields=*&returnGeometry=true&f=json"
                        print(f"   Probando capa {layer_id}: {test_url}")
                        
                        test_response = requests.get(test_url, timeout=10)
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            features = test_data.get('features', [])
                            print(f"   ✅ Capa {layer_id}: {len(features)} features")
                            break
                        else:
                            print(f"   ❌ Capa {layer_id}: Error {test_response.status_code}")
                
                return True
                
            except json.JSONDecodeError:
                print(f"❌ Error: Respuesta no es JSON válido")
                print(f"   Primeros 200 caracteres: {response.text[:200]}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_arcgis_query(url, name):
    """Prueba una consulta específica al servicio"""
    try:
        print(f"🔍 Probando consulta: {name}")
        
        query_url = f"{url}/0/query"
        params = {
            'where': '1=1',
            'outFields': '*',
            'outSR': '4326',
            'f': 'json',
            'returnGeometry': 'true'
        }
        
        response = requests.get(query_url, params=params, timeout=15)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'error' in data:
                    print(f"❌ Error en respuesta: {data['error']}")
                    return False
                elif 'features' in data:
                    print(f"✅ Consulta exitosa: {len(data['features'])} features")
                    return True
                else:
                    print(f"⚠️ Respuesta inesperada: {list(data.keys())}")
                    return False
            except json.JSONDecodeError:
                print(f"⚠️ Respuesta no es JSON válido")
                print(f"   Primeros 200 caracteres: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🚇 Probando servicios ArcGIS de transporte de Madrid\n")
    
    # URLs correctas proporcionadas por el usuario
    services = [
        {
            'url': 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/Lineas_Metro/FeatureServer?f=json',
            'name': 'Metro de Madrid'
        },
        {
            'url': 'https://services5.arcgis.com/UxADft6QPcvFyDU1/ArcGIS/rest/services/M5_Lineas/FeatureServer?f=json',
            'name': 'Cercanías Renfe'
        }
    ]
    
    for service in services:
        test_arcgis_service(service['url'], service['name'])
        print()

if __name__ == "__main__":
    main() 