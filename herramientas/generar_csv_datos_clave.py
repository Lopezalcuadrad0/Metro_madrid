#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERAR CSV DATOS CLAVE - Metro de Madrid
=========================================

Genera un CSV con datos clave de todas las estaciones desde la base de datos fija.
Este CSV se cargará al inicio de la aplicación para búsquedas rápidas.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

# Configuración
DB_PATH = 'db/estaciones_fijas_v2.db'
CSV_PATH = 'datos_clave_estaciones.csv'

def generar_csv_datos_clave():
    """Genera un CSV con datos clave de todas las estaciones"""
    
    print("Generando CSV con datos clave de estaciones...")
    
    # Lista de tablas de líneas
    lineas_tablas = [
        'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
        'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
    ]
    
    # Mapeo de nombres de líneas
    nombres_lineas = {
        'linea_1': '1', 'linea_2': '2', 'linea_3': '3', 'linea_4': '4', 
        'linea_5': '5', 'linea_6': '6', 'linea_7': '7', 'linea_8': '8', 
        'linea_9': '9', 'linea_10': '10', 'linea_11': '11', 'linea_12': '12', 
        'linea_Ramal': 'Ramal'
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Lista para almacenar todos los datos
        todos_datos = []
        
        for tabla in lineas_tablas:
            print(f"Procesando {tabla}...")
            
            # Obtener datos de la tabla
            query = f"""
            SELECT 
                id_fijo,
                nombre,
                orden_en_linea,
                url,
                id_modal,
                zona_tarifaria,
                estacion_accesible
            FROM {tabla}
            ORDER BY orden_en_linea
            """
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                # Agregar información de línea
                df['linea'] = nombres_lineas.get(tabla, tabla)
                df['tabla_origen'] = tabla
                
                # Renombrar columnas para consistencia
                df = df.rename(columns={
                    'orden_en_linea': 'orden',
                    'zona_tarifaria': 'zona',
                    'estacion_accesible': 'accesible'
                })
                
                # Agregar a la lista
                todos_datos.append(df)
                
                print(f"  OK: {len(df)} estaciones de {tabla}")
            else:
                print(f"  ADVERTENCIA: No hay datos en {tabla}")
        
        conn.close()
        
        if todos_datos:
            # Combinar todos los datos
            df_completo = pd.concat(todos_datos, ignore_index=True)
            
            # --- CÁLCULO DE CORRESPONDENCIAS ---
            print("\nCalculando correspondencias...")
            # 1. Crear un mapa de estación -> [líneas]
            correspondencias_map = {}
            for _, row in df_completo.iterrows():
                nombre = row['nombre']
                linea = str(row['linea'])
                if nombre not in correspondencias_map:
                    correspondencias_map[nombre] = []
                if linea not in correspondencias_map[nombre]:
                    correspondencias_map[nombre].append(linea)
            
            # 2. Añadir la columna de correspondencias
            def calcular_correspondencias(row):
                nombre = row['nombre']
                linea_actual = str(row['linea'])
                todas_las_lineas = correspondencias_map.get(nombre, [])
                # Las correspondencias son las otras líneas en esa estación
                otras_lineas = [l for l in todas_las_lineas if l != linea_actual]
                # Guardar como un string que se pueda evaluar (como una lista)
                return str(otras_lineas)
            
            df_completo['correspondencias'] = df_completo.apply(calcular_correspondencias, axis=1)
            print("✅ Correspondencias calculadas.")
            
            # Ordenar por línea y orden
            df_completo = df_completo.sort_values(['linea', 'orden'])
            
            # Guardar CSV
            column_order = [
                'id_fijo', 'nombre', 'linea', 'orden', 'correspondencias',
                'zona', 'accesible', 'id_modal', 'url', 'tabla_origen'
            ]
            df_completo = df_completo[column_order]
            df_completo.to_csv(CSV_PATH, index=False, encoding='utf-8')
            
            print(f"\nCSV generado exitosamente: {CSV_PATH}")
            print(f"Total de estaciones: {len(df_completo)}")
            print(f"Lineas incluidas: {df_completo['linea'].nunique()}")
            
            # Mostrar estadísticas por línea
            print("\nEstadisticas por linea:")
            stats = df_completo.groupby('linea').agg({
                'id_fijo': 'count',
                'id_modal': lambda x: x.notna().sum()
            }).rename(columns={'id_fijo': 'total_estaciones', 'id_modal': 'con_id_modal'})
            
            for linea, row in stats.iterrows():
                print(f"  Linea {linea}: {row['total_estaciones']} estaciones ({row['con_id_modal']} con id_modal)")
            
            print(f"  Lineas unicas: {df_completo['linea'].nunique()}")
            print(f"  Estaciones unicas: {df_completo['nombre'].nunique()}")
            print(f"  Columnas: {df_completo.columns.tolist()}")
            
            return True
        else:
            print("ERROR: No se encontraron datos en ninguna tabla")
            return False
            
    except Exception as e:
        print(f"ERROR generando CSV: {e}")
        return False

def verificar_csv():
    """Verifica que el CSV se generó correctamente"""
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        print(f"\nVerificacion del CSV:")
        print(f"  Archivo: {CSV_PATH}")
        print(f"  Filas: {len(df)}")
        print(f"  Lineas unicas: {df['linea'].nunique()}")
        print(f"  Estaciones unicas: {df['nombre'].nunique()}")
        print(f"  Columnas: {df.columns.tolist()}")
        
        # Mostrar primeras filas
        print(f"\nPrimeras 5 filas:")
        print(df.head().to_string(index=False))
        
        return True
    else:
        print(f"ERROR: No se encontro el archivo {CSV_PATH}")
        return False

if __name__ == "__main__":
    print("GENERADOR DE CSV DATOS CLAVE - METRO DE MADRID")
    print("=" * 50)
    
    # Generar CSV
    if generar_csv_datos_clave():
        # Verificar resultado
        verificar_csv()
    else:
        print("ERROR en la generacion del CSV") 