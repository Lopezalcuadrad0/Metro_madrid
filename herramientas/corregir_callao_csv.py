#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir específicamente el problema de Callao en los archivos CSV
Asegura que Callao aparezca tanto en línea 3 como en línea 5
"""

import pandas as pd
import os

def corregir_callao_csv():
    """Corrige la entrada de Callao en los archivos CSV"""
    
    print("🔧 CORRIGIENDO ENTRADA DE CALLAO EN ARCHIVOS CSV")
    print("=" * 60)
    
    # 1. Corregir datos_clave_estaciones.csv
    print("\n📖 Corrigiendo datos_clave_estaciones.csv...")
    try:
        df = pd.read_csv('datos_clave_estaciones.csv')
        print(f"✅ Archivo leído: {len(df)} estaciones")
        
        # Eliminar entradas incorrectas de Callao
        df = df[~((df['nombre'] == 'Callao') & (df['linea'] == '5') & (df['tabla_origen'] == 'linea_3'))]
        
        # Buscar la entrada correcta de Callao para línea 5
        callao_l5 = df[(df['nombre'] == 'Callao') & (df['linea'] == '5') & (df['tabla_origen'] == 'linea_5')]
        
        if not callao_l5.empty:
            # Crear entrada para Callao en línea 3
            callao_l3_row = callao_l5.iloc[0].copy()
            callao_l3_row['linea'] = '3'
            callao_l3_row['tabla_origen'] = 'linea_3'
            callao_l3_row['url'] = 'https://www.metromadrid.es/es/linea/linea-3#estacion-307'
            
            # Añadir la nueva entrada
            df = pd.concat([df, pd.DataFrame([callao_l3_row])], ignore_index=True)
            
            # Ordenar por línea y orden
            df = df.sort_values(['linea', 'orden'])
            
            # Guardar archivo corregido
            df.to_csv('datos_clave_estaciones.csv', index=False, encoding='utf-8')
            print("✅ datos_clave_estaciones.csv corregido")
        else:
            print("⚠️ No se encontró entrada de Callao para línea 5")
            
    except Exception as e:
        print(f"❌ Error corrigiendo datos_clave_estaciones.csv: {e}")
    
    # 2. Corregir datos_clave_estaciones_actualizado.csv
    print("\n📖 Corrigiendo datos_clave_estaciones_actualizado.csv...")
    try:
        df = pd.read_csv('datos_clave_estaciones_actualizado.csv')
        print(f"✅ Archivo leído: {len(df)} estaciones")
        
        # Buscar la entrada de Callao para línea 5
        callao_l5 = df[(df['nombre'] == 'Callao') & (df['linea'] == '5')]
        
        if not callao_l5.empty:
            # Crear entrada para Callao en línea 3
            callao_l3_row = callao_l5.iloc[0].copy()
            callao_l3_row['linea'] = '3'
            callao_l3_row['tabla_origen'] = 'linea_3'
            callao_l3_row['url'] = 'https://www.metromadrid.es/es/linea/linea-3#estacion-307'
            
            # Añadir la nueva entrada
            df = pd.concat([df, pd.DataFrame([callao_l3_row])], ignore_index=True)
            
            # Ordenar por línea y orden
            df = df.sort_values(['linea', 'orden'])
            
            # Guardar archivo corregido
            df.to_csv('datos_clave_estaciones_actualizado.csv', index=False, encoding='utf-8')
            print("✅ datos_clave_estaciones_actualizado.csv corregido")
        else:
            print("⚠️ No se encontró entrada de Callao para línea 5")
            
    except Exception as e:
        print(f"❌ Error corrigiendo datos_clave_estaciones_actualizado.csv: {e}")
    
    # 3. Verificar corrección
    print("\n🔍 Verificando corrección...")
    
    # Verificar datos_clave_estaciones.csv
    try:
        df = pd.read_csv('datos_clave_estaciones.csv')
        callao_entries = df[df['nombre'] == 'Callao']
        print(f"Callao en datos_clave_estaciones.csv: {len(callao_entries)} entradas")
        for _, row in callao_entries.iterrows():
            print(f"  - Línea {row['linea']}: {row['nombre']} (ID: {row['id_fijo']}) - Tabla: {row['tabla_origen']}")
    except Exception as e:
        print(f"❌ Error verificando datos_clave_estaciones.csv: {e}")
    
    # Verificar datos_clave_estaciones_actualizado.csv
    try:
        df = pd.read_csv('datos_clave_estaciones_actualizado.csv')
        callao_entries = df[df['nombre'] == 'Callao']
        print(f"Callao en datos_clave_estaciones_actualizado.csv: {len(callao_entries)} entradas")
        for _, row in callao_entries.iterrows():
            print(f"  - Línea {row['linea']}: {row['nombre']} (ID: {row['id_fijo']}) - Tabla: {row['tabla_origen']}")
    except Exception as e:
        print(f"❌ Error verificando datos_clave_estaciones_actualizado.csv: {e}")
    
    print("\n🎉 Corrección completada")

if __name__ == "__main__":
    corregir_callao_csv() 