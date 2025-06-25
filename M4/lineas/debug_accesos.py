#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG ACCESOS - Metro de Madrid
===============================
Script para debuggear específicamente la extracción de accesos
"""

import os
import re

# Configuración
DATOS_LINEAS_PATH = os.path.join(os.path.dirname(__file__), 'M4', 'lineas')

def debug_accesos_estacion(archivo_path, nombre_estacion):
    """Debug de accesos de una estación específica"""
    print(f"\n🔍 DEBUGGING ACCESOS: {nombre_estacion}")
    print("=" * 50)
    
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {archivo_path}: {e}")
        return
    
    # Buscar la sección de la estación
    patrones = [
        rf"{re.escape(nombre_estacion)}\s*icono",
        rf"{re.escape(nombre_estacion)}\s*Zona tarifaria",
        rf"{re.escape(nombre_estacion)}\s*$",
        rf"{re.escape(nombre_estacion)}\s*\n"
    ]
    
    inicio = -1
    for patron in patrones:
        match = re.search(patron, contenido, re.IGNORECASE)
        if match:
            inicio = match.start()
            break
    
    if inicio == -1:
        print(f"❌ No se encontró la estación '{nombre_estacion}'")
        return
    
    # Buscar el final de la sección
    siguiente_patron = r'\n[A-Z][^a-z].*?(?:icono|Zona tarifaria)'
    siguiente_match = re.search(siguiente_patron, contenido[inicio+len(nombre_estacion):])
    
    if siguiente_match:
        fin = inicio + len(nombre_estacion) + siguiente_match.start()
    else:
        fin = len(contenido)
    
    seccion = contenido[inicio:fin]
    print(f"📄 Tamaño de sección: {len(seccion)} caracteres")
    
    # Buscar sección de accesos
    accesos_match = re.search(r'Accesos:(.*?)(?=\n[A-Z]|$)', seccion, re.DOTALL)
    if not accesos_match:
        print("❌ No se encontró sección de accesos")
        return
    
    accesos_texto = accesos_match.group(1)
    print(f"📝 Sección de accesos encontrada ({len(accesos_texto)} caracteres):")
    print("=" * 40)
    print(accesos_texto)
    print("=" * 40)
    
    # Procesar líneas de accesos
    lineas = accesos_texto.strip().split('\n')
    print(f"\n📊 Análisis de {len(lineas)} líneas:")
    
    for i, linea in enumerate(lineas):
        linea_stripped = linea.strip()
        print(f"  Línea {i+1}: '{linea_stripped}'")
        
        if linea_stripped:
            if linea_stripped.startswith('El horario'):
                print(f"    → Ignorada (horario)")
            elif linea_stripped.startswith('VESTÍBULO'):
                print(f"    → Ignorada (encabezado)")
            elif '\t' in linea_stripped:
                partes = linea_stripped.split('\t')
                print(f"    → ACCESO ENCONTRADO: vestíbulo='{partes[0].strip()}', nombre='{partes[1].strip()}'")
            else:
                print(f"    → Posible dirección o texto libre")

def main():
    """Función principal"""
    print("🚇 DEBUG ACCESOS DE ESTACIONES")
    print("=" * 60)
    
    # Debug de algunas estaciones conocidas
    estaciones_test = [
        ('datosl1.txt', 'Pinar de Chamartín'),
        ('datosl1.txt', 'Bambú'),
        ('datosR.txt', 'Ópera'),
        ('datosR.txt', 'Príncipe Pío')
    ]
    
    for archivo, estacion in estaciones_test:
        archivo_path = os.path.join(DATOS_LINEAS_PATH, archivo)
        if os.path.exists(archivo_path):
            debug_accesos_estacion(archivo_path, estacion)
        else:
            print(f"❌ No se encuentra el archivo: {archivo_path}")

if __name__ == "__main__":
    main() 