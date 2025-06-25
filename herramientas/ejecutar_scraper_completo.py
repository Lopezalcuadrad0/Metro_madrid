#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sqlite3
from datetime import datetime
from scraper_datos_detallados import ScraperDatosDetallados

def obtener_estaciones_pendientes():
    """Obtiene las estaciones que necesitan datos detallados"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Obtener todas las estaciones que no tienen datos detallados o los tienen muy antiguos
        estaciones_pendientes = []
        
        # Obtener todas las líneas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
        lineas = [row[0] for row in cursor.fetchall()]
        
        for linea in lineas:
            print(f"[INFO] Verificando estaciones en {linea}...")
            
            # Verificar si la tabla tiene las columnas necesarias
            cursor.execute(f"PRAGMA table_info({linea})")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'ultima_actualizacion_detalles' not in columnas:
                print(f"  [WARN] Tabla {linea} no tiene columna de última actualización")
                continue
            
            # Buscar estaciones sin datos detallados o con datos antiguos (más de 30 días)
            cursor.execute(f"""
                SELECT id_fijo, nombre, url 
                FROM {linea} 
                WHERE ultima_actualizacion_detalles IS NULL 
                   OR ultima_actualizacion_detalles < datetime('now', '-30 days')
                   OR direccion_completa IS NULL
                   OR correspondencias IS NULL
                   OR correspondencias = '[]'
                ORDER BY id_fijo
            """)
            
            estaciones_linea = cursor.fetchall()
            for estacion in estaciones_linea:
                estaciones_pendientes.append({
                    'linea': linea,
                    'id_fijo': estacion[0],
                    'nombre': estacion[1],
                    'url': estacion[2]
                })
            
            print(f"  [INFO] {len(estaciones_linea)} estaciones pendientes en {linea}")
        
        conn.close()
        return estaciones_pendientes
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo estaciones pendientes: {e}")
        return []

def verificar_actualizacion(linea, id_fijo, nombre):
    """Verifica que la estación se haya actualizado correctamente"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar que la estación tenga datos actualizados
        cursor.execute(f"""
            SELECT direccion_completa, accesos, servicios, vestibulos, correspondencias, ultima_actualizacion_detalles
            FROM {linea}
            WHERE id_fijo = ?
        """, (id_fijo,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            direccion, accesos, servicios, vestibulos, correspondencias, ultima_actualizacion = resultado
            
            if ultima_actualizacion:
                # Verificar que la actualización sea reciente (últimos 5 minutos)
                try:
                    fecha_actualizacion = datetime.fromisoformat(ultima_actualizacion)
                    ahora = datetime.now()
                    diferencia = ahora - fecha_actualizacion
                    
                    if diferencia.total_seconds() < 300:  # 5 minutos
                        print(f"    [OK] Estación {nombre} actualizada correctamente")
                        print(f"      Dirección: {direccion or 'No encontrada'}")
                        print(f"      Accesos: {len(accesos.split('; ')) if accesos else 0}")
                        print(f"      Servicios: {len(servicios.split('; ')) if servicios else 0}")
                        print(f"      Vestíbulos: {len(vestibulos.split('; ')) if vestibulos else 0}")
                        print(f"      Conexiones: {len(correspondencias.split('; ')) if correspondencias else 0}")
                        return True
                    else:
                        print(f"    [WARN] Estación {nombre} tiene datos antiguos")
                        return False
                except:
                    print(f"    [WARN] Error verificando fecha de actualización para {nombre}")
                    return False
            else:
                print(f"    [WARN] Estación {nombre} no tiene fecha de actualización")
                return False
        else:
            print(f"    [WARN] No se encontró la estación {nombre} en la base de datos")
            return False
            
    except Exception as e:
        print(f"    [ERROR] Error verificando actualización: {e}")
        return False

def verificar_datos_guardados():
    """Verifica que los datos se hayan guardado correctamente en la base de datos"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        print("[INFO] Verificando datos guardados en la base de datos...")
        
        # Obtener estadísticas de datos guardados
        total_estaciones = 0
        estaciones_con_servicios = 0
        estaciones_con_accesos = 0
        estaciones_con_conexiones = 0
        estaciones_completas = 0
        
        # Obtener todas las líneas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
        lineas = [row[0] for row in cursor.fetchall()]
        
        for linea in lineas:
            # Contar estaciones con diferentes tipos de datos
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN servicios IS NOT NULL AND servicios != '' AND servicios != '[]' THEN 1 ELSE 0 END) as con_servicios,
                    SUM(CASE WHEN accesos IS NOT NULL AND accesos != '' AND accesos != '[]' THEN 1 ELSE 0 END) as con_accesos,
                    SUM(CASE WHEN correspondencias IS NOT NULL AND correspondencias != '' AND correspondencias != '[]' THEN 1 ELSE 0 END) as con_conexiones,
                    SUM(CASE WHEN servicios IS NOT NULL AND servicios != '' AND servicios != '[]' 
                              AND accesos IS NOT NULL AND accesos != '' AND accesos != '[]'
                              AND correspondencias IS NOT NULL AND correspondencias != '' AND correspondencias != '[]'
                         THEN 1 ELSE 0 END) as completas
                FROM {linea}
            """)
            
            resultado = cursor.fetchone()
            if resultado:
                total, servicios, accesos, conexiones, completas = resultado
                total_estaciones += total
                estaciones_con_servicios += servicios
                estaciones_con_accesos += accesos
                estaciones_con_conexiones += conexiones
                estaciones_completas += completas
                
                print(f"  {linea}: {servicios}/{total} servicios, {accesos}/{total} accesos, {conexiones}/{total} conexiones, {completas}/{total} completas")
        
        conn.close()
        
        print(f"\n[RESUMEN] DATOS GUARDADOS:")
        print(f"  Total estaciones: {total_estaciones}")
        print(f"  Con servicios: {estaciones_con_servicios} ({estaciones_con_servicios/total_estaciones*100:.1f}%)")
        print(f"  Con accesos: {estaciones_con_accesos} ({estaciones_con_accesos/total_estaciones*100:.1f}%)")
        print(f"  Con conexiones: {estaciones_con_conexiones} ({estaciones_con_conexiones/total_estaciones*100:.1f}%)")
        print(f"  Completas (servicios + accesos + conexiones): {estaciones_completas} ({estaciones_completas/total_estaciones*100:.1f}%)")
        
        # Mostrar algunas estaciones con conexiones como ejemplo
        print(f"\n[EJEMPLOS] Estaciones con conexiones encontradas:")
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        for linea in lineas[:3]:  # Solo las primeras 3 líneas para no saturar
            cursor.execute(f"""
                SELECT nombre, correspondencias 
                FROM {linea} 
                WHERE correspondencias IS NOT NULL 
                AND correspondencias != '' 
                AND correspondencias != '[]'
                LIMIT 2
            """)
            
            ejemplos = cursor.fetchall()
            for nombre, conexiones in ejemplos:
                print(f"  {nombre} ({linea}): {conexiones}")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Error verificando datos guardados: {e}")

def ejecutar_scraper_completo():
    """Ejecuta el scraper completo para todas las estaciones pendientes"""
    print("=== SCRAPER COMPLETO DE DATOS DETALLADOS ===")
    print(f"Iniciando: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Inicializar scraper
    scraper = ScraperDatosDetallados()
    
    # Obtener estaciones pendientes
    estaciones_pendientes = obtener_estaciones_pendientes()
    
    if not estaciones_pendientes:
        print("[INFO] No hay estaciones pendientes de actualización")
        return
    
    print(f"\n[INFO] Total de estaciones pendientes: {len(estaciones_pendientes)}")
    
    # Estadísticas
    estaciones_procesadas = 0
    estaciones_exitosas = 0
    estaciones_fallidas = 0
    
    # Procesar cada estación
    for i, estacion in enumerate(estaciones_pendientes, 1):
        linea = estacion['linea']
        id_fijo = estacion['id_fijo']
        nombre = estacion['nombre']
        url = estacion['url']
        
        print(f"\n[{i}/{len(estaciones_pendientes)}] Procesando: {nombre} ({linea}, ID: {id_fijo})")
        
        try:
            # Scrapear estación
            datos = scraper.scrape_estacion_detallada(url)
            
            if datos:
                # Actualizar base de datos
                if scraper.actualizar_estacion_detallada(linea, id_fijo, datos):
                    # Verificar actualización
                    if verificar_actualizacion(linea, id_fijo, nombre):
                        estaciones_exitosas += 1
                        print(f"    [SUCCESS] Estación {nombre} procesada y verificada correctamente")
                    else:
                        estaciones_fallidas += 1
                        print(f"    [FAIL] Estación {nombre} no se verificó correctamente")
                else:
                    estaciones_fallidas += 1
                    print(f"    [FAIL] Error actualizando estación {nombre} en la base de datos")
            else:
                estaciones_fallidas += 1
                print(f"    [FAIL] No se obtuvieron datos para la estación {nombre}")
            
            estaciones_procesadas += 1
            
            # Pausa reducida entre estaciones para mayor velocidad
            if i < len(estaciones_pendientes):
                print(f"    [INFO] Esperando 1 segundo antes de la siguiente estación...")
                time.sleep(1)  # Reducido de 3 a 1 segundo
            
        except Exception as e:
            estaciones_fallidas += 1
            estaciones_procesadas += 1
            print(f"    [ERROR] Error procesando estación {nombre}: {e}")
            continue
    
    # Resumen final
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Estaciones procesadas: {estaciones_procesadas}")
    print(f"Estaciones exitosas: {estaciones_exitosas}")
    print(f"Estaciones fallidas: {estaciones_fallidas}")
    print(f"Tasa de éxito: {(estaciones_exitosas/estaciones_procesadas*100):.1f}%" if estaciones_procesadas > 0 else "N/A")
    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar que los datos se guardaron correctamente
    print(f"\n=== VERIFICACIÓN DE DATOS GUARDADOS ===")
    verificar_datos_guardados()

if __name__ == "__main__":
    ejecutar_scraper_completo() 