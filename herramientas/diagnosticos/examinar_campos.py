#!/usr/bin/env python3
"""
Script para examinar los campos disponibles en cada capa de transporte
"""

import requests
import json

def examinar_campos(endpoint, nombre):
    """Examina los campos disponibles en un endpoint"""
    try:
        print(f"\n🔍 Examinando campos de {nombre}...")
        print("=" * 50)
        
        response = requests.get(f"http://localhost:5001{endpoint}", timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'data' in data:
                features = data['data'].get('features', [])
                if features:
                    # Tomar el primer feature como ejemplo
                    first_feature = features[0]
                    properties = first_feature.get('properties', {})
                    
                    print(f"📊 Total de features: {len(features)}")
                    print(f"📋 Campos disponibles en properties:")
                    
                    for key, value in properties.items():
                        print(f"   - {key}: {value}")
                    
                    # Buscar campos que podrían ser nombres
                    nombre_candidates = []
                    direccion_candidates = []
                    
                    for key, value in properties.items():
                        key_lower = key.lower()
                        if any(word in key_lower for word in ['nombre', 'name', 'denominacion', 'title']):
                            nombre_candidates.append(key)
                        if any(word in key_lower for word in ['direccion', 'address', 'via', 'calle']):
                            direccion_candidates.append(key)
                    
                    print(f"\n🎯 Posibles campos de NOMBRE: {nombre_candidates}")
                    print(f"📍 Posibles campos de DIRECCIÓN: {direccion_candidates}")
                    
                else:
                    print("❌ No hay features en los datos")
            else:
                print("❌ Respuesta no exitosa")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Función principal"""
    print("🔍 EXAMINANDO CAMPOS DE TODAS LAS CAPAS")
    print("=" * 60)
    
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD")
    ]
    
    for endpoint, nombre in endpoints:
        examinar_campos(endpoint, nombre)
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main() 