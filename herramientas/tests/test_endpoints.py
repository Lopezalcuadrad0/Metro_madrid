#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar los endpoints de la API de transporte
"""

import requests
import json
import time

def test_endpoint(url, name):
    """Prueba un endpoint específico"""
    try:
        print(f"🔍 Probando {name}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total = data.get('total', 0)
                print(f"✅ {name}: OK - {total} elementos")
                return True
            else:
                print(f"❌ {name}: Error - {data.get('error', 'Error desconocido')}")
                return False
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ {name}: Timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Error de red - {e}")
        return False
    except Exception as e:
        print(f"❌ {name}: Error inesperado - {e}")
        return False

def main():
    """Función principal de pruebas"""
    base_url = "http://localhost:5001"
    
    endpoints = [
        ("/api/lines/global-status", "Estado Global"),
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD"),
    ]
    
    print("🚇 Iniciando pruebas de endpoints...")
    print("=" * 50)
    
    results = []
    for endpoint, name in endpoints:
        url = base_url + endpoint
        success = test_endpoint(url, name)
        results.append((name, success))
        time.sleep(1)  # Pausa entre requests
    
    print("=" * 50)
    print("📊 Resumen de resultados:")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ OK" if success else "❌ FALLÓ"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Resultado: {successful}/{total} endpoints funcionando")
    
    if successful == total:
        print("🎉 ¡Todos los endpoints funcionan correctamente!")
    else:
        print("⚠️ Algunos endpoints tienen problemas")

if __name__ == "__main__":
    main() 