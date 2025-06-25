#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear la base de datos GTFS del Metro de Madrid
a partir de los archivos CSV existentes.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

def create_gtfs_database():
    """Crea la base de datos GTFS del Metro de Madrid"""
    
    # Ruta de la base de datos
    db_path = "metro_madrid.db"
    
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Base de datos existente eliminada: {db_path}")
    
    # Crear conexión
    conn = sqlite3.connect(db_path)
    print(f"🔧 Creando base de datos GTFS: {db_path}")
    
    try:
        # Cargar archivos CSV
        print("📂 Cargando archivos CSV...")
        
        # Agency
        agency_df = pd.read_csv("agency.txt")
        agency_df.to_sql('agency', conn, if_exists='replace', index=False)
        print(f"✅ Agency: {len(agency_df)} registros")
        
        # Calendar
        calendar_df = pd.read_csv("calendar.txt")
        calendar_df.to_sql('calendar', conn, if_exists='replace', index=False)
        print(f"✅ Calendar: {len(calendar_df)} registros")
        
        # Calendar Dates
        calendar_dates_df = pd.read_csv("calendar_dates.txt")
        calendar_dates_df.to_sql('calendar_dates', conn, if_exists='replace', index=False)
        print(f"✅ Calendar Dates: {len(calendar_dates_df)} registros")
        
        # Fare Attributes
        fare_attributes_df = pd.read_csv("fare_attributes.txt")
        fare_attributes_df.to_sql('fare_attributes', conn, if_exists='replace', index=False)
        print(f"✅ Fare Attributes: {len(fare_attributes_df)} registros")
        
        # Fare Rules
        fare_rules_df = pd.read_csv("fare_rules.txt")
        fare_rules_df.to_sql('fare_rules', conn, if_exists='replace', index=False)
        print(f"✅ Fare Rules: {len(fare_rules_df)} registros")
        
        # Feed Info
        feed_info_df = pd.read_csv("feed_info.txt")
        feed_info_df.to_sql('feed_info', conn, if_exists='replace', index=False)
        print(f"✅ Feed Info: {len(feed_info_df)} registros")
        
        # Frequencies
        frequencies_df = pd.read_csv("frequencies.txt")
        frequencies_df.to_sql('frequencies', conn, if_exists='replace', index=False)
        print(f"✅ Frequencies: {len(frequencies_df)} registros")
        
        # Routes
        routes_df = pd.read_csv("routes.txt")
        routes_df.to_sql('routes', conn, if_exists='replace', index=False)
        print(f"✅ Routes: {len(routes_df)} registros")
        
        # Shapes
        shapes_df = pd.read_csv("shapes.txt")
        shapes_df.to_sql('shapes', conn, if_exists='replace', index=False)
        print(f"✅ Shapes: {len(shapes_df)} registros")
        
        # Stops
        stops_df = pd.read_csv("stops.txt")
        stops_df.to_sql('stops', conn, if_exists='replace', index=False)
        print(f"✅ Stops: {len(stops_df)} registros")
        
        # Stop Times
        stop_times_df = pd.read_csv("stop_times.txt")
        stop_times_df.to_sql('stop_times', conn, if_exists='replace', index=False)
        print(f"✅ Stop Times: {len(stop_times_df)} registros")
        
        # Trips
        trips_df = pd.read_csv("trips.txt")
        trips_df.to_sql('trips', conn, if_exists='replace', index=False)
        print(f"✅ Trips: {len(trips_df)} registros")
        
        # Crear índices para mejorar el rendimiento
        print("🔍 Creando índices...")
        
        # Índices para stops
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stops_stop_id ON stops(stop_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stops_stop_name ON stops(stop_name)")
        
        # Índices para routes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_routes_route_id ON routes(route_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_routes_route_short_name ON routes(route_short_name)")
        
        # Índices para trips
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips(route_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_trip_id ON trips(trip_id)")
        
        # Índices para stop_times
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_trip_id ON stop_times(trip_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_stop_id ON stop_times(stop_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stop_times_arrival_time ON stop_times(arrival_time)")
        
        # Índices para shapes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shapes_shape_id ON shapes(shape_id)")
        
        # Verificar tablas creadas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📊 Tablas creadas en la base de datos:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   • {table[0]}: {count} registros")
        
        # Estadísticas generales
        print(f"\n🎯 Estadísticas de la base de datos GTFS:")
        print(f"   • Total de estaciones: {len(stops_df)}")
        print(f"   • Total de rutas: {len(routes_df)}")
        print(f"   • Total de viajes: {len(trips_df)}")
        print(f"   • Total de horarios: {len(stop_times_df)}")
        print(f"   • Total de shapes: {len(shapes_df)}")
        
        conn.commit()
        print(f"\n✅ Base de datos GTFS creada exitosamente: {db_path}")
        print(f"📁 Tamaño del archivo: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
        
    except Exception as e:
        print(f"❌ Error creando la base de datos: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_gtfs_data():
    """Verifica que los datos GTFS sean válidos"""
    
    print("\n🔍 Verificando datos GTFS...")
    
    try:
        conn = sqlite3.connect("metro_madrid.db")
        
        # Verificar que las estaciones tengan coordenadas
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stops WHERE stop_lat IS NULL OR stop_lon IS NULL")
        null_coords = cursor.fetchone()[0]
        
        if null_coords == 0:
            print("✅ Todas las estaciones tienen coordenadas válidas")
        else:
            print(f"⚠️ {null_coords} estaciones sin coordenadas")
        
        # Verificar que las rutas tengan colores
        cursor.execute("SELECT COUNT(*) FROM routes WHERE route_color IS NULL")
        null_colors = cursor.fetchone()[0]
        
        if null_colors == 0:
            print("✅ Todas las rutas tienen colores definidos")
        else:
            print(f"⚠️ {null_colors} rutas sin colores")
        
        # Verificar horarios
        cursor.execute("SELECT COUNT(*) FROM stop_times WHERE arrival_time IS NULL")
        null_times = cursor.fetchone()[0]
        
        if null_times == 0:
            print("✅ Todos los horarios tienen tiempos de llegada")
        else:
            print(f"⚠️ {null_times} horarios sin tiempos de llegada")
        
        # Mostrar algunas líneas disponibles
        cursor.execute("SELECT route_short_name, route_long_name, route_color FROM routes ORDER BY route_short_name")
        routes = cursor.fetchall()
        
        print(f"\n🚇 Líneas disponibles en GTFS:")
        for route in routes[:10]:  # Mostrar solo las primeras 10
            print(f"   • Línea {route[0]}: {route[1]} (Color: {route[2]})")
        
        if len(routes) > 10:
            print(f"   ... y {len(routes) - 10} líneas más")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")

if __name__ == "__main__":
    print("🚇 CREANDO BASE DE DATOS GTFS DEL METRO DE MADRID")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("agency.txt"):
        print("❌ Error: No se encontró agency.txt")
        print("   Asegúrate de ejecutar este script desde el directorio M4/")
        exit(1)
    
    # Crear base de datos
    create_gtfs_database()
    
    # Verificar datos
    verify_gtfs_data()
    
    print("\n🎉 ¡Base de datos GTFS lista para usar!")
    print("   La aplicación ahora podrá mostrar horarios y rutas GTFS.") 