#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la ruta del Metro Ligero
"""

import requests
import sys

def test_metro_ligero_routes():
    """Prueba las rutas del Metro Ligero"""
    base_url = "http://localhost:5001"  # Puerto 5001 para la app del Metro Ligero
    
    routes_to_test = [
        "/",
        "/mapa-metro-ligero",
        "/metro-ligero", 
        "/ml"
    ]
    
    api_routes_to_test = [
        "/api/lines/global-status",
        "/api/metro-ligero/lines",
        "/api/metro-ligero/stations"
    ]
    
    print("🔍 Probando rutas del Metro Ligero en puerto 5001...")
    print("=" * 50)
    
    # Probar rutas principales
    print("📋 RUTAS PRINCIPALES:")
    for route in routes_to_test:
        try:
            print(f"📡 Probando: {route}")
            response = requests.get(f"{base_url}{route}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {route} - OK (Status: {response.status_code})")
                if "Metro Ligero Madrid" in response.text:
                    print("   ✅ Contenido correcto detectado")
                else:
                    print("   ⚠️ Contenido no reconocido")
            else:
                print(f"❌ {route} - Error (Status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {route} - Error de conexión: {e}")
        print("-" * 30)
    
    # Probar endpoints de API
    print("\n🔌 ENDPOINTS DE API:")
    for route in api_routes_to_test:
        try:
            print(f"📡 Probando: {route}")
            response = requests.get(f"{base_url}{route}", timeout=15)
            
            if response.status_code == 200:
                print(f"✅ {route} - OK (Status: {response.status_code})")
                try:
                    data = response.json()
                    if data.get('success'):
                        if 'lines' in data:
                            print(f"   📊 Líneas encontradas: {len(data['lines'])}")
                        if 'stations' in data:
                            print(f"   🚉 Estaciones encontradas: {len(data['stations'])}")
                        if 'total' in data:
                            print(f"   📈 Total: {data['total']}")
                    else:
                        print(f"   ⚠️ API devolvió error: {data.get('error', 'Desconocido')}")
                except:
                    print("   ⚠️ Respuesta no es JSON válido")
            else:
                print(f"❌ {route} - Error (Status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {route} - Error de conexión: {e}")
        print("-" * 30)
    
    print("🎯 Pruebas completadas!")

if __name__ == "__main__":
    test_metro_ligero_routes() 