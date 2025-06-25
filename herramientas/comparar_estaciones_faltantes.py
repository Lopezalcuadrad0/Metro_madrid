#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar estaciones entre archivos CSV
Identifica qué estaciones del archivo original faltan en los archivos de datos clave
"""

import pandas as pd
import os

def comparar_estaciones():
    """Compara las estaciones entre los diferentes archivos CSV"""
    
    print("🔍 COMPARANDO ESTACIONES ENTRE ARCHIVOS CSV")
    print("=" * 60)
    
    # 1. Leer archivo original (estaciones_procesadas.csv)
    print("\n📖 Leyendo archivo original: datos_estaciones/estaciones_procesadas.csv")
    try:
        df_original = pd.read_csv('datos_estaciones/estaciones_procesadas.csv')
        print(f"✅ Archivo original: {len(df_original)} estaciones")
    except Exception as e:
        print(f"❌ Error leyendo archivo original: {e}")
        return
    
    # 2. Leer archivo datos_clave_estaciones.csv
    print("\n📖 Leyendo archivo: datos_clave_estaciones.csv")
    try:
        df_clave = pd.read_csv('datos_clave_estaciones.csv')
        print(f"✅ Archivo datos_clave: {len(df_clave)} estaciones")
    except Exception as e:
        print(f"❌ Error leyendo datos_clave: {e}")
        df_clave = pd.DataFrame()
    
    # 3. Leer archivo datos_clave_estaciones_actualizado.csv
    print("\n📖 Leyendo archivo: datos_clave_estaciones_actualizado.csv")
    try:
        df_actualizado = pd.read_csv('datos_clave_estaciones_actualizado.csv')
        print(f"✅ Archivo actualizado: {len(df_actualizado)} estaciones")
    except Exception as e:
        print(f"❌ Error leyendo actualizado: {e}")
        df_actualizado = pd.DataFrame()
    
    # 4. Crear conjunto de estaciones del archivo original
    # Formato: (linea, nombre, id_fijo)
    estaciones_originales = set()
    for _, row in df_original.iterrows():
        linea = str(row['line_number'])
        nombre = row['station_name'].strip()
        id_fijo = int(row['station_id'])
        estaciones_originales.add((linea, nombre, id_fijo))
    
    print(f"\n📊 Total estaciones originales: {len(estaciones_originales)}")
    
    # 5. Crear conjunto de estaciones del archivo datos_clave
    estaciones_clave = set()
    if not df_clave.empty:
        for _, row in df_clave.iterrows():
            linea = str(row['linea'])
            nombre = row['nombre'].strip()
            id_fijo = int(row['id_fijo'])
            estaciones_clave.add((linea, nombre, id_fijo))
    
    # 6. Crear conjunto de estaciones del archivo actualizado
    estaciones_actualizado = set()
    if not df_actualizado.empty:
        for _, row in df_actualizado.iterrows():
            linea = str(row['linea'])
            nombre = row['nombre'].strip()
            id_fijo = int(row['id_fijo'])
            estaciones_actualizado.add((linea, nombre, id_fijo))
    
    # 7. Encontrar estaciones faltantes
    print("\n🔍 ANALIZANDO ESTACIONES FALTANTES")
    print("-" * 40)
    
    # Estaciones que faltan en datos_clave
    faltantes_clave = estaciones_originales - estaciones_clave
    print(f"\n❌ Estaciones faltantes en datos_clave_estaciones.csv: {len(faltantes_clave)}")
    
    if faltantes_clave:
        print("\n📋 Lista de estaciones faltantes:")
        for linea, nombre, id_fijo in sorted(faltantes_clave):
            print(f"  - Línea {linea}: {nombre} (ID: {id_fijo})")
    
    # Estaciones que faltan en actualizado
    faltantes_actualizado = estaciones_originales - estaciones_actualizado
    print(f"\n❌ Estaciones faltantes en datos_clave_estaciones_actualizado.csv: {len(faltantes_actualizado)}")
    
    if faltantes_actualizado:
        print("\n📋 Lista de estaciones faltantes:")
        for linea, nombre, id_fijo in sorted(faltantes_actualizado):
            print(f"  - Línea {linea}: {nombre} (ID: {id_fijo})")
    
    # 8. Análisis por líneas
    print("\n📊 ANÁLISIS POR LÍNEAS")
    print("-" * 30)
    
    lineas_originales = {}
    for linea, nombre, id_fijo in estaciones_originales:
        if linea not in lineas_originales:
            lineas_originales[linea] = []
        lineas_originales[linea].append((nombre, id_fijo))
    
    for linea in sorted(lineas_originales.keys()):
        total_linea = len(lineas_originales[linea])
        faltantes_linea_clave = len([(l, n, i) for l, n, i in faltantes_clave if l == linea])
        faltantes_linea_actualizado = len([(l, n, i) for l, n, i in faltantes_actualizado if l == linea])
        
        print(f"Línea {linea}: {total_linea} estaciones totales")
        if faltantes_linea_clave > 0:
            print(f"  - Faltantes en datos_clave: {faltantes_linea_clave}")
        if faltantes_linea_actualizado > 0:
            print(f"  - Faltantes en actualizado: {faltantes_linea_actualizado}")
    
    # 9. Resumen final
    print("\n📈 RESUMEN FINAL")
    print("=" * 30)
    print(f"Total estaciones originales: {len(estaciones_originales)}")
    print(f"Estaciones en datos_clave: {len(estaciones_clave)}")
    print(f"Estaciones en actualizado: {len(estaciones_actualizado)}")
    print(f"Faltantes en datos_clave: {len(faltantes_clave)}")
    print(f"Faltantes en actualizado: {len(faltantes_actualizado)}")
    
    # 10. Guardar reporte
    if faltantes_clave or faltantes_actualizado:
        print("\n💾 Guardando reporte de estaciones faltantes...")
        
        # Crear DataFrame con estaciones faltantes
        reporte_data = []
        for linea, nombre, id_fijo in sorted(faltantes_clave | faltantes_actualizado):
            falta_clave = (linea, nombre, id_fijo) in faltantes_clave
            falta_actualizado = (linea, nombre, id_fijo) in faltantes_actualizado
            
            reporte_data.append({
                'linea': linea,
                'nombre': nombre,
                'id_fijo': id_fijo,
                'falta_en_datos_clave': falta_clave,
                'falta_en_actualizado': falta_actualizado
            })
        
        df_reporte = pd.DataFrame(reporte_data)
        df_reporte.to_csv('estaciones_faltantes_report.csv', index=False, encoding='utf-8')
        print("✅ Reporte guardado en: estaciones_faltantes_report.csv")
    
    return faltantes_clave, faltantes_actualizado

if __name__ == "__main__":
    comparar_estaciones() 