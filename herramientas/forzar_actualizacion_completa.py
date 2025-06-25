#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from scraper_datos_detallados import ScraperDatosDetallados
import time

def forzar_actualizacion_completa():
    """Fuerza la actualización completa de todas las estaciones pendientes"""
    print("🚀 FORZANDO ACTUALIZACIÓN COMPLETA")
    print("=" * 50)
    
    db_path = 'db/estaciones_fijas_v2.db'
    lineas_tablas = [
        'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
        'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
    ]
    
    scraper = ScraperDatosDetallados()
    total_procesadas = 0
    total_exitosas = 0
    
    try:
        conn = sqlite3.connect(db_path)
        
        for tabla in lineas_tablas:
            print(f"\n📋 Procesando {tabla}...")
            
            # Obtener TODAS las estaciones con URL (sin filtrar por datos existentes)
            query = f"""
            SELECT id_fijo, nombre, url 
            FROM {tabla} 
            WHERE url IS NOT NULL 
            AND url != '' 
            ORDER BY orden_en_linea
            """
            
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print(f"  ⚠️  No hay estaciones con URL en {tabla}")
                continue
            
            print(f"  📊 {len(df)} estaciones encontradas en {tabla}")
            
            for idx, row in df.iterrows():
                total_procesadas += 1
                
                print(f"\n[{total_procesadas}] {row['nombre']} ({tabla})")
                print(f"  URL: {row['url']}")
                
                # Scrapear datos detallados
                datos = scraper.scrape_estacion_detallada(row['url'])
                
                if datos:
                    # Actualizar en la base de datos
                    if scraper.actualizar_estacion_detallada(tabla, row['id_fijo'], datos):
                        total_exitosas += 1
                        print(f"  ✅ Actualizada")
                    else:
                        print(f"  ❌ Error actualizando BD")
                else:
                    print(f"  ❌ Sin datos obtenidos")
                
                # Pausa entre requests
                time.sleep(1)
        
        conn.close()
        
        print(f"\n🎉 ACTUALIZACIÓN COMPLETADA")
        print("=" * 30)
        print(f"Total procesadas: {total_procesadas}")
        print(f"Exitosas: {total_exitosas}")
        print(f"Fallidas: {total_procesadas - total_exitosas}")
        print(f"Tasa de éxito: {(total_exitosas/total_procesadas*100):.1f}%" if total_procesadas > 0 else "N/A")
        
        return total_exitosas > 0
        
    except Exception as e:
        print(f"❌ Error en actualización: {e}")
        return False

if __name__ == "__main__":
    forzar_actualizacion_completa() 