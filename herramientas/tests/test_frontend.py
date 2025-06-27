#!/usr/bin/env python3
"""
Script para simular las peticiones del frontend
"""

import requests
import json

def test_frontend_request(endpoint, nombre):
    """Simula una petición del frontend"""
    try:
        print(f"\n🌐 Simulando petición frontend para {nombre}...")
        
        # Simular petición como lo haría el navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(f"http://localhost:5001{endpoint}", headers=headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Respuesta válida")
                print(f"Success: {data.get('success', 'N/A')}")
                
                if data.get('success') and 'data' in data:
                    features = data['data'].get('features', [])
                    print(f"Features: {len(features)}")
                    return True
                else:
                    print(f"❌ Formato incorrecto: {data}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error JSON: {e}")
                print(f"Respuesta: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🌐 PRUEBA DE PETICIONES FRONTEND")
    print("=" * 50)
    
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD")
    ]
    
    exitosos = 0
    for endpoint, nombre in endpoints:
        if test_frontend_request(endpoint, nombre):
            exitosos += 1
        print("-" * 40)
    
    print(f"\n🎯 Resultado: {exitosos}/{len(endpoints)} peticiones exitosas")
    
    if exitosos == len(endpoints):
        print("✅ Todas las peticiones funcionan correctamente")
        print("💡 El problema puede estar en el JavaScript del frontend")
    else:
        print("❌ Algunas peticiones fallan")
        print("💡 Revisar la aplicación Flask")

if __name__ == "__main__":
    main() 