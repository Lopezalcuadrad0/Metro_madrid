#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del mapa de metro ligero
"""

import requests
import json
import time

def test_endpoint(url, name):
    """Prueba un endpoint específico"""
    try:
        print(f"🔄 Probando {name}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'success' in data and data['success']:
                # Manejo especial para el endpoint de estado global
                if 'global-status' in url:
                    if 'lines' in data:
                        line_count = len(data['lines'])
                        print(f"✅ {name}: {line_count} líneas de estado cargadas correctamente")
                        return True
                    else:
                        print(f"⚠️ {name}: Respuesta exitosa pero sin datos de líneas")
                        return False
                # Para endpoints GeoJSON
                elif 'data' in data and 'features' in data['data']:
                    feature_count = len(data['data']['features'])
                    print(f"✅ {name}: {feature_count} elementos cargados correctamente")
                    return True
                else:
                    print(f"⚠️ {name}: Respuesta exitosa pero sin datos GeoJSON")
                    return False
            else:
                print(f"❌ {name}: Error en la respuesta - {data.get('error', 'Error desconocido')}")
                return False
        else:
            print(f"❌ {name}: Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {name}: Error de conexión - {str(e)}")
        return False

def main():
    """Función principal de prueba"""
    print("🚇 Iniciando pruebas del mapa de metro ligero...")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Lista de endpoints a probar
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD"),
        ("/api/lines/global-status", "Estado Global")
    ]
    
    results = []
    
    for endpoint, name in endpoints:
        success = test_endpoint(f"{base_url}{endpoint}", name)
        results.append((name, success))
        time.sleep(0.5)  # Pequeña pausa entre requests
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 50)
    
    successful = 0
    for name, success in results:
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        print(f"{status} - {name}")
        if success:
            successful += 1
    
    print(f"\n🎯 Resultado: {successful}/{len(results)} endpoints funcionando correctamente")
    
    if successful == len(results):
        print("🎉 ¡TODOS LOS ENDPOINTS ESTÁN FUNCIONANDO PERFECTAMENTE!")
        print("🌐 Puedes acceder al mapa en: http://localhost:5001/mapa-metro-ligero")
    else:
        print("⚠️ Algunos endpoints tienen problemas. Revisa los errores arriba.")
    
    print("\n🔧 Para ver el mapa completo, abre:")
    print("   http://localhost:5001/mapa-metro-ligero")
    print("   http://localhost:5001/")
    print("   http://localhost:5001/metro-ligero")

if __name__ == "__main__":
    main() 