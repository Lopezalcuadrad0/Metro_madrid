#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from scraper_datos_detallados import ScraperDatosDetallados
import time

def obtener_estaciones_pendientes():
    """Obtiene todas las estaciones que necesitan datos detallados"""
    db_path = 'db/estaciones_fijas_v2.db'
    
    lineas_tablas = [
        'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
        'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
    ]
    
    estaciones_pendientes = []
    
    try:
        conn = sqlite3.connect(db_path)
        
        for tabla in lineas_tablas:
            # Buscar estaciones que NO tienen datos detallados completos
            query = f"""
            SELECT id_fijo, nombre, url
            FROM {tabla} 
            WHERE url IS NOT NULL 
            AND url != '' 
            AND (
                direccion_completa IS NULL 
                OR direccion_completa = '' 
                OR accesos IS NULL 
                OR accesos = ''
                OR servicios IS NULL 
                OR servicios = ''
            )
            ORDER BY orden_en_linea
            """
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                df['tabla_origen'] = tabla
                df['linea'] = tabla.replace('linea_', '')  # Extraer número de línea del nombre de tabla
                estaciones_pendientes.append(df)
                print(f"[INFO] {tabla}: {len(df)} estaciones pendientes")
        
        conn.close()
        
        if estaciones_pendientes:
            # Combinar todos los DataFrames
            todas_estaciones = pd.concat(estaciones_pendientes, ignore_index=True)
            print(f"\n[INFO] Total estaciones pendientes: {len(todas_estaciones)}")
            return todas_estaciones
        else:
            print("[INFO] No hay estaciones pendientes")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"[ERROR] Error obteniendo estaciones pendientes: {e}")
        return pd.DataFrame()

def procesar_estaciones_pendientes(estaciones_df):
    """Procesa las estaciones pendientes con el scraper"""
    if estaciones_df.empty:
        print("[INFO] No hay estaciones para procesar")
        return
    
    scraper = ScraperDatosDetallados()
    
    total_procesadas = 0
    total_exitosas = 0
    
    print(f"\n🚀 PROCESANDO {len(estaciones_df)} ESTACIONES PENDIENTES")
    print("=" * 60)
    
    for _, estacion in estaciones_df.iterrows():
        total_procesadas += 1
        
        print(f"\n[{total_procesadas}/{len(estaciones_df)}] Procesando: {estacion['nombre']} (Línea {estacion['linea']})")
        print(f"  URL: {estacion['url']}")
        
        # Scrapear datos detallados
        datos = scraper.scrape_estacion_detallada(estacion['url'])
        
        if datos:
            # Actualizar en la base de datos
            if scraper.actualizar_estacion_detallada(estacion['tabla_origen'], estacion['id_fijo'], datos):
                total_exitosas += 1
                print(f"  ✅ Actualizada correctamente")
            else:
                print(f"  ❌ Error actualizando en BD")
        else:
            print(f"  ❌ Sin datos obtenidos")
        
        # Pausa entre requests
        time.sleep(2)
    
    print(f"\n📊 RESUMEN FINAL")
    print("=" * 30)
    print(f"Total procesadas: {total_procesadas}")
    print(f"Exitosas: {total_exitosas}")
    print(f"Fallidas: {total_procesadas - total_exitosas}")
    print(f"Tasa de éxito: {(total_exitosas/total_procesadas*100):.1f}%" if total_procesadas > 0 else "N/A")

def verificar_resultado():
    """Verifica el resultado después del procesamiento"""
    print("\n🔍 VERIFICANDO RESULTADO FINAL")
    print("=" * 40)
    
    db_path = 'db/estaciones_fijas_v2.db'
    lineas_tablas = [
        'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
        'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        
        total_estaciones = 0
        total_con_datos = 0
        
        for tabla in lineas_tablas:
            # Contar estaciones totales y con datos detallados
            query_total = f"SELECT COUNT(*) as total FROM {tabla}"
            query_con_datos = f"""
            SELECT COUNT(*) as con_datos 
            FROM {tabla} 
            WHERE direccion_completa IS NOT NULL 
            AND direccion_completa != ''
            AND accesos IS NOT NULL 
            AND accesos != ''
            """
            
            total = pd.read_sql_query(query_total, conn).iloc[0]['total']
            con_datos = pd.read_sql_query(query_con_datos, conn).iloc[0]['con_datos']
            
            total_estaciones += total
            total_con_datos += con_datos
            
            print(f"{tabla}: {con_datos}/{total} estaciones con datos completos")
        
        conn.close()
        
        print(f"\n📈 RESUMEN GENERAL:")
        print(f"Total estaciones: {total_estaciones}")
        print(f"Con datos completos: {total_con_datos}")
        print(f"Sin datos completos: {total_estaciones - total_con_datos}")
        print(f"Porcentaje de cobertura: {(total_con_datos/total_estaciones*100):.1f}%" if total_estaciones > 0 else "N/A")
        
        if total_con_datos == total_estaciones:
            print("🎉 ¡TODAS LAS ESTACIONES TIENEN DATOS COMPLETOS!")
        else:
            print(f"⚠️  Aún faltan {total_estaciones - total_con_datos} estaciones por completar")
        
    except Exception as e:
        print(f"[ERROR] Error verificando resultado: {e}")

def main():
    print("🔧 COMPLETADOR DE DATOS FALTANTES - METRO DE MADRID")
    print("=" * 60)
    print("Este script procesa específicamente las estaciones que NO tienen datos detallados")
    print()
    
    # Obtener estaciones pendientes
    estaciones_pendientes = obtener_estaciones_pendientes()
    
    if estaciones_pendientes.empty:
        print("✅ No hay estaciones pendientes. La base de datos está completa.")
        return
    
    # Mostrar estaciones pendientes
    print("\n📋 ESTACIONES PENDIENTES:")
    for _, estacion in estaciones_pendientes.iterrows():
        print(f"  - {estacion['nombre']} (Línea {estacion['linea']})")
    
    # Confirmar procesamiento
    print(f"\n⚠️  Se van a procesar {len(estaciones_pendientes)} estaciones")
    confirmacion = input("¿Continuar? (s/N): ").strip().lower()
    
    if confirmacion in ['s', 'si', 'sí', 'y', 'yes']:
        # Procesar estaciones
        procesar_estaciones_pendientes(estaciones_pendientes)
        
        # Verificar resultado
        verificar_resultado()
    else:
        print("❌ Procesamiento cancelado")

if __name__ == "__main__":
    main() 