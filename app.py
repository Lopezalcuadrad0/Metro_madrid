#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
METRO DE MADRID - APLICACIÓN WEB COMPLETA
=========================================

Aplicación Flask para mostrar información del Metro de Madrid
con datos en tiempo real, horarios, mapas y estadísticas.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, flash
import sqlite3
import json
import os
from datetime import datetime, timedelta, time
import pandas as pd
import time
import threading
import subprocess
import sys
import re
import requests
from bs4 import BeautifulSoup
import random
import unicodedata
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from forms import RegistrationForm, LoginForm

# Importar rutas de transporte
try:
    from transport_routes import add_transport_routes
    TRANSPORT_ROUTES_AVAILABLE = True
    print("Rutas de transporte disponibles")
except ImportError:
    print("Rutas de transporte no disponibles")
    TRANSPORT_ROUTES_AVAILABLE = False

# Importar scraper Ninja
try:
    sys.path.append('herramientas')
    from scraper_ninja_tiempo_real import ScraperNinjaTiempoReal
    NINJA_SCRAPER_AVAILABLE = True
    print("Scraper Ninja disponible")
except ImportError:
    print("Scraper Ninja no disponible")
    NINJA_SCRAPER_AVAILABLE = False

# Importar scraper de accesos reales
try:
    sys.path.append('herramientas')
    from scraper_accesos_reales import ScraperAccesosReales
    ACCESOS_SCRAPER_AVAILABLE = True
    print("Scraper de accesos reales disponible")
except ImportError:
    print("Scraper de accesos reales no disponible")
    ACCESOS_SCRAPER_AVAILABLE = False

# Importar el scraper de accesos oficiales de MetroMadrid
try:
    from herramientas.scraper_accesos_metromadrid import extraer_accesos_metromadrid
    METROMADRID_ACCESOS_AVAILABLE = True
except Exception as e:
    print(f"Scraper de accesos MetroMadrid no disponible: {e}")
    METROMADRID_ACCESOS_AVAILABLE = False

# Configuración
app = Flask(__name__)
app.config['SECRET_KEY'] = 'metro_madrid_secret_key_2024'

# Inicialización de extensiones
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Ruta a la que se redirige si el usuario no está logueado
login_manager.login_message_category = 'info' # Categoría de mensaje para flash

# Clase User para Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# User loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Aquí deberías cargar el usuario desde tu base de datos
    # Por ahora, simplemente devolvemos un usuario de prueba
    return User(1, "admin")

# Añadir rutas de transporte si están disponibles
if TRANSPORT_ROUTES_AVAILABLE:
    add_transport_routes(app)
    print("✅ Funcionalidades de transporte público migradas correctamente")

# Rutas de archivos
DB_PATH = 'db/estaciones_fijas_v2.db'
DB_RELACIONAL_PATH = 'db/estaciones_fijas_v2.db'
GTFS_DB_PATH = 'M4/metro_madrid.db'
CSV_DATOS_CLAVE = 'datos_clave_estaciones_definitivo.csv'

# URL de la API oficial de BiciMAD
BICIMAD_URL = "https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.json"

def load_bicimad_data():
    """Carga los datos de BiciMAD desde la API oficial de EMT Madrid"""
    try:
        print("🔄 Cargando datos de BiciMAD desde API oficial...")
        response = requests.get(BICIMAD_URL, timeout=10)
        
        if response.status_code == 200:
            bicimad_raw = response.json()
            stations = []
            
            for feature in bicimad_raw.get('features', []):
                if feature.get('geometry') and feature.get('properties'):
                    coords = feature['geometry']['coordinates']
                    props = feature['properties']
                    
                    # Determinar estado y color basado en los datos
                    activate = props.get('Activate', 1)
                    dock_bikes = props.get('DockBikes', 0)
                    free_bases = props.get('FreeBases', 0)
                    
                    # Solo mostrar estaciones activas
                    if activate == 1:
                        # Determinar color basado en disponibilidad
                        if dock_bikes > 0 and free_bases > 0:
                            color = '#4CAF50'  # Verde: bicis y anclajes disponibles
                            status = 'disponible'
                        elif dock_bikes > 0:
                            color = '#FF9800'  # Naranja: solo bicis disponibles
                            status = 'solo_bicis'
                        elif free_bases > 0:
                            color = '#2196F3'  # Azul: solo anclajes disponibles
                            status = 'solo_anclajes'
                        else:
                            color = '#F44336'  # Rojo: sin disponibilidad
                            status = 'sin_disponibilidad'
                        
                        station_data = {
                            'name': props.get('Name', 'Estación BiciMAD'),
                            'lat': coords[1],
                            'lon': coords[0],
                            'address': props.get('Address', ''),
                            'dock_bikes': dock_bikes,
                            'free_bases': free_bases,
                            'total_bases': props.get('TotalBases', 0),
                            'status': status,
                            'color': color,
                            'icon': '🚲'
                        }
                        stations.append(station_data)
            
            print(f"✅ BiciMAD cargado: {len(stations)} estaciones activas")
            return {'stations': stations}
        else:
            print(f"❌ Error cargando BiciMAD: Status {response.status_code}")
            return {'stations': []}
            
    except Exception as e:
        print(f"❌ Error cargando BiciMAD: {e}")
        return {'stations': []}

# Importar auto-updater (si existe)
try:
    sys.path.append('config')
    from auto_updater_7min import start_auto_updater, stop_auto_updater, get_updater_status
    AUTO_UPDATER_AVAILABLE = True
except ImportError:
    print("Auto-updater no disponible")
    AUTO_UPDATER_AVAILABLE = False

# Variables globales para datos clave
datos_clave_estaciones = None
datos_clave_cargados = False

# Variables globales para GTFS
metro_data = {
    'routes': {},
    'stops': {},
    'trips': {},
    'stop_times': {},
    'shapes': {},
    'frequencies': {},
    'calendar': {},
    'calendar_dates': {}
}

# Diccionario centralizado con toda la información de las líneas
LINEAS_CONFIG = {
    '1':  {'id': '1',  'name': 'Línea 1',  'color': '#00AEEF', 'color_secondary': '#87CEEB', 'text_color': '#FFFFFF'},
    '2':  {'id': '2',  'name': 'Línea 2',  'color': '#FF0000', 'color_secondary': '#FA8072', 'text_color': '#FFFFFF'},
    '3':  {'id': '3',  'name': 'Línea 3',  'color': '#FFD700', 'color_secondary': '#FFEEAA', 'text_color': '#000000'},
    '4':  {'id': '4',  'name': 'Línea 4',  'color': '#B25400', 'color_secondary': '#E59A5C', 'text_color': '#FFFFFF'},
    '5':  {'id': '5',  'name': 'Línea 5',  'color': '#39B54A', 'color_secondary': '#98FB98', 'text_color': '#FFFFFF'},
    '6':  {'id': '6',  'name': 'Línea 6',  'color': '#9E9E9E', 'color_secondary': '#DCDCDC', 'text_color': '#FFFFFF'},
    '7':  {'id': '7',  'name': 'Línea 7',  'color': '#FF9800', 'color_secondary': '#FFD580', 'text_color': '#FFFFFF'},
    '8':  {'id': '8',  'name': 'Línea 8',  'color': '#FF69B4', 'color_secondary': '#FFB6C1', 'text_color': '#FFFFFF'},
    '9':  {'id': '9',  'name': 'Línea 9',  'color': '#9C27B0', 'color_secondary': '#D8BFD8', 'text_color': '#FFFFFF'},
    '10': {'id': '10', 'name': 'Línea 10', 'color': '#0D47A1', 'color_secondary': '#6495ED', 'text_color': '#FFFFFF'},
    '11': {'id': '11', 'name': 'Línea 11', 'color': '#006400', 'color_secondary': '#66CDAA', 'text_color': '#FFFFFF'},
    '12': {'id': '12', 'name': 'Línea 12', 'color': '#a49a00', 'color_secondary': '#D2CB7E', 'text_color': '#FFFFFF'},
    'R':  {'id': 'R',  'name': 'Ramal',    'color': '#0055A4', 'color_secondary': '#4A90E2', 'text_color': '#FFFFFF'},
    # Metro Ligero
    'ML1': {'id': 'ML1', 'name': 'Metro Ligero 1', 'color': '#70C5E8', 'color_secondary': '#B8DDF0', 'text_color': '#FFFFFF', 'type': 'metro_ligero', 'stations_count': 16, 'length_km': '5.4'},
    'ML2': {'id': 'ML2', 'name': 'Metro Ligero 2', 'color': '#9B4782', 'color_secondary': '#C08FB2', 'text_color': '#FFFFFF', 'type': 'metro_ligero', 'stations_count': 13, 'length_km': '8.7'},
    'ML3': {'id': 'ML3', 'name': 'Metro Ligero 3', 'color': '#DE1E40', 'color_secondary': '#E86B85', 'text_color': '#FFFFFF', 'type': 'metro_ligero', 'stations_count': 16, 'length_km': '13.7'}
}

# Configuración de Cercanías Madrid
CERCANIAS_CONFIG = {
    'C-1': {'id': 'C-1', 'name': 'C-1', 'color': '#70C5E8', 'color_secondary': '#B8DDF0', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Chamartín - Aeropuerto T4', 'stations_count': 17, 'length_km': '36.9'},
    'C-2': {'id': 'C-2', 'name': 'C-2', 'color': '#00B04F', 'color_secondary': '#66D485', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Guadalajara – Alcalá de Henares – Atocha – Chamartín', 'stations_count': 15, 'length_km': '85.2'},
    'C-3': {'id': 'C-3', 'name': 'C-3', 'color': '#9B4782', 'color_secondary': '#C08FB2', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Aranjuez – Atocha – Sol - Chamartín', 'stations_count': 22, 'length_km': '62.8'},
    'C-4': {'id': 'C-4', 'name': 'C-4', 'color': '#004E98', 'color_secondary': '#4A7BC8', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Atocha - Sol - Chamartín – Cantoblanco', 'stations_count': 12, 'length_km': '25.1'},
    'C-5': {'id': 'C-5', 'name': 'C-5', 'color': '#F2C500', 'color_secondary': '#F6D84A', 'text_color': '#000000', 'type': 'cercanias', 'description': 'Móstoles El Soto – Atocha – Fuenlabrada - Humanes', 'stations_count': 18, 'length_km': '34.7'},
    'C-7': {'id': 'C-7', 'name': 'C-7', 'color': '#DE1E40', 'color_secondary': '#E86B85', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Alcalá de Henares – Atocha – Chamartín – P. Pío', 'stations_count': 16, 'length_km': '42.3'},
    'C-8': {'id': 'C-8', 'name': 'C-8', 'color': '#808080', 'color_secondary': '#B3B3B3', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Guadalajara- Alcalá de Henares-Atocha-Chamartín – Villalba', 'stations_count': 24, 'length_km': '118.4'},
    'C-9': {'id': 'C-9', 'name': 'C-9', 'color': '#F09600', 'color_secondary': '#F5B84A', 'text_color': '#FFFFFF', 'type': 'cercanias', 'description': 'Cercedilla – Cotos', 'stations_count': 8, 'length_km': '18.2'},
    'C-10': {'id': 'C-10', 'name': 'C-10', 'color': '#B0D136', 'color_secondary': '#C8E066', 'text_color': '#000000', 'type': 'cercanias', 'description': 'Villalba – Príncipe Pío – Atocha – Recoletos - Chamartín', 'stations_count': 20, 'length_km': '58.7'}
}

# ============================================================================
# FUNCIONES DE CARGA DE DATOS CLAVE (OPCIONAL)
# ============================================================================

def cargar_datos_clave():
    """Carga los datos clave desde el CSV al inicio de la aplicación (OPCIONAL)"""
    global datos_clave_estaciones, datos_clave_cargados
    try:
        print(f" Intentando cargar datos clave desde: {CSV_DATOS_CLAVE}")
        print(f" Ruta absoluta: {os.path.abspath(CSV_DATOS_CLAVE)}")
        print(f"¿Existe el archivo?: {os.path.exists(CSV_DATOS_CLAVE)}")
        
        if not os.path.exists(CSV_DATOS_CLAVE):
            print(f"No se encontró el CSV de datos clave: {CSV_DATOS_CLAVE}")
            print("El sistema funcionará sin el CSV, usando búsqueda en base de datos")
            return False
        
        print("Cargando CSV...")
        # Cargar CSV
        datos_clave_estaciones = pd.read_csv(CSV_DATOS_CLAVE, encoding='utf-8')
        print(f"SV cargado: {len(datos_clave_estaciones)} filas")
        
        # Recalcular SIEMPRE la columna normalizada
        print("Calculando columna normalizada...")
        datos_clave_estaciones['nombre_normalizado'] = (
            datos_clave_estaciones['nombre']
            .str.lower()
            .str.normalize('NFD')
            .str.encode('ascii', errors='ignore')
            .str.decode('utf-8')
        )
        
        datos_clave_cargados = True
        print(f" Datos clave cargados exitosamente. Total: {len(datos_clave_estaciones)} estaciones")
        return True
    except Exception as e:
        print(f" Error cargando datos clave: {e}")
        import traceback
        traceback.print_exc()
        print("El sistema funcionará sin el CSV, usando búsqueda en base de datos")
        return False

def buscar_estacion_por_nombre(nombre_busqueda, limite=10):
    """Busca estaciones por nombre usando los datos clave cargados o base de datos"""
    global datos_clave_estaciones, datos_clave_cargados
    if not datos_clave_cargados or datos_clave_estaciones is None:
        print("Usando busqueda en base de datos (mas lenta pero funcional)")
        return buscar_estacion_por_nombre_db(nombre_busqueda, limite)
    try:
        # Normalizar nombre de búsqueda
        nombre_normalizado = nombre_busqueda.lower()
        nombre_normalizado = unicodedata.normalize('NFD', nombre_normalizado).encode('ascii', errors='ignore').decode('utf-8')
        
        # Búsqueda en la columna 'nombre' (que sí existe en el CSV)
        # Búsqueda exacta
        exacta = datos_clave_estaciones[datos_clave_estaciones['nombre'].str.lower() == nombre_busqueda.lower()]
        # Búsqueda parcial
        parcial = datos_clave_estaciones[datos_clave_estaciones['nombre'].str.lower().str.contains(nombre_busqueda.lower(), na=False)]
        
        # Combinar resultados
        resultados = pd.concat([exacta, parcial]).drop_duplicates(subset=['id_fijo', 'linea']).head(limite)
        
        # Convertir a lista de diccionarios
        estaciones = []
        for _, row in resultados.iterrows():
            estacion = {
                'id_fijo': int(row['id_fijo']),
                'nombre': row['nombre'],
                'linea': row['linea'],
                'orden': int(row['orden']) if pd.notna(row['orden']) else None,
                'url': row['url'] if pd.notna(row['url']) else None,
                'id_modal': int(row['id_modal']) if pd.notna(row['id_modal']) else None,
                'zona_tarifaria': row['zona'] if pd.notna(row['zona']) else None,
                'estacion_accesible': row['accesible'] if pd.notna(row['accesible']) else None,
                'tabla_origen': row['tabla_origen']
            }
            estaciones.append(estacion)
        return estaciones
    except Exception as e:
        print(f"ERROR en busqueda por nombre: {e}")
        return []

def buscar_estacion_por_nombre_db(nombre_busqueda, limite=10):
    """Búsqueda alternativa en base de datos si no hay datos clave"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Normalizar nombre de búsqueda (igual que en la función principal)
        nombre_normalizado = nombre_busqueda.lower()
        nombre_normalizado = unicodedata.normalize('NFD', nombre_normalizado).encode('ascii', errors='ignore').decode('utf-8')
        
        # Lista de tablas de líneas
        lineas_tablas = [
            'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
            'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
        ]
        
        estaciones = []
        
        for tabla in lineas_tablas:
            # Usar búsqueda más flexible que incluya normalización
            query = f"""
            SELECT id_fijo, nombre, orden, url, id_modal, direccion_ida, direccion_vuelta
            FROM {tabla}
            WHERE LOWER(nombre) LIKE LOWER(?)
               OR LOWER(REPLACE(REPLACE(REPLACE(nombre, 'á', 'a'), 'é', 'e'), 'Ã­', 'i')) LIKE LOWER(?)
               OR LOWER(REPLACE(REPLACE(REPLACE(nombre, 'ó', 'o'), 'ú', 'u'), 'ñ', 'n')) LIKE LOWER(?)
            ORDER BY orden
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[f'%{nombre_busqueda}%', f'%{nombre_normalizado}%', f'%{nombre_normalizado}%', limite])
            
            if not df.empty:
                for _, row in df.iterrows():
                    estacion = {
                        'id_fijo': int(row['id_fijo']),
                        'nombre': row['nombre'],
                        'linea': tabla.replace('linea_', ''),
                        'orden': int(row['orden']) if pd.notna(row['orden']) else None,
                        'url': row['url'] if pd.notna(row['url']) else None,
                        'id_modal': int(row['id_modal']) if pd.notna(row['id_modal']) else None,
                        'direccion_ida': row['direccion_ida'] if pd.notna(row['direccion_ida']) else None,
                        'direccion_vuelta': row['direccion_vuelta'] if pd.notna(row['direccion_vuelta']) else None,
                        'tabla_origen': tabla
                    }
                    estaciones.append(estacion)
        
        conn.close()
        return estaciones[:limite]
        
    except Exception as e:
        print(f" Error en búsqueda en base de datos: {e}")
        return []

def obtener_datos_estacion_completos(id_fijo, tabla_origen):
    """Obtiene datos completos de una estación desde la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        query = f"""
        SELECT *
        FROM {tabla_origen}
        WHERE id_fijo = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[id_fijo])
        conn.close()
        
        if not df.empty:
            return df.iloc[0].to_dict()
        else:
            return None
            
    except Exception as e:
        print(f" Error obteniendo datos completos: {e}")
        return None

# ============================================================================
# FUNCIONES GTFS
# ============================================================================

def load_gtfs_data():
    """Carga los datos GTFS desde la base de datos"""
    try:
        if not os.path.exists(GTFS_DB_PATH):
            print(f" No se encontró la base de datos GTFS: {GTFS_DB_PATH}")
            return False
        
        conn = sqlite3.connect(GTFS_DB_PATH)
        
        df_routes = pd.read_sql_query("SELECT * FROM routes", conn)
        for _, row in df_routes.iterrows():
            metro_data['routes'][row['route_id']] = row.to_dict()
        
        df_stops = pd.read_sql_query("SELECT * FROM stops", conn)
        for _, row in df_stops.iterrows():
            metro_data['stops'][row['stop_id']] = row.to_dict()
        
        df_trips = pd.read_sql_query("SELECT * FROM trips", conn)
        for _, row in df_trips.iterrows():
            metro_data['trips'][row['trip_id']] = row.to_dict()
        
        df_stop_times = pd.read_sql_query("SELECT * FROM stop_times ORDER BY trip_id, stop_sequence", conn)
        for trip_id, group in df_stop_times.groupby('trip_id'):
            metro_data['stop_times'][trip_id] = group.to_dict('records')
        
        try:
            df_frequencies = pd.read_sql_query("SELECT * FROM frequencies", conn)
            for trip_id, group in df_frequencies.groupby('trip_id'):
                metro_data['frequencies'][trip_id] = group.to_dict('records')
        except:
            print("Tabla frequencies no encontrada")
        
        try:
            df_shapes = pd.read_sql_query("SELECT * FROM shapes ORDER BY shape_id, shape_pt_sequence", conn)
            for shape_id, group in df_shapes.groupby('shape_id'):
                metro_data['shapes'][shape_id] = group.to_dict('records')
        except:
            print("Tabla shapes no encontrada")
        
        try:
            df_calendar = pd.read_sql_query("SELECT * FROM calendar", conn)
            for _, row in df_calendar.iterrows():
                metro_data['calendar'][row['service_id']] = row.to_dict()
        except:
            print("Tabla calendar no encontrada")
        
        conn.close()
        print(f" Datos GTFS cargados: {len(metro_data['routes'])} rutas, {len(metro_data['stops'])} paradas")
        return True
        
    except Exception as e:
        print(f" Error cargando datos GTFS: {e}")
        return False

def time_to_seconds(time_str):
    """Convierte tiempo HH:MM:SS a segundos"""
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

def seconds_to_time(seconds):
    """Convierte segundos a tiempo HH:MM:SS"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_current_service_ids():
    """Obtiene los service_ids activos para hoy"""
    today = datetime.now()
    weekday = today.weekday()  # 0=Lunes, 6=Domingo
    
    active_services = []
    for service_id, calendar in metro_data['calendar'].items():
        if weekday == 0 and calendar['monday'] == 1:
            active_services.append(service_id)
        elif weekday == 1 and calendar['tuesday'] == 1:
            active_services.append(service_id)
        elif weekday == 2 and calendar['wednesday'] == 1:
            active_services.append(service_id)
        elif weekday == 3 and calendar['thursday'] == 1:
            active_services.append(service_id)
        elif weekday == 4 and calendar['friday'] == 1:
            active_services.append(service_id)
        elif weekday == 5 and calendar['saturday'] == 1:
            active_services.append(service_id)
        elif weekday == 6 and calendar['sunday'] == 1:
            active_services.append(service_id)
    
    return active_services

def get_active_trips_with_frequencies(target_time):
    """Obtiene viajes activos con frecuencias para una hora específica"""
    active_services = get_current_service_ids()
    target_seconds = time_to_seconds(target_time)
    
    active_trips = []
    
    for trip_id, trip in metro_data['trips'].items():
        if trip['service_id'] in active_services:
            # Verificar si tiene frecuencias
            if trip_id in metro_data['frequencies']:
                for freq in metro_data['frequencies'][trip_id]:
                    start_seconds = time_to_seconds(freq['start_time'])
                    end_seconds = time_to_seconds(freq['end_time'])
                    
                    if start_seconds <= target_seconds <= end_seconds:
                        # Calcular cuántos trenes han pasado
                        elapsed = target_seconds - start_seconds
                        train_count = elapsed // freq['headway_secs'] + 1
                        
                        for i in range(min(train_count, 3)):  # Máximo 3 trenes
                            trip_copy = trip.copy()
                            trip_copy['trip_id'] = f"{trip_id}_freq_{i}"
                            trip_copy['frequency'] = freq
                            trip_copy['train_number'] = i + 1
                            active_trips.append(trip_copy)
            else:
                # Viaje sin frecuencias, verificar horarios
                if trip_id in metro_data['stop_times']:
                    stop_times = metro_data['stop_times'][trip_id]
                    if stop_times:
                        first_time = time_to_seconds(stop_times[0]['departure_time'])
                        last_time = time_to_seconds(stop_times[-1]['arrival_time'])
                        
                        if first_time <= target_seconds <= last_time + 3600:  # +1 hora de margen
                            active_trips.append(trip)
    
    return active_trips

def generate_extra_trains(target_time):
    """Genera trenes adicionales para líneas principales"""
    extra_trains = []
    target_seconds = time_to_seconds(target_time)
    
    # Línea 1: Trenes cada 3-5 minutos
    for i in range(10):
        train_time = target_seconds + (i * 240)  # 4 minutos
        if train_time < target_seconds + 3600:  # Solo para la próxima hora
            extra_trains.append({
                'route_id': 'L1',
                'trip_id': f'L1_extra_{i}',
                'direction': 'ida' if i % 2 == 0 else 'vuelta',
                'departure_time': seconds_to_time(train_time),
                'headway': 240
            })
    
    # Línea 6: Trenes cada 4-6 minutos
    for i in range(8):
        train_time = target_seconds + (i * 300)  # 5 minutos
        if train_time < target_seconds + 3600:
            extra_trains.append({
                'route_id': 'L6',
                'trip_id': f'L6_extra_{i}',
                'direction': 'ida' if i % 2 == 0 else 'vuelta',
                'departure_time': seconds_to_time(train_time),
                'headway': 300
            })
    
    return extra_trains

def generate_ramal_trains(target_time):
    """Genera trenes del ramal"""
    ramal_trains = []
    target_seconds = time_to_seconds(target_time)
    
    # Ramal: Trenes cada 10-15 minutos
    for i in range(4):
        train_time = target_seconds + (i * 600)  # 10 minutos
        if train_time < target_seconds + 3600:
            ramal_trains.append({
                'route_id': 'Ramal',
                'trip_id': f'R_extra_{i}',
                'direction': 'ida' if i % 2 == 0 else 'vuelta',
                'departure_time': seconds_to_time(train_time),
                'headway': 600
            })
    
    return ramal_trains

def simulate_train_movement():
    """Simula el movimiento de trenes en tiempo real"""
    current_time = datetime.now()
    current_time_str = current_time.strftime('%H:%M:%S')
    
    # Obtener trenes activos
    active_trips = get_active_trips_with_frequencies(current_time_str)
    extra_trains = generate_extra_trains(current_time_str)
    ramal_trains = generate_ramal_trains(current_time_str)
    
    all_trains = []
    
    # Procesar trenes GTFS
    for trip in active_trips:
        if trip['trip_id'] in metro_data['stop_times']:
            stop_times = metro_data['stop_times'][trip['trip_id']]
            position = calculate_train_position(trip, current_time_str)
            
            all_trains.append({
                'trip_id': trip['trip_id'],
                'route_id': trip['route_id'],
                'position': position,
                'next_stop': get_next_stop(trip, current_time_str),
                'status': 'en_movimiento'
            })
    
    # Procesar trenes extra
    for train in extra_trains + ramal_trains:
        all_trains.append({
            'trip_id': train['trip_id'],
            'route_id': train['route_id'],
            'position': 'simulado',
            'next_stop': 'próxima_estación',
            'status': 'simulado'
        })
    
    return all_trains

def calculate_train_position(train, current_time):
    """Calcula la posición actual de un tren"""
    # Implementación simplificada
    return "entre_estaciones"

def get_next_stop(train, current_time):
    """Obtiene la próxima parada de un tren"""
    # Implementación simplificada
    return "próxima_estación"

# ============================================================================
# FUNCIONES DE BASE DE DATOS FIJA
# ============================================================================

def get_db_connection(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_stations_from_db():
    conn = get_db_connection()
    all_stations = []
    line_tables = [f'linea_{i}' for i in range(1, 13)] + ['linea_Ramal']
    for table in line_tables:
        try:
            rows = conn.execute(f'SELECT * FROM {table}').fetchall()
            for row in rows:
                all_stations.append(dict(row))
        except sqlite3.OperationalError:
            continue
    conn.close()
    return all_stations

def verificar_base_datos_fija():
    """Verifica la integridad de la base de datos de estaciones fijas"""
    print("Verificando la base de datos de estaciones fijas...")
    if not os.path.exists(DB_PATH):
        print(f" Error: No se encuentra el archivo de base de datos en {DB_PATH}")
        return False
    
    conn = get_db_connection()
    total_estaciones = 0
    lineas_ok = True
    
    line_tables = [f'linea_{i}' for i in range(1, 13)] + ['linea_Ramal']
    
    for tabla in line_tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            print(f"Línea {tabla.split('_')[-1]}: {count} estaciones")
            total_estaciones += count
        except sqlite3.OperationalError:
            print(f" Error: La tabla '{tabla}' no se encuentra en la base de datos.")
            lineas_ok = False

    conn.close()
    
    if lineas_ok and total_estaciones > 0:
        print(f" Base de datos fija verificada: {total_estaciones} estaciones totales")
        return True
    else:
        print(" Verificación de la base de datos fija fallida.")
        return False

# ============================================================================
# RUTAS DE LA APLICACIÓN
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Por ahora, aceptamos cualquier usuario/contraseña
        user = User(1, form.username.data)
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Por ahora, solo mostramos un mensaje de éxito
        flash('¡Tu cuenta ha sido creada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/line/<line_id>')
@login_required
def line_detail_view(line_id):
    """Página de detalle de una línea."""
    line_info = LINEAS_CONFIG.get(line_id)
    if not line_info:
        return "Linea no encontrada", 404
    
    # Obtener el estado de la línea
    line_status_data = None
    try:
        conn = get_db_connection('estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estado_lineas'")
        if cursor.fetchone():
            cursor.execute("SELECT estado, descripcion FROM estado_lineas WHERE linea = ? ORDER BY timestamp DESC LIMIT 1", (line_id,))
            row = cursor.fetchone()
            if row:
                line_status_data = {
                    'estado': row[0],
                    'descripcion': row[1]
                }
        conn.close()
    except Exception as e:
        print(f"Error al obtener estado de línea {line_id}: {e}")

    # Obtener otras líneas para el menú lateral
    other_lines = []
    for id, info in LINEAS_CONFIG.items():
        if id != line_id and not info.get('type') == 'metro_ligero':
            other_lines.append(info)

    # Añadir toda la información necesaria
    line_info['status'] = line_status_data
    line_info['linea'] = line_id  # Para mantener compatibilidad

    return render_template('line_detail.html', 
                         line_info=line_info,
                         other_lines=other_lines)

@app.route('/station', methods=['GET', 'POST'])
@login_required
def station_page():
    """Página de búsqueda de estaciones"""
    resultados = []
    query = ''
    
    if request.method == 'POST':
        query = request.form.get('station_name', '').strip()
    elif request.method == 'GET':
        query = request.args.get('q', '').strip()
    
    if query:
        resultados = buscar_estacion_por_nombre(query, limite=10)
    
    return render_template('station.html', resultados=resultados, query=query)

@app.route('/status')
@login_required
def status():
    return render_template('status.html')

@app.route('/account')
@login_required
def account():
    """Página de cuenta de usuario"""
    # Por ahora, devolvemos un diccionario vacío para grouped_fav_stations
    grouped_fav_stations = {}
    return render_template('account.html', grouped_fav_stations=grouped_fav_stations)

@app.route('/cercanias')
@login_required
def cercanias():
    """Vista del mapa integrado de transporte"""
    try:
        # Cargar datos de Metro
        with open('static/data/metro_con_capas.json', 'r', encoding='utf-8') as f:
            metro_raw = json.load(f)
            metro_data = transform_metro_data(metro_raw)
            print("✅ Datos de Metro cargados")

        # Cargar datos de Metro Ligero
        with open('static/data/metro_ligero_final.json', 'r', encoding='utf-8') as f:
            metro_ligero_raw = json.load(f)
            metro_ligero_data = transform_metro_data_with_layers(metro_ligero_raw)
            print("✅ Datos de Metro Ligero cargados")

        # Cargar datos de Cercanías (rutas reales)
        with open('static/data/cercanias_completo.json', 'r', encoding='utf-8') as f:
            cercanias_raw = json.load(f)
            # Transformar los datos para que el JS use estaciones y tramos
            cercanias_data = {
                'estaciones': cercanias_raw['estaciones'],
                'tramos': cercanias_raw['tramos']  # Usar tramos en lugar de rutas
            }
            print("✅ Datos de Cercanías (rutas reales) cargados: {} estaciones, {} tramos".format(len(cercanias_data['estaciones']), len(cercanias_data['tramos'])))

        # Cargar datos de BiciMAD
        bicimad_data = load_bicimad_data()

        return render_template('cercanias.html',
                            metro_data=metro_data,
                            metro_ligero_data=metro_ligero_data,
                            cercanias_data=cercanias_data,
                            bicimad_data=bicimad_data)
    except Exception as e:
        print(f'❌ Error en cercanias: {e}')
        import traceback
        traceback.print_exc()
        return render_template('cercanias.html',
                            metro_data={'stations': [], 'lines': []},
                            metro_ligero_data={'stations': [], 'lines': []},
                              cercanias_data={'estaciones': [], 'rutas': []},
                            bicimad_data={'stations': []})

@app.route('/test')
def test():
    """Endpoint de prueba simple"""
    return "✅ Flask funciona correctamente"

@app.route('/mapa-v5')
@login_required
def mapa_rutas_v5():
    """Vista del mapa de rutas v5.0"""
    return render_template('mapa_rutas_v5.html')

@app.route('/api/stations/all')
def api_stations_all():
    """API para obtener todas las estaciones desde la base de datos con coordenadas"""
    try:
        conn = get_db_connection()
        
        # Usar la tabla estaciones_completas que tiene coordenadas
        query = """
        SELECT id_fijo, nombre, linea, orden_en_linea, latitud, longitud, 
               zona_tarifaria, estacion_accesible, correspondencias, 
               direccion_completa, calle, distrito, barrio
            FROM estaciones_completas 
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
            ORDER BY linea, orden_en_linea
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        estaciones = []
        for row in rows:
            estacion = {
                'id': row[0],
                'name': row[1],
                'line': row[2],
                'order': row[3],
                'lat': float(row[4]),
                'lon': float(row[5]),
                'zone': row[6],
                'accessible': row[7],
                'connections': row[8],
                'address': row[9],
                'street': row[10],
                'district': row[11],
                'neighborhood': row[12]
            }
            estaciones.append(estacion)
        
        conn.close()
        
        print(f"✅ API stations/all: {len(estaciones)} estaciones desde BD con coordenadas")
        return jsonify(estaciones)
        
    except Exception as e:
        print(f"❌ Error en API stations/all (BD): {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/lines/all')
def api_lines_all():
    """API para obtener todas las líneas"""
    try:
        lines_data = []
        
        # Líneas de Metro
        for line_id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
            line_info = LINEAS_CONFIG.get(line_id, {})
            line_data = {
                'id': line_id,
                'name': line_info.get('name', f'Línea {line_id}'),
                'color': line_info.get('color', '#00AA66'),
                'type': 'metro',
                'stations': [],
                'coordinates': []
            }
            
            # Obtener estaciones de esta línea
            try:
                conn = get_db_connection()
                table_name = f'linea_{line_id}' if line_id != 'R' else 'linea_Ramal'
                cursor = conn.cursor()
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if cursor.fetchone():
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    columns = [col[1] for col in columns_info]
                    
                    # Buscar columnas
                    name_column = None
                    lat_column = None
                    lon_column = None
                    
                    for col in columns:
                        if 'nombre' in col.lower():
                            name_column = col
                        elif 'lat' in col.lower():
                            lat_column = col
                        elif 'lon' in col.lower() or 'long' in col.lower():
                            lon_column = col
                    
                    if name_column:
                        rows = conn.execute(f'SELECT * FROM {table_name} ORDER BY orden_en_linea').fetchall()
                        for row in rows:
                            station_data = dict(zip(columns, row))
                            # Convertir bytes a string si es necesario
                            for key, value in station_data.items():
                                if isinstance(value, bytes):
                                    station_data[key] = value.decode('utf-8', errors='ignore')
                            
                            station_info = {
                                'name': station_data.get(name_column, 'Estación'),
                                'lat': station_data.get(lat_column, 40.4168),
                                'lon': station_data.get(lon_column, -3.7038)
                            }
                            line_data['stations'].append(station_info)
                            
                            # Añadir coordenadas para la línea
                            if station_info['lat'] and station_info['lon']:
                                line_data['coordinates'].append([station_info['lat'], station_info['lon']])
                
                conn.close()
            except Exception as e:
                print(f"⚠️ Error obteniendo estaciones de línea {line_id}: {e}")
            
            lines_data.append(line_data)
        
        print(f"✅ API lines/all: {len(lines_data)} líneas")
        return jsonify(lines_data)
        
    except Exception as e:
        print(f"❌ Error en API lines/all: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/lines/global-status')
def api_lines_global_status():
    """API para obtener el estado global de las líneas usando el scraper"""
    try:
        lines_status = {}
        
        # Usar el scraper de estado si está disponible
        if ACCESOS_SCRAPER_AVAILABLE:
            try:
                scraper = ScraperAccesosReales()
                status_data = scraper.obtener_estado_lineas()
                
                for line_id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                    if line_id in status_data:
                        lines_status[line_id] = {
                            'status': status_data[line_id].get('estado', 'normal'),
                            'description': status_data[line_id].get('descripcion', 'Circulación normal'),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        lines_status[line_id] = {
                            'status': 'normal',
                            'description': 'Circulación normal',
                            'timestamp': datetime.now().isoformat()
                        }
                
                print(f"✅ API lines/global-status: {len(lines_status)} líneas (usando scraper)")
            except Exception as e:
                print(f"⚠️ Error usando scraper de estado: {e}")
                # Fallback a estado simulado
                for line_id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                    lines_status[line_id] = {
                        'status': 'normal',
                        'description': 'Circulación normal',
                        'timestamp': datetime.now().isoformat()
                    }
        else:
            # Estado simulado si no hay scraper
            for line_id in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                lines_status[line_id] = {
                    'status': 'normal',
                    'description': 'Circulación normal',
                    'timestamp': datetime.now().isoformat()
                }
        
        print(f"✅ API lines/global-status: {len(lines_status)} líneas")
        return jsonify(lines_status)
        
    except Exception as e:
        print(f"❌ Error en API lines/global-status: {e}")
        return jsonify({})

@app.route('/api/v5/route')
def api_v5_route():
    """API para calcular rutas v5"""
    try:
        origen = request.args.get('origen', '').strip()
        destino = request.args.get('destino', '').strip()
        algoritmo = request.args.get('algoritmo', 'dijkstra_bidirectional')
        optimizacion = request.args.get('optimizacion', 'min_time')
        
        if not origen or not destino:
            return jsonify({
                'success': False,
                'error': 'Origen y destino son requeridos'
            }), 400
        
        # Simulación de cálculo de ruta
        ruta_simulada = {
            'origen': origen,
            'destino': destino,
            'tiempo_total': 25.5,
            'transbordos': 2,
            'estaciones': 8,
            'algoritmo': algoritmo,
            'optimizacion': optimizacion,
            'path': [
                {
                    'estacion': origen,
                    'coordenadas': [40.4168, -3.7038],
                    'linea': '1',
                    'es_transbordo': False
                },
                {
                    'estacion': 'Estación Intermedia',
                    'coordenadas': [40.4200, -3.7000],
                    'linea': '1',
                    'es_transbordo': True
                },
                {
                    'estacion': destino,
                    'coordenadas': [40.4100, -3.6900],
                    'linea': '2',
                    'es_transbordo': False
                }
            ],
            'recorrido': [
                {
                    'linea': '1',
                    'desde': origen,
                    'hasta': 'Estación Intermedia',
                    'estaciones': 3
                },
                {
                    'transbordo': 'Estación Intermedia',
                    'a_linea': '2'
                },
                {
                    'linea': '2',
                    'desde': 'Estación Intermedia',
                    'hasta': destino,
                    'estaciones': 5
                }
            ]
        }
        
        print(f"✅ API v5/route: Ruta calculada {origen} → {destino}")
        return jsonify({
            'success': True,
            'data': {
                'ruta': ruta_simulada
            }
        })
        
    except Exception as e:
        print(f"❌ Error en API v5/route: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/lines/<line_id>/stations')
def api_line_stations(line_id):
    """API para obtener las estaciones de una línea específica desde estaciones_completas"""
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor()
        
        # Usar la tabla estaciones_completas que tiene toda la información
        query = """
        SELECT id_fijo, nombre, linea, orden_en_linea, correspondencias, 
               latitud, longitud, zona_tarifaria, estacion_accesible
        FROM estaciones_completas 
        WHERE linea = ? AND latitud IS NOT NULL AND longitud IS NOT NULL
        ORDER BY orden_en_linea
        """
        
        cursor.execute(query, (line_id,))
        rows = cursor.fetchall()
        
        stations = []
        for i, row in enumerate(rows):
            # Convertir bytes a string si es necesario
            station_data = {
                'id_fijo': row[0],
                'nombre': row[1] if not isinstance(row[1], bytes) else row[1].decode('utf-8', errors='ignore'),
                'linea': row[2] if not isinstance(row[2], bytes) else row[2].decode('utf-8', errors='ignore'),
                'orden_en_linea': row[3],
                'correspondencias': row[4] if not isinstance(row[4], bytes) else row[4].decode('utf-8', errors='ignore'),
                'latitud': row[5],
                'longitud': row[6],
                'zona_tarifaria': row[7],
                'estacion_accesible': row[8]
            }
            
            # Procesar correspondencias
            correspondencias = []
            if station_data['correspondencias']:
                corr_str = station_data['correspondencias']
                if corr_str:
                    # Extraer solo números de línea del texto descriptivo
                    # Buscar patrones como "Línea 1", "Línea 2", etc.
                    lineas_encontradas = re.findall(r'Línea\s+(\d+)', str(corr_str))
                    correspondencias = lineas_encontradas
                    
                    # También buscar líneas de Cercanías
                    cercanias_encontradas = re.findall(r'Cercanías\s+(\w+)', str(corr_str))
                    correspondencias.extend([f'C{linea}' for linea in cercanias_encontradas])
                    
                    # Buscar autobuses
                    if 'Autobuses' in str(corr_str):
                        correspondencias.append('Autobuses')
                    
                    # Buscar intercambiador
                    if 'Intercambiador' in str(corr_str):
                        correspondencias.append('Intercambiador')
            
            # Determinar si es terminal (primera o última estación)
            is_terminus = (i == 0 or i == len(rows) - 1)
            
            station = {
                'name': station_data['nombre'],
                'id_fijo': station_data['id_fijo'],
                'correspondencias': correspondencias,
                'is_terminus': is_terminus,
                'lat': station_data['latitud'],
                'lon': station_data['longitud'],
                'zona': station_data['zona_tarifaria'],
                'accesible': station_data['estacion_accesible']
            }
            
            stations.append(station)
        
        conn.close()
        
        print(f"✅ API lines/{line_id}/stations: {len(stations)} estaciones desde estaciones_completas")
        return jsonify({'stations': stations})
        
    except Exception as e:
        print(f"❌ Error en API lines/{line_id}/stations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'stations': []})

@app.route('/api/favorites/check/line/<line_id>')
def api_check_favorite_line(line_id):
    """API para verificar si una línea está en favoritos"""
    try:
        # Por ahora, devolver simulado
        return jsonify({'is_favorite': False})
    except Exception as e:
        print(f"❌ Error en API favorites/check/line/{line_id}: {e}")
        return jsonify({'is_favorite': False})

@app.route('/api/favorites/lines/<line_id>', methods=['POST', 'DELETE'])
def api_toggle_favorite_line(line_id):
    """API para añadir/eliminar línea de favoritos"""
    try:
        # Por ahora, devolver simulado
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Error en API favorites/lines/{line_id}: {e}")
        return jsonify({'success': False})

@app.route('/api/station/raw-trains/<station_name>')
def api_station_raw_trains(station_name):
    """API para obtener horarios de trenes de una estación"""
    try:
        # Simulación de datos de trenes
        trains_data = {
            'lineas': [
                {
                    'numero': '1',
                    'direcciones': [
                        {
                            'destino': 'Pinar de Chamartín',
                            'tiempos': ['3', '7', '12']
                        },
                        {
                            'destino': 'Valdecarros',
                            'tiempos': ['5', '9', '15']
                        }
                    ]
                }
            ]
        }
        
        print(f"✅ API station/raw-trains/{station_name}: Datos simulados")
        return jsonify({
            'success': True,
            'trains_data': trains_data
        })
        
    except Exception as e:
        print(f"❌ Error en API station/raw-trains/{station_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/station/closed-status/<station_name>')
def api_station_closed_status(station_name):
    """API para verificar si una estación está cerrada"""
    try:
        # Por ahora, todas las estaciones están abiertas
        return jsonify({
            'cerrada': False,
            'motivo': ''
        })
        
    except Exception as e:
        print(f"❌ Error en API station/closed-status/{station_name}: {e}")
        return jsonify({
            'cerrada': False,
            'motivo': ''
        })

@app.route('/api/favorites/check/station/<station_id>/<line_id>')
def api_check_favorite_station(station_id, line_id):
    """API para verificar si una estación está en favoritos"""
    try:
        # Por ahora, devolver simulado
        return jsonify({'is_favorite': False})
        
    except Exception as e:
        print(f"❌ Error en API favorites/check/station/{station_id}/{line_id}: {e}")
        return jsonify({'is_favorite': False})

@app.route('/api/favorites/stations/<station_id>/<line_id>', methods=['POST', 'DELETE'])
def api_toggle_favorite_station(station_id, line_id):
    """API para añadir/eliminar estación de favoritos"""
    try:
        # Por ahora, devolver simulado
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Error en API favorites/stations/{station_id}/{line_id}: {e}")
        return jsonify({'success': False})

# ============================================================================
# FUNCIONES DE TRANSFORMACIÓN DE DATOS
# ============================================================================

def transform_metro_data(data):
    """Transforma los datos de Metro/Metro Ligero al formato esperado por el frontend"""
    transformed = {
        'stations': [],
        'lines': []
    }
    try:
        # Si los datos vienen en formato GeoJSON
        if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            for feature in data.get('features', []):
                if feature['geometry']['type'] == 'LineString':
                    coordinates = [[coord[1], coord[0]] for coord in feature['geometry']['coordinates']]
                    line_data = {
                        'coordinates': coordinates,
                        'color': feature.get('properties', {}).get('color', '#00AA66'),
                        'name': feature.get('properties', {}).get('name', 'Metro Ligero')
                    }
                    transformed['lines'].append(line_data)
                elif feature['geometry']['type'] == 'Point':
                    lat = feature['geometry']['coordinates'][1]
                    lon = feature['geometry']['coordinates'][0]
                    station_data = {
                        'name': feature.get('properties', {}).get('name', 'Estación'),
                        'lat': lat,
                        'lon': lon,
                        'lines': feature.get('properties', {}).get('lines', []),
                        'connections': feature.get('properties', {}).get('connections', [])
                    }
                    transformed['stations'].append(station_data)
        # Si los datos vienen en el formato de Metro Madrid (estaciones)
        elif isinstance(data, dict) and 'estaciones' in data:
            for est in data['estaciones']:
                lat = est.get('LATITUD') or est.get('lat')
                lon = est.get('LONGITUD') or est.get('lon')
                if lat and lon:
                    # Extraer línea del código de empresa (ej: "0124" -> línea 1)
                    codigo_empresa = est.get('CODIGOEMPRESA', '')
                    linea = None
                    if codigo_empresa and len(codigo_empresa) >= 2:
                        linea = codigo_empresa[:2]  # Primeros 2 dígitos son la línea
                        if linea.startswith('0'):
                            linea = linea[1]  # Quitar el 0 inicial
                    
                    station_data = {
                        'name': est.get('DENOMINACION', est.get('NOMBRE', 'Estación')),
                        'lat': float(lat),
                        'lon': float(lon),
                        'lines': [linea] if linea else [],
                        'connections': est.get('CONEXIONES', [])
                    }
                    transformed['stations'].append(station_data)
        elif isinstance(data, dict) and ('stations' in data or 'lines' in data):
            transformed = data
    except Exception as e:
        print(f"Error transformando datos de Metro/Metro Ligero: {e}")
        import traceback
        traceback.print_exc()
    return transformed

def transform_metro_data_with_layers(data):
    """Transforma los datos de Metro Ligero con capas por línea"""
    transformed = {
        'stations': [],
        'lines': [],
        'layers': {},
        'colors': {}
    }
    try:
        # Procesar estaciones
        if 'stations' in data:
            transformed['stations'] = data['stations']
        
        # Procesar líneas y crear capas por línea
        if 'lines' in data:
            transformed['lines'] = data['lines']
            
            # Agrupar líneas por tipo de línea
            lines_by_type = {}
            for line in data['lines']:
                line_type = line.get('line', 'ML1')
                if line_type not in lines_by_type:
                    lines_by_type[line_type] = []
                lines_by_type[line_type].append(line)
            
            # Crear capas por línea
            for line_type, lines in lines_by_type.items():
                layer_id = f'metro_ligero_{line_type.lower()}'
                layer_name = f'Metro Ligero {line_type[-1]}'
                
                # Obtener color de la línea
                color = data.get('colors', {}).get(line_type, '#70C5E8')
                
                transformed['layers'][layer_id] = {
                    'id': layer_id,
                    'name': layer_name,
                    'type': 'metro_ligero',
                    'line_type': line_type,
                    'visible': False,  # Por defecto no visible
                    'lines': [line['id'] for line in lines],
                    'color': color,
                    'icon': f'/static/logos/lineas/ml{line_type[-1]}.svg'
                }
                
                # Agregar color al diccionario de colores
                transformed['colors'][line_type] = color
        
        # Agregar metadatos si existen
        if 'metadata' in data:
            transformed['metadata'] = data['metadata']
            
    except Exception as e:
        print(f"Error transformando datos de Metro Ligero con capas: {e}")
        import traceback
        traceback.print_exc()
    
    return transformed

def transform_cercanias_data(data):
    """Transforma los datos de Cercanías al formato esperado por el frontend con rutas reales"""
    transformed = {
        'stations': [],
        'lines': []
    }
    try:
        # Si los datos vienen en formato GeoJSON
        if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            for feature in data.get('features', []):
                if feature['geometry']['type'] == 'LineString':
                    coordinates = [[coord[1], coord[0]] for coord in feature['geometry']['coordinates']]
                    line_data = {
                        'coordinates': coordinates,
                        'color': feature.get('properties', {}).get('color', '#E20714'),
                        'name': feature.get('properties', {}).get('name', 'Cercanías')
                    }
                    transformed['lines'].append(line_data)
                elif feature['geometry']['type'] == 'Point':
                    lat = feature['geometry']['coordinates'][1]
                    lon = feature['geometry']['coordinates'][0]
                    props = feature.get('properties', {})
                    station_data = {
                        'name': props.get('name', 'Estación'),
                        'lat': float(lat),
                        'lon': float(lon),
                        'lines': props.get('lines', []),
                        'connections': props.get('connections', []),
                        'zone': props.get('zone', 'A')
                    }
                    transformed['stations'].append(station_data)
        # Si los datos vienen en el formato de Cercanías corregido (estaciones con latitud/longitud)
        elif isinstance(data, dict) and 'estaciones' in data:
            for est in data['estaciones']:
                # Buscar coordenadas en diferentes formatos posibles
                lat = est.get('latitud') or est.get('LATITUD') or est.get('lat')
                lon = est.get('longitud') or est.get('LONGITUD') or est.get('lon')
                
                if lat and lon:
                    # Obtener línea de la estación
                    linea = est.get('linea', '')
                    
                    station_data = {
                        'name': est.get('nombre', est.get('DENOMINACION', est.get('NOMBRE', 'Estación'))),
                        'lat': float(lat),
                        'lon': float(lon),
                        'lines': [linea] if linea else [],
                        'connections': est.get('conexiones', est.get('CONEXIONES', [])),
                        'zone': est.get('zona', est.get('ZONA', 'A')),
                        'codigo': est.get('codigo', ''),
                        'municipio': est.get('municipio', ''),
                        'provincia': est.get('provincia', '')
                    }
                    transformed['stations'].append(station_data)
        elif isinstance(data, dict) and ('stations' in data or 'lines' in data):
            if 'stations' in data:
                for station in data['stations']:
                    if 'lat' in station and 'lon' in station:
                        station['lat'] = float(station['lat'])
                        station['lon'] = float(station['lon'])
            transformed = data
        
        print(f"✅ Datos de Cercanías transformados: {len(transformed['stations'])} estaciones, {len(transformed['lines'])} líneas")
    except Exception as e:
        print(f"❌ Error transformando datos de Cercanías: {e}")
        import traceback
        traceback.print_exc()
    return transformed

# ============================================================================
# BLOQUE PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # Cargar datos clave (opcional)
    cargar_datos_clave()
    
    # Iniciar el auto-updater si está disponible
    if AUTO_UPDATER_AVAILABLE:
        start_auto_updater()
    
    # Iniciar la aplicación
    app.run(host='0.0.0.0', port=5000, debug=True)
