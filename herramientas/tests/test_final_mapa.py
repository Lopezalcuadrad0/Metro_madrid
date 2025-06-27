#!/usr/bin/env python3
"""
Script de prueba final para verificar que el mapa funciona correctamente
"""

import requests
import json

def test_popup_data(endpoint, nombre):
    """Prueba que los datos para popups estén disponibles"""
    try:
        print(f"\n🔍 Probando datos de popup para {nombre}...")
        
        response = requests.get(f"http://localhost:5001{endpoint}", timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'data' in data:
                features = data['data'].get('features', [])
                if features:
                    # Tomar el primer feature
                    first_feature = features[0]
                    properties = first_feature.get('properties', {})
                    
                    print(f"📊 Total de features: {len(features)}")
                    
                    # Verificar campos según el tipo
                    if 'bicimad' in endpoint:
                        nombre_campo = properties.get('Name') or properties.get('name')
                        direccion_campo = properties.get('Address') or properties.get('address')
                        print(f"✅ BiciMAD - Nombre: {nombre_campo}")
                        print(f"✅ BiciMAD - Dirección: {direccion_campo}")
                        print(f"✅ BiciMAD - Bicis disponibles: {properties.get('DockBikes')}")
                        print(f"✅ BiciMAD - Anclajes libres: {properties.get('FreeBases')}")
                        
                    elif 'metro_ligero' in endpoint:
                        nombre_campo = properties.get('DENOMINACION') or properties.get('denominacion')
                        direccion_campo = properties.get('DIRECCION') or properties.get('direccion')
                        print(f"✅ Metro Ligero - Nombre: {nombre_campo}")
                        print(f"✅ Metro Ligero - Dirección: {direccion_campo}")
                        print(f"✅ Metro Ligero - Línea: {properties.get('NUMEROLINEAUSUARIO')}")
                        
                    elif 'metro' in endpoint:
                        nombre_campo = properties.get('DENOMINACION') or properties.get('denominacion')
                        direccion_campo = properties.get('DIRECCION') or properties.get('direccion')
                        print(f"✅ Metro - Nombre: {nombre_campo}")
                        print(f"✅ Metro - Dirección: {direccion_campo}")
                        print(f"✅ Metro - Línea: {properties.get('NUMEROLINEAUSUARIO')}")
                        
                    else:
                        # Otros transportes
                        nombre_campo = properties.get('Name') or properties.get('NOMBRE') or properties.get('DENOMINACION')
                        direccion_campo = properties.get('Address') or properties.get('DIRECCION')
                        print(f"✅ {nombre} - Nombre: {nombre_campo}")
                        print(f"✅ {nombre} - Dirección: {direccion_campo}")
                    
                    return True
                else:
                    print("❌ No hay features en los datos")
                    return False
            else:
                print("❌ Respuesta no exitosa")
                return False
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🎯 PRUEBA FINAL DEL MAPA CON POPUPS")
    print("=" * 60)
    
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD")
    ]
    
    successful = 0
    for endpoint, nombre in endpoints:
        if test_popup_data(endpoint, nombre):
            successful += 1
        print("-" * 40)
    
    print(f"\n🎯 RESULTADO: {successful}/{len(endpoints)} capas con datos de popup correctos")
    
    if successful == len(endpoints):
        print("🎉 ¡TODAS LAS CAPAS TIENEN DATOS CORRECTOS PARA POPUPS!")
        print("🌐 Abre http://localhost:5001/mapa-metro-ligero y haz clic en los puntos para ver los popups")
    else:
        print("⚠️ Algunas capas pueden no mostrar información completa en los popups")
    
    print("\n📋 Instrucciones:")
    print("1. Abre http://localhost:5001/mapa-metro-ligero")
    print("2. Activa las capas que quieras ver")
    print("3. Haz clic en cualquier punto del mapa")
    print("4. Deberías ver popups con nombre, dirección e información adicional")

if __name__ == "__main__":
    main() 