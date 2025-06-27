#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTOR DE CONEXIONES DE CERCANÍAS
====================================

Extrae las conexiones entre estaciones de Cercanías y determina qué líneas son coincidentes,
priorizando mostrar las del número más bajo.
"""

import json
import re
from collections import defaultdict

def extraer_conexiones_cercanias():
    """Extrae las conexiones entre estaciones de Cercanías"""
    
    # Leer el archivo de datos
    with open('static/data/coincidentes cercanias', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Dividir por líneas de Cercanías
    lineas_cercanias = re.split(r'\n(C\d+[ab]?)\n', contenido)
    
    conexiones = {}
    estaciones_por_linea = {}
    estaciones_coincidentes = {}
    
    # Procesar cada línea
    for i in range(1, len(lineas_cercanias), 2):
        if i + 1 < len(lineas_cercanias):
            linea = lineas_cercanias[i]
            contenido_linea = lineas_cercanias[i + 1]
            
            print(f"Procesando línea {linea}...")
            
            # Extraer estaciones de esta línea
            estaciones = []
            lineas_estacion = contenido_linea.split('\n')
            
            for j, linea_estacion in enumerate(lineas_estacion):
                linea_estacion = linea_estacion.strip()
                if linea_estacion and not linea_estacion.startswith('·') and not linea_estacion.startswith('C') and not linea_estacion.startswith('Línea'):
                    # Es una estación
                    if 'min' in linea_estacion:
                        # Extraer solo el nombre de la estación (antes del tiempo)
                        nombre_estacion = linea_estacion.split('·')[0].strip()
                        if nombre_estacion:
                            estaciones.append(nombre_estacion)
                    else:
                        # Estación sin tiempo
                        if not any(palabra in linea_estacion.lower() for palabra in ['aparcabicis', 'metro', 'bus', 'conexión', 'accesible', 'asistencia', 'aparcamiento', 'media distancia', 'ave', 'avant', 'civis']):
                            estaciones.append(linea_estacion)
            
            if estaciones:
                estaciones_por_linea[linea] = estaciones
                print(f"  Estaciones encontradas: {len(estaciones)}")
                for estacion in estaciones[:5]:  # Mostrar solo las primeras 5
                    print(f"    - {estacion}")
                if len(estaciones) > 5:
                    print(f"    ... y {len(estaciones) - 5} más")
    
    # Identificar estaciones coincidentes
    estacion_a_lineas = defaultdict(list)
    
    for linea, estaciones in estaciones_por_linea.items():
        for estacion in estaciones:
            estacion_a_lineas[estacion].append(linea)
    
    # Encontrar estaciones que pertenecen a múltiples líneas
    for estacion, lineas in estacion_a_lineas.items():
        if len(lineas) > 1:
            # Ordenar líneas por número (priorizar las más bajas)
            lineas_ordenadas = sorted(lineas, key=lambda x: (
                int(re.search(r'C(\d+)', x).group(1)) if re.search(r'C(\d+)', x) else 999,
                x
            ))
            
            estaciones_coincidentes[estacion] = {
                'lineas': lineas_ordenadas,
                'linea_principal': lineas_ordenadas[0],  # La línea con número más bajo
                'total_lineas': len(lineas)
            }
    
    # Crear estructura de conexiones
    conexiones = {
        'estaciones_por_linea': estaciones_por_linea,
        'estaciones_coincidentes': estaciones_coincidentes,
        'estadisticas': {
            'total_lineas': len(estaciones_por_linea),
            'total_estaciones': sum(len(estaciones) for estaciones in estaciones_por_linea.values()),
            'estaciones_coincidentes': len(estaciones_coincidentes),
            'lineas_identificadas': list(estaciones_por_linea.keys())
        }
    }
    
    # Guardar resultados
    with open('static/data/conexiones_cercanias.json', 'w', encoding='utf-8') as f:
        json.dump(conexiones, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Archivo generado: static/data/conexiones_cercanias.json")
    print(f"📊 Estadísticas:")
    print(f"   - Líneas identificadas: {conexiones['estadisticas']['total_lineas']}")
    print(f"   - Total estaciones: {conexiones['estadisticas']['total_estaciones']}")
    print(f"   - Estaciones coincidentes: {conexiones['estadisticas']['estaciones_coincidentes']}")
    print(f"   - Líneas: {', '.join(conexiones['estadisticas']['lineas_identificadas'])}")
    
    # Mostrar algunas estaciones coincidentes importantes
    print(f"\n🔗 Estaciones coincidentes importantes:")
    estaciones_importantes = [
        'Madrid Chamartín-Clara Campoamor',
        'Madrid Atocha Cercanías',
        'Nuevos Ministerios',
        'Sol',
        'Príncipe Pío',
        'Alcalá de Henares',
        'Torrejón de Ardoz',
        'Coslada',
        'Vicálvaro',
        'Vallecas'
    ]
    
    for estacion in estaciones_importantes:
        if estacion in estaciones_coincidentes:
            info = estaciones_coincidentes[estacion]
            print(f"   {estacion}: {', '.join(info['lineas'])} (Principal: {info['linea_principal']})")
    
    return conexiones

def procesar_archivo_manual():
    """Procesa el archivo de forma manual analizando la estructura"""
    
    with open('static/data/coincidentes cercanias', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Dividir por líneas de Cercanías
    lineas_cercanias = re.split(r'\n(C\d+[ab]?)\n', contenido)
    
    estaciones_por_linea = {}
    
    # Procesar cada línea
    for i in range(1, len(lineas_cercanias), 2):
        if i + 1 < len(lineas_cercanias):
            linea = lineas_cercanias[i]
            contenido_linea = lineas_cercanias[i + 1]
            
            print(f"Procesando línea {linea}...")
            
            # Buscar estaciones en el contenido
            estaciones = []
            lineas_estacion = contenido_linea.split('\n')
            
            for linea_estacion in lineas_estacion:
                linea_estacion = linea_estacion.strip()
                
                # Buscar patrones de estaciones
                if 'min' in linea_estacion and '·' in linea_estacion:
                    # Formato: "Estación · X min"
                    partes = linea_estacion.split('·')
                    if len(partes) >= 2:
                        nombre = partes[0].strip()
                        if nombre and not any(palabra in nombre.lower() for palabra in ['aparcabicis', 'metro', 'bus', 'conexión', 'accesible', 'asistencia', 'aparcamiento', 'media distancia', 'ave', 'avant', 'civis']):
                            estaciones.append(nombre)
                
                elif linea_estacion and not linea_estacion.startswith('·') and not linea_estacion.startswith('C') and not linea_estacion.startswith('Línea'):
                    # Estación sin tiempo
                    if not any(palabra in linea_estacion.lower() for palabra in ['aparcabicis', 'metro', 'bus', 'conexión', 'accesible', 'asistencia', 'aparcamiento', 'media distancia', 'ave', 'avant', 'civis', 'min']):
                        estaciones.append(linea_estacion)
            
            if estaciones:
                estaciones_por_linea[linea] = estaciones
                print(f"  Estaciones encontradas: {len(estaciones)}")
                for estacion in estaciones[:5]:  # Mostrar solo las primeras 5
                    print(f"    - {estacion}")
                if len(estaciones) > 5:
                    print(f"    ... y {len(estaciones) - 5} más")
    
    return estaciones_por_linea

if __name__ == '__main__':
    # Probar el procesamiento manual primero
    print("Procesamiento manual del archivo:")
    estaciones_por_linea = procesar_archivo_manual()
    
    # Luego procesar las conexiones
    print("\n" + "="*50)
    print("Procesamiento de conexiones:")
    extraer_conexiones_cercanias() 