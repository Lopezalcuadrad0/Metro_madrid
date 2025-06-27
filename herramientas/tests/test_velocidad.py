#!/usr/bin/env python3
"""
Script para medir la velocidad de carga de las capas
"""

import requests
import time
import statistics

def medir_velocidad_endpoint(endpoint, nombre):
    """Mide la velocidad de carga de un endpoint"""
    print(f"\n⏱️ Probando velocidad de {nombre}...")
    
    tiempos = []
    errores = 0
    
    # Hacer 3 pruebas para obtener un promedio
    for i in range(3):
        try:
            inicio = time.time()
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=60)
            fin = time.time()
            
            if response.status_code == 200:
                tiempo = fin - inicio
                tiempos.append(tiempo)
                print(f"  Prueba {i+1}: {tiempo:.2f}s")
            else:
                errores += 1
                print(f"  Prueba {i+1}: Error HTTP {response.status_code}")
                
        except Exception as e:
            errores += 1
            print(f"  Prueba {i+1}: Error - {str(e)}")
    
    if tiempos:
        tiempo_promedio = statistics.mean(tiempos)
        tiempo_min = min(tiempos)
        tiempo_max = max(tiempos)
        
        print(f"✅ {nombre}:")
        print(f"   Promedio: {tiempo_promedio:.2f}s")
        print(f"   Mínimo: {tiempo_min:.2f}s")
        print(f"   Máximo: {tiempo_max:.2f}s")
        
        return tiempo_promedio
    else:
        print(f"❌ {nombre}: No se pudo medir (errores: {errores})")
        return None

def main():
    """Función principal"""
    print("🚀 PRUEBA DE VELOCIDAD DE CARGA")
    print("=" * 50)
    
    endpoints = [
        ("/api/transport/metro_ligero", "Metro Ligero"),
        ("/api/transport/metro", "Metro de Madrid"),
        ("/api/transport/cercanias", "Cercanías"),
        ("/api/transport/autobuses_urbanos", "Autobuses Urbanos"),
        ("/api/transport/autobuses_interurbanos", "Autobuses Interurbanos"),
        ("/api/transport/bicimad", "BiciMAD")
    ]
    
    resultados = {}
    tiempos_totales = []
    
    for endpoint, nombre in endpoints:
        tiempo = medir_velocidad_endpoint(endpoint, nombre)
        if tiempo:
            resultados[nombre] = tiempo
            tiempos_totales.append(tiempo)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VELOCIDADES")
    print("=" * 50)
    
    # Ordenar por velocidad
    resultados_ordenados = sorted(resultados.items(), key=lambda x: x[1])
    
    for i, (nombre, tiempo) in enumerate(resultados_ordenados, 1):
        print(f"{i}. {nombre}: {tiempo:.2f}s")
    
    if tiempos_totales:
        tiempo_total_promedio = statistics.mean(tiempos_totales)
        print(f"\n⏱️ Tiempo promedio total: {tiempo_total_promedio:.2f}s")
        
        # Clasificar velocidad
        if tiempo_total_promedio < 5:
            print("🚀 ¡Excelente velocidad!")
        elif tiempo_total_promedio < 10:
            print("✅ Buena velocidad")
        elif tiempo_total_promedio < 20:
            print("⚠️ Velocidad aceptable")
        else:
            print("🐌 Velocidad lenta - considerar más optimizaciones")
    
    print("\n💡 Consejos de optimización:")
    print("- El cache de 5 minutos debería hacer la segunda carga mucho más rápida")
    print("- Las capas grandes (Metro) pueden tardar más en la primera carga")
    print("- BiciMAD debería ser muy rápido por usar datos oficiales")

if __name__ == "__main__":
    main() 