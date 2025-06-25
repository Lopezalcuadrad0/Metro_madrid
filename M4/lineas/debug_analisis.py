#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG ANALISIS - Metro de Madrid
================================
Script para debuggear por qué no se extraen los datos de las líneas
"""

import os
import re

# Configuración
DATOS_LINEAS_PATH = os.path.join(os.path.dirname(__file__), 'M4', 'lineas')

def debug_archivo_linea(archivo_path, numero_linea):
    """Debug de un archivo específico"""
    print(f"\n🔍 DEBUGGING {os.path.basename(archivo_path)} (Línea {numero_linea})")
    print("=" * 60)
    
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {archivo_path}: {e}")
        return
    
    print(f"📄 Tamaño del archivo: {len(contenido)} caracteres")
    
    # Buscar las primeras estaciones
    estaciones_prueba = ['Pinar de Chamartín', 'Bambú', 'Chamartín', 'Plaza de Castilla']
    
    for estacion in estaciones_prueba:
        print(f"\n🔎 Buscando estación: '{estacion}'")
        
        # Buscar la estación en el contenido
        patrones = [
            rf"{re.escape(estacion)}\s*icono",
            rf"{re.escape(estacion)}\s*Zona tarifaria",
            rf"{re.escape(estacion)}\s*$",
            rf"{re.escape(estacion)}\s*\n"
        ]
        
        encontrada = False
        for i, patron in enumerate(patrones):
            match = re.search(patron, contenido, re.IGNORECASE)
            if match:
                print(f"  ✅ Encontrada con patrón {i+1}: '{patron}'")
                encontrada = True
                break
        
        if not encontrada:
            print(f"  ❌ NO ENCONTRADA")
            
            # Buscar variaciones
            variaciones = [
                estacion.lower(),
                estacion.upper(),
                estacion.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u'),
                estacion.replace(' ', '')
            ]
            
            for var in variaciones:
                if var in contenido.lower():
                    print(f"    🔍 Variación encontrada: '{var}'")
    
    # Buscar secciones de accesos
    print(f"\n🔍 Buscando secciones de accesos...")
    accesos_matches = re.findall(r'Accesos:(.*?)(?=\n[A-Z]|$)', contenido, re.DOTALL)
    print(f"  📊 Encontradas {len(accesos_matches)} secciones de accesos")
    
    if accesos_matches:
        print(f"  📝 Primera sección de accesos:")
        print(f"    {accesos_matches[0][:200]}...")

def main():
    """Función principal"""
    print("🚇 DEBUG ANALISIS DE ARCHIVOS DE LÍNEAS")
    print("=" * 60)
    
    if not os.path.exists(DATOS_LINEAS_PATH):
        print(f"❌ No se encuentra el directorio: {DATOS_LINEAS_PATH}")
        return
    
    # Debug de la línea 1
    archivo_l1 = os.path.join(DATOS_LINEAS_PATH, 'datosl1.txt')
    if os.path.exists(archivo_l1):
        debug_archivo_linea(archivo_l1, '1')
    else:
        print(f"❌ No se encuentra el archivo: {archivo_l1}")
    
    # Debug de la línea R
    archivo_r = os.path.join(DATOS_LINEAS_PATH, 'datosR.txt')
    if os.path.exists(archivo_r):
        debug_archivo_linea(archivo_r, 'R')
    else:
        print(f"❌ No se encuentra el archivo: {archivo_r}")

if __name__ == "__main__":
    main() 