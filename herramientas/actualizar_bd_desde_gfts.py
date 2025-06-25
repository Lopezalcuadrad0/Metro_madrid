#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACTUALIZAR BASE DE DATOS DESDE GTFS
===================================

Actualiza la base de datos con información completa del archivo GTFS stops.txt
Incluye estaciones, accesos, accesibilidad y coordenadas exactas.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

def actualizar_bd_desde_gtfs():
    """Actualiza la base de datos con información del archivo GTFS"""
    
    print("🔄 ACTUALIZANDO BASE DE DATOS DESDE GTFS")
    print("=" * 60)
    
    # 1. Leer archivo GTFS
    print("\n📖 Leyendo archivo GTFS stops.txt...")
    try:
        df_gtfs = pd.read_csv('M4/stops.txt')
        print(f"✅ Cargadas {len(df_gtfs)} filas del archivo GTFS")
    except Exception as e:
        print(f"❌ Error leyendo archivo GTFS: {e}")
        return False
    
    # 2. Conectar a la base de datos
    print("\n🗄️ Conectando a la base de datos...")
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        print("✅ Conexión establecida")
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False
    
    # 3. Crear tabla de estaciones GTFS
    print("\n🏗️ Creando tabla de estaciones GTFS...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estaciones_gtfs (
                stop_id TEXT PRIMARY KEY,
                stop_code TEXT,
                stop_name TEXT,
                stop_desc TEXT,
                stop_lat REAL,
                stop_lon REAL,
                zone_id TEXT,
                stop_url TEXT,
                location_type INTEGER,
                parent_station TEXT,
                stop_timezone TEXT,
                wheelchair_boarding INTEGER,
                accesible_silla_ruedas BOOLEAN,
                tipo_registro TEXT,
                linea TEXT,
                ultima_actualizacion TEXT
            )
        """)
        print("✅ Tabla estaciones_gtfs creada/verificada")
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False
    
    # 4. Crear tabla de accesos
    print("\n🏗️ Creando tabla de accesos...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accesos_estaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stop_id TEXT,
                estacion_principal TEXT,
                nombre_acceso TEXT,
                direccion TEXT,
                latitud REAL,
                longitud REAL,
                tipo_acceso TEXT,
                accesible_silla_ruedas BOOLEAN,
                linea TEXT,
                ultima_actualizacion TEXT,
                FOREIGN KEY (stop_id) REFERENCES estaciones_gtfs (stop_id)
            )
        """)
        print("✅ Tabla accesos_estaciones creada/verificada")
    except Exception as e:
        print(f"❌ Error creando tabla accesos: {e}")
        return False
    
    # 5. Procesar datos GTFS
    print("\n🔄 Procesando datos GTFS...")
    
    # Limpiar tablas existentes
    cursor.execute("DELETE FROM estaciones_gtfs")
    cursor.execute("DELETE FROM accesos_estaciones")
    
    estaciones_procesadas = 0
    accesos_procesados = 0
    
    for _, row in df_gtfs.iterrows():
        stop_id = row['stop_id']
        stop_name = row['stop_name']
        stop_desc = row['stop_desc']
        stop_lat = row['stop_lat']
        stop_lon = row['stop_lon']
        location_type = row['location_type']
        wheelchair_boarding = row['wheelchair_boarding']
        
        # Convertir wheelchair_boarding a booleano
        # 0 = No accesible, 2 = Accesible
        accesible_silla_ruedas = (wheelchair_boarding == 2)
        
        # Determinar tipo de registro y línea
        if stop_id.startswith('par_4_'):
            tipo_registro = 'parada'
            linea = '4'
        elif stop_id.startswith('acc_4_'):
            tipo_registro = 'acceso'
            linea = '4'
        elif stop_id.startswith('est_90_'):
            tipo_registro = 'intercambio'
            linea = 'intercambio'
        else:
            tipo_registro = 'otro'
            linea = 'desconocida'
        
        # Insertar en estaciones_gtfs
        cursor.execute("""
            INSERT INTO estaciones_gtfs (
                stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon,
                zone_id, stop_url, location_type, parent_station, stop_timezone,
                wheelchair_boarding, accesible_silla_ruedas, tipo_registro, linea, ultima_actualizacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stop_id, row['stop_code'], stop_name, stop_desc, stop_lat, stop_lon,
            row['zone_id'], row['stop_url'], location_type, row['parent_station'],
            row['stop_timezone'], wheelchair_boarding, accesible_silla_ruedas, tipo_registro, linea,
            datetime.now().isoformat()
        ))
        estaciones_procesadas += 1
        
        # Si es un acceso, insertar también en tabla de accesos
        if tipo_registro == 'acceso':
            # Extraer nombre de la estación principal del parent_station
            estacion_principal = row['parent_station'] if row['parent_station'] else 'Desconocida'
            
            # Determinar tipo de acceso basado en el nombre
            nombre_acceso = stop_name
            if 'ascensor' in nombre_acceso.lower():
                tipo_acceso = 'ascensor'
            elif 'intercambiador' in nombre_acceso.lower():
                tipo_acceso = 'intercambiador'
            elif 'rampa' in nombre_acceso.lower():
                tipo_acceso = 'rampa'
            else:
                tipo_acceso = 'vestíbulo'
            
            cursor.execute("""
                INSERT INTO accesos_estaciones (
                    stop_id, estacion_principal, nombre_acceso, direccion,
                    latitud, longitud, tipo_acceso, accesible_silla_ruedas,
                    linea, ultima_actualizacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stop_id, estacion_principal, nombre_acceso, stop_desc,
                stop_lat, stop_lon, tipo_acceso, accesible_silla_ruedas,
                linea, datetime.now().isoformat()
            ))
            accesos_procesados += 1
    
    # 6. Crear índices para mejorar rendimiento
    print("\n🔍 Creando índices...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estaciones_tipo ON estaciones_gtfs(tipo_registro)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estaciones_linea ON estaciones_gtfs(linea)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_estaciones_accesible ON estaciones_gtfs(accesible_silla_ruedas)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accesos_estacion ON accesos_estaciones(estacion_principal)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accesos_tipo ON accesos_estaciones(tipo_acceso)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accesos_coords ON accesos_estaciones(latitud, longitud)")
        print("✅ Índices creados")
    except Exception as e:
        print(f"⚠️ Error creando índices: {e}")
    
    # 7. Commit y cerrar conexión
    conn.commit()
    conn.close()
    
    # 8. Mostrar estadísticas
    print(f"\n📊 ESTADÍSTICAS DE ACTUALIZACIÓN")
    print("-" * 40)
    print(f"Total registros GTFS: {len(df_gtfs)}")
    print(f"Estaciones procesadas: {estaciones_procesadas}")
    print(f"Accesos procesados: {accesos_procesados}")
    
    # 9. Mostrar resumen por tipo
    print(f"\n📋 RESUMEN POR TIPO:")
    df_tipos = df_gtfs['stop_id'].str.extract(r'^(\w+)_')[0].value_counts()
    for tipo, cantidad in df_tipos.items():
        print(f"  {tipo}: {cantidad} registros")
    
    # 10. Mostrar accesibilidad
    print(f"\n♿ ACCESIBILIDAD:")
    df_wheelchair = df_gtfs['wheelchair_boarding'].value_counts()
    for codigo, cantidad in df_wheelchair.items():
        significado = {
            0: 'No accesible',
            2: 'Accesible'
        }.get(codigo, f'Código {codigo}')
        print(f"  {significado}: {cantidad} registros")
    
    # 11. Mostrar coordenadas disponibles
    print(f"\n🗺️ COORDENADAS:")
    coordenadas_validas = df_gtfs[(df_gtfs['stop_lat'].notna()) & (df_gtfs['stop_lon'].notna())]
    print(f"  Registros con coordenadas: {len(coordenadas_validas)}")
    print(f"  Registros sin coordenadas: {len(df_gtfs) - len(coordenadas_validas)}")
    
    # 12. Mostrar direcciones disponibles
    print(f"\n📍 DIRECCIONES:")
    direcciones_validas = df_gtfs[df_gtfs['stop_desc'].notna() & (df_gtfs['stop_desc'] != '')]
    print(f"  Registros con direcciones: {len(direcciones_validas)}")
    print(f"  Registros sin direcciones: {len(df_gtfs) - len(direcciones_validas)}")
    
    print(f"\n✅ Base de datos actualizada exitosamente!")
    print(f"📁 Archivo fuente: M4/stops.txt")
    print(f"🗄️ Base de datos: db/estaciones_fijas_v2.db")
    print(f"🗺️ Coordenadas listas para mostrar en mapa")
    print(f"📍 Direcciones disponibles para mostrar")
    
    return True

def verificar_actualizacion():
    """Verifica que la actualización se realizó correctamente"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        
        # Verificar estaciones
        df_estaciones = pd.read_sql_query("""
            SELECT tipo_registro, COUNT(*) as cantidad 
            FROM estaciones_gtfs 
            GROUP BY tipo_registro
        """, conn)
        
        # Verificar accesos
        df_accesos = pd.read_sql_query("""
            SELECT tipo_acceso, COUNT(*) as cantidad 
            FROM accesos_estaciones 
            GROUP BY tipo_acceso
        """, conn)
        
        # Verificar accesibilidad
        df_accesibilidad = pd.read_sql_query("""
            SELECT accesible_silla_ruedas, COUNT(*) as cantidad 
            FROM estaciones_gtfs 
            GROUP BY accesible_silla_ruedas
        """, conn)
        
        print(f"\n🔍 VERIFICACIÓN DE ACTUALIZACIÓN")
        print("=" * 40)
        print(f"Estaciones por tipo:")
        for _, row in df_estaciones.iterrows():
            print(f"  {row['tipo_registro']}: {row['cantidad']}")
        
        print(f"\nAccesos por tipo:")
        for _, row in df_accesos.iterrows():
            print(f"  {row['tipo_acceso']}: {row['cantidad']}")
        
        print(f"\nAccesibilidad:")
        for _, row in df_accesibilidad.iterrows():
            estado = "Accesible" if row['accesible_silla_ruedas'] else "No accesible"
            print(f"  {estado}: {row['cantidad']}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error verificando actualización: {e}")
        return False

if __name__ == "__main__":
    if actualizar_bd_desde_gtfs():
        verificar_actualizacion()
    else:
        print("❌ Error en la actualización")
