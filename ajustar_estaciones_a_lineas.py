import json
import sqlite3
import math
from shapely.geometry import Point, LineString
import numpy as np

def distancia_punto_a_linea(punto, linea):
    """
    Calcula la distancia mínima de un punto a una línea (polilínea).
    Retorna la distancia y el punto más cercano en la línea.
    """
    punto_shapely = Point(punto)
    linea_shapely = LineString(linea)
    
    # Encontrar el punto más cercano en la línea
    punto_cercano = linea_shapely.interpolate(linea_shapely.project(punto_shapely))
    
    # Calcular distancia
    distancia = punto_shapely.distance(punto_cercano)
    
    return distancia, (punto_cercano.x, punto_cercano.y)

def ajustar_estaciones_a_lineas():
    """
    Ajusta las coordenadas de las estaciones para que se alineen con las líneas del metro.
    Lee desde la base de datos GTFS y ajusta según metro_routes.json
    """
    
    print("🔄 Iniciando ajuste de coordenadas de estaciones...")
    
    # --- 1. Conectar a la base de datos GTFS ---
    try:
        conn_gtfs = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor_gtfs = conn_gtfs.cursor()
        print("✅ Conexión a base de datos estaciones_fijas_v2 establecida")
    except sqlite3.Error as e:
        print(f"❌ Error al conectar con la base de datos estaciones_fijas_v2: {e}")
        return
    
    # --- 2. Cargar rutas de líneas ---
    try:
        with open('static/data/metro_routes.json', 'r', encoding='utf-8') as f:
            rutas_metro = json.load(f)
        print("✅ Rutas de metro cargadas correctamente")
    except FileNotFoundError:
        print("❌ Error: No se encontró static/data/metro_routes.json")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON de rutas: {e}")
        return
    
    # --- 3. Preparar diccionario de rutas por línea ---
    rutas_por_linea = {}
    for linea in rutas_metro.get('lines', []):
        linea_id = str(linea.get('line'))
        if linea_id and 'paths' in linea:
            if linea_id not in rutas_por_linea:
                rutas_por_linea[linea_id] = []
            # Convertir paths a formato (lon, lat) para Shapely
            for path in linea['paths']:
                rutas_por_linea[linea_id].append([(coord[1], coord[0]) for coord in path])
    
    print(f"📊 Procesando {len(rutas_por_linea)} líneas con rutas")
    
    # --- 4. Obtener estaciones de la base de datos ---
    try:
        cursor_gtfs.execute('''
            SELECT DISTINCT nombre, latitud, longitud 
            FROM estaciones_completas 
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
            ORDER BY nombre
        ''')
        estaciones_db = cursor_gtfs.fetchall()
        print(f"✅ Se encontraron {len(estaciones_db)} estaciones en la base de datos")
    except sqlite3.Error as e:
        print(f"❌ Error al consultar estaciones: {e}")
        conn_gtfs.close()
        return
    
    # --- 5. Procesar cada estación ---
    estaciones_ajustadas = 0
    estaciones_sin_cambios = 0
    cambios_realizados = []
    
    for nombre, lat_original, lon_original in estaciones_db:
        punto_original = (lon_original, lat_original)  # Shapely usa (lon, lat)
        
        # Buscar en qué líneas está esta estación
        lineas_estacion = []
        for linea_id, rutas in rutas_por_linea.items():
            distancia_minima_linea = float('inf')
            punto_cercano_linea = None
            
            for ruta in rutas:
                distancia, punto_cercano = distancia_punto_a_linea(punto_original, ruta)
                if distancia < distancia_minima_linea:
                    distancia_minima_linea = distancia
                    punto_cercano_linea = punto_cercano
            
            # Si está muy cerca (menos de 300 metros), considerar que pertenece a esta línea
            if distancia_minima_linea * 111000 < 300:  # 300 metros
                lineas_estacion.append((linea_id, distancia_minima_linea, punto_cercano_linea))
        
        if lineas_estacion:
            # Si está en múltiples líneas, usar la más cercana
            if len(lineas_estacion) > 1:
                # Ordenar por distancia y tomar la más cercana
                lineas_estacion.sort(key=lambda x: x[1])
                linea_id, distancia, punto_cercano = lineas_estacion[0]
                
                lat_ajustada = punto_cercano[1]
                lon_ajustada = punto_cercano[0]
                distancia_promedio = distancia
                lineas_str = f"L{linea_id}"
            else:
                # Solo una línea
                linea_id, distancia, punto_cercano = lineas_estacion[0]
                lat_ajustada = punto_cercano[1]
                lon_ajustada = punto_cercano[0]
                distancia_promedio = distancia
                lineas_str = f"L{linea_id}"
            
            # Calcular distancia en metros
            distancia_metros = distancia_promedio * 111000
            
            # Solo ajustar si la distancia es significativa (> 20 metros)
            if distancia_metros > 20:
                # Actualizar en la base de datos
                cursor_gtfs.execute('''
                    UPDATE estaciones_completas 
                    SET latitud = ?, longitud = ? 
                    WHERE nombre = ?
                ''', (lat_ajustada, lon_ajustada, nombre))
                
                estaciones_ajustadas += 1
                
                cambios_realizados.append({
                    'estacion': nombre,
                    'lineas': lineas_str,
                    'distancia_original_metros': round(distancia_metros, 2),
                    'coordenadas_originales': (lat_original, lon_original),
                    'coordenadas_ajustadas': (lat_ajustada, lon_ajustada)
                })
                
                print(f"  ✅ {nombre} ({lineas_str}): ajustada {distancia_metros:.1f}m")
            else:
                estaciones_sin_cambios += 1
                print(f"  ⏭️  {nombre} ({lineas_str}): ya bien posicionada ({distancia_metros:.1f}m)")
        else:
            estaciones_sin_cambios += 1
            print(f"  ❓ {nombre}: no se encontró línea cercana")
    
    # --- 6. Confirmar cambios en la base de datos ---
    conn_gtfs.commit()
    print(f"\n💾 Cambios guardados en la base de datos GTFS")
    
    # --- 7. Generar resumen ---
    print(f"\n📊 RESUMEN DEL AJUSTE:")
    print(f"   • Estaciones ajustadas: {estaciones_ajustadas}")
    print(f"   • Estaciones sin cambios: {estaciones_sin_cambios}")
    print(f"   • Total procesadas: {estaciones_ajustadas + estaciones_sin_cambios}")
    
    if cambios_realizados:
        print(f"\n🔍 CAMBIOS MÁS SIGNIFICATIVOS:")
        # Ordenar por distancia (mayor primero)
        cambios_ordenados = sorted(cambios_realizados, 
                                 key=lambda x: x['distancia_original_metros'], 
                                 reverse=True)
        
        for i, cambio in enumerate(cambios_ordenados[:10]):  # Top 10
            print(f"   {i+1}. {cambio['estacion']} ({cambio['lineas']}): "
                  f"{cambio['distancia_original_metros']}m")
    
    # --- 8. Generar CSV de resumen ---
    try:
        import csv
        with open('estaciones_ajustadas_resumen.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Estación', 'Líneas', 'Distancia_Original_m', 'Lat_Original', 'Lon_Original', 'Lat_Ajustada', 'Lon_Ajustada'])
            
            for cambio in cambios_realizados:
                writer.writerow([
                    cambio['estacion'],
                    cambio['lineas'],
                    cambio['distancia_original_metros'],
                    cambio['coordenadas_originales'][0],
                    cambio['coordenadas_originales'][1],
                    cambio['coordenadas_ajustadas'][0],
                    cambio['coordenadas_ajustadas'][1]
                ])
        print(f"📄 Resumen CSV guardado en estaciones_ajustadas_resumen.csv")
    except Exception as e:
        print(f"⚠️  No se pudo generar CSV de resumen: {e}")
    
    # --- 9. Cerrar conexión ---
    conn_gtfs.close()
    print(f"\n✅ Proceso completado exitosamente!")

if __name__ == "__main__":
    ajustar_estaciones_a_lineas() 