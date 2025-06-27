#!/usr/bin/env python3
"""
Script de diagnóstico para identificar errores en las capas
"""

import requests
import json

def diagnosticar_endpoint(endpoint, nombre):
    """Diagnostica un endpoint específico"""
    try:
        print(f"\n🔍 Diagnosticando {nombre}...")
        print(f"URL: http://localhost:5001{endpoint}")
        
        response = requests.get(f"http://localhost:5001{endpoint}", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Respuesta JSON válida")
                
                if 'success' in data:
                    print(f"Success: {data['success']}")
                    if not data['success']:
                        print(f"❌ Error en respuesta: {data.get('error', 'Error desconocido')}")
                        return False
                    
                    if 'data' in data:
                        features = data['data'].get('features', [])
                        print(f"Features encontradas: {len(features)}")
                        return True
                    else:
                        print("❌ No hay campo 'data' en la respuesta")
                        return False
                else:
                    print("❌ No hay campo 'success' en la respuesta")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error decodificando JSON: {e}")
                print(f"Respuesta: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - la solicitud tardó demasiado")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - no se puede conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚨 DIAGNÓSTICO DE ERRORES EN CAPAS")
    print("=" * 50)
    
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD")
    ]
    
    resultados = []
    
    for endpoint, nombre in endpoints:
        resultado = diagnosticar_endpoint(endpoint, nombre)
        resultados.append((nombre, resultado))
        print("-" * 40)
    
    print("\n📊 RESUMEN DE DIAGNÓSTICO")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        status = "✅ FUNCIONA" if resultado else "❌ ERROR"
        print(f"{status} - {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 Resultado: {exitosos}/{len(resultados)} endpoints funcionando")
    
    if exitosos == len(resultados):
        print("🎉 ¡Todos los endpoints funcionan correctamente!")
    else:
        print("⚠️ Algunos endpoints tienen problemas")
        print("\n💡 Posibles soluciones:")
        print("1. Reiniciar la aplicación: python app_metro_ligero.py")
        print("2. Verificar la conexión a internet")
        print("3. Comprobar que los servicios ArcGIS estén disponibles")

if __name__ == "__main__":
    main() 