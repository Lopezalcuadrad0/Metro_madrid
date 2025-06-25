#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sqlite3
from datetime import datetime
from scraper_datos_detallados import ScraperDatosDetallados

def obtener_estaciones_prueba(limite=10):
    """Obtiene las primeras estaciones para pruebas rápidas"""
    try:
        conn = sqlite3.connect('../db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        estaciones_prueba = []
        
        # Obtener todas las líneas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
        lineas = [row[0] for row in cursor.fetchall()]
        
        for linea in lineas:
            # Obtener las primeras estaciones de cada línea
            cursor.execute(f"""
                SELECT id_fijo, nombre, url 
                FROM {linea} 
                WHERE url IS NOT NULL 
                AND url != '' 
                ORDER BY id_fijo
                LIMIT 2
            """)
            
            estaciones_linea = cursor.fetchall()
            for estacion in estaciones_linea:
                estaciones_prueba.append({
                    'linea': linea,
                    'id_fijo': estacion[0],
                    'nombre': estacion[1],
                    'url': estacion[2]
                })
                
                if len(estaciones_prueba) >= limite:
                    break
            
            if len(estaciones_prueba) >= limite:
                break
        
        conn.close()
        return estaciones_prueba[:limite]
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo estaciones de prueba: {e}")
        return []

def verificar_actualizacion_rapida(linea, id_fijo, nombre):
    """Verificación rápida de actualización"""
    try:
        conn = sqlite3.connect('../db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT servicios, accesos, correspondencias, ultima_actualizacion_detalles
            FROM {linea}
            WHERE id_fijo = ?
        """, (id_fijo,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            servicios, accesos, correspondencias, ultima_actualizacion = resultado
            
            if ultima_actualizacion:
                print(f"    [OK] {nombre}: ✅ Servicios: {len(servicios.split('; ')) if servicios else 0}, "
                      f"Accesos: {len(accesos.split('; ')) if accesos else 0}, "
                      f"Conexiones: {len(correspondencias.split('; ')) if correspondencias else 0}")
                return True
            else:
                print(f"    [FAIL] {nombre}: ❌ Sin fecha de actualización")
                return False
        else:
            print(f"    [FAIL] {nombre}: ❌ No encontrada en BD")
            return False
            
    except Exception as e:
        print(f"    [ERROR] {nombre}: ❌ Error: {e}")
        return False

def ejecutar_scraper_rapido():
    """Ejecuta el scraper rápido para pruebas"""
    print("=== SCRAPER RÁPIDO DE PRUEBA ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Inicializar scraper
    scraper = ScraperDatosDetallados()
    
    # Obtener estaciones de prueba
    estaciones_prueba = obtener_estaciones_prueba(10)
    
    if not estaciones_prueba:
        print("[ERROR] No se encontraron estaciones para probar")
        return
    
    print(f"\n[INFO] Procesando {len(estaciones_prueba)} estaciones de prueba...")
    
    # Estadísticas
    estaciones_procesadas = 0
    estaciones_exitosas = 0
    estaciones_fallidas = 0
    
    # Procesar cada estación
    for i, estacion in enumerate(estaciones_prueba, 1):
        linea = estacion['linea']
        id_fijo = estacion['id_fijo']
        nombre = estacion['nombre']
        url = estacion['url']
        
        print(f"\n[{i}/{len(estaciones_prueba)}] Procesando: {nombre} ({linea})")
        
        try:
            # Scrapear estación
            datos = scraper.scrape_estacion_detallada(url)
            
            if datos:
                # Actualizar base de datos
                if scraper.actualizar_estacion_detallada(linea, id_fijo, datos):
                    # Verificación rápida
                    if verificar_actualizacion_rapida(linea, id_fijo, nombre):
                        estaciones_exitosas += 1
                    else:
                        estaciones_fallidas += 1
                else:
                    estaciones_fallidas += 1
                    print(f"    [FAIL] Error actualizando BD")
            else:
                estaciones_fallidas += 1
                print(f"    [FAIL] Sin datos obtenidos")
            
            estaciones_procesadas += 1
            
            # Pausa mínima
            if i < len(estaciones_prueba):
                time.sleep(0.5)  # Solo 0.5 segundos
            
        except Exception as e:
            estaciones_fallidas += 1
            estaciones_procesadas += 1
            print(f"    [ERROR] Error: {e}")
            continue
    
    # Resumen final
    print(f"\n=== RESUMEN RÁPIDO ===")
    print(f"Estaciones procesadas: {estaciones_procesadas}")
    print(f"Estaciones exitosas: {estaciones_exitosas}")
    print(f"Estaciones fallidas: {estaciones_fallidas}")
    print(f"Tasa de éxito: {(estaciones_exitosas/estaciones_procesadas*100):.1f}%" if estaciones_procesadas > 0 else "N/A")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificación rápida de datos guardados
    print(f"\n=== VERIFICACIÓN RÁPIDA ===")
    verificar_datos_guardados_rapido()

def verificar_datos_guardados_rapido():
    """Verificación rápida de datos guardados"""
    try:
        conn = sqlite3.connect('../db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Contar estaciones con conexiones
        cursor.execute("""
            SELECT COUNT(*) as total_con_conexiones
            FROM (
                SELECT correspondencias FROM linea_1 WHERE correspondencias IS NOT NULL AND correspondencias != '' AND correspondencias != '[]'
                UNION ALL
                SELECT correspondencias FROM linea_2 WHERE correspondencias IS NOT NULL AND correspondencias != '' AND correspondencias != '[]'
                UNION ALL
                SELECT correspondencias FROM linea_3 WHERE correspondencias IS NOT NULL AND correspondencias != '' AND correspondencias != '[]'
            )
        """)
        
        total_con_conexiones = cursor.fetchone()[0]
        
        # Mostrar algunas estaciones con conexiones
        print(f"[INFO] Estaciones con conexiones encontradas: {total_con_conexiones}")
        
        # Ejemplos de conexiones
        for linea in ['linea_1', 'linea_2', 'linea_3']:
            cursor.execute(f"""
                SELECT nombre, correspondencias 
                FROM {linea} 
                WHERE correspondencias IS NOT NULL 
                AND correspondencias != '' 
                AND correspondencias != '[]'
                LIMIT 1
            """)
            
            resultado = cursor.fetchone()
            if resultado:
                nombre, conexiones = resultado
                print(f"  {nombre}: {conexiones}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Error en verificación rápida: {e}")

if __name__ == "__main__":
    ejecutar_scraper_rapido() 