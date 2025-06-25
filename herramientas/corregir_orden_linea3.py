#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir el orden de las estaciones en la línea 3
Especialmente para corregir la entrada de Callao
"""

import pandas as pd

def corregir_orden_linea3():
    """Corrige el orden de las estaciones en la línea 3"""
    
    print("🔧 CORRIGIENDO ORDEN DE ESTACIONES EN LÍNEA 3")
    print("=" * 50)
    
    # Leer el archivo CSV
    print("\n📖 Leyendo datos_clave_estaciones.csv...")
    try:
        df = pd.read_csv('datos_clave_estaciones.csv')
        print(f"✅ Archivo leído: {len(df)} estaciones")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return
    
    # Filtrar solo las estaciones de la línea 3
    linea_3 = df[df['linea'] == '3'].copy()
    print(f"\n📊 Estaciones en línea 3: {len(linea_3)}")
    
    # Mostrar estaciones actuales de línea 3
    print("\n📋 Estaciones actuales de línea 3:")
    for _, row in linea_3.iterrows():
        print(f"  {row['orden']:2d}. {row['nombre']} (ID: {row['id_fijo']}) - Tabla: {row['tabla_origen']}")
    
    # Corregir la entrada de Callao
    print("\n🔧 Corrigiendo entrada de Callao...")
    
    # Buscar la entrada incorrecta de Callao
    callao_incorrecto = df[(df['nombre'] == 'Callao') & (df['linea'] == '5') & (df['tabla_origen'] == 'linea_3')]
    
    if not callao_incorrecto.empty:
        # Corregir la entrada de Callao
        df.loc[(df['nombre'] == 'Callao') & (df['linea'] == '5') & (df['tabla_origen'] == 'linea_3'), 'linea'] = '3'
        df.loc[(df['nombre'] == 'Callao') & (df['linea'] == '3') & (df['tabla_origen'] == 'linea_3'), 'orden'] = 15
        df.loc[(df['nombre'] == 'Callao') & (df['linea'] == '3') & (df['tabla_origen'] == 'linea_3'), 'url'] = 'https://www.metromadrid.es/es/linea/linea-3#estacion-307'
        print("✅ Entrada de Callao corregida")
    else:
        print("⚠️ No se encontró entrada incorrecta de Callao")
    
    # Reordenar todas las estaciones de línea 3 según el orden correcto
    print("\n🔄 Reordenando estaciones de línea 3...")
    
    # Orden correcto de estaciones en línea 3 (según el archivo original)
    orden_correcto = [
        'El Casar', 'Villaverde Alto', 'San Cristóbal', 'Villaverde Bajo Cruce',
        'Ciudad de los Ángeles', 'San Fermín – Orcasur', 'Hospital 12 de Octubre',
        'Almendrales', 'Legazpi', 'Delicias', 'Palos de la Frontera', 'Embajadores',
        'Lavapiés', 'Sol', 'Callao', 'Plaza de España', 'Ventura Rodríguez',
        'Argüelles', 'Moncloa'
    ]
    
    # Aplicar el orden correcto
    for idx, nombre in enumerate(orden_correcto, 1):
        mask = (df['nombre'] == nombre) & (df['linea'] == '3')
        if df[mask].shape[0] > 0:
            df.loc[mask, 'orden'] = idx
            print(f"  {idx:2d}. {nombre}")
    
    # Ordenar el DataFrame por línea y orden
    df = df.sort_values(['linea', 'orden'])
    
    # Guardar archivo corregido
    print(f"\n💾 Guardando archivo corregido...")
    try:
        df.to_csv('datos_clave_estaciones.csv', index=False, encoding='utf-8')
        print("✅ datos_clave_estaciones.csv guardado")
    except Exception as e:
        print(f"❌ Error guardando archivo: {e}")
        return
    
    # Verificar corrección
    print("\n🔍 Verificando corrección...")
    linea_3_corregida = df[df['linea'] == '3'].copy()
    print(f"\n📋 Estaciones corregidas de línea 3:")
    for _, row in linea_3_corregida.iterrows():
        print(f"  {row['orden']:2d}. {row['nombre']} (ID: {row['id_fijo']}) - Tabla: {row['tabla_origen']}")
    
    # Verificar Callao específicamente
    callao_entries = df[df['nombre'] == 'Callao']
    print(f"\n📋 Entradas de Callao:")
    for _, row in callao_entries.iterrows():
        print(f"  - Línea {row['linea']}: {row['nombre']} (ID: {row['id_fijo']}) - Orden: {row['orden']} - Tabla: {row['tabla_origen']}")
    
    print("\n🎉 Corrección completada")

if __name__ == "__main__":
    corregir_orden_linea3() 