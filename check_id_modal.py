#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar qué estaciones no tienen id_modal
"""

import pandas as pd
import sqlite3
import os

def cargar_datos_clave():
    """Carga los datos clave de estaciones desde el CSV"""
    try:
        csv_path = 'datos_clave_estaciones_actualizado.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"✅ Datos clave cargados: {len(df)} estaciones")
            return df
        else:
            print(f"❌ No se encontró el archivo: {csv_path}")
            return None
    except Exception as e:
        print(f"❌ Error cargando datos clave: {e}")
        return None

def verificar_id_modal():
    """Verifica qué estaciones no tienen id_modal"""
    print("🔍 Verificando estaciones sin id_modal...")
    print("=" * 50)
    
    # Cargar datos clave
    df = cargar_datos_clave()
    if df is None:
        return
    
    # Verificar si existe la columna id_modal
    if 'id_modal' not in df.columns:
        print("❌ No existe la columna 'id_modal' en el CSV")
        return
    
    # Filtrar estaciones sin id_modal
    estaciones_sin_id_modal = df[
        (df['id_modal'].isna()) | 
        (df['id_modal'] == '') |
        (df['id_modal'] == None)
    ]
    
    # Estadísticas
    total_estaciones = len(df)
    estaciones_sin_id = len(estaciones_sin_id_modal)
    porcentaje = (estaciones_sin_id / total_estaciones) * 100
    
    print(f"📊 ESTADÍSTICAS:")
    print(f"   Total de estaciones: {total_estaciones}")
    print(f"   Estaciones sin id_modal: {estaciones_sin_id}")
    print(f"   Porcentaje sin id_modal: {porcentaje:.1f}%")
    print()
    
    if estaciones_sin_id == 0:
        print("✅ Todas las estaciones tienen id_modal")
        return
    
    # Mostrar estaciones sin id_modal
    print(f"❌ ESTACIONES SIN ID_MODAL ({estaciones_sin_id}):")
    print("-" * 50)
    
    for _, row in estaciones_sin_id_modal.iterrows():
        print(f"   🚇 {row['nombre']} (Línea {row['linea']}) - ID: {row['id_fijo']}")
    
    print()
    print("📋 LISTA COMPLETA PARA COPIAR:")
    print("-" * 50)
    for _, row in estaciones_sin_id_modal.iterrows():
        print(f"{row['nombre']},{row['linea']},{row['id_fijo']},{row.get('tabla_origen', 'N/A')}")
    
    # Verificar por línea
    print()
    print("📊 POR LÍNEA:")
    print("-" * 50)
    por_linea = estaciones_sin_id_modal.groupby('linea').size()
    for linea, count in por_linea.items():
        print(f"   Línea {linea}: {count} estaciones sin id_modal")

def verificar_base_datos():
    """Verifica también en la base de datos SQLite"""
    print()
    print("🗄️ Verificando en base de datos SQLite...")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        
        # Lista de tablas de líneas
        lineas_tablas = [
            'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
            'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
        ]
        
        total_bd = 0
        sin_id_modal_bd = 0
        
        for tabla in lineas_tablas:
            try:
                # Verificar si la tabla existe
                cursor = conn.cursor()
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'")
                if not cursor.fetchone():
                    continue
                
                # Contar total y sin id_modal
                cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                total_tabla = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE id_modal IS NULL OR id_modal = ''")
                sin_id_modal_tabla = cursor.fetchone()[0]
                
                if sin_id_modal_tabla > 0:
                    print(f"   {tabla}: {sin_id_modal_tabla}/{total_tabla} sin id_modal")
                    
                    # Mostrar estaciones específicas
                    cursor.execute(f"SELECT nombre, id_fijo FROM {tabla} WHERE id_modal IS NULL OR id_modal = ''")
                    estaciones = cursor.fetchall()
                    for nombre, id_fijo in estaciones:
                        print(f"      - {nombre} (ID: {id_fijo})")
                
                total_bd += total_tabla
                sin_id_modal_bd += sin_id_modal_tabla
                
            except Exception as e:
                print(f"   Error en tabla {tabla}: {e}")
        
        conn.close()
        
        print()
        print(f"📊 BASE DE DATOS:")
        print(f"   Total: {total_bd} estaciones")
        print(f"   Sin id_modal: {sin_id_modal_bd}")
        if total_bd > 0:
            print(f"   Porcentaje: {(sin_id_modal_bd/total_bd)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")

if __name__ == "__main__":
    print("🚇 VERIFICADOR DE ID_MODAL - METRO DE MADRID")
    print("=" * 60)
    
    verificar_id_modal()
    verificar_base_datos()
    
    print()
    print("✅ Verificación completada")
    print("💡 Para arreglar: añade los id_modal faltantes a la base de datos") 