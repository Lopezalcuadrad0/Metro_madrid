#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para regenerar completamente los archivos CSV de datos clave
Incluye todas las estaciones del archivo original estaciones_procesadas.csv
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

def regenerar_csv_datos_clave():
    """Regenera los archivos CSV de datos clave con todas las estaciones"""
    
    print("🔄 REGENERANDO ARCHIVOS CSV DE DATOS CLAVE")
    print("=" * 60)
    
    # 1. Leer archivo original
    print("\n📖 Leyendo archivo original: datos_estaciones/estaciones_procesadas.csv")
    try:
        df_original = pd.read_csv('datos_estaciones/estaciones_procesadas.csv')
        print(f"✅ Archivo original: {len(df_original)} estaciones")
    except Exception as e:
        print(f"❌ Error leyendo archivo original: {e}")
        return False
    
    # 2. Conectar a la base de datos para obtener datos adicionales
    print("\n🗄️ Conectando a la base de datos...")
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        print("✅ Conexión a base de datos establecida")
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False
    
    # 3. Procesar cada estación del archivo original
    print("\n🔄 Procesando estaciones...")
    datos_clave = []
    
    for idx, row in df_original.iterrows():
        linea = str(row['line_number'])
        nombre = row['station_name'].strip()
        id_fijo = int(row['station_id'])
        url = row['url']
        
        # Buscar datos adicionales en la base de datos
        datos_adicionales = obtener_datos_adicionales(conn, linea, id_fijo, nombre)
        
        # Crear entrada para datos clave
        entrada = {
            'id_fijo': id_fijo,
            'nombre': nombre,
            'linea': linea,
            'orden': datos_adicionales.get('orden', idx + 1),
            'url': url,
            'id_modal': datos_adicionales.get('id_modal'),
            'zona': datos_adicionales.get('zona', 'A'),
            'accesible': datos_adicionales.get('accesible', False),
            'correspondencias': datos_adicionales.get('correspondencias', '[]'),
            'tabla_origen': f'linea_{linea}'
        }
        
        datos_clave.append(entrada)
        
        if (idx + 1) % 50 == 0:
            print(f"  Procesadas {idx + 1}/{len(df_original)} estaciones...")
    
    conn.close()
    
    # 4. Crear DataFrame
    df_datos_clave = pd.DataFrame(datos_clave)
    
    # 5. Ordenar por línea y orden
    df_datos_clave = df_datos_clave.sort_values(['linea', 'orden'])
    
    # 6. Guardar archivo datos_clave_estaciones.csv
    print(f"\n💾 Guardando datos_clave_estaciones.csv...")
    try:
        df_datos_clave.to_csv('datos_clave_estaciones.csv', index=False, encoding='utf-8')
        print(f"✅ datos_clave_estaciones.csv guardado: {len(df_datos_clave)} estaciones")
    except Exception as e:
        print(f"❌ Error guardando datos_clave_estaciones.csv: {e}")
        return False
    
    # 7. Guardar archivo datos_clave_estaciones_actualizado.csv
    print(f"💾 Guardando datos_clave_estaciones_actualizado.csv...")
    try:
        df_datos_clave.to_csv('datos_clave_estaciones_actualizado.csv', index=False, encoding='utf-8')
        print(f"✅ datos_clave_estaciones_actualizado.csv guardado: {len(df_datos_clave)} estaciones")
    except Exception as e:
        print(f"❌ Error guardando datos_clave_estaciones_actualizado.csv: {e}")
        return False
    
    # 8. Verificar que todas las estaciones están incluidas
    print("\n🔍 Verificando inclusión de estaciones...")
    estaciones_originales = set()
    for _, row in df_original.iterrows():
        linea = str(row['line_number'])
        nombre = row['station_name'].strip()
        id_fijo = int(row['station_id'])
        estaciones_originales.add((linea, nombre, id_fijo))
    
    estaciones_incluidas = set()
    for _, row in df_datos_clave.iterrows():
        linea = str(row['linea'])
        nombre = row['nombre'].strip()
        id_fijo = int(row['id_fijo'])
        estaciones_incluidas.add((linea, nombre, id_fijo))
    
    faltantes = estaciones_originales - estaciones_incluidas
    if faltantes:
        print(f"⚠️ Aún faltan {len(faltantes)} estaciones:")
        for linea, nombre, id_fijo in sorted(faltantes):
            print(f"  - Línea {linea}: {nombre} (ID: {id_fijo})")
    else:
        print("✅ Todas las estaciones están incluidas correctamente")
    
    # 9. Resumen final
    print("\n📈 RESUMEN FINAL")
    print("=" * 30)
    print(f"Estaciones originales: {len(estaciones_originales)}")
    print(f"Estaciones incluidas: {len(estaciones_incluidas)}")
    print(f"Estaciones faltantes: {len(faltantes)}")
    print(f"Archivos generados: 2")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

def obtener_datos_adicionales(conn, linea, id_fijo, nombre):
    """Obtiene datos adicionales de la base de datos"""
    datos = {}
    
    try:
        # Intentar obtener datos de la tabla específica de la línea
        tabla_linea = f'linea_{linea}'
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla_linea,))
        if cursor.fetchone():
            # Buscar la estación en la tabla específica
            cursor.execute(f"""
                SELECT orden, id_modal, zona_tarifaria, estacion_accesible, correspondencias
                FROM {tabla_linea}
                WHERE id_fijo = ? OR nombre = ?
            """, (id_fijo, nombre))
            
            row = cursor.fetchone()
            if row:
                datos['orden'] = row[0] if row[0] else 1
                datos['id_modal'] = row[1] if row[1] else None
                datos['zona'] = row[2] if row[2] else 'A'
                datos['accesible'] = row[3] == 'Sí' if row[3] else False
                datos['correspondencias'] = row[4] if row[4] else '[]'
        
        # Si no se encontró en la tabla específica, buscar en estaciones_completas
        if not datos:
            cursor.execute("""
                SELECT orden_en_linea, zona_tarifaria, estacion_accesible, correspondencias
                FROM estaciones_completas
                WHERE id_fijo = ? AND linea = ?
            """, (id_fijo, linea))
            
            row = cursor.fetchone()
            if row:
                datos['orden'] = row[0] if row[0] else 1
                datos['zona'] = row[1] if row[1] else 'A'
                datos['accesible'] = row[2] == 'Sí' if row[2] else False
                datos['correspondencias'] = row[3] if row[3] else '[]'
    
    except Exception as e:
        print(f"⚠️ Error obteniendo datos adicionales para {nombre}: {e}")
    
    return datos

if __name__ == "__main__":
    success = regenerar_csv_datos_clave()
    if success:
        print("\n🎉 ¡Archivos CSV regenerados exitosamente!")
    else:
        print("\n❌ Error regenerando archivos CSV") 