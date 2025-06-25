# TEST COMMENT
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
METRO DE MADRID - APLICACIÓN WEB COMPLETA
=========================================

Aplicación Flask para mostrar información del Metro de Madrid
con datos en tiempo real, horarios, mapas y estadí­sticas.
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
login_manager.login_message_category = 'info' # Categorí­a de mensaje para flash

# Rutas de archivos
DB_PATH = 'db/estaciones_fijas_v2.db'
DB_RELACIONAL_PATH = 'db/estaciones_fijas_v2.db'
GTFS_DB_PATH = 'M4/metro_madrid.db'
CSV_DATOS_CLAVE = 'datos_clave_estaciones_definitivo.csv'

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
    'R':  {'id': 'R',  'name': 'Ramal',    'color': '#0055A4', 'color_secondary': '#4A90E2', 'text_color': '#FFFFFF'}
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
        
        # Búsqueda en la columna 'nombre' (que sí­ existe en el CSV)
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
    """Obtiene viajes activos con frecuencias para una hora especí­fica"""
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

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/station', methods=['GET', 'POST'])
@login_required
def station_page():
    """Página de búsqueda de estaciones"""
    resultados = []
    query = ''
    if request.method == 'POST':
        query = request.form.get('station_name', '').strip()
    else:
        query = request.args.get('q', '').strip()
    
        if query:
            resultados = buscar_estacion_por_nombre(query, limite=10)
    return render_template('station.html', resultados=resultados, query=query)

@app.route('/station/<station_name>')
@login_required
def station_page_dynamic(station_name):
    """Página especínica para una estación por nombre"""
    print(f"Buscando estacion: '{station_name}'")
    
    # Buscar la estación en la base de datos
    estaciones = buscar_estacion_por_nombre(station_name, limite=1)
    print(f" Resultados exactos: {len(estaciones) if estaciones else 0}")
    
    if estaciones:
        # Estación encontrada exactamente
        estacion_data = estaciones[0]
        print(f" Estación encontrada exactamente: {estacion_data['nombre']}")
        return render_template('station.html', 
                             station_name=station_name,
                             station_data=estacion_data,
                             auto_load=True)
    else:
        # Estación no encontrada exactamente, buscar coincidencias para mostrar opciones
        print(f" Buscando coincidencias para: '{station_name}'")
        estaciones_coincidencia = buscar_estacion_por_nombre(station_name, limite=10)
        print(f" Coincidencias encontradas: {len(estaciones_coincidencia) if estaciones_coincidencia else 0}")
        
        if estaciones_coincidencia:
            # Encontró coincidencias, mostrar página con opciones de búsqueda
            print(f" Mostrando opciones de búsqueda para: '{station_name}'")
            return render_template('station.html', 
                                 station_name=station_name,
                                 station_data=None,
                                 auto_load=False,
                                 search_results=estaciones_coincidencia,
                                 search_query=station_name)
        else:
            # No hay coincidencias, mostrar página de búsqueda vacía
            print(f" No se encontraron coincidencias para: '{station_name}'")
            return render_template('station.html', 
                                 station_name=station_name,
                                 station_data=None,
                                 auto_load=False)

@app.route('/station/id/<int:station_id>')
@login_required
def station_page_by_id(station_id):
    """Página especínica para una estación por ID fijo"""
    # Solo renderizar la plantilla sin pasar variables
    # El JavaScript se encargará de cargar los datos
    return render_template('station.html')

@app.route('/line')
@login_required
def line_redirect():
    """Redirige /line a /1 (Línea 1)"""
    return redirect(url_for('line_detail', line_id='1'))

@app.route('/line/<line_id>')
@login_required
def line_detail(line_id):
    """Página de detalle de una línea, ahora unificada y robusta."""
    line_info = LINEAS_CONFIG.get(line_id)
    if not line_info:
        return "Linea no encontrada", 404

    # Añadimos la clave 'linea' para mantener compatibilidad con plantillas que la usen
    line_info['linea'] = line_id
    
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
                    'descripcion': row[1] if row[1] else 'Sin descripción'
                }
            else:
                line_status_data = {
                    'estado': 'Normal',
                    'descripcion': 'Circulación normal'
                }
        else:
            line_status_data = {
                'estado': 'Normal',
                'descripcion': 'Circulación normal'
            }
        
        conn.close()
        
    except Exception as e:
        print(f"Error obteniendo estado de línea {line_id}: {e}")
        line_status_data = {
            'estado': 'No disponible',
            'descripcion': 'Estado no disponible'
        }
    
    line_info['status'] = line_status_data

    # Obtener todas las demás líneas para la barra lateral
    other_lines = [config for id, config in LINEAS_CONFIG.items() if id != line_id]

    return render_template('line_detail.html', line_info=line_info, other_lines=other_lines)

@app.route('/lines-overview')
@login_required
def lines_overview():
    """Ruta obsoleta que ahora redirige a /status."""
    return redirect(url_for('status'))

@app.route('/api/routes')
def get_routes():
    """Endpoint para obtener las rutas del metro para el mapa"""
    try:
        # Intentar cargar el archivo de rutas JSON con manejo de errores mejorado
        import os
        routes_file = 'static/data/metro_routes.json'
        
        if os.path.exists(routes_file):
            try:
                # Verificar el tamaño del archivo
                file_size = os.path.getsize(routes_file)
                print(f"Cargando archivo de rutas: {file_size} bytes")
                
                # Si el archivo es muy grande (>10MB), usar fallback
                if file_size > 10 * 1024 * 1024:  # 10MB
                    print("Archivo demasiado grande, usando datos básicos")
                    raise Exception("Archivo demasiado grande")
                
                with open(routes_file, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                print("Archivo de rutas cargado exitosamente")
                return jsonify(routes_data)
                
            except Exception as file_error:
                print(f"Error cargando archivo JSON: {file_error}")
                # Fallback a datos básicos
                pass
        
        # Fallback: generar datos básicos desde la configuración
        print("Generando datos básicos de rutas")
        lines = []
        for line_id, config in LINEAS_CONFIG.items():
            lines.append({
                'line': line_id,
                'name': config['name'],
                'color': config['color'],
                'paths': []  # Sin rutas geográficas por ahora
            })
        
        return jsonify({
            'success': True,
            'lines': lines,
            'total': len(lines)
        })
            
    except Exception as e:
        print(f"Error en /api/routes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/test')
def test_api():
    """Ruta de prueba para verificar que el servidor responde"""
    return jsonify({
        'message': 'API funcionando correctamente',
        'timestamp': datetime.now().isoformat(),
        'success': True
    })

@app.route('/test-map-routes')
def test_map_routes():
    """Ruta de prueba alternativa para la calculadora de rutas"""
    return render_template('map_routes.html')

@app.route('/static/data/metro_routes.json')
def serve_metro_routes():
    """Servir el archivo de rutas del metro de forma optimizada"""
    try:
        import os
        routes_file = 'static/data/metro_routes.json'
        
        if os.path.exists(routes_file):
            return send_file(routes_file, mimetype='application/json')
        else:
            # Si no existe el archivo, devolver datos básicos
            lines = []
            for line_id, config in LINEAS_CONFIG.items():
                lines.append({
                    'line': line_id,
                    'name': config['name'],
                    'color': config['color'],
                    'paths': []
                })
            return jsonify({'lines': lines})
    except Exception as e:
        print(f"Error sirviendo metro_routes.json: {e}")
        return jsonify({'error': 'Error loading routes'}), 500

@app.route('/schedules')
@login_required
def schedules():
    return render_template('schedules.html')

@app.route('/seguridad')
@login_required
def seguridad():
    return render_template('seguridad.html')

@app.route('/about_us')
@login_required
def about_us():
    return render_template('about_us.html')

@app.route('/about_me')
@login_required
def about_me():
    return render_template('about_me.html')

@app.route('/about_u')
@login_required
def about_u():
    return render_template('about_u.html')

@app.route('/test-modern-trains')
@login_required
def test_modern_trains():
    """Página de prueba para el sistema moderno de trenes"""
    return render_template('test_modern_trains.html')

@app.route('/status')
@login_required
def status():
    return render_template('status.html')

@app.route('/station/<nombre>')
@login_required
def station_page_by_name(nombre):
    return render_template('station.html', nombre=nombre)

@app.route('/station/<lineNumber>/<stationId>')
@login_required
def station_page_by_line_and_id(lineNumber, stationId):
    return render_template('station.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/station/search')
def search_station_api():
    """API para buscar estaciones por nombre (para autocompletado)"""
    query = request.args.get('q', '').strip() or request.args.get('term', '').strip()
    if not query:
        return jsonify([])

    # Usar el nuevo sistema de búsqueda con datos clave
    estaciones = buscar_estacion_por_nombre(query, limite=15)
    
    # Formatear resultados para autocompletado
    resultados = []
    
    for estacion in estaciones:
        resultados.append({
            'nombre': estacion['nombre'],
            'linea': estacion['linea'],
            'id_fijo': estacion['id_fijo'],
            'id_modal': estacion.get('id_modal'),
            'orden': estacion.get('orden'),
            'url': estacion.get('url'),
            'direccion_ida': estacion.get('direccion_ida'),
            'direccion_vuelta': estacion.get('direccion_vuelta'),
            'tabla_origen': estacion.get('tabla_origen')
        })
    
    return jsonify(resultados)

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Endpoint para obtener estadí­sticas del dashboard"""
    try:
        # Conectar a la base de datos de estaciones fijas
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Contar estaciones únicas y líneas activas
        estaciones_unicas = 0
        lineas_activas = 0
        total_estaciones = 0
        
        # Verificar cada tabla de línea
        line_tables = [f'linea_{i}' for i in range(1, 13)] + ['linea_Ramal']
        
        for tabla in line_tables:
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                if count > 0:
                    lineas_activas += 1
                    total_estaciones += count
                    
                    # Contar estaciones únicas por nombre
                    cursor.execute(f"SELECT COUNT(DISTINCT nombre) FROM {tabla}")
                    estaciones_unicas += cursor.fetchone()[0]
            except sqlite3.OperationalError:
                continue
        
        conn.close()
        
        return jsonify({
            'statistics': {
                'unique_stations': estaciones_unicas,
                'active_lines': lineas_activas,
                'total_stations': total_estaciones,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error en /api/dashboard/stats: {e}")
        return jsonify({
            'statistics': {
                'unique_stations': 0,
                'active_lines': 0,
                'total_stations': 0,
                'last_updated': datetime.now().isoformat()
            }
        }), 500

@app.route('/api/stations/all')
def get_all_stations():
    """Obtener todas las estaciones con coordenadas para el mapa"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Usar la nueva tabla combinada que tiene coordenadas
        cursor.execute("""
            SELECT id_fijo, nombre, linea, latitud, longitud, zona_tarifaria, 
                   estacion_accesible, correspondencias
            FROM estaciones_completas 
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
            ORDER BY linea, orden_en_linea
        """)
        
        stations = []
        for row in cursor.fetchall():
            id_fijo, nombre, linea, lat, lon, zona, accesible, correspondencias = row
            
            # Procesar correspondencias
            corr_list = []
            if correspondencias:
                try:
                    corr_data = eval(correspondencias)
                    if isinstance(corr_data, list):
                        corr_list = [str(corr) for corr in corr_data]
                except:
                    pass
            
            station = {
                'id': id_fijo,
                'name': nombre,
                'line': linea,
                'lat': float(lat) if lat else None,
                'lon': float(lon) if lon else None,
                'zone': zona,
                'accessible': accesible == 'Sí­',
                'connections': corr_list
            }
            stations.append(station)
        
        conn.close()
        
        print(f" Mapa: {len(stations)} estaciones con coordenadas")
        return jsonify(stations)
        
    except Exception as e:
        print(f" Error en /api/stations/all: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stations/accesses')
def get_station_accesses():
    """Obtener todos los accesos/salidas de estaciones desde stops.txt para mostrar en el mapa"""
    try:
        import os
        import csv
        
        accesses = []
        stops_file = 'M4/stops.txt'
        
        if not os.path.exists(stops_file):
            return jsonify({'error': 'Archivo stops.txt no encontrado'}), 404
        
        with open(stops_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Solo procesar accesos (location_type = 2)
                if row.get('location_type') == '2':
                    stop_name = row.get('stop_name', '')
                    stop_desc = row.get('stop_desc', '')
                    lat = row.get('stop_lat')
                    lon = row.get('stop_lon')
                    
                    if lat and lon:
                        # Determinar tipo de acceso
                        access_type = 'exit'  # Por defecto es salida
                        emoji = '🚪'  # Emoji por defecto
                        
                        if 'ascensor' in stop_name.lower():
                            access_type = 'elevator'
                            emoji = '🛗'
                        elif 'escalera' in stop_name.lower() or 'escalator' in stop_name.lower():
                            access_type = 'escalator'
                            emoji = '⬆️'
                        
                        access = {
                            'name': stop_name,
                            'description': stop_desc,
                            'lat': float(lat),
                            'lon': float(lon),
                            'type': access_type,
                            'emoji': emoji
                        }
                        accesses.append(access)
        
        print(f" Mapa: {len(accesses)} accesos/salidas cargados")
        return jsonify(accesses)
        
    except Exception as e:
        print(f" Error en /api/stations/accesses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lines/<line_id>/stations')
def get_line_stations(line_id):
    """Devuelve las estaciones de una línea especí­fica, incluyendo su estado (cerrada/operativa) y motivo de cierre si aplica"""
    # Mapear line_id a número de línea
    line_mapping = {
        '1': 1, '2': 2, '3': 3, '4': 4,
        '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, '11': 11, '12': 12,
        'R': 'Ramal', 'Ramal': 'Ramal'
    }
    
    line_number = line_mapping.get(line_id)
    if line_number is None:
        return jsonify({'error': f'Línea {line_id} no encontrada'}), 404
    
    try:
        # Leer el CSV de datos clave
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        # Filtrar por línea
        if line_number == 'Ramal':
            stations_df = df[df['linea'] == 'Ramal']
        else:
            # Convertir la columna linea a int para comparación correcta
            df['linea'] = pd.to_numeric(df['linea'], errors='coerce')
            stations_df = df[df['linea'] == int(line_number)]
        
        # Obtener estado de la línea desde la base de datos
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estado_lineas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linea TEXT NOT NULL,
                estado TEXT NOT NULL,
                clase_css TEXT,
                descripcion TEXT,
                estaciones_cerradas TEXT,
                accesos_cerrados TEXT,
                incidencias TEXT,
                url_origen TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        cursor.execute("""
            SELECT estaciones_cerradas FROM estado_lineas 
            WHERE linea = ? ORDER BY timestamp DESC LIMIT 1
        """, (line_id,))
        row = cursor.fetchone()
        conn.close()
        estaciones_cerradas = []
        motivos_cierre = {}
        if row:
            try:
                estaciones_cerradas_data = json.loads(row['estaciones_cerradas'])
                estaciones_cerradas = [e['nombre'] for e in estaciones_cerradas_data]
                motivos_cierre = {e['nombre']: e.get('motivo', '') for e in estaciones_cerradas_data}
            except Exception:
                estaciones_cerradas = []
                motivos_cierre = {}
        
        # Ordenar por la columna orden
        stations_df = stations_df.sort_values('orden')
        
        # Identificar estaciones terminus
        if not stations_df.empty:
            terminus_ids = [stations_df.iloc[0]['id_fijo'], stations_df.iloc[-1]['id_fijo']]
        else:
            terminus_ids = []

        # Formatear las estaciones para el frontend
        stations_data = []
        for _, row in stations_df.iterrows():
            def clean_value(x, default=None):
                return default if pd.isna(x) else x

            def to_bool(val):
                if pd.isna(val): return False
                return str(val).lower() in ['true', '1', 't', 'y', 'yes', 'sí­', 'si', 'verdadero']

            nombre_estacion = clean_value(row.get('nombre'), 'N/A')
            id_fijo = int(clean_value(row.get('id_fijo'), 0))
            cerrada = nombre_estacion in estaciones_cerradas
            motivo_cierre = motivos_cierre.get(nombre_estacion) if cerrada else None

            services = {
                'accessible': to_bool(row.get('accessible')),
                'defibrillator': to_bool(row.get('defibrillator')),
                'elevators': to_bool(row.get('elevators')),
                'escalators': to_bool(row.get('escalators')),
                'historical': to_bool(row.get('historical')),
                'mobileCoverage': to_bool(row.get('mobileCoverage')),
                'shops': to_bool(row.get('shops'))
            }

            # Obtener correspondencias de la columna 'correspondencias' que es un string tipo "['2', '7']"
            try:
                correspondencias_str = clean_value(row.get('correspondencias'), '[]')
                correspondencias = json.loads(correspondencias_str.replace("'", '"'))
            except (json.JSONDecodeError, TypeError):
                correspondencias = []

            station_info = {
                'id_fijo': id_fijo,
                'name': nombre_estacion,
                'orden': int(clean_value(row.get('orden'), 0)),
                'url': clean_value(row.get('url')),
                'tariffZone': clean_value(row.get('zona'), 'A'),
                'services': services,
                'cerrada': cerrada,
                'motivo_cierre': motivo_cierre,
                'is_terminus': id_fijo in terminus_ids,
                'correspondencias': correspondencias
            }
            stations_data.append(station_info)
        
        return jsonify({'stations': stations_data})
    except Exception as e:
        # Log del error para depuración
        print(f"Error en get_line_stations para línea {line_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

@app.route('/api/station/detailed/<station_name>')
def get_detailed_station_data(station_name):
    """Obtiene datos detallados de una estación usando el scraper."""
    # Temporalmente deshabilitado - el scraper no tiene el método scrape_station_by_name
    # from herramientas.scraper_datos_detallados import ScraperDatosDetallados
    # scraper = ScraperDatosDetallados()
    # data = scraper.scrape_station_by_name(station_name)
    # scraper.close()
    # if data:
    #     return jsonify(data)
    # else:
    #     return jsonify({'error': 'No se pudieron obtener los datos detallados'}), 404
    return jsonify({'error': 'Funcionalidad temporalmente deshabilitada'}), 404

@app.route('/api/station/realtime/<station_name>')
def get_realtime_station_data(station_name):
    """Endpoint que devuelve datos en tiempo real y estáticos de una estación usando la base moderna"""
    try:
        print(f"--- REALTIME_API: Buscando datos para: '{station_name}' ---")
        estaciones_exactas = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones_exactas:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        estacion_linea = estaciones_exactas[0]
        id_fijo = estacion_linea['id_fijo']
        linea = estacion_linea['linea']
        url = estacion_linea.get('url', '')
        id_modal = estacion_linea.get('id_modal')

        # 1. Obtener próximos trenes (scraper Ninja)
        proximos_trenes_html = '<div class="no-data">No disponible</div>'
        if id_modal:
            try:
                # Usar el scraper Ninja para obtener datos en tiempo real
                from herramientas.scraper_ninja_tiempo_real import ScraperNinjaTiempoReal
                scraper = ScraperNinjaTiempoReal()
                url_proximos_trenes = f"https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}"
                ninja_data = scraper.scrape_estacion_tiempo_real(url_proximos_trenes)
                proximos_trenes_html = ninja_data.get('proximos_trenes_html', '<div class="no-data">No disponible</div>') if ninja_data else '<div class="no-data">No disponible</div>'
                print(f"--- REALTIME_API: Datos Ninja obtenidos para ID {id_modal} ---")
            except Exception as e:
                print(f"--- REALTIME_API: Error Ninja: {e} ---")

        # 2. Datos detallados (placeholder)
        detalles_scrapeados = {'info': 'Datos detallados temporalmente no disponibles'}

        # 3. Datos guardados de la base moderna
        datos_guardados = []
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            tabla_linea = f"linea_{linea}"
            cursor.execute(f"""
                SELECT id_fijo, nombre, zona_tarifaria, estacion_accesible, 
                       ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                       bibliometro, tiendas, correspondencias, url, servicios,
                       accesos, vestibulos, nombres_acceso, intercambiadores
                FROM {tabla_linea} 
                WHERE id_fijo = ?
            """, (id_fijo,))
            row = cursor.fetchone()
            conn.close()
            if row:
                id_fijo, nombre, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url, servicios, accesos, vestibulos, nombres_acceso, intercambiadores = row
                # Procesar servicios
                servicios_list = []
                servicios_estructurados = []
                if servicios:
                    servicios_text = servicios.replace(';', ',').replace(';', ',')
                    servicios_list = [s.strip() for s in servicios_text.split(',') if s.strip()]
                    # Crear objetos estructurados para servicios
                    iconos_servicios = {
                        'Ascensores': '🚇', 'Desfibrilador': '💓', 'Escaleras mecanicas': '🚇',
                        'Cobertura movil': '📱', 'Estacion accesible': '♿', 'Tiendas': '🏪',
                        'Bibliometro': '📚', 'Oficina de gestion TTP': '🏢', 'Parking disuasorio de pago': '🅿️',
                        'Quioscos ONCE': '👁️', 'adaptada para discapacitados': '♿'
                    }
                    for servicio in servicios_list:
                        icono = iconos_servicios.get(servicio, '🔧')
                        servicios_estructurados.append({
                            'tipo_servicio': servicio,  # Cambiar 'nombre' por 'tipo_servicio'
                            'icono': icono,
                            'disponible': True
                        })
                
                # Procesar correspondencias
                corr_list = []
                if correspondencias:
                    try:
                        corr_data = eval(correspondencias)
                        if isinstance(corr_data, list):
                            corr_list = [str(corr) for corr in corr_data]
                    except:
                        pass
                
                # Procesar accesos
                accesos_list = []
                accesos_estructurados = []
                if accesos:
                    accesos_text = accesos.replace(';', ',').replace(';', ',')
                    accesos_list = [a.strip() for a in accesos_text.split(',') if a.strip()]
                    # Intentar parsear accesos para crear objetos estructurados
                    for acceso in accesos_list:
                        # Mejorar el parsing de accesos
                        nombre = acceso
                        vestibulo = 'No especificado'
                        direccion = None  # No incluir si no hay dirección
                        
                        # Patrón 1: "Nombre - Vestí­bulo: Dirección"
                        if ' - ' in acceso and ':' in acceso:
                            partes = acceso.split(' - ', 1)
                            nombre = partes[0].strip()
                            resto = partes[1].strip()
                            if ':' in resto:
                                vestibulo_parte, direccion = resto.split(':', 1)
                                vestibulo = vestibulo_parte.strip()
                                direccion = direccion.strip()
                        
                        # Patrón 2: "Nombre - Vestí­bulo" (sin dirección)
                        elif ' - ' in acceso:
                            partes = acceso.split(' - ', 1)
                            nombre = partes[0].strip()
                            vestibulo = partes[1].strip()
                        
                        # Patrón 3: Solo nombre
                        else:
                            nombre = acceso.strip()
                        
                        # Filtrar accesos mal formateados o muy largos
                        if (len(nombre) > 50 or nombre.isdigit() or len(nombre) < 3 or
                            ':' in nombre or nombre.startswith('pares') or 
                            nombre.startswith('4:') or nombre.startswith('31 (') or
                            'Pedro ValdiviaPedro Valdivia' in nombre or
                            'Prí­ncipe de Vergara)' in nombre):
                            continue
                        
                        # Limpiar vestí­bulos muy largos
                        if len(vestibulo) > 100:
                            vestibulo = vestibulo[:50] + "..."
                        
                        # Solo incluir si tiene un nombre válido y no es redundante
                        if (nombre and nombre != 'No especificado' and 
                            not nombre.startswith('pares') and 
                            not nombre.startswith('4:') and
                            not nombre.startswith('31 (') and
                            'Pedro ValdiviaPedro Valdivia' not in nombre and
                            'Prí­ncipe de Vergara)' not in nombre):
                            
                            acceso_obj = {
                                'nombre': nombre,
                                'vestibulo': vestibulo
                            }
                            # Solo incluir dirección si existe y no es "Dirección no especificada"
                            if direccion and direccion != 'Dirección no especificada':
                                acceso_obj['direccion'] = direccion
                            
                            accesos_estructurados.append(acceso_obj)
                
                # Formatear datos para compatibilidad con el frontend
                datos_formateados = {
                    'id_fijo': id_fijo,
                    'nombre': nombre,
                    'linea': linea,
                    'url': url,
                    'id_modal': id_modal,
                    'zona_tarifaria': zona,
                    'ultima_actualizacion_detalles': datetime.now().isoformat(),
                    'modulos': {
                        'servicios': {
                            'disponible': len(servicios_list) > 0,
                            'datos': servicios_estructurados,
                            'total': len(servicios_list)
                        },
                        'accesos': {
                            'disponible': len(accesos_list) > 0,
                            'datos': accesos_estructurados,
                            'total': len(accesos_list)
                        },
                        'conexiones': {
                            'disponible': len(corr_list) > 0,
                            'datos': corr_list,
                            'total': len(corr_list)
                        }
                    },
                    # Datos estructurados para el frontend
                    'servicios_estructurados': servicios_estructurados,
                    'accesos_estructurados': accesos_estructurados,
                    # Datos legacy para compatibilidad
                    'servicios': '; '.join(servicios_list) if servicios_list else '',
                    'accesos': '; '.join(accesos_list) if accesos_list else '',
                    'correspondencias': '; '.join(corr_list) if corr_list else ''
                }
                datos_guardados.append(datos_formateados)
        except Exception as e:
            print(f"Error obteniendo datos de la nueva BD para {station_name}: {e}")
            datos_guardados.append({
                'id_fijo': id_fijo,
                'nombre': estacion_linea['nombre'],
                'linea': linea,
                'url': url,
                'id_modal': id_modal,
                'servicios': '',
                'accesos': '',
                'correspondencias': ''
            })
        print(f"--- REALTIME_API: Devolviendo datos para '{station_name}' ---")
        return jsonify({
            'next_trains_html': proximos_trenes_html,
            'details': detalles_scrapeados,
            'stored_data': datos_guardados,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[REALTIME_API] Error: {e}")
        return jsonify({'error': f'Error obteniendo datos: {str(e)}'}), 500

def convertir_proximos_trenes_a_html_personalizado(html_content, station_name):
    """
    Convierte el HTML de la API de Metro en un formato personalizado,
    extrayendo de forma precisa los datos de cada línea y dirección.
    """
    try:
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html_content, 'html.parser')
        colores_lineas = {
            '1': '#00AEEF', '2': '#FF0000', '3': '#FFDF00', '4': '#824100',
            '5': '#339900', '6': '#999999', '7': '#FF6600', '8': '#FF69B4',
            '9': '#990066', '10': '#000099', '11': '#006600', '12': '#999933',
            'Ramal': '#FFFFFF'
        }
        
        lineas_data = {}

        # Busca cada bloque de información de una dirección de una línea
        direction_blocks = soup.find_all('div', class_='text__info-estacion--tit-icon')

        # Caso especial para el Ramal
        ramal_block = soup.find('img', src=re.compile(r'ramal\.svg'))
        if ramal_block:
            ramal_container = ramal_block.find_parent('div', class_='small-12')
            if ramal_container:
                # Buscar el texto "Actualmente sin previsión"
                sin_prevision = ramal_container.find('p', string=re.compile(r'Actualmente sin previsión'))
                if sin_prevision:
                    lineas_data['Ramal'] = {
                        'numero': 'Ramal',
                        'nombre': 'Ramal',
                        'color': '#FFFFFF',
                        'logo': '/static/logos/lineas/ramal.svg',
                        'direcciones': [{
                            'destino': 'Sin previsión',
                            'tiempos': [],
                            'proximo_tren': None,
                            'todos_tiempos': [],
                            'sin_prevision': True
                        }]
                    }

        for block in direction_blocks:
            main_block = block.find_parent('div', class_=re.compile(r'columns'))
            if not main_block: continue

            line_img = main_block.find('img', src=re.compile(r'linea-'))
            if not line_img: continue
            
            linea_num_match = re.search(r'linea-(\w+)', line_img.get('src', ''))
            if not linea_num_match: continue
            linea_num = linea_num_match.group(1).replace('-circular', '')
            
            destino_span = block.find('span', class_='tiempo-espera__destino', string=re.compile(r'Direcci.n|Andén'))
            if not destino_span: continue
            
            destino_text = destino_span.get_text(strip=True)
            
            # CORRECCIÓN: Se quita la palabra "Dirección", etc. del inicio del texto.
            destino = re.sub(r'^(Direcci.n|Destino|And.n)\s*', '', destino_text, flags=re.IGNORECASE).strip()
            
            destino = re.sub(r'\s*-\s*\d+$', '', destino).strip()

            if not destino or len(destino) < 3: continue

            tiempos = []
            time_spans = block.find_all('span', class_='tiempo-espera__minutos')
            for span in time_spans:
                time_match = re.search(r'(\d+)\s*min', span.get_text())
                if time_match:
                    tiempos.append(time_match.group(1))

            if not tiempos: continue

            if linea_num not in lineas_data:
                lineas_data[linea_num] = {
                    'color': colores_lineas.get(linea_num, '#333333'),
                    'direcciones': []
                }
            
            if not any(d['destino'] == destino for d in lineas_data[linea_num]['direcciones']):
                lineas_data[linea_num]['direcciones'].append({
                    'destino': destino,
                    'tiempos': tiempos
                })
        
        if not lineas_data:
            return ''

        html_personalizado = '<div class="lines-grid-multi">'
        for linea_num, data in sorted(lineas_data.items()):
            color = data['color']
            direcciones = data['direcciones']
            linea_nombre = f'Línea {linea_num}'
            linea_svg = f'linea-{linea_num}'
            num_sentidos = len(direcciones)
            sentido_texto = f"{num_sentidos} sentido{'s' if num_sentidos > 1 else ''}"
            
            html_personalizado += f'''
                <div class="line-card-multi" style="border-left-color: {color}">
                    <div class="line-header" style="color: {color}">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <img src="/static/logos/lineas/{linea_svg}.svg" alt="{linea_nombre}" style="width: 20px; height: 20px;">
                            <strong>{linea_nombre}</strong>
                        </div>
                        <span class="directions-count">{sentido_texto}</span>
                    </div>
                    <div class="directions-container">
            '''
            for i, direccion in enumerate(direcciones):
                direction_icon = "⬅️" if i == 0 else "➡️"
                direction_name = "IDA" if num_sentidos > 1 and i == 0 else "VUELTA" if num_sentidos > 1 else "ÚNICO"
                
                tiempos_html = " y ".join([f"<strong>{t} min</strong>" for t in direccion['tiempos']])
                
                html_personalizado += f'''
                        <div class="line-direction" style="border-left: 3px solid {color}">
                            <div class="direction-header">
                                <span class="direction-icon">{direction_icon}</span>
                                <span class="direction-name">{direction_name}</span>
                            </div>
                            <div class="line-name" style="color: {color}">
                                <img src="/static/logos/lineas/{linea_svg}.svg" alt="{linea_nombre}" style="width: 16px; height: 16px; margin-right: 5px;">
                                {linea_nombre}
                            </div>
                            <div class="line-destination">
                                <strong>Destino:</strong> {direccion['destino']}
                            </div>
                            <div class="line-times">
                                <strong>Tiempos:</strong> {tiempos_html}
                            </div>
                        </div>
                '''
            html_personalizado += '</div></div>'
        html_personalizado += '</div>'
        return html_personalizado
        
    except Exception as e:
        print(f"[ERROR] Excepción en convertir_proximos_trenes: {e}")
        return ""

@app.route('/api/station/status/database')
def get_station_status_database():
    """Endpoint de depuración para ver el contenido de la tabla station_status."""
    DB_STATUS_PATH = 'db/estaciones_fijas_v2.db'
    if not os.path.exists(DB_STATUS_PATH):
        return jsonify({'error': 'La base de datos de estado no existe.'}), 404
        
    try:
        conn = sqlite3.connect(DB_STATUS_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='station_status'")
        if not cursor.fetchone():
            return jsonify({'error': 'La tabla station_status no existe.'}), 404
        
        cursor.execute("SELECT * FROM station_status ORDER BY last_updated DESC LIMIT 50")
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        
        conn.close()
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/station/status/check')
def check_station_status():
    """Endpoint para verificar el estado de una estación especí­fica"""
    station_name = request.args.get('station', '')
    if not station_name:
        return jsonify({'error': 'Debe especificar una estación'}), 400
        
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM station_status 
            WHERE station_name LIKE ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (f'%{station_name}%',))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify(dict(row))
        else:
            return jsonify({'error': f'No se encontró información para la estación {station_name}'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NINJA SCRAPER - DATOS EN TIEMPO REAL
# ============================================================================

@app.route('/api/station/ninjascrap/<station_name>')
def ninjascrap_station(station_name):
    """Endpoint para ejecutar Scraper Ninja en una estación especí­fica"""
    try:
        print(f"[NINJA] Iniciando scraper para estación: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404
        
        station_data = estaciones[0]
        print(f"[NINJA] Estación encontrada: {station_data['nombre']} (Línea {station_data['linea']})")
        
        # Verificar que tenga URL
        if not station_data.get('url'):
            return jsonify({'error': f'La estación {station_name} no tiene URL configurada'}), 404
        
        # Ejecutar scraper Ninja
        scraper = ScraperNinjaTiempoReal()
        ninjascrap_data = scraper.scrape_estacion_tiempo_real(station_data['url'])
        
        if not ninjascrap_data:
            return jsonify({'error': 'Error ejecutando scraper Ninja'}), 500
        
        # Combinar datos estáticos con datos dinámicos
        resultado = {
            'station_name': station_data['nombre'],
            'linea': station_data['linea'],
            'station_url': station_data['url'],
            'zona_tarifaria': station_data.get('zona_tarifaria', 'No disponible'),
            'last_update': ninjascrap_data.get('ultima_actualizacion', 'No disponible'),
            'proximos_trenes_html': ninjascrap_data.get('proximos_trenes_html', ''),
            'estado_ascensores': ninjascrap_data.get('estado_ascensores', 'No disponible'),
            'estado_escaleras': ninjascrap_data.get('estado_escaleras', 'No disponible'),
            'timestamp_scraping': ninjascrap_data.get('timestamp_scraping', ''),
            'scraper_status': 'success'
        }
        
        print(f"[NINJA] Scraping completado para {station_name}")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[NINJA] Error en scraper: {e}")
        return jsonify({
            'error': f'Error ejecutando scraper: {str(e)}',
            'scraper_status': 'error'
        }), 500

@app.route('/api/station/refresh-trains/<station_name>')
def refresh_trains_with_ninja(station_name):
    """Devuelve los próximos trenes usando el id_modal correcto de la base de datos."""
    try:
        print(f"[REFRESH] Actualizando próximos trenes para: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        id_modal = station_data.get('id_modal')
        if not id_modal:
            return jsonify({'error': f'id_modal no disponible para {station_name}'}), 404

        print(f"[REFRESH] Estación: {station_data['nombre']}, id_modal: {id_modal}")

        # Consultar la API de Metro de Madrid usando el id_modal correcto
        api_url = f'https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}'
        print(f"[REFRESH] Consultando: {api_url}")
        
        import requests
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # La API puede devolver JSON (lista o dict) o HTML
        proximos_trenes_html = ''
        try:
            response_json = response.json()
            if isinstance(response_json, list) and response_json:
                proximos_trenes_html = response_json[0].get('data', '')
            elif isinstance(response_json, dict):
                proximos_trenes_html = response_json.get('data', '')
            else:
                proximos_trenes_html = ''
        except Exception:
            proximos_trenes_html = response.text

        print(f"[REFRESH] Respuesta recibida, longitud: {len(proximos_trenes_html)}")
        # ----- DEBUG: Imprimir el HTML crudo -----
        print(f"[DEBUG] RAW HTML from Metro API:\n{proximos_trenes_html}")
        # ----------------------------------------

        # Procesar solo si hay datos reales
        processed_html = convertir_proximos_trenes_a_html_personalizado(proximos_trenes_html, station_data['nombre'])
        
        print(f"[REFRESH] HTML procesado, longitud: {len(processed_html)}")

        if not processed_html:
            # Si el parseo falla, devolver un error especí­fico.
            resultado = {
                'success': False,
                'error': 'No se pudieron procesar los datos de los trenes. La estructura de la web de Metro podrí­a haber cambiado o no hay trenes en este momento.',
                'station_name': station_data['nombre'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            resultado = {
                'success': True,
                'next_trains_html': processed_html,
                'station_name': station_data['nombre'],
                'timestamp': datetime.now().isoformat(),
                'id_modal_used': id_modal,
                'api_url_consulted': api_url
            }
        
        print(f"[REFRESH] Actualización completada para {station_name}")
        return jsonify(resultado)

    except requests.RequestException as e:
        print(f"[REFRESH] Error de red: {e}")
        return jsonify({
            'error': f'Error consultando la API: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        print(f"[REFRESH] Error general: {e}")
        return jsonify({
            'error': f'Error procesando la solicitud: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500

def simulate_ninjascrap_data(station_data):
    """Función de simulación para cuando el scraper Ninja no está disponible"""
    return {
        'proximos_trenes_html': f'<div class="simulated-data"><p>Datos simulados para {station_data["nombre"]}</p><p>Próximos trenes: 2 min, 5 min, 8 min</p></div>',
        'estado_ascensores': 'Operativo (simulado)',
        'estado_escaleras': 'Operativo (simulado)',
        'ultima_actualizacion': 'Simulado',
        'timestamp_scraping': datetime.now().isoformat()
    }

# ============================================================================
# NUEVO ENDPOINT PARA DATOS CRUDOS DE PRÓXIMOS TRENES
# ============================================================================

@app.route('/api/station/raw-trains/<station_name>')
def get_raw_trains_data(station_name):
    """Devuelve datos crudos de próximos trenes en formato JSON para procesamiento en frontend"""
    try:
        print(f"[RAW_TRAINS] Obteniendo datos crudos para: {station_name}")
        
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        id_modal = station_data.get('id_modal')
        if not id_modal:
            return jsonify({'error': f'id_modal no disponible para {station_name}'}), 404

        # Simular datos por ahora
        return jsonify({
            'success': True,
            'station_name': station_name,
            'raw_data': 'Datos crudos simulados'
        })
        
    except Exception as e:
        print(f"[RAW_TRAINS] Error: {e}")
        return jsonify({'error': str(e)}), 500
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
METRO DE MADRID - APLICACIÓN WEB COMPLETA
=========================================

Aplicación Flask para mostrar información del Metro de Madrid
con datos en tiempo real, horarios, mapas y estadí­sticas.
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
login_manager.login_message_category = 'info' # Categorí­a de mensaje para flash

# Rutas de archivos
DB_PATH = 'db/estaciones_fijas_v2.db'
DB_RELACIONAL_PATH = 'db/estaciones_fijas_v2.db'
GTFS_DB_PATH = 'M4/metro_madrid.db'
CSV_DATOS_CLAVE = 'datos_clave_estaciones_definitivo.csv'

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
    'R':  {'id': 'R',  'name': 'Ramal',    'color': '#0055A4', 'color_secondary': '#4A90E2', 'text_color': '#FFFFFF'}
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
        
        # Búsqueda en la columna 'nombre' (que sí­ existe en el CSV)
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
    """Obtiene viajes activos con frecuencias para una hora especí­fica"""
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

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/station', methods=['GET', 'POST'])
@login_required
def station_page():
    """Página de búsqueda de estaciones"""
    resultados = []
    query = ''
    if request.method == 'POST':
        query = request.form.get('station_name', '').strip()
    else:
        query = request.args.get('q', '').strip()
    
        if query:
            resultados = buscar_estacion_por_nombre(query, limite=10)
    return render_template('station.html', resultados=resultados, query=query)

@app.route('/station/<station_name>')
@login_required
def station_page_dynamic(station_name):
    """Página especínica para una estación por nombre"""
    print(f"Buscando estacion: '{station_name}'")
    
    # Buscar la estación en la base de datos
    estaciones = buscar_estacion_por_nombre(station_name, limite=1)
    print(f" Resultados exactos: {len(estaciones) if estaciones else 0}")
    
    if estaciones:
        # Estación encontrada exactamente
        estacion_data = estaciones[0]
        print(f" Estación encontrada exactamente: {estacion_data['nombre']}")
        return render_template('station.html', 
                             station_name=station_name,
                             station_data=estacion_data,
                             auto_load=True)
    else:
        # Estación no encontrada exactamente, buscar coincidencias para mostrar opciones
        print(f" Buscando coincidencias para: '{station_name}'")
        estaciones_coincidencia = buscar_estacion_por_nombre(station_name, limite=10)
        print(f" Coincidencias encontradas: {len(estaciones_coincidencia) if estaciones_coincidencia else 0}")
        
        if estaciones_coincidencia:
            # Encontró coincidencias, mostrar página con opciones de búsqueda
            print(f" Mostrando opciones de búsqueda para: '{station_name}'")
            return render_template('station.html', 
                                 station_name=station_name,
                                 station_data=None,
                                 auto_load=False,
                                 search_results=estaciones_coincidencia,
                                 search_query=station_name)
        else:
            # No hay coincidencias, mostrar página de búsqueda vacía
            print(f" No se encontraron coincidencias para: '{station_name}'")
            return render_template('station.html', 
                                 station_name=station_name,
                                 station_data=None,
                                 auto_load=False)

@app.route('/station/id/<int:station_id>')
@login_required
def station_page_by_id(station_id):
    """Página especínica para una estación por ID fijo"""
    # Solo renderizar la plantilla sin pasar variables
    # El JavaScript se encargará de cargar los datos
    return render_template('station.html')

@app.route('/line')
@login_required
def line_redirect():
    """Redirige /line a /1 (Línea 1)"""
    return redirect(url_for('line_detail', line_id='1'))

@app.route('/line/<line_id>')
@login_required
def line_detail(line_id):
    """Página de detalle de una línea, ahora unificada y robusta."""
    line_info = LINEAS_CONFIG.get(line_id)
    if not line_info:
        return "Linea no encontrada", 404

    # Añadimos la clave 'linea' para mantener compatibilidad con plantillas que la usen
    line_info['linea'] = line_id
    
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
                    'descripcion': row[1] if row[1] else 'Sin descripción'
                }
            else:
                line_status_data = {
                    'estado': 'Normal',
                    'descripcion': 'Circulación normal'
                }
        else:
            line_status_data = {
                'estado': 'Normal',
                'descripcion': 'Circulación normal'
            }
        
        conn.close()
        
    except Exception as e:
        print(f"Error obteniendo estado de línea {line_id}: {e}")
        line_status_data = {
            'estado': 'No disponible',
            'descripcion': 'Estado no disponible'
        }
    
    line_info['status'] = line_status_data

    # Obtener todas las demás líneas para la barra lateral
    other_lines = [config for id, config in LINEAS_CONFIG.items() if id != line_id]

    return render_template('line_detail.html', line_info=line_info, other_lines=other_lines)

@app.route('/lines-overview')
@login_required
def lines_overview():
    """Ruta obsoleta que ahora redirige a /status."""
    return redirect(url_for('status'))

@app.route('/map')
@login_required
def map_view():
    return render_template('map.html')

@app.route('/schedules')
@login_required
def schedules():
    return render_template('schedules.html')

@app.route('/seguridad')
@login_required
def seguridad():
    return render_template('seguridad.html')

@app.route('/about_us')
@login_required
def about_us():
    return render_template('about_us.html')

@app.route('/about_me')
@login_required
def about_me():
    return render_template('about_me.html')

@app.route('/about_u')
@login_required
def about_u():
    return render_template('about_u.html')

@app.route('/test-modern-trains')
@login_required
def test_modern_trains():
    """Página de prueba para el sistema moderno de trenes"""
    return render_template('test_modern_trains.html')

@app.route('/status')
@login_required
def status():
    return render_template('status.html')

@app.route('/station/<nombre>')
@login_required
def station_page_by_name(nombre):
    return render_template('station.html', nombre=nombre)

@app.route('/station/<lineNumber>/<stationId>')
@login_required
def station_page_by_line_and_id(lineNumber, stationId):
    return render_template('station.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/station/search')
def search_station_api():
    """API para buscar estaciones por nombre (para autocompletado)"""
    query = request.args.get('q', '').strip() or request.args.get('term', '').strip()
    if not query:
        return jsonify([])

    # Usar el nuevo sistema de búsqueda con datos clave
    estaciones = buscar_estacion_por_nombre(query, limite=15)
    
    # Formatear resultados para autocompletado
    resultados = []
    
    for estacion in estaciones:
        resultados.append({
            'nombre': estacion['nombre'],
            'linea': estacion['linea'],
            'id_fijo': estacion['id_fijo'],
            'id_modal': estacion.get('id_modal'),
            'orden': estacion.get('orden'),
            'url': estacion.get('url'),
            'direccion_ida': estacion.get('direccion_ida'),
            'direccion_vuelta': estacion.get('direccion_vuelta'),
            'tabla_origen': estacion.get('tabla_origen')
        })
    
    return jsonify(resultados)

@app.route('/api/lines')
def get_lines():
    """Endpoint para obtener todas las líneas disponibles"""
    try:
        # Leer el CSV de datos clave para obtener las líneas
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        # Obtener líneas únicas
        lineas_unicas = df['linea'].unique()
        
        lineas_reales = []
        for linea_db in lineas_unicas:
            # Convertir a string y limpiar
            linea_id = str(linea_db).strip()
            
            # Solo incluir si está en LINEAS_CONFIG
            if linea_id in LINEAS_CONFIG:
                config = LINEAS_CONFIG[linea_id]
                lineas_reales.append({
                    'id': linea_id,
                    'name': config['name'],
                    'color': config['color'],
                    'color_secondary': config['color_secondary'],
                    'text_color': config['text_color']
                })
        
        return jsonify({
            'lines': lineas_reales,
            'total': len(lineas_reales)
        })
    except Exception as e:
        print(f"Error en /api/lines: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """Endpoint para obtener estadí­sticas del dashboard"""
    try:
        # Conectar a la base de datos de estaciones fijas
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Contar estaciones únicas y líneas activas
        estaciones_unicas = 0
        lineas_activas = 0
        total_estaciones = 0
        
        # Verificar cada tabla de línea
        line_tables = [f'linea_{i}' for i in range(1, 13)] + ['linea_Ramal']
        
        for tabla in line_tables:
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                if count > 0:
                    lineas_activas += 1
                    total_estaciones += count
                    
                    # Contar estaciones únicas por nombre
                    cursor.execute(f"SELECT COUNT(DISTINCT nombre) FROM {tabla}")
                    estaciones_unicas += cursor.fetchone()[0]
            except sqlite3.OperationalError:
                continue
        
        conn.close()
        
        return jsonify({
            'statistics': {
                'unique_stations': estaciones_unicas,
                'active_lines': lineas_activas,
                'total_stations': total_estaciones,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error en /api/dashboard/stats: {e}")
        return jsonify({
            'statistics': {
                'unique_stations': 0,
                'active_lines': 0,
                'total_stations': 0,
                'last_updated': datetime.now().isoformat()
            }
        }), 500

@app.route('/api/stations/all')
def get_all_stations():
    """Obtener todas las estaciones con coordenadas para el mapa"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Usar la nueva tabla combinada que tiene coordenadas
        cursor.execute("""
            SELECT id_fijo, nombre, linea, latitud, longitud, zona_tarifaria, 
                   estacion_accesible, correspondencias
            FROM estaciones_completas 
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
            ORDER BY linea, orden_en_linea
        """)
        
        stations = []
        for row in cursor.fetchall():
            id_fijo, nombre, linea, lat, lon, zona, accesible, correspondencias = row
            
            # Procesar correspondencias
            corr_list = []
            if correspondencias:
                try:
                    corr_data = eval(correspondencias)
                    if isinstance(corr_data, list):
                        corr_list = [str(corr) for corr in corr_data]
                except:
                    pass
            
            station = {
                'id': id_fijo,
                'name': nombre,
                'line': linea,
                'lat': float(lat) if lat else None,
                'lon': float(lon) if lon else None,
                'zone': zona,
                'accessible': accesible == 'Sí­',
                'connections': corr_list
            }
            stations.append(station)
        
        conn.close()
        
        print(f" Mapa: {len(stations)} estaciones con coordenadas")
        return jsonify(stations)
        
    except Exception as e:
        print(f" Error en /api/stations/all: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stations/accesses')
def get_station_accesses():
    """Obtener todos los accesos/salidas de estaciones desde stops.txt para mostrar en el mapa"""
    try:
        import os
        import csv
        
        accesses = []
        stops_file = 'M4/stops.txt'
        
        if not os.path.exists(stops_file):
            return jsonify({'error': 'Archivo stops.txt no encontrado'}), 404
        
        with open(stops_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Solo procesar accesos (location_type = 2)
                if row.get('location_type') == '2':
                    stop_name = row.get('stop_name', '')
                    stop_desc = row.get('stop_desc', '')
                    lat = row.get('stop_lat')
                    lon = row.get('stop_lon')
                    
                    if lat and lon:
                        # Determinar tipo de acceso
                        access_type = 'exit'  # Por defecto es salida
                        emoji = '🚪'  # Emoji por defecto
                        
                        if 'ascensor' in stop_name.lower():
                            access_type = 'elevator'
                            emoji = '🛗'
                        elif 'escalera' in stop_name.lower() or 'escalator' in stop_name.lower():
                            access_type = 'escalator'
                            emoji = '⬆️'
                        
                        access = {
                            'name': stop_name,
                            'description': stop_desc,
                            'lat': float(lat),
                            'lon': float(lon),
                            'type': access_type,
                            'emoji': emoji
                        }
                        accesses.append(access)
        
        print(f" Mapa: {len(accesses)} accesos/salidas cargados")
        return jsonify(accesses)
        
    except Exception as e:
        print(f" Error en /api/stations/accesses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lines/<line_id>/stations')
def get_line_stations(line_id):
    """Devuelve las estaciones de una línea especí­fica, incluyendo su estado (cerrada/operativa) y motivo de cierre si aplica"""
    # Mapear line_id a número de línea
    line_mapping = {
        '1': 1, '2': 2, '3': 3, '4': 4,
        '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, '10': 10, '11': 11, '12': 12,
        'R': 'Ramal', 'Ramal': 'Ramal'
    }
    
    line_number = line_mapping.get(line_id)
    if line_number is None:
        return jsonify({'error': f'Línea {line_id} no encontrada'}), 404
    
    try:
        # Leer el CSV de datos clave
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        # Filtrar por línea
        if line_number == 'Ramal':
            stations_df = df[df['linea'] == 'Ramal']
        else:
            # Convertir la columna linea a int para comparación correcta
            df['linea'] = pd.to_numeric(df['linea'], errors='coerce')
            stations_df = df[df['linea'] == int(line_number)]
        
        # Obtener estado de la línea desde la base de datos
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estado_lineas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linea TEXT NOT NULL,
                estado TEXT NOT NULL,
                clase_css TEXT,
                descripcion TEXT,
                estaciones_cerradas TEXT,
                accesos_cerrados TEXT,
                incidencias TEXT,
                url_origen TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        cursor.execute("""
            SELECT estaciones_cerradas FROM estado_lineas 
            WHERE linea = ? ORDER BY timestamp DESC LIMIT 1
        """, (line_id,))
        row = cursor.fetchone()
        conn.close()
        estaciones_cerradas = []
        motivos_cierre = {}
        if row:
            try:
                estaciones_cerradas_data = json.loads(row['estaciones_cerradas'])
                estaciones_cerradas = [e['nombre'] for e in estaciones_cerradas_data]
                motivos_cierre = {e['nombre']: e.get('motivo', '') for e in estaciones_cerradas_data}
            except Exception:
                estaciones_cerradas = []
                motivos_cierre = {}
        
        # Ordenar por la columna orden
        stations_df = stations_df.sort_values('orden')
        
        # Identificar estaciones terminus
        if not stations_df.empty:
            terminus_ids = [stations_df.iloc[0]['id_fijo'], stations_df.iloc[-1]['id_fijo']]
        else:
            terminus_ids = []

        # Formatear las estaciones para el frontend
        stations_data = []
        for _, row in stations_df.iterrows():
            def clean_value(x, default=None):
                return default if pd.isna(x) else x

            def to_bool(val):
                if pd.isna(val): return False
                return str(val).lower() in ['true', '1', 't', 'y', 'yes', 'sí­', 'si', 'verdadero']

            nombre_estacion = clean_value(row.get('nombre'), 'N/A')
            id_fijo = int(clean_value(row.get('id_fijo'), 0))
            cerrada = nombre_estacion in estaciones_cerradas
            motivo_cierre = motivos_cierre.get(nombre_estacion) if cerrada else None

            services = {
                'accessible': to_bool(row.get('accessible')),
                'defibrillator': to_bool(row.get('defibrillator')),
                'elevators': to_bool(row.get('elevators')),
                'escalators': to_bool(row.get('escalators')),
                'historical': to_bool(row.get('historical')),
                'mobileCoverage': to_bool(row.get('mobileCoverage')),
                'shops': to_bool(row.get('shops'))
            }

            # Obtener correspondencias de la columna 'correspondencias' que es un string tipo "['2', '7']"
            try:
                correspondencias_str = clean_value(row.get('correspondencias'), '[]')
                correspondencias = json.loads(correspondencias_str.replace("'", '"'))
            except (json.JSONDecodeError, TypeError):
                correspondencias = []

            station_info = {
                'id_fijo': id_fijo,
                'name': nombre_estacion,
                'orden': int(clean_value(row.get('orden'), 0)),
                'url': clean_value(row.get('url')),
                'tariffZone': clean_value(row.get('zona'), 'A'),
                'services': services,
                'cerrada': cerrada,
                'motivo_cierre': motivo_cierre,
                'is_terminus': id_fijo in terminus_ids,
                'correspondencias': correspondencias
            }
            stations_data.append(station_info)
        
        return jsonify({'stations': stations_data})
    except Exception as e:
        # Log del error para depuración
        print(f"Error en get_line_stations para línea {line_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500

@app.route('/api/station/detailed/<station_name>')
def get_detailed_station_data(station_name):
    """Obtiene datos detallados de una estación usando el scraper."""
    # Temporalmente deshabilitado - el scraper no tiene el método scrape_station_by_name
    # from herramientas.scraper_datos_detallados import ScraperDatosDetallados
    # scraper = ScraperDatosDetallados()
    # data = scraper.scrape_station_by_name(station_name)
    # scraper.close()
    # if data:
    #     return jsonify(data)
    # else:
    #     return jsonify({'error': 'No se pudieron obtener los datos detallados'}), 404
    return jsonify({'error': 'Funcionalidad temporalmente deshabilitada'}), 404

@app.route('/api/station/realtime/<station_name>')
def get_realtime_station_data(station_name):
    """Endpoint que devuelve datos en tiempo real y estáticos de una estación usando la base moderna"""
    try:
        print(f"--- REALTIME_API: Buscando datos para: '{station_name}' ---")
        estaciones_exactas = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones_exactas:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        estacion_linea = estaciones_exactas[0]
        id_fijo = estacion_linea['id_fijo']
        linea = estacion_linea['linea']
        url = estacion_linea.get('url', '')
        id_modal = estacion_linea.get('id_modal')

        # 1. Obtener próximos trenes (scraper Ninja)
        proximos_trenes_html = '<div class="no-data">No disponible</div>'
        if id_modal:
            try:
                # Usar el scraper Ninja para obtener datos en tiempo real
                from herramientas.scraper_ninja_tiempo_real import ScraperNinjaTiempoReal
                scraper = ScraperNinjaTiempoReal()
                url_proximos_trenes = f"https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}"
                ninja_data = scraper.scrape_estacion_tiempo_real(url_proximos_trenes)
                proximos_trenes_html = ninja_data.get('proximos_trenes_html', '<div class="no-data">No disponible</div>') if ninja_data else '<div class="no-data">No disponible</div>'
                print(f"--- REALTIME_API: Datos Ninja obtenidos para ID {id_modal} ---")
            except Exception as e:
                print(f"--- REALTIME_API: Error Ninja: {e} ---")

        # 2. Datos detallados (placeholder)
        detalles_scrapeados = {'info': 'Datos detallados temporalmente no disponibles'}

        # 3. Datos guardados de la base moderna
        datos_guardados = []
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            tabla_linea = f"linea_{linea}"
            cursor.execute(f"""
                SELECT id_fijo, nombre, zona_tarifaria, estacion_accesible, 
                       ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                       bibliometro, tiendas, correspondencias, url, servicios,
                       accesos, vestibulos, nombres_acceso, intercambiadores
                FROM {tabla_linea} 
                WHERE id_fijo = ?
            """, (id_fijo,))
            row = cursor.fetchone()
            conn.close()
            if row:
                id_fijo, nombre, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url, servicios, accesos, vestibulos, nombres_acceso, intercambiadores = row
                # Procesar servicios
                servicios_list = []
                servicios_estructurados = []
                if servicios:
                    servicios_text = servicios.replace(';', ',').replace(';', ',')
                    servicios_list = [s.strip() for s in servicios_text.split(',') if s.strip()]
                    # Crear objetos estructurados para servicios
                    iconos_servicios = {
                        'Ascensores': '🚇', 'Desfibrilador': '💓', 'Escaleras mecanicas': '🚇',
                        'Cobertura movil': '📱', 'Estacion accesible': '♿', 'Tiendas': '🏪',
                        'Bibliometro': '📚', 'Oficina de gestion TTP': '🏢', 'Parking disuasorio de pago': '🅿️',
                        'Quioscos ONCE': '👁️', 'adaptada para discapacitados': '♿'
                    }
                    for servicio in servicios_list:
                        icono = iconos_servicios.get(servicio, '🔧')
                        servicios_estructurados.append({
                            'tipo_servicio': servicio,  # Cambiar 'nombre' por 'tipo_servicio'
                            'icono': icono,
                            'disponible': True
                        })
                
                # Procesar correspondencias
                corr_list = []
                if correspondencias:
                    try:
                        corr_data = eval(correspondencias)
                        if isinstance(corr_data, list):
                            corr_list = [str(corr) for corr in corr_data]
                    except:
                        pass
                
                # Procesar accesos
                accesos_list = []
                accesos_estructurados = []
                if accesos:
                    accesos_text = accesos.replace(';', ',').replace(';', ',')
                    accesos_list = [a.strip() for a in accesos_text.split(',') if a.strip()]
                    # Intentar parsear accesos para crear objetos estructurados
                    for acceso in accesos_list:
                        # Mejorar el parsing de accesos
                        nombre = acceso
                        vestibulo = 'No especificado'
                        direccion = None  # No incluir si no hay dirección
                        
                        # Patrón 1: "Nombre - Vestí­bulo: Dirección"
                        if ' - ' in acceso and ':' in acceso:
                            partes = acceso.split(' - ', 1)
                            nombre = partes[0].strip()
                            resto = partes[1].strip()
                            if ':' in resto:
                                vestibulo_parte, direccion = resto.split(':', 1)
                                vestibulo = vestibulo_parte.strip()
                                direccion = direccion.strip()
                        
                        # Patrón 2: "Nombre - Vestí­bulo" (sin dirección)
                        elif ' - ' in acceso:
                            partes = acceso.split(' - ', 1)
                            nombre = partes[0].strip()
                            vestibulo = partes[1].strip()
                        
                        # Patrón 3: Solo nombre
                        else:
                            nombre = acceso.strip()
                        
                        # Filtrar accesos mal formateados o muy largos
                        if (len(nombre) > 50 or nombre.isdigit() or len(nombre) < 3 or
                            ':' in nombre or nombre.startswith('pares') or 
                            nombre.startswith('4:') or nombre.startswith('31 (') or
                            'Pedro ValdiviaPedro Valdivia' in nombre or
                            'Prí­ncipe de Vergara)' in nombre):
                            continue
                        
                        # Limpiar vestí­bulos muy largos
                        if len(vestibulo) > 100:
                            vestibulo = vestibulo[:50] + "..."
                        
                        # Solo incluir si tiene un nombre válido y no es redundante
                        if (nombre and nombre != 'No especificado' and 
                            not nombre.startswith('pares') and 
                            not nombre.startswith('4:') and
                            not nombre.startswith('31 (') and
                            'Pedro ValdiviaPedro Valdivia' not in nombre and
                            'Prí­ncipe de Vergara)' not in nombre):
                            
                            acceso_obj = {
                                'nombre': nombre,
                                'vestibulo': vestibulo
                            }
                            # Solo incluir dirección si existe y no es "Dirección no especificada"
                            if direccion and direccion != 'Dirección no especificada':
                                acceso_obj['direccion'] = direccion
                            
                            accesos_estructurados.append(acceso_obj)
                
                # Formatear datos para compatibilidad con el frontend
                datos_formateados = {
                    'id_fijo': id_fijo,
                    'nombre': nombre,
                    'linea': linea,
                    'url': url,
                    'id_modal': id_modal,
                    'zona_tarifaria': zona,
                    'ultima_actualizacion_detalles': datetime.now().isoformat(),
                    'modulos': {
                        'servicios': {
                            'disponible': len(servicios_list) > 0,
                            'datos': servicios_estructurados,
                            'total': len(servicios_list)
                        },
                        'accesos': {
                            'disponible': len(accesos_list) > 0,
                            'datos': accesos_estructurados,
                            'total': len(accesos_list)
                        },
                        'conexiones': {
                            'disponible': len(corr_list) > 0,
                            'datos': corr_list,
                            'total': len(corr_list)
                        }
                    },
                    # Datos estructurados para el frontend
                    'servicios_estructurados': servicios_estructurados,
                    'accesos_estructurados': accesos_estructurados,
                    # Datos legacy para compatibilidad
                    'servicios': '; '.join(servicios_list) if servicios_list else '',
                    'accesos': '; '.join(accesos_list) if accesos_list else '',
                    'correspondencias': '; '.join(corr_list) if corr_list else ''
                }
                datos_guardados.append(datos_formateados)
        except Exception as e:
            print(f"Error obteniendo datos de la nueva BD para {station_name}: {e}")
            datos_guardados.append({
                'id_fijo': id_fijo,
                'nombre': estacion_linea['nombre'],
                'linea': linea,
                'url': url,
                'id_modal': id_modal,
                'servicios': '',
                'accesos': '',
                'correspondencias': ''
            })
        print(f"--- REALTIME_API: Devolviendo datos para '{station_name}' ---")
        return jsonify({
            'next_trains_html': proximos_trenes_html,
            'details': detalles_scrapeados,
            'stored_data': datos_guardados,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[REALTIME_API] Error: {e}")
        return jsonify({'error': f'Error obteniendo datos: {str(e)}'}), 500

def convertir_proximos_trenes_a_html_personalizado(html_content, station_name):
    """
    Convierte el HTML de la API de Metro en un formato personalizado,
    extrayendo de forma precisa los datos de cada línea y dirección.
    """
    try:
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html_content, 'html.parser')
        colores_lineas = {
            '1': '#00AEEF', '2': '#FF0000', '3': '#FFDF00', '4': '#824100',
            '5': '#339900', '6': '#999999', '7': '#FF6600', '8': '#FF69B4',
            '9': '#990066', '10': '#000099', '11': '#006600', '12': '#999933',
            'Ramal': '#FFFFFF'
        }
        
        lineas_data = {}

        # Busca cada bloque de información de una dirección de una línea
        direction_blocks = soup.find_all('div', class_='text__info-estacion--tit-icon')

        # Caso especial para el Ramal
        ramal_block = soup.find('img', src=re.compile(r'ramal\.svg'))
        if ramal_block:
            ramal_container = ramal_block.find_parent('div', class_='small-12')
            if ramal_container:
                # Buscar el texto "Actualmente sin previsión"
                sin_prevision = ramal_container.find('p', string=re.compile(r'Actualmente sin previsión'))
                if sin_prevision:
                    lineas_data['Ramal'] = {
                        'numero': 'Ramal',
                        'nombre': 'Ramal',
                        'color': '#FFFFFF',
                        'logo': '/static/logos/lineas/ramal.svg',
                        'direcciones': [{
                            'destino': 'Sin previsión',
                            'tiempos': [],
                            'proximo_tren': None,
                            'todos_tiempos': [],
                            'sin_prevision': True
                        }]
                    }

        for block in direction_blocks:
            main_block = block.find_parent('div', class_=re.compile(r'columns'))
            if not main_block: continue

            line_img = main_block.find('img', src=re.compile(r'linea-'))
            if not line_img: continue
            
            linea_num_match = re.search(r'linea-(\w+)', line_img.get('src', ''))
            if not linea_num_match: continue
            linea_num = linea_num_match.group(1).replace('-circular', '')
            
            destino_span = block.find('span', class_='tiempo-espera__destino', string=re.compile(r'Direcci.n|Andén'))
            if not destino_span: continue
            
            destino_text = destino_span.get_text(strip=True)
            
            # CORRECCIÓN: Se quita la palabra "Dirección", etc. del inicio del texto.
            destino = re.sub(r'^(Direcci.n|Destino|And.n)\s*', '', destino_text, flags=re.IGNORECASE).strip()
            
            destino = re.sub(r'\s*-\s*\d+$', '', destino).strip()

            if not destino or len(destino) < 3: continue

            tiempos = []
            time_spans = block.find_all('span', class_='tiempo-espera__minutos')
            for span in time_spans:
                time_match = re.search(r'(\d+)\s*min', span.get_text())
                if time_match:
                    tiempos.append(time_match.group(1))

            if not tiempos: continue

            if linea_num not in lineas_data:
                lineas_data[linea_num] = {
                    'color': colores_lineas.get(linea_num, '#333333'),
                    'direcciones': []
                }
            
            if not any(d['destino'] == destino for d in lineas_data[linea_num]['direcciones']):
                lineas_data[linea_num]['direcciones'].append({
                    'destino': destino,
                    'tiempos': tiempos
                })
        
        if not lineas_data:
            return ''

        html_personalizado = '<div class="lines-grid-multi">'
        for linea_num, data in sorted(lineas_data.items()):
            color = data['color']
            direcciones = data['direcciones']
            linea_nombre = f'Línea {linea_num}'
            linea_svg = f'linea-{linea_num}'
            num_sentidos = len(direcciones)
            sentido_texto = f"{num_sentidos} sentido{'s' if num_sentidos > 1 else ''}"
            
            html_personalizado += f'''
                <div class="line-card-multi" style="border-left-color: {color}">
                    <div class="line-header" style="color: {color}">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <img src="/static/logos/lineas/{linea_svg}.svg" alt="{linea_nombre}" style="width: 20px; height: 20px;">
                            <strong>{linea_nombre}</strong>
                        </div>
                        <span class="directions-count">{sentido_texto}</span>
                    </div>
                    <div class="directions-container">
            '''
            for i, direccion in enumerate(direcciones):
                direction_icon = "⬅️" if i == 0 else "➡️"
                direction_name = "IDA" if num_sentidos > 1 and i == 0 else "VUELTA" if num_sentidos > 1 else "ÚNICO"
                
                tiempos_html = " y ".join([f"<strong>{t} min</strong>" for t in direccion['tiempos']])
                
                html_personalizado += f'''
                        <div class="line-direction" style="border-left: 3px solid {color}">
                            <div class="direction-header">
                                <span class="direction-icon">{direction_icon}</span>
                                <span class="direction-name">{direction_name}</span>
                            </div>
                            <div class="line-name" style="color: {color}">
                                <img src="/static/logos/lineas/{linea_svg}.svg" alt="{linea_nombre}" style="width: 16px; height: 16px; margin-right: 5px;">
                                {linea_nombre}
                            </div>
                            <div class="line-destination">
                                <strong>Destino:</strong> {direccion['destino']}
                            </div>
                            <div class="line-times">
                                <strong>Tiempos:</strong> {tiempos_html}
                            </div>
                        </div>
                '''
            html_personalizado += '</div></div>'
        html_personalizado += '</div>'
        return html_personalizado
        
    except Exception as e:
        print(f"[ERROR] Excepción en convertir_proximos_trenes: {e}")
        return ""

@app.route('/api/station/status/database')
def get_station_status_database():
    """Endpoint de depuración para ver el contenido de la tabla station_status."""
    DB_STATUS_PATH = 'db/estaciones_fijas_v2.db'
    if not os.path.exists(DB_STATUS_PATH):
        return jsonify({'error': 'La base de datos de estado no existe.'}), 404
        
    try:
        conn = sqlite3.connect(DB_STATUS_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='station_status'")
        if not cursor.fetchone():
            return jsonify({'error': 'La tabla station_status no existe.'}), 404
        
        cursor.execute("SELECT * FROM station_status ORDER BY last_updated DESC LIMIT 50")
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        
        conn.close()
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/station/status/check')
def check_station_status():
    """Endpoint para verificar el estado de una estación especí­fica"""
    station_name = request.args.get('station', '')
    if not station_name:
        return jsonify({'error': 'Debe especificar una estación'}), 400
        
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM station_status 
            WHERE station_name LIKE ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (f'%{station_name}%',))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify(dict(row))
        else:
            return jsonify({'error': f'No se encontró información para la estación {station_name}'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NINJA SCRAPER - DATOS EN TIEMPO REAL
# ============================================================================

@app.route('/api/station/ninjascrap/<station_name>')
def ninjascrap_station(station_name):
    """Endpoint para ejecutar Scraper Ninja en una estación especí­fica"""
    try:
        print(f"[NINJA] Iniciando scraper para estación: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404
        
        station_data = estaciones[0]
        print(f"[NINJA] Estación encontrada: {station_data['nombre']} (Línea {station_data['linea']})")
        
        # Verificar que tenga URL
        if not station_data.get('url'):
            return jsonify({'error': f'La estación {station_name} no tiene URL configurada'}), 404
        
        # Ejecutar scraper Ninja
        scraper = ScraperNinjaTiempoReal()
        ninjascrap_data = scraper.scrape_estacion_tiempo_real(station_data['url'])
        
        if not ninjascrap_data:
            return jsonify({'error': 'Error ejecutando scraper Ninja'}), 500
        
        # Combinar datos estáticos con datos dinámicos
        resultado = {
            'station_name': station_data['nombre'],
            'linea': station_data['linea'],
            'station_url': station_data['url'],
            'zona_tarifaria': station_data.get('zona_tarifaria', 'No disponible'),
            'last_update': ninjascrap_data.get('ultima_actualizacion', 'No disponible'),
            'proximos_trenes_html': ninjascrap_data.get('proximos_trenes_html', ''),
            'estado_ascensores': ninjascrap_data.get('estado_ascensores', 'No disponible'),
            'estado_escaleras': ninjascrap_data.get('estado_escaleras', 'No disponible'),
            'timestamp_scraping': ninjascrap_data.get('timestamp_scraping', ''),
            'scraper_status': 'success'
        }
        
        print(f"[NINJA] Scraping completado para {station_name}")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[NINJA] Error en scraper: {e}")
        return jsonify({
            'error': f'Error ejecutando scraper: {str(e)}',
            'scraper_status': 'error'
        }), 500

@app.route('/api/station/refresh-trains/<station_name>')
def refresh_trains_with_ninja(station_name):
    """Devuelve los próximos trenes usando el id_modal correcto de la base de datos."""
    try:
        print(f"[REFRESH] Actualizando próximos trenes para: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        id_modal = station_data.get('id_modal')
        if not id_modal:
            return jsonify({'error': f'id_modal no disponible para {station_name}'}), 404

        print(f"[REFRESH] Estación: {station_data['nombre']}, id_modal: {id_modal}")

        # Consultar la API de Metro de Madrid usando el id_modal correcto
        api_url = f'https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}'
        print(f"[REFRESH] Consultando: {api_url}")
        
        import requests
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # La API puede devolver JSON (lista o dict) o HTML
        proximos_trenes_html = ''
        try:
            response_json = response.json()
            if isinstance(response_json, list) and response_json:
                proximos_trenes_html = response_json[0].get('data', '')
            elif isinstance(response_json, dict):
                proximos_trenes_html = response_json.get('data', '')
            else:
                proximos_trenes_html = ''
        except Exception:
            proximos_trenes_html = response.text

        print(f"[REFRESH] Respuesta recibida, longitud: {len(proximos_trenes_html)}")
        # ----- DEBUG: Imprimir el HTML crudo -----
        print(f"[DEBUG] RAW HTML from Metro API:\n{proximos_trenes_html}")
        # ----------------------------------------

        # Procesar solo si hay datos reales
        processed_html = convertir_proximos_trenes_a_html_personalizado(proximos_trenes_html, station_data['nombre'])
        
        print(f"[REFRESH] HTML procesado, longitud: {len(processed_html)}")

        if not processed_html:
            # Si el parseo falla, devolver un error especí­fico.
            resultado = {
                'success': False,
                'error': 'No se pudieron procesar los datos de los trenes. La estructura de la web de Metro podrí­a haber cambiado o no hay trenes en este momento.',
                'station_name': station_data['nombre'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            resultado = {
                'success': True,
                'next_trains_html': processed_html,
                'station_name': station_data['nombre'],
                'timestamp': datetime.now().isoformat(),
                'id_modal_used': id_modal,
                'api_url_consulted': api_url
            }
        
        print(f"[REFRESH] Actualización completada para {station_name}")
        return jsonify(resultado)

    except requests.RequestException as e:
        print(f"[REFRESH] Error de red: {e}")
        return jsonify({
            'error': f'Error consultando la API: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        print(f"[REFRESH] Error general: {e}")
        return jsonify({
            'error': f'Error procesando la solicitud: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500

def simulate_ninjascrap_data(station_data):
    """Función de simulación para cuando el scraper Ninja no está disponible"""
    return {
        'proximos_trenes_html': f'<div class="simulated-data"><p>Datos simulados para {station_data["nombre"]}</p><p>Próximos trenes: 2 min, 5 min, 8 min</p></div>',
        'estado_ascensores': 'Operativo (simulado)',
        'estado_escaleras': 'Operativo (simulado)',
        'ultima_actualizacion': 'Simulado',
        'timestamp_scraping': datetime.now().isoformat()
    }

# ============================================================================
# NUEVO ENDPOINT PARA DATOS CRUDOS DE PRÓXIMOS TRENES
# ============================================================================

@app.route('/api/station/raw-trains/<station_name>')
def get_raw_trains_data(station_name):
    """Devuelve datos crudos de próximos trenes en formato JSON para procesamiento en frontend"""
    try:
        print(f"[RAW_TRAINS] Obteniendo datos crudos para: {station_name}")
        
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        id_modal = station_data.get('id_modal')
        if not id_modal:
            return jsonify({'error': f'id_modal no disponible para {station_name}'}), 404

        print(f"[RAW_TRAINS] Estación: {station_data['nombre']}, id_modal: {id_modal}")

        # Consultar la API de Metro de Madrid
        api_url = f'https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}'
        print(f"[RAW_TRAINS] Consultando: {api_url}")
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # Extraer HTML de la respuesta
        proximos_trenes_html = ''
        try:
            response_json = response.json()
            if isinstance(response_json, list) and response_json:
                proximos_trenes_html = response_json[0].get('data', '')
            elif isinstance(response_json, dict):
                proximos_trenes_html = response_json.get('data', '')
            else:
                proximos_trenes_html = ''
        except Exception:
            proximos_trenes_html = response.text

        print(f"[RAW_TRAINS] HTML obtenido, longitud: {len(proximos_trenes_html)}")

        # Procesar HTML para extraer datos estructurados
        trains_data = parse_raw_trains_html(proximos_trenes_html)
        
        resultado = {
            'success': True,
            'station_name': station_data['nombre'],
            'station_line': station_data['linea'],
            'timestamp': datetime.now().isoformat(),
            'id_modal_used': id_modal,
            'api_url_consulted': api_url,
            'raw_html': proximos_trenes_html,  # Para debugging
            'trains_data': trains_data
        }
        
        print(f"[RAW_TRAINS] Datos procesados exitosamente")
        return jsonify(resultado)

    except requests.RequestException as e:
        print(f"[RAW_TRAINS] Error de red: {e}")
        return jsonify({
            'error': f'Error consultando la API: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500
    except Exception as e:
        print(f"[RAW_TRAINS] Error general: {e}")
        return jsonify({
            'error': f'Error procesando la solicitud: {str(e)}',
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }), 500

def get_line_logo(linea_num):
    """Obtiene el logo correcto para una línea especí­fica"""
    logo_mapping = {
        '1': 'linea-1',
        '2': 'linea-2', 
        '3': 'linea-3',
        '4': 'linea-4',
        '5': 'linea-5',
        '6': 'linea-6-circular',  # Caso especial para línea 6
        '7': 'linea-7',
        '8': 'linea-8',
        '9': 'linea-9',
        '10': 'linea-10',
        '11': 'linea-11',
        '12': 'linea-12-metrosur',  # Caso especial para línea 12
        'Ramal': 'ramal'
    }
    return f'/static/logos/lineas/{logo_mapping.get(linea_num, f"linea-{linea_num}")}.svg'

def parse_raw_trains_html(html_content):
    """
    Parsea el HTML crudo de la API de Metro y extrae datos estructurados
    Devuelve un diccionario con información organizada por línea
    """
    try:
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Configuración de colores de líneas
        colores_lineas = {
            '1': '#00AEEF', '2': '#FF0000', '3': '#FFDF00', '4': '#824100',
            '5': '#339900', '6': '#999999', '7': '#FF6600', '8': '#FF69B4',
            '9': '#990066', '10': '#000099', '11': '#006600', '12': '#999933',
            'Ramal': '#FFFFFF'
        }
        
        lineas_data = {}

        # Buscar cada bloque de información de una dirección de una línea
        direction_blocks = soup.find_all('div', class_='text__info-estacion--tit-icon')

        # Caso especial para el Ramal
        ramal_block = soup.find('img', src=re.compile(r'ramal\.svg'))
        if ramal_block:
            ramal_container = ramal_block.find_parent('div', class_='small-12')
            if ramal_container:
                # Buscar el texto "Actualmente sin previsión"
                sin_prevision = ramal_container.find('p', string=re.compile(r'Actualmente sin previsión'))
                if sin_prevision:
                    lineas_data['Ramal'] = {
                        'numero': 'Ramal',
                        'nombre': 'Ramal',
                        'color': '#FFFFFF',
                        'logo': '/static/logos/lineas/ramal.svg',
                        'direcciones': [{
                            'destino': 'Sin previsión',
                            'tiempos': [],
                            'proximo_tren': None,
                            'todos_tiempos': [],
                            'sin_prevision': True
                        }]
                    }

        for block in direction_blocks:
            main_block = block.find_parent('div', class_=re.compile(r'columns'))
            if not main_block: continue

            # Extraer número de línea de la imagen
            line_img = main_block.find('img', src=re.compile(r'linea-'))
            if not line_img: continue
            
            linea_num_match = re.search(r'linea-(\w+)', line_img.get('src', ''))
            if not linea_num_match: continue
            linea_num = linea_num_match.group(1).replace('-circular', '').replace('-metrosur', '')
            
            # Manejar caso especial del Ramal
            if linea_num == 'ramal':
                linea_num = 'Ramal'
            
            # Extraer destino
            destino_span = block.find('span', class_='tiempo-espera__destino', string=re.compile(r'Direcci.n|Andén'))
            if not destino_span: continue
            
            destino_text = destino_span.get_text(strip=True)
            destino = re.sub(r'^(Direcci.n|Destino|And.n)\s*', '', destino_text, flags=re.IGNORECASE).strip()
            destino = re.sub(r'\s*-\s*\d+$', '', destino).strip()

            if not destino or len(destino) < 3: continue

            # Extraer tiempos
            tiempos = []
            time_spans = block.find_all('span', class_='tiempo-espera__minutos')
            for span in time_spans:
                time_match = re.search(r'(\d+)\s*min', span.get_text())
                if time_match:
                    tiempos.append(int(time_match.group(1)))

            if not tiempos: continue

            # Organizar datos por línea
            if linea_num not in lineas_data:
                lineas_data[linea_num] = {
                    'numero': linea_num,
                    'nombre': f'Línea {linea_num}',
                    'color': colores_lineas.get(linea_num, '#333333'),
                    'logo': get_line_logo(linea_num),
                    'direcciones': []
                }
            
            # Evitar duplicados de destino
            if not any(d['destino'] == destino for d in lineas_data[linea_num]['direcciones']):
                lineas_data[linea_num]['direcciones'].append({
                    'destino': destino,
                    'tiempos': tiempos,
                    'proximo_tren': tiempos[0] if tiempos else None,
                    'todos_tiempos': tiempos
                })

        # Convertir a lista y ordenar por número de línea
        lineas_list = list(lineas_data.values())
        
        # Priorizar la línea actual (si se proporciona)
        def sort_key(linea):
            # Si es la línea actual, ponerla primero
            if hasattr(sort_key, 'linea_actual') and linea['numero'] == sort_key.linea_actual:
                return -1  # Número negativo para que aparezca primero
            # Para líneas numéricas, ordenar por número
            if linea['numero'].isdigit():
                return int(linea['numero'])
            # Para líneas especiales, ponerlas al final
            return 999
        
        # Intentar detectar la línea actual del contexto
        # Buscar en el HTML para ver qué línea es la principal
        linea_actual = None
        if 'Ramal' in lineas_data:
            linea_actual = 'Ramal'
        else:
            # Buscar la primera línea que aparezca
            for linea in lineas_list:
                if linea['numero'].isdigit():
                    linea_actual = linea['numero']
                    break
        
        if linea_actual:
            sort_key.linea_actual = linea_actual
        
        lineas_list.sort(key=sort_key)
        
        return {
            'lineas': lineas_list,
            'total_lineas': len(lineas_list),
            'timestamp_parseo': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[ERROR] Excepción en parse_raw_trains_html: {e}")
        return {
            'lineas': [],
            'total_lineas': 0,
            'error': str(e),
            'timestamp_parseo': datetime.now().isoformat()
        }

# ============================================================================
# ENDPOINTS PARA ESTADO DE LÍNEAS
# ============================================================================

@app.route('/api/lines/status')
def get_lines_status():
    """Endpoint para obtener el estado de todas las líneas"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estado_lineas'")
        if not cursor.fetchone():
            # No hay tabla, crear datos por defecto
            lineas_por_defecto = []
            for linea in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                lineas_por_defecto.append({
                    'number': linea,
                    'name': f'Línea {linea}' if linea != 'R' else 'Línea Ramal',
                    'status': 'normal',
                    'closed_stations': []
                })
            conn.close()
            return jsonify(lineas_por_defecto)
        
        # Obtener el estado más reciente de cada línea
        cursor.execute("""
            SELECT linea, estado, clase_css, descripcion, estaciones_cerradas, 
                   accesos_cerrados, incidencias, url_origen, timestamp
            FROM estado_lineas 
            WHERE id IN (
                SELECT MAX(id) 
                FROM estado_lineas 
                GROUP BY linea
            )
            ORDER BY linea
        """)
        
        lineas_estado = []
        for row in cursor.fetchall():
            linea_data = dict(row)
            # Parsear JSON de estaciones cerradas, accesos cerrados e incidencias
            try:
                estaciones_cerradas = json.loads(linea_data['estaciones_cerradas']) if linea_data['estaciones_cerradas'] else []
                accesos_cerrados = json.loads(linea_data.get('accesos_cerrados', '[]')) if linea_data.get('accesos_cerrados') else []
                incidencias = json.loads(linea_data['incidencias']) if linea_data['incidencias'] else []
            except:
                estaciones_cerradas = []
                accesos_cerrados = []
                incidencias = []
            
            # Convertir al formato que espera el frontend
            linea_formato = {
                'number': linea_data['linea'],
                'name': f"Línea {linea_data['linea']}" if linea_data['linea'] != 'R' else 'Línea Ramal',
                'status': linea_data['estado'].lower() if linea_data['estado'] else 'normal',
                'closed_stations': [est['nombre'] for est in estaciones_cerradas] if estaciones_cerradas else []
            }
            
            lineas_estado.append(linea_formato)
        
        conn.close()
        
        # Si no hay datos, crear datos por defecto
        if not lineas_estado:
            lineas_por_defecto = []
            for linea in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
                lineas_por_defecto.append({
                    'number': linea,
                    'name': f'Línea {linea}' if linea != 'R' else 'Línea Ramal',
                    'status': 'normal',
                    'closed_stations': []
                })
            return jsonify(lineas_por_defecto)
        
        return jsonify(lineas_estado)
        
    except Exception as e:
        print(f"Error en /api/lines/status: {e}")
        # En caso de error, devolver datos por defecto
        lineas_por_defecto = []
        for linea in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']:
            lineas_por_defecto.append({
                'number': linea,
                'name': f'Línea {linea}' if linea != 'R' else 'Línea Ramal',
                'status': 'normal',
                'closed_stations': []
            })
        return jsonify(lineas_por_defecto)

@app.route('/api/station/closed-status/<station_name>')
def get_station_closed_status(station_name):
    """Endpoint para obtener el estado de cierre de una estación especí­fica"""
    try:
        print(f"[DEBUG] Verificando estado de estación: '{station_name}'")
        
        # Función de normalización
        def normalizar(texto):
            if not isinstance(texto, str):
                return ""
            return unicodedata.normalize('NFD', texto).encode('ascii', errors='ignore').decode('utf-8').lower().strip()
        
        # 1. Buscar la estación en el CSV para obtener el ID
        import pandas as pd
        try:
            df_estaciones = pd.read_csv('datos_estaciones/estaciones_procesadas.csv')
            nombre_normalizado = normalizar(station_name)
            
            # Buscar en la columna station_name
            for idx, row in df_estaciones.iterrows():
                if normalizar(row['station_name']) == nombre_normalizado:
                    station_id = row['station_id']
                    print(f"[DEBUG] Estación encontrada en CSV: {row['station_name']} (ID: {station_id})")
                    break
            else:
                print(f"[DEBUG]  Estación '{station_name}' no encontrada en CSV")
                return jsonify({'cerrada': False, 'motivo': None})
                
        except Exception as e:
            print(f"[DEBUG] Error leyendo CSV: {e}")
            return jsonify({'cerrada': False, 'motivo': None})
        
        # 2. Buscar en la base de datos de estado de líneas
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estado_lineas'")
        if not cursor.fetchone():
            print("[DEBUG] No existe tabla estado_lineas")
            return jsonify({'cerrada': False, 'motivo': None})
        
        # Buscar la estación en todas las líneas
        cursor.execute("""
            SELECT estaciones_cerradas, linea, timestamp
            FROM estado_lineas 
            ORDER BY timestamp DESC
        """)
        
        rows = cursor.fetchall()
        print(f"[DEBUG] Procesando {len(rows)} registros de estado")
        
        for row in rows:
            try:
                estaciones_cerradas = json.loads(row[0]) if row[0] else []
                linea = row[1]
                timestamp = row[2]
                
                # Buscar la estación en esta línea
                for estacion in estaciones_cerradas:
                    if normalizar(estacion.get('nombre', '')) == nombre_normalizado:
                        print(f"[DEBUG]  Estación '{station_name}' encontrada cerrada en línea {linea}")
                        return jsonify({
                            'cerrada': True,
                            'motivo': estacion.get('motivo', 'Estación cerrada temporalmente'),
                            'linea': linea,
                            'id_estacion': estacion.get('id_estacion'),
                            'timestamp': timestamp
                        })
                        
            except Exception as e:
                print(f"[DEBUG] Error procesando línea {row[1] if len(row) > 1 else 'desconocida'}: {e}")
                continue
        
        print(f"[DEBUG]  Estación '{station_name}' no encontrada en ninguna línea")
        return jsonify({'cerrada': False, 'motivo': None})
        
    except Exception as e:
        print(f"[DEBUG] Error general: {e}")
        return jsonify({'cerrada': False, 'motivo': None, 'error': str(e)})
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/lines/<line_id>/status')
def get_line_status(line_id):
    """Endpoint para obtener el estado de una línea especí­fica"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verificar si existe la tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estado_lineas'")
        if not cursor.fetchone():
            # No hay tabla, usar detección automática
            print(f"No hay tabla de estado, usando detección automática para línea {line_id}")
            estado_auto = detectar_estado_linea_automatico(line_id)
            conn.close()
            return jsonify({
                'linea': line_id,
                'estado': estado_auto['estado'],
                'descripcion': estado_auto['descripcion'],
                'clase_css': estado_auto['clase_css'],
                'motivo': estado_auto['motivo'],
                'estaciones_cerradas': [],
                'accesos_cerrados': [],
                'incidencias': [],
                'timestamp': datetime.now().isoformat(),
                'detectado_automaticamente': True
            })
        
        # Obtener el estado más reciente de la línea
        cursor.execute("""
            SELECT linea, estado, clase_css, descripcion, estaciones_cerradas, 
                   accesos_cerrados, incidencias, url_origen, timestamp
            FROM estado_lineas 
            WHERE linea = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (line_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # No hay datos en la base de datos, usar detección automática
            print(f" No hay datos de estado, usando detección automática para línea {line_id}")
            estado_auto = detectar_estado_linea_automatico(line_id)
            return jsonify({
                'linea': line_id,
                'estado': estado_auto['estado'],
                'descripcion': estado_auto['descripcion'],
                'clase_css': estado_auto['clase_css'],
                'motivo': estado_auto['motivo'],
                'estaciones_cerradas': [],
                'accesos_cerrados': [],
                'incidencias': [],
                'timestamp': datetime.now().isoformat(),
                'detectado_automaticamente': True
            })
        
        linea_data = dict(row)
        # Parsear JSON de estaciones cerradas, accesos cerrados e incidencias
        try:
            linea_data['estaciones_cerradas'] = json.loads(linea_data['estaciones_cerradas'])
            linea_data['accesos_cerrados'] = json.loads(linea_data.get('accesos_cerrados', '[]'))
            linea_data['incidencias'] = json.loads(linea_data['incidencias'])
        except:
            linea_data['estaciones_cerradas'] = []
            linea_data['accesos_cerrados'] = []
            linea_data['incidencias'] = []
        
        linea_data['detectado_automaticamente'] = False
        return jsonify(linea_data)
        
    except Exception as e:
        print(f" Error en get_line_status para línea {line_id}: {e}")
        # En caso de error, usar detección automática como fallback
        estado_auto = detectar_estado_linea_automatico(line_id)
        return jsonify({
            'linea': line_id,
            'estado': estado_auto['estado'],
            'descripcion': estado_auto['descripcion'],
            'clase_css': estado_auto['clase_css'],
            'motivo': estado_auto['motivo'],
            'estaciones_cerradas': [],
            'accesos_cerrados': [],
            'incidencias': [],
            'timestamp': datetime.now().isoformat(),
            'detectado_automaticamente': True,
            'error_fallback': str(e)
        })

@app.route('/api/lines/status/update')
def update_lines_status():
    """Endpoint para actualizar el estado de todas las líneas"""
    try:
        # Importar el scraper
        from herramientas.scraper_estado_lineas import ScraperEstadoLineas
        
        scraper = ScraperEstadoLineas()
        resultados = scraper.obtener_estado_todas_lineas()
        
        return jsonify({
            'success': True,
            'lineas_procesadas': len(resultados),
            'resultados': resultados,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def inicializar_aplicacion():
    """Función para inicializar la aplicación"""
    print("\n INICIANDO APLICACIÓN METRO DE MADRID")
    print("==================================================")
    
    # 1. (Eliminado) Verificar base de datos fija
    # if not verificar_base_datos_fija():
    #     print("" La aplicación no puede continuar sin la base de datos fija.")
    #     sys.exit(1)
    
    # 2. Cargar datos clave desde CSV
    print("\n CARGANDO DATOS CLAVE...")
    if cargar_datos_clave():
        print(" Datos clave cargados exitosamente")
    else:
        print("No se pudieron cargar los datos clave, usando búsqueda en base de datos")
    
    # 3. Cargar datos GTFS
    if not load_gtfs_data():
        print(" La aplicación no puede continuar sin los datos GTFS.")
        sys.exit(1)

    # 4. Actualizar estado nocturno automáticamente al arrancar
    print("\n VERIFICANDO ESTADO NOCTURNO...")
    if actualizar_estado_nocturno_global():
        print(" Estado nocturno actualizado correctamente")
    else:
        print("Error actualizando estado nocturno")

    # 5. Iniciar auto-updater si está disponible
    if AUTO_UPDATER_AVAILABLE:
        start_auto_updater()
        print(f" Auto-updater iniciado: {get_updater_status()}")
    
    print("\n Aplicación inicializada correctamente")
    print("Servidor iniciado en http://localhost:5000")

def obtener_datos_estacion_relacional(nombre_estacion):
    "Obtiene datos detallados de una estación desde la base de datos relacional"
    try:
        conn = sqlite3.connect(DB_RELACIONAL_PATH)
        cursor = conn.cursor()
        
        # Buscar la estación por nombre
        cursor.execute('''
            SELECT id_fijo, nombre, linea, url, orden_en_linea, ultima_actualizacion
            FROM estaciones 
            WHERE LOWER(nombre) = LOWER(?)
            LIMIT 1
        ''', (nombre_estacion,))
        
        estacion = cursor.fetchone()
        if not estacion:
            conn.close()
            return None
        
        id_fijo, nombre, linea, url, orden_en_linea, ultima_actualizacion = estacion
        
        # Obtener detalles de la estación
        cursor.execute('''
            SELECT direccion_completa, calle, codigo_postal, distrito, barrio, 
                   vestibulos, ultima_actualizacion_detalles
            FROM detalles_estaciones 
            WHERE id_fijo = ?
        ''', (id_fijo,))
        
        detalles = cursor.fetchone()
        
        # Obtener accesos
        cursor.execute('''
            SELECT vestibulo, nombre_acceso, direccion
            FROM accesos 
            WHERE id_fijo = ?
            ORDER BY vestibulo, nombre_acceso
        ''', (id_fijo,))
        
        accesos = cursor.fetchall()
        
        # Obtener servicios
        cursor.execute('''
            SELECT tipo_servicio, disponible
            FROM servicios 
            WHERE id_fijo = ?
            ORDER BY tipo_servicio
        ''', (id_fijo,))
        
        servicios = cursor.fetchall()
        
        # Obtener correspondencias
        cursor.execute('''
            SELECT tipo_conexion, detalle
            FROM correspondencias 
            WHERE id_fijo = ?
            ORDER BY detalle
        ''', (id_fijo,))
        
        correspondencias = cursor.fetchall()
        
        conn.close()
        
        # Formatear datos para la respuesta
        datos_estacion = {
            'id_fijo': id_fijo,
            'nombre': nombre,
            'linea': linea,
            'url': url,
            'orden_en_linea': orden_en_linea,
            'ultima_actualizacion': ultima_actualizacion,
            'detalles': {
                'direccion_completa': detalles[0] if detalles else None,
                'calle': detalles[1] if detalles else None,
                'codigo_postal': detalles[2] if detalles else None,
                'distrito': detalles[3] if detalles else None,
                'barrio': detalles[4] if detalles else None,
                'vestibulos': detalles[5] if detalles else None,
                'ultima_actualizacion_detalles': detalles[6] if detalles else None
            },
            'accesos': [
                {
                    'vestibulo': acc[0],
                    'nombre_acceso': acc[1],
                    'direccion': acc[2]
                } for acc in accesos
            ],
            'servicios': [
                {
                    'tipo_servicio': serv[0],
                    'disponible': bool(serv[1])
                } for serv in servicios
            ],
            'correspondencias': [
                {
                    'tipo_conexion': corr[0],
                    'detalle': corr[1]
                } for corr in correspondencias
            ]
        }
        
        return datos_estacion
        
    except Exception as e:
        print(f"Error obteniendo datos relacionales de {nombre_estacion}: {e}")
        return None

def buscar_estacion_por_id(id_fijo):
    "Busca una estación por id_fijo en los datos clave o en la base de datos"
    global datos_clave_estaciones, datos_clave_cargados
    if datos_clave_cargados and datos_clave_estaciones is not None:
        try:
            row = datos_clave_estaciones[datos_clave_estaciones['id_fijo'] == id_fijo]
            if not row.empty:
                row = row.iloc[0]
                return {
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
        except Exception as e:
            print(f"Error buscando estación por id_fijo: {e}")
    # Fallback a base de datos
    try:
        conn = sqlite3.connect(DB_PATH)
        lineas_tablas = [
            'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
            'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
        ]
        for tabla in lineas_tablas:
            query = f"SELECT * FROM {tabla} WHERE id_fijo = ? LIMIT 1"
            df = pd.read_sql_query(query, conn, params=[id_fijo])
            if not df.empty:
                row = df.iloc[0]
                conn.close()
                return {
                    'id_fijo': int(row['id_fijo']),
                    'nombre': row['nombre'],
                    'linea': tabla.replace('linea_', ''),
                    'orden': int(row['orden']) if 'orden' in row and pd.notna(row['orden']) else None,
                    'url': row['url'] if 'url' in row and pd.notna(row['url']) else None,
                    'id_modal': int(row['id_modal']) if 'id_modal' in row and pd.notna(row['id_modal']) else None,
                    'zona_tarifaria': row['zona'] if 'zona' in row and pd.notna(row['zona']) else None,
                    'estacion_accesible': row['accesible'] if 'accesible' in row and pd.notna(row['accesible']) else None,
                    'tabla_origen': tabla
                }
        conn.close()
    except Exception as e:
        print(f"Error buscando estación por id_fijo en BD: {e}")
    return None

def generate_ramal_trains_data(station_name):
    "Genera datos simulados de trenes para el Ramal"
    try:
        # El Ramal solo tiene 2 estaciones: Ópera y Príncipe Pío
        if station_name.lower() not in ['ópera', 'opera', 'príncipe pío', 'principe pio']:
            return None
            
        # Simular tiempos basados en la hora actual
        from datetime import datetime
        now = datetime.now()
        minute = now.minute
        
        # Trenes cada 10-15 minutos aproximadamente
        base_times = [3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58]
        
        # Ajustar tiempos según la hora actual
        adjusted_times = []
        for base_time in base_times:
            if base_time > minute:
                adjusted_times.append(base_time - minute)
        
        # Si no hay tiempos futuros en esta hora, añadir algunos de la siguiente
        if len(adjusted_times) < 3:
            for i in range(3 - len(adjusted_times)):
                adjusted_times.append(60 - minute + (i * 10))
        
        # Tomar solo los próximos 3 trenes
        tiempos = sorted(adjusted_times)[:3]
        
        # Determinar destino según la estación
        if station_name.lower() in ['ópera', 'opera']:
            destino = 'Príncipe Pío'
        else:
            destino = 'Ópera'
        
        return {
            'lineas': [{
                'numero': 'Ramal',
                'nombre': 'Ramal',
                'color': '#FFFFFF',
                'logo': '/static/logos/lineas/ramal.svg',
                'direcciones': [{
                    'destino': destino,
                    'tiempos': tiempos,
                    'proximo_tren': tiempos[0] if tiempos else None,
                    'todos_tiempos': tiempos
                }]
            }],
            'total_lineas': 1,
            'timestamp_parseo': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error generando datos del Ramal: {e}")
        return None

@app.route('/test-scraper')
def test_scraper_page():
    "Página de prueba para el scraper frontend"
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Scraper Frontend</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .result { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 3px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>Test Scraper Frontend</h1>
        
        <div class="test-section">
            <h2>1. Test Búsqueda de Estación</h2>
            <input type="text" id="stationSearch" placeholder="Nombre de estación" value="Pinar de Chamartín">
            <button onclick="testSearch()"> Buscar</button>
            <div id="searchResult" class="result"></div>
        </div>
        
        <div class="test-section">
            <h2>2. Test Scraper Ninja</h2>
            <input type="text" id="stationName" placeholder="Nombre de estación" value="Pinar de Chamartín">
            <button onclick="testNinjaScraper()"> Scraper Ninja</button>
            <div id="ninjaResult" class="result"></div>
        </div>
        
        <div class="test-section">
            <h2>3. Test Refresh Trains</h2>
            <input type="text" id="stationNameRefresh" placeholder="Nombre de estación" value="Pinar de Chamartín">
            <button onclick="testRefreshTrains()">"„ Refresh Trains</button>
            <div id="refreshResult" class="result"></div>
        </div>

        <script>
            async function testSearch() {
                const stationName = document.getElementById("stationSearch").value;
                const resultDiv = document.getElementById("searchResult");
                
                try {
                    resultDiv.innerHTML = " Buscando...";
                    
                    const response = await fetch(`/api/station/search?q=${encodeURIComponent(stationName)}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `<div class="success"> Búsqueda exitosa: ${data.length} resultados</div>
                            <pre>${JSON.stringify(data, null, 2)}</pre>`;
                    } else {
                        resultDiv.innerHTML = `<div class="error"> Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error"> Error de conexión: ${error.message}</div>`;
                }
            }
            
            async function testNinjaScraper() {
                const stationName = document.getElementById("stationName").value;
                const resultDiv = document.getElementById("ninjaResult");
                
                try {
                    resultDiv.innerHTML = "Ejecutando scraper Ninja...";
                    
                    const response = await fetch(`/api/station/ninjascrap/${encodeURIComponent(stationName)}`);
                    const data = await response.json();
                    
                    if (response.ok && data.scraper_status === "success") {
                        resultDiv.innerHTML = `<div class="success"> Scraper Ninja exitoso</div>
                            <p><strong>Estación:</strong> ${data.station_name}</p>
                            <p><strong>Línea:</strong> ${data.linea}</p>
                            <p><strong>Última actualización:</strong> ${data.last_update}</p>
                            <p><strong>Estado ascensores:</strong> ${data.estado_ascensores}</p>
                            <p><strong>Estado escaleras:</strong> ${data.estado_escaleras}</p>
                            <details>
                                <summary>HTML Próximos Trenes</summary>
                                <pre>${data.proximos_trenes_html}</pre>
                            </details>`;
                    } else {
                        resultDiv.innerHTML = `<div class="error"> Error: ${data.error || "Error desconocido"}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error"> Error de conexión: ${error.message}</div>`;
                }
            }
            
            async function testRefreshTrains() {
                const stationName = document.getElementById("stationNameRefresh").value;
                const resultDiv = document.getElementById("refreshResult");
                
                try {
                    resultDiv.innerHTML = Refrescando trenes...";
                    
                    const response = await fetch(`/api/station/refresh-trains/${encodeURIComponent(stationName)}`);
                    const data = await response.json();
                    
                    if (response.ok && data.success) {
                        resultDiv.innerHTML = `<div class="success"> Refresh exitoso</div>
                            <p><strong>Estación:</strong> ${data.station_name}</p>
                            <p><strong>ID Modal usado:</strong> ${data.id_modal_used}</p>
                            <p><strong>Timestamp:</strong> ${data.timestamp}</p>
                            <details>
                                <summary>HTML Próximos Trenes</summary>
                                <pre>${data.next_trains_html}</pre>
                            </details>`;
                    } else {
                        resultDiv.innerHTML = `<div class="error"> Error: ${data.error || "Error desconocido"}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="error"> Error de conexión: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/station/intelligent/<station_name>')
def get_intelligent_station_data(station_name):
    "Endpoint inteligente que combina datos estáticos y dinámicos de una estación"
    try:
        print(f"[INTELLIGENT] Obteniendo datos inteligentes para: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        print(f"[INTELLIGENT] Estación encontrada: {station_data['nombre']} (Línea {station_data['linea']})")

        # Obtener datos estáticos de la base de datos
        static_data = {
            'name': station_data['nombre'],
            'line': station_data['linea'],
            'id_fijo': station_data['id_fijo'],
            'id_modal': station_data.get('id_modal'),
            'url': station_data.get('url'),
            'zona_tarifaria': station_data.get('zona_tarifaria', 'A'),
            'correspondencias': station_data.get('correspondencias', []),
            'services': {
                'accessible': station_data.get('accessible', False),
                'defibrillator': station_data.get('defibrillator', False),
                'elevators': station_data.get('elevators', False),
                'escalators': station_data.get('escalators', False),
                'historical': station_data.get('historical', False),
                'mobileCoverage': station_data.get('mobileCoverage', False),
                'shops': station_data.get('shops', False)
            }
        }

        # Obtener datos dinámicos del scraper Ninja
        dynamic_data = {}
        try:
            scraper = ScraperNinjaTiempoReal()
            ninja_data = scraper.scrape_estacion_tiempo_real(station_data.get('url', ''))
            
            if ninja_data:
                dynamic_data = {
                    'elevator_status': ninja_data.get('estado_ascensores', 'No disponible'),
                    'escalator_status': ninja_data.get('estado_escaleras', 'No disponible'),
                    'last_update': ninja_data.get('ultima_actualizacion', 'No disponible'),
                    'proximos_trenes_html': ninja_data.get('proximos_trenes_html', ''),
                    'timestamp_scraping': ninja_data.get('timestamp_scraping', '')
                }
        except Exception as e:
            print(f"[INTELLIGENT] Error en scraper Ninja: {e}")
            dynamic_data = {
                'elevator_status': 'Error obteniendo datos',
                'escalator_status': 'Error obteniendo datos',
                'last_update': 'Error',
                'proximos_trenes_html': '<p>Error obteniendo próximos trenes</p>',
                'timestamp_scraping': datetime.now().isoformat()
            }

        # Combinar datos
        resultado = {
            'success': True,
            'static': static_data,
            'dynamic': dynamic_data,
            'station_name': station_data['nombre'],
            'timestamp': datetime.now().isoformat()
        }

        print(f"[INTELLIGENT] Datos inteligentes obtenidos para {station_name}")
        return jsonify(resultado)

    except Exception as e:
        print(f"[INTELLIGENT] Error: {e}")
        return jsonify({
            'error': f'Error obteniendo datos inteligentes: {str(e)}',
            'success': False
        }), 500

@app.route('/api/station/<lineNumber>/<stationId>')
def get_station_data_by_id(lineNumber, stationId):
    "Endpoint que usa directamente el id_fijo para obtener datos de una estación, y añade paradas cercanas y líneas disponibles"
    try:
        print(f"[STATION_BY_ID] Obteniendo datos para línea {lineNumber}, estación ID {stationId}")

        import pandas as pd
        # Leer el CSV de datos clave
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        # Filtrar por línea
        df['linea'] = df['linea'].astype(str)
        df_linea = df[df['linea'] == str(lineNumber)].sort_values('orden')
        # Buscar la estación actual por id_fijo
        df_linea = df_linea.reset_index(drop=True)
        idx = df_linea[df_linea['id_fijo'] == int(stationId)].index.tolist()
        if not idx:
            return jsonify({'error': f'Estación no encontrada: ID {stationId}, Línea {lineNumber}'}), 404
        idx = idx[0]
        
        # Lógica especial para líneas circulares (6 y 12)
        is_circular = str(lineNumber) in ['6', '12']
        
        if is_circular:
            # Para líneas circulares, mostrar 4 antes y 4 después, tratando la línea como un bucle
            paradas_cercanas = []
            total_estaciones = len(df_linea)
            
            # Generar índices en bucle: 4 antes + estación actual + 4 después
            for offset in range(-4, 5):  # -4, -3, -2, -1, 0, 1, 2, 3, 4
                circular_idx = (idx + offset) % total_estaciones
                row = df_linea.iloc[circular_idx]
                paradas_cercanas.append({
                    'id_fijo': int(row['id_fijo']),
                    'name': row['nombre'],
                    'orden': int(row['orden']),
                    'correspondencias': [],
                    'is_actual': int(row['id_fijo']) == int(stationId),
                    'linea': str(row['linea'])
                })
        else:
            # Lógica normal para líneas lineales
            start = max(0, idx-4)
            end = min(len(df_linea), idx+5)
            paradas_cercanas = []
            for i in range(start, end):
                row = df_linea.iloc[i]
                paradas_cercanas.append({
                    'id_fijo': int(row['id_fijo']),
                    'name': row['nombre'],
                    'orden': int(row['orden']),
                    'correspondencias': [],
                    'is_actual': int(row['id_fijo']) == int(stationId),
                    'linea': str(row['linea'])
                })
        # Añadir correspondencias reales si existen
        for parada in paradas_cercanas:
            corr = df[(df['id_fijo'] == parada['id_fijo']) & (df['linea'] == str(lineNumber))]
            if not corr.empty and 'correspondencias' in corr.columns:
                try:
                    import json
                    parada['correspondencias'] = json.loads(str(corr.iloc[0]['correspondencias']).replace("'", '"'))
                except:
                    parada['correspondencias'] = []
        # Buscar todas las líneas que pasan por esa estación (por id_fijo)
        lineas_disponibles = df[df['id_fijo'] == int(stationId)]['linea'].unique().tolist()
        # --- Resto del endpoint original ---
        import sqlite3
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        tabla_linea = f"linea_{lineNumber}"
        cursor.execute(f"""
            SELECT id_fijo, nombre, zona_tarifaria, estacion_accesible, 
                   ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                   bibliometro, tiendas, correspondencias, url, servicios,
                   accesos, vestibulos, nombres_acceso, intercambiadores
            FROM {tabla_linea} 
            WHERE id_fijo = ?
        """, (stationId,))
        row = cursor.fetchone()
        if not row:
            # Si no se encuentra, buscar en estaciones_completas
            cursor.execute("""
                SELECT id_fijo, nombre, linea, zona_tarifaria, estacion_accesible, 
                       ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                       bibliometro, tiendas, correspondencias, url
                FROM estaciones_completas 
                WHERE id_fijo = ? AND linea = ?
            """, (stationId, lineNumber))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': f'Estación no encontrada: ID {stationId}, Línea {lineNumber}'}), 404
            # Si viene de estaciones_completas, la columna linea está incluida
            (id_fijo, nombre, linea, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url) = row
        else:
            # Si viene de la tabla de la línea, la columna linea NO está incluida, la añadimos manualmente
            (id_fijo, nombre, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url, servicios, accesos, vestibulos, nombres_acceso, intercambiadores) = row
            linea = str(lineNumber)
        conn.close()
        # Procesar correspondencias
        corr_list = []
        if correspondencias:
            try:
                corr_data = eval(correspondencias)
                if isinstance(corr_data, list):
                    corr_list = [str(corr) for corr in corr_data]
            except:
                pass
        # Procesar accesos
        accesos_list = []
        if 'accesos' in locals() and accesos:
            accesos_text = accesos.replace(';', ',').replace(';', ',')
            accesos_list = [a.strip() for a in accesos_text.split(',') if a.strip()]
        # Procesar servicios
        servicios_list = []
        if 'servicios' in locals() and servicios:
            servicios_text = servicios.replace(';', ',').replace(';', ',')
            raw_servicios = [s.strip() for s in servicios_text.split(',') if s.strip()]
            
            # Filtrar duplicados de accesibilidad - mantener solo "Estación accesible"
            has_accessibility = False
            for servicio in raw_servicios:
                if 'accesible' in servicio.lower() or 'adaptada para discapacitados' in servicio.lower():
                    if not has_accessibility:
                        servicios_list.append('Estación accesible')
                        has_accessibility = True
                else:
                    servicios_list.append(servicio)
        static_data = {
            'name': nombre,
            'line': linea,
            'id_fijo': id_fijo,
            'url': url,
            'zona_tarifaria': zona,
            'correspondencias': corr_list,
            'accesos': accesos_list,
            'vestibulos': vestibulos.split(';') if 'vestibulos' in locals() and vestibulos else [],
            'nombres_acceso': nombres_acceso.split(';') if 'nombres_acceso' in locals() and nombres_acceso else [],
            'intercambiadores': intercambiadores.split(';') if 'intercambiadores' in locals() and intercambiadores else [],
            'services': {
                'accessible': accesible == 'Sí­' or ('servicios' in locals() and (('Estación accesible' in servicios) or ('adaptada para discapacitados' in servicios))),
                'defibrillator': desfibrilador == 'Sí­' or ('servicios' in locals() and 'Desfibrilador' in servicios),
                'elevators': ascensores == 'Sí­' or ('servicios' in locals() and 'Ascensores' in servicios),
                'escalators': escaleras == 'Sí­' or ('servicios' in locals() and 'Escaleras' in servicios),
                'historical': ('servicios' in locals() and 'Histórico' in servicios),
                'mobileCoverage': cobertura == 'Sí­' or ('servicios' in locals() and 'Cobertura móvil' in servicios),
                'shops': tiendas == 'Sí­' or ('servicios' in locals() and 'Tiendas' in servicios),
                'bibliometro': bibliometro == 'Sí­' or ('servicios' in locals() and 'Bibliometro' in servicios),
                'ttp_office': ('servicios' in locals() and (('TTP' in servicios) or ('Oficina de gestión TTP' in servicios))),
                'park_ride': ('servicios' in locals() and (('Park and ride' in servicios) or ('Parking' in servicios) or ('disuasorio' in servicios))),
                'once': ('servicios' in locals() and (('O.N.C.E.' in servicios) or ('ONCE' in servicios)))
            },
            'servicios_detallados': servicios_list
        }
        from datetime import datetime
        dynamic_data = {
            'elevator_status': 'Operativo' if static_data['services'].get('elevators', False) else 'No disponible',
            'escalator_status': 'Operativo' if static_data['services'].get('escalators', False) else 'No disponible',
            'last_update': datetime.now().strftime('%H:%M:%S'),
            'proximos_trenes_html': '<p>Datos de próximos trenes no disponibles</p>',
            'timestamp_scraping': datetime.now().isoformat()
        }
        resultado = {
            'success': True,
            'data': {
                'static': static_data,
                'dynamic': dynamic_data,
                'paradas_cercanas': paradas_cercanas,
                'lineas_disponibles': lineas_disponibles
            },
            'from_cache': False,
            'station_name': nombre,
            'timestamp': datetime.now().isoformat()
        }
        print(f"[STATION_BY_ID] Datos obtenidos para {nombre}")
        return jsonify(resultado)
    except Exception as e:
        print(f"[STATION_BY_ID] Error: {e}")
        return jsonify({
            'error': f'Error obteniendo datos: {str(e)}',
            'success': False
        }), 500

@app.route('/api/station/<lineNumber>/<stationId>/complete')
def get_complete_station_data(lineNumber, stationId):
    """Endpoint completo que obtiene todos los datos de servicios"""
    try:
        print(f"[COMPLETE] Obteniendo datos completos para línea {lineNumber}, estación ID {stationId}")
        
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Buscar en la tabla de la línea específica
        tabla_linea = f"linea_{lineNumber}"
        cursor.execute(f"""
            SELECT id_fijo, nombre, zona_tarifaria, estacion_accesible, 
                   ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                   bibliometro, tiendas, correspondencias, url, servicios,
                   accesos, vestibulos, nombres_acceso, intercambiadores
            FROM {tabla_linea} 
            WHERE id_fijo = ?
        """, (stationId,))
        
        row = cursor.fetchone()
        
        # Variables para los datos
        servicios = None
        accesos = None
        vestibulos = None
        nombres_acceso = None
        intercambiadores = None
        
        if not row:
            # Si no se encuentra, buscar en estaciones_completas
            print(f"[COMPLETE] No encontrado en {tabla_linea}, buscando en estaciones_completas")
            cursor.execute("""
                SELECT id_fijo, nombre, linea, zona_tarifaria, estacion_accesible, 
                       ascensores, escaleras_mecanicas, desfibrilador, cobertura_movil, 
                       bibliometro, tiendas, correspondencias, url
                FROM estaciones_completas 
                WHERE id_fijo = ? AND linea = ?
            """, (stationId, lineNumber))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({'error': f'Estación no encontrada: ID {stationId}, Línea {lineNumber}'}), 404
            # Si viene de estaciones_completas, la columna linea está incluida pero no tiene servicios detallados
            (id_fijo, nombre, linea, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url) = row
            print(f"[COMPLETE] Encontrado en estaciones_completas: {nombre}")
        else:
            # Si viene de la tabla de la línea, tiene todas las columnas
            (id_fijo, nombre, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url, servicios, accesos, vestibulos, nombres_acceso, intercambiadores) = row
            linea = str(lineNumber)
            print(f"[COMPLETE] Encontrado en {tabla_linea}: {nombre}")
        
        conn.close()
        
        id_fijo, nombre, zona, accesible, ascensores, escaleras, desfibrilador, cobertura, bibliometro, tiendas, correspondencias, url, servicios, accesos, vestibulos, nombres_acceso, intercambiadores = row
        
        # Procesar servicios
        servicios_list = []
        if servicios:
            servicios_text = servicios.replace(';', ',').replace(';', ',')
            raw_servicios = [s.strip() for s in servicios_text.split(',') if s.strip()]
            
            # Filtrar duplicados de accesibilidad - mantener solo "Estación accesible"
            has_accessibility = False
            for servicio in raw_servicios:
                if 'accesible' in servicio.lower() or 'adaptada para discapacitados' in servicio.lower():
                    if not has_accessibility:
                        servicios_list.append('Estación accesible')
                        has_accessibility = True
                else:
                    servicios_list.append(servicio)
        
        # Procesar correspondencias
        corr_list = []
        if correspondencias:
            try:
                corr_data = eval(correspondencias)
                if isinstance(corr_data, list):
                    corr_list = [str(corr) for corr in corr_data]
            except:
                pass
        
        # Procesar accesos
        accesos_list = []
        if accesos:
            accesos_text = accesos.replace(';', ',').replace(';', ',')
            accesos_list = [a.strip() for a in accesos_text.split(',') if a.strip()]
        
        # Datos estáticos completos
        static_data = {
            'name': nombre,
            'line': lineNumber,
            'id_fijo': id_fijo,
            'url': url,
            'zona_tarifaria': zona,
            'correspondencias': corr_list,
            'accesos': accesos_list,
            'vestibulos': vestibulos.split(';') if vestibulos else [],
            'nombres_acceso': nombres_acceso.split(';') if nombres_acceso else [],
            'intercambiadores': intercambiadores.split(';') if intercambiadores else [],
            'services': {
                'accessible': accesible == 'Sí­' or 'Estación accesible' in servicios or 'adaptada para discapacitados' in servicios,
                'defibrillator': desfibrilador == 'Sí­' or 'Desfibrilador' in servicios,
                'elevators': ascensores == 'Sí­' or 'Ascensores' in servicios,
                'escalators': escaleras == 'Sí­' or 'Escaleras' in servicios,
                'historical': 'Histórico' in servicios,
                'mobileCoverage': cobertura == 'Sí­' or 'Cobertura móvil' in servicios,
                'shops': tiendas == 'Sí­' or 'Tiendas' in servicios,
                'bibliometro': bibliometro == 'Sí­' or 'Bibliometro' in servicios,
                'ttp_office': 'TTP' in servicios or 'Oficina de gestión TTP' in servicios,
                'park_ride': 'Park and ride' in servicios or 'Parking' in servicios or 'disuasorio' in servicios,
                'once': 'O.N.C.E.' in servicios or 'ONCE' in servicios
            },
            'servicios_detallados': servicios_list
        }
        
        resultado = {
            'success': True,
            'data': {
                'static': static_data,
                'dynamic': {
                    'elevator_status': 'Operativo' if static_data['services']['elevators'] else 'No disponible',
                    'escalator_status': 'Operativo' if static_data['services']['escalators'] else 'No disponible',
                    'last_update': datetime.now().strftime('%H:%M:%S'),
                    'timestamp_scraping': datetime.now().isoformat()
                }
            },
            'station_name': nombre,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[COMPLETE] Datos completos obtenidos para {nombre}")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[COMPLETE] Error: {e}")
        return jsonify({
            'error': f'Error obteniendo datos completos: {str(e)}',
            'success': False
        }), 500

def detectar_estado_linea_automatico(line_id):
    """
    Detecta automáticamente el estado de una línea basándose en:
    1. Horario nocturno (2:30 AM - 6:00 AM)
    2. Disponibilidad de trenes en estaciones terminus
    """
    from datetime import datetime, time
    import requests
    
    try:
        # Obtener hora actual
        now = datetime.now()
        current_time = now.time()
        
        # Definir horario nocturno
        night_start = time(2, 30)  # 2:30 AM
        night_end = time(6, 0)     # 6:00 AM
        
        # Verificar si estamos en horario nocturno
        is_night_time = (current_time >= night_start and current_time <= night_end)
        
        if not is_night_time:
            # Fuera del horario nocturno, línea operativa
            return {
                'estado': 'Normal',
                'descripcion': 'Circulación normal',
                'clase_css': 'operativa',
                'motivo': None
            }
        
        # En horario nocturno, verificar trenes en estaciones terminus
        print(f"Verificando estado nocturno para línea {line_id}")
        
        # Obtener estaciones terminus de la línea
        terminus_stations = obtener_estaciones_terminus(line_id)
        if not terminus_stations:
            return {
                'estado': 'Cerrada',
                'descripcion': 'Cerrada por horario nocturno',
                'clase_css': 'cerrada',
                'motivo': 'Horario nocturno - No se pudieron verificar estaciones terminus'
            }
        
        # Verificar trenes en las estaciones terminus
        trains_found = False
        for station in terminus_stations:
            try:
                # Usar el endpoint de trenes crudos para verificar disponibilidad
                response = requests.get(f"http://localhost:5000/api/station/raw-trains/{station['nombre']}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('trenes') and len(data['trenes']) > 0:
                        trains_found = True
                        print(f" Trenes encontrados en {station['nombre']}")
                        break
                    else:
                        print(f" No hay trenes en {station['nombre']}")
                else:
                    print(f"Error verificando {station['nombre']}: {response.status_code}")
            except Exception as e:
                print(f"Error verificando {station['nombre']}: {e}")
                continue
        
        if trains_found:
            return {
                'estado': 'Normal',
                'descripcion': 'Circulación nocturna',
                'clase_css': 'operativa',
                'motivo': None
            }
        else:
            return {
                'estado': 'Cerrada',
                'descripcion': 'Cerrada por horario nocturno',
                'clase_css': 'cerrada',
                'motivo': 'Horario nocturno - Sin trenes en estaciones terminus'
            }
            
    except Exception as e:
        print(f" Error detectando estado automático de línea {line_id}: {e}")
        return {
            'estado': 'No disponible',
            'descripcion': 'Estado no disponible',
            'clase_css': 'no-disponible',
            'motivo': f'Error: {str(e)}'
        }

def obtener_estaciones_terminus(line_id):
    """
    Obtiene las estaciones terminus (primera y última) de una línea
    """
    try:
        # Leer el CSV de datos clave
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        # Filtrar por línea
        if line_id == 'R' or line_id == 'Ramal':
            stations_df = df[df['linea'] == 'Ramal']
        else:
            # Convertir la columna linea a int para comparación correcta
            df['linea'] = pd.to_numeric(df['linea'], errors='coerce')
            stations_df = df[df['linea'] == int(line_id)]
        
        if stations_df.empty:
            return []
        
        # Ordenar por orden y obtener primera y última estación
        stations_df = stations_df.sort_values('orden')
        
        terminus = []
        
        # Primera estación
        first_station = stations_df.iloc[0]
        terminus.append({
            'nombre': first_station['nombre'],
            'id_fijo': first_station['id_fijo'],
            'tipo': 'inicio'
        })
        
        # Última estación (si es diferente a la primera)
        last_station = stations_df.iloc[-1]
        if last_station['id_fijo'] != first_station['id_fijo']:
            terminus.append({
                'nombre': last_station['nombre'],
                'id_fijo': last_station['id_fijo'],
                'tipo': 'fin'
            })
        
        print(f"Estaciones terminus línea {line_id}: {[t['nombre'] for t in terminus]}")
        return terminus
        
    except Exception as e:
        print(f" Error obteniendo estaciones terminus de línea {line_id}: {e}")
        return []

def actualizar_estado_nocturno_global():
    """
    Actualiza el estado de todas las líneas en horario nocturno y lo mantiene persistente
    hasta que termine el horario nocturno
    """
    from datetime import datetime, time
    
    try:
        # Obtener hora actual
        now = datetime.now()
        current_time = now.time()
        
        # Definir horario nocturno
        night_start = time(2, 30)  # 2:30 AM
        night_end = time(6, 0)     # 6:00 AM
        
        # Verificar si estamos en horario nocturno
        is_night_time = (current_time >= night_start and current_time <= night_end)
        
        print(f" Verificando horario nocturno: {current_time.strftime('%H:%M:%S')}")
        print(f" Es horario nocturno: {is_night_time}")
        
        # Conectar a la base de datos
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Crear tabla de estado de líneas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estado_lineas (
                linea TEXT PRIMARY KEY,
                estado TEXT NOT NULL,
                descripcion TEXT,
                clase_css TEXT,
                motivo TEXT,
                ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detectado_automaticamente BOOLEAN DEFAULT FALSE,
                horario_nocturno BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Verificar si la tabla existe pero no tiene todas las columnas
        cursor.execute("PRAGMA table_info(estado_lineas)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Agregar columnas faltantes de forma segura para versiones antiguas de SQLite
        if 'motivo' not in columns:
            cursor.execute("ALTER TABLE estado_lineas ADD COLUMN motivo TEXT")
        
        if 'detectado_automaticamente' not in columns:
            cursor.execute("ALTER TABLE estado_lineas ADD COLUMN detectado_automaticamente BOOLEAN")
            cursor.execute("UPDATE estado_lineas SET detectado_automaticamente = 0 WHERE detectado_automaticamente IS NULL")
        
        if 'horario_nocturno' not in columns:
            cursor.execute("ALTER TABLE estado_lineas ADD COLUMN horario_nocturno BOOLEAN")
            cursor.execute("UPDATE estado_lineas SET horario_nocturno = 0 WHERE horario_nocturno IS NULL")

        if 'ultima_actualizacion' not in columns:
            cursor.execute("ALTER TABLE estado_lineas ADD COLUMN ultima_actualizacion TIMESTAMP")
            cursor.execute("UPDATE estado_lineas SET ultima_actualizacion = CURRENT_TIMESTAMP WHERE ultima_actualizacion IS NULL")
        
        # Commit de los cambios de esquema
        conn.commit()
        
        # Lista de todas las líneas
        lineas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']
        
        for linea in lineas:
            if is_night_time:
                # En horario nocturno, verificar estado automático
                estado_auto = detectar_estado_linea_automatico(linea)
                
                # Actualizar en la base de datos
                cursor.execute("""
                    INSERT OR REPLACE INTO estado_lineas 
                    (linea, estado, descripcion, clase_css, motivo, ultima_actualizacion, detectado_automaticamente, horario_nocturno)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    linea,
                    estado_auto['estado'],
                    estado_auto['descripcion'],
                    estado_auto['clase_css'],
                    estado_auto['motivo'],
                    datetime.now().isoformat(),
                    True,
                    True
                ))
                
                print(f" Línea {linea}: {estado_auto['estado']} - {estado_auto['descripcion']}")
                
            else:
                # Fuera del horario nocturno, verificar si hay estado guardado de horario nocturno
                cursor.execute("""
                    SELECT horario_nocturno FROM estado_lineas 
                    WHERE linea = ? AND horario_nocturno = 1
                """, (linea,))
                
                if cursor.fetchone():
                    # Limpiar estado nocturno y restaurar estado normal
                    cursor.execute("""
                        UPDATE estado_lineas 
                        SET estado = 'Normal', 
                            descripcion = 'Circulación normal',
                            clase_css = 'operativa',
                            motivo = NULL,
                            ultima_actualizacion = ?,
                            detectado_automaticamente = FALSE,
                            horario_nocturno = FALSE
                        WHERE linea = ?
                    """, (datetime.now().isoformat(), linea))
                    
                    print(f" Lí­nea {linea}: Restaurado estado normal")
        
        conn.commit()
        conn.close()
        
        print(f" Estado nocturno actualizado para todas las li­neas")
        return True
        
    except Exception as e:
        print(f" Error actualizando estado nocturno global: {e}")
        return False

@app.route('/api/lines/status/update-nocturno')
def update_nocturno_status():
    """
    Endpoint para actualizar automáticamente el estado nocturno de todas las líneas
    """
    try:
        success = actualizar_estado_nocturno_global()
        if success:
            return jsonify({
                'success': True,
                'message': 'Estado nocturno actualizado correctamente',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error actualizando estado nocturno',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/lines/global-status')
def global_status():
    """
    Status global que se activa automáticamente en horario nocturno (2:30 AM - 6:00 AM)
    """
    from datetime import datetime, time
    
    try:
        # Obtener hora actual
        now = datetime.now()
        current_time = now.time()
        
        # Definir horario nocturno
        night_start = time(2, 30)  # 2:30 AM
        night_end = time(6, 0)     # 6:00 AM
        
        # Verificar si estamos en horario nocturno
        is_night_time = (current_time >= night_start and current_time <= night_end)
        
        if not is_night_time:
            # Fuera del horario nocturno, no hay status global
            return jsonify({
                'activo': False,
                'motivo': 'Fuera del horario nocturno',
                'lineas_afectadas': []
            })
        
        # En horario nocturno, activar status global directamente
        lineas_todas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R']
        
        return jsonify({
            'activo': True,
            'motivo': 'Horario nocturno - Metro cerrado de 2:30 AM a 6:00 AM',
            'lineas_afectadas': lineas_todas,
            'hora_actual': current_time.strftime('%H:%M:%S'),
            'horario_nocturno': f'{night_start.strftime("%H:%M")} - {night_end.strftime("%H:%M")}'
        })
        
    except Exception as e:
        print(f" Error en global_status: {e}")
        return jsonify({
            'activo': False,
            'motivo': f'Error: {str(e)}',
            'lineas_afectadas': []
        }), 500

@app.route('/test-status-global')
def test_status_global_page():
    """Página de prueba para el status global"""
    return render_template('test_status_global_frontend.html')

@app.route('/api/station/model3d/<station_name>')
def get_station_model3d(station_name):
    """Endpoint para obtener información del modelo 3D de una estación"""
    try:
        print(f"[MODEL3D] Buscando modelo 3D para: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404
        
        station_data = estaciones[0]
        line_number = station_data['linea']
        
        # Normalizar nombre de estación
        def normalizar_nombre(nombre):
            if not nombre:
                return ""
            nombre = nombre.lower()
            nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í­', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            nombre = nombre.replace('í¼', 'u').replace('Ã§', 'c')
            nombre = ''.join(c for c in nombre if c.isalnum() or c.isspace())
            nombre = nombre.replace(' ', '_')
            return nombre
        
        normalized_name = normalizar_nombre(station_name)
        model_path = f"static/model_3D/linea_{line_number}/{normalized_name}.png"
        
        # Verificar si el archivo existe
        if os.path.exists(model_path):
            # Calcular tamaño del archivo
            file_size = os.path.getsize(model_path)
            file_size_mb = file_size / (1024 * 1024)
            
            return jsonify({
                'success': True,
                'station_name': station_name,
                'line_number': line_number,
                'model_path': f"/{model_path}",
                'file_size_mb': round(file_size_mb, 2),
                'available': True,
                'download_url': f"http://estacions.albertguillaumes.cat/img/madrid/{normalized_name}.png"
            })
        else:
            return jsonify({
                'success': True,
                'station_name': station_name,
                'line_number': line_number,
                'available': False,
                'download_url': f"http://estacions.albertguillaumes.cat/img/madrid/{normalized_name}.png",
                'message': 'Modelo 3D no disponible localmente'
            })
            
    except Exception as e:
        print(f"[MODEL3D] Error: {e}")
        return jsonify({
            'error': f'Error obteniendo información del modelo 3D: {str(e)}',
            'success': False
        }), 500


    """Endpoint para servir imágenes 3D directamente"""
    try:
        from flask import send_file
        
        # Normalizar nombre de estación
        def normalizar_nombre(nombre):
            if not nombre:
                return ""
            nombre = nombre.lower()
            nombre = nombre.replace('á', 'a').replace('é', 'e').replace('Ã­', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            nombre = nombre.replace('Ã¼', 'u').replace('Ã§', 'c')
            nombre = ''.join(c for c in nombre if c.isalnum() or c.isspace())
            nombre = nombre.replace(' ', '_')
            return nombre
        
        normalized_name = normalizar_nombre(station_name)
        image_path = f"static/model_3D/linea_{line_number}/{normalized_name}.png"
        
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Imagen no encontrada'}), 404
            
    except Exception as e:
        print(f"[MODEL3D_IMAGE] Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/station/real-accesses/<station_name>')
def get_real_station_accesses(station_name):
    """Endpoint para obtener accesos reales de una estación usando scraping"""
    try:
        print(f"[REAL_ACCESSES] Obteniendo accesos reales para: {station_name}")
        
        # Buscar la estación en la base de datos
        estaciones = buscar_estacion_por_nombre(station_name, limite=1)
        if not estaciones:
            return jsonify({'error': f'Estación no encontrada: {station_name}'}), 404

        station_data = estaciones[0]
        station_url = station_data.get('url')
        
        if not station_url:
            return jsonify({'error': f'La estación {station_name} no tiene URL configurada'}), 404

        # Usar el scraper de accesos reales
        if ACCESOS_SCRAPER_AVAILABLE:
            scraper = ScraperAccesosReales()
            resultado = scraper.obtener_accesos_estacion(station_name, station_url)
            scraper.close()
            
            if resultado['success']:
                return jsonify({
                    'success': True,
                    'station_name': station_name,
                    'accesos': resultado['accesos'],
                    'total_accesos': resultado['total_accesos'],
                    'timestamp': resultado['timestamp'],
                    'url_origen': resultado['url_origen']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': resultado.get('error', 'Error desconocido'),
                    'station_name': station_name,
                    'accesos': [],
                    'timestamp': datetime.now().isoformat()
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Scraper de accesos no disponible',
                'station_name': station_name,
                'accesos': [],
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        print(f"[REAL_ACCESSES] Error: {e}")
        return jsonify({
            'error': f'Error obteniendo accesos reales: {str(e)}',
            'success': False
        }), 500

def detectar_estado_linea_automatico_directo(line_id):
    """
    Detecta el estado de una línea llamando a las funciones directamente,
    sin hacer una petición HTTP a sí­ misma para evitar timeouts.
    """
    try:
        now = datetime.now()
        current_time = now.time()
        
        night_start = time(2, 30)
        night_end = time(6, 0)
        
        is_night_time = (current_time >= night_start and current_time <= night_end)
        
        if not is_night_time:
            return {'estado': 'Normal', 'descripcion': 'Circulación normal', 'clase_css': 'operativa', 'motivo': None}

        terminus_stations = obtener_estaciones_terminus(line_id)
        if not terminus_stations:
            return {'estado': 'Cerrada', 'descripcion': 'Cerrada por horario nocturno', 'clase_css': 'cerrada', 'motivo': 'No se encontraron terminus'}

        trains_found = False
        for station in terminus_stations:
            try:
                # Llamada directa a la lógica de obtención de datos
                id_modal = station.get('id_modal')
                if not id_modal:
                    # Si no hay id_modal, buscarlo
                    estacion_buscada = buscar_estacion_por_nombre(station['nombre'], limite=1)
                    if estacion_buscada:
                        id_modal = estacion_buscada[0].get('id_modal')

                if not id_modal:
                    print(f"No se pudo encontrar id_modal para {station['nombre']}")
                    continue
                
                api_url = f'https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}'
                response = requests.get(api_url, timeout=5)
                
                if response.status_code == 200:
                    html_content = response.text
                    if '"status":"KO"' not in html_content and 'próximos trenes' in html_content:
                        trains_found = True
                        print(f" Trenes encontrados en {station['nombre']} (directo)")
                        break
                    else:
                        print(f" No hay trenes en {station['nombre']} (directo)")
            except Exception as e:
                print(f"Error verificando {station['nombre']} (directo): {e}")
                continue
        
        if trains_found:
            return {'estado': 'Normal', 'descripcion': 'Circulación nocturna', 'clase_css': 'operativa', 'motivo': None}
        else:
            return {'estado': 'Cerrada', 'descripcion': 'Cerrada por horario nocturno', 'clase_css': 'cerrada', 'motivo': 'Sin trenes en terminus'}

    except Exception as e:
        print(f" Error detectando estado automático (directo) de línea {line_id}: {e}")
        return {'estado': 'No disponible', 'descripcion': 'Estado no disponible', 'clase_css': 'no-disponible', 'motivo': f'Error: {str(e)}'}

# ============================================================================
# RUTAS DE AUTENTICACIÓN DE USUARIOS
# ============================================================================

@app.route("/register", methods=['GET', 'POST'])
def register():
    """Página de registro de nuevos usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.create(username=form.username.data, email=form.email.data, password=form.password.data)
        if user:
            login_user(user)
            flash(f'¡Cuenta creada para {form.username.data}! Ya puedes empezar.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ha ocurrido un error durante el registro.', 'danger')
    return render_template('register.html', title='Registro', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión de usuarios."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Inicio de sesión fallido. Por favor, comprueba el email y la contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)


@app.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash('Has cerrado la sesión.', 'info')
    return redirect(url_for('index'))


@app.route("/account")
@login_required
def account():
    """Página del perfil del usuario."""
    # Obtener líneas y estaciones favoritas del usuario
    favorite_lines = get_user_favorite_lines(current_user.id)
    favorite_stations = get_user_favorite_stations(current_user.id)
    
    return render_template('account.html', title='Mi Cuenta', 
                         favorite_lines=favorite_lines, 
                         favorite_stations=favorite_stations)


# ============================================================================
# MODELOS DE DATOS Y GESTIÓN DE USUARIOS
# ============================================================================

class User(UserMixin):
    """Modelo de usuario para la gestión de sesiones y autenticación."""
    def __init__(self, user_id, username, email, password_hash, created_at=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        if isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        else:
            self.created_at = created_at

    def check_password(self, password):
        """Verifica si la contraseña proporcionada coincide con el hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_id(user_id):
        """Obtiene un usuario por su ID de la base de datos."""
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user_data:
            return User(user_id=user_data['id'], username=user_data['username'], email=user_data['email'], password_hash=user_data['password_hash'], created_at=user_data['created_at'])
        return None
    
    @staticmethod
    def get_by_email(email):
        """Obtiene un usuario por su email de la base de datos."""
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user_data:
            return User(user_id=user_data['id'], username=user_data['username'], email=user_data['email'], password_hash=user_data['password_hash'], created_at=user_data['created_at'])
        return None

    @staticmethod
    def create(username, email, password):
        """Crea un nuevo usuario y lo guarda en la base de datos."""
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None

@login_manager.user_loader
def load_user(user_id):
    """Función de callback de Flask-Login para recargar el usuario desde la sesión."""
    return User.get_by_id(int(user_id))

@app.route('/api/station/accesses/metromadrid/<station_id>')
def get_accesses_metromadrid(station_id):
    """Devuelve los accesos oficiales de MetroMadrid para una estación por id."""
    if not METROMADRID_ACCESOS_AVAILABLE:
        return jsonify({'error': 'Scraper de accesos de MetroMadrid no disponible'}), 500
    try:
        accesos = extraer_accesos_metromadrid(station_id)
        return jsonify({
            'station_id': station_id,
            'accesos': accesos,
            'total': len(accesos),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Error extrayendo accesos: {str(e)}'}), 500

import unicodedata

def normalizar_nombre(nombre):
    return ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

@app.route('/api/station/accesses/gtfs/<identificador>')
def get_accesses_gtfs(identificador):
    try:
        print(f"[GTFS_ACCESSES] Obteniendo accesos DB para: {identificador}")
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Buscar por id_fijo si es número
        if identificador.isdigit():
            cursor.execute("SELECT id_fijo, nombre, linea FROM estaciones_completas WHERE id_fijo = ? LIMIT 1", (int(identificador),))
        else:
            nombre_normalizado = normalizar_nombre(identificador)
        estacion = cursor.fetchone()
        if not estacion:
            conn.close()
            return jsonify({'error': f'No se encontró la estación: {identificador}'}), 404
        id_fijo, nombre_estacion, linea = estacion
        
        # Obtener accesos únicos de accesos_normalizados (eliminar duplicados)
        cursor.execute("""
            SELECT DISTINCT vestibulo, nombre_acceso, direccion, tipo_acceso, accesible_silla_ruedas
            FROM accesos_normalizados 
            WHERE station_id = ? 
            ORDER BY vestibulo, nombre_acceso
        """, (id_fijo,))
        
        accesos = []
        for row in cursor.fetchall():
            accesos.append({
                'vestibulo': row[0],
                'nombre': row[1],
                'direccion': row[2],
                'tipo_acceso': row[3],
                'accesible': bool(row[4])
            })
        
        print(f"[GTFS_ACCESSES] Encontrados {len(accesos)} accesos únicos para {nombre_estacion}")
        
        # Obtener servicios de la tabla de línea
        servicios = []
        try:
            tabla_linea = f"linea_{linea}"
            cursor.execute(f"SELECT servicios FROM {tabla_linea} WHERE id_fijo = ?", (id_fijo,))
            row = cursor.fetchone()
            if row and row[0]:
                servicios = [s.strip() for s in row[0].replace(';', ',').split(',') if s.strip()]
        except Exception as e:
            print(f"Error obteniendo servicios: {e}")
            servicios = []
        
        conn.close()
        return jsonify({
            'estacion': {
                'nombre': nombre_estacion,
                'id_fijo': id_fijo,
                'linea': linea
            },
            'accesos': accesos,
            'servicios': servicios,
            'total': len(accesos)
        })
    except Exception as e:
        print(f"[GTFS_ACCESSES] Error: {e}")
        return jsonify({'error': f'Error obteniendo accesos GTFS: {str(e)}'}), 500

@app.route('/api/station/connections/<identificador>')
def get_station_connections(identificador):
    """Endpoint que devuelve las conexiones de una estación desde la tabla conexiones_normalizadas"""
    try:
        print(f"[CONNECTIONS] Obteniendo conexiones para: {identificador}")
        
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Buscar por id_fijo si es número
        if identificador.isdigit():
            station_id = int(identificador)
            cursor.execute("SELECT id_fijo, nombre, linea FROM estaciones_completas WHERE id_fijo = ? LIMIT 1", (station_id,))
        else:
            nombre_normalizado = normalizar_nombre(identificador)
            cursor.execute("SELECT id_fijo, nombre, linea FROM estaciones_completas WHERE lower(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, 'á', 'a'), 'é', 'e'), 'Ã­', 'i'), 'ó', 'o'), 'ú', 'u'), 'Ã¼', 'u'), 'ñ', 'n')) LIKE ? LIMIT 1", (f'%{nombre_normalizado}%',))
            estacion = cursor.fetchone()
            if not estacion:
                conn.close()
                return jsonify({'error': f'No se encontró la estación: {identificador}'}), 404
            station_id = estacion[0]
            nombre_estacion = estacion[1]
            linea = estacion[2]
        
        # Obtener conexiones desde la tabla normalizada
        cursor.execute("""
            SELECT DISTINCT tipo_conexion, nombre_conexion, icono, descripcion
            FROM conexiones_normalizadas 
            WHERE station_id = ?
            ORDER BY tipo_conexion, nombre_conexion
        """, (station_id,))
        
        conexiones_raw = cursor.fetchall()
        conn.close()
        
        # Procesar conexiones
        conexiones = []
        for conexion in conexiones_raw:
            tipo_conexion, nombre_conexion, icono, descripcion = conexion
            conexiones.append({
                'linea': nombre_conexion,  # Usar nombre_conexion como línea para compatibilidad
                'tipo': tipo_conexion,
                'icono': icono,
                'descripcion': descripcion,
                'disponible': True
            })
        
        # Si no hay conexiones en la tabla normalizada, intentar con correspondencias (fallback)
        if not conexiones:
            print(f"[CONNECTIONS] No se encontraron conexiones en tabla normalizada, intentando correspondencias...")
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT correspondencias FROM estaciones_completas WHERE id_fijo = ?", (station_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0]:
                correspondencias_raw = row[0]
                try:
                    # Intentar parsear como JSON primero
                    if correspondencias_raw.startswith('[') or correspondencias_raw.startswith('{'):
                        conexiones_data = json.loads(correspondencias_raw)
                        if isinstance(conexiones_data, list):
                            for conexion in conexiones_data:
                                if isinstance(conexion, dict):
                                    conexiones.append({
                                        'linea': conexion.get('linea', str(conexion)),
                                        'tipo': 'Metro',
                                        'disponible': True
                                    })
                                else:
                                    conexiones.append({
                                        'linea': str(conexion),
                                        'tipo': 'Metro',
                                        'disponible': True
                                    })
                    else:
                        # Si no es JSON, procesar como texto separado por comas
                        conexiones_text = correspondencias_raw.replace(';', ',').replace(';', ',')
                        conexiones_list = [c.strip() for c in conexiones_text.split(',') if c.strip()]
                        
                        for conexion in conexiones_list:
                            if conexion and len(conexion) > 1 and conexion != '[]':
                                conexiones.append({
                                    'linea': conexion.strip(),
                                    'tipo': 'Metro',
                                    'disponible': True
                                })
                except Exception as e:
                    print(f"Error procesando correspondencias: {e}")
        
        print(f"[CONNECTIONS] Encontradas {len(conexiones)} conexiones para estación ID {station_id}")
        
        return jsonify({
            'estacion': {
                'nombre': nombre_estacion if 'nombre_estacion' in locals() else f'Estación {station_id}', 
                'id_fijo': station_id,
                'linea': linea if 'linea' in locals() else 'N/A'
            }, 
            'conexiones': conexiones,
            'total': len(conexiones)
        })
        
    except Exception as e:
        print(f"[CONNECTIONS] Error: {e}")
        return jsonify({'error': f'Error obteniendo conexiones: {str(e)}'}), 500

@app.route('/api/station/realtime/<identificador>')
def get_realtime_station_data_by_id_or_name(identificador):
    """Endpoint que devuelve datos en tiempo real usando ID o nombre de estación"""
    try:
        print(f"--- REALTIME_API: Buscando datos para: '{identificador}' ---")
        
        # Buscar estación en la base de datos relacional
        print(f"--- REALTIME_API: Conectando a estaciones_relacional.db ---")
        conn = sqlite3.connect('db/estaciones_relacional.db')
        cursor = conn.cursor()
        
        # Buscar por id_fijo si es número
        if identificador.isdigit():
            print(f"--- REALTIME_API: Buscando por ID {identificador} ---")
            # Primero buscar por id_modal
            cursor.execute("SELECT id_fijo, nombre, id_modal, linea, url FROM estaciones WHERE id_modal = ? LIMIT 1", (int(identificador),))
            estacion = cursor.fetchone()
            
            # Si no se encuentra por id_modal, buscar por id_fijo
            if not estacion:
                print(f"--- REALTIME_API: No encontrada por id_modal, buscando por id_fijo ---")
                cursor.execute("SELECT id_fijo, nombre, id_modal, linea, url FROM estaciones WHERE id_fijo = ? LIMIT 1", (int(identificador),))
                estacion = cursor.fetchone()
        else:
            print(f"--- REALTIME_API: Buscando por nombre {identificador} ---")
            nombre_normalizado = normalizar_nombre(identificador)
            cursor.execute("SELECT id_fijo, nombre, id_modal, linea, url FROM estaciones WHERE lower(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, 'á', 'a'), 'é', 'e'), 'Ã­', 'i'), 'ó', 'o'), 'ú', 'u'), 'Ã¼', 'u'), 'ñ', 'n')) LIKE ? LIMIT 1", (f'%{nombre_normalizado}%',))
            estacion = cursor.fetchone()
        
        print(f"--- REALTIME_API: Resultado búsqueda: {estacion} ---")
        conn.close()
        
        # Si no se encuentra en estaciones_relacional.db, buscar en estaciones_fijas_v2.db
        if not estacion:
            print(f"--- REALTIME_API: No encontrada en estaciones_relacional.db, buscando en estaciones_fijas_v2.db ---")
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Buscar en todas las tablas de líneas
            line_tables = [f'linea_{i}' for i in range(1, 13)] + ['linea_Ramal']
            
            for tabla in line_tables:
                try:
                    if identificador.isdigit():
                        # Primero buscar por id_modal
                        cursor.execute(f"SELECT id_fijo, nombre, url FROM {tabla} WHERE id_modal = ? LIMIT 1", (int(identificador),))
                        estacion = cursor.fetchone()
                        
                        # Si no se encuentra por id_modal, buscar por id_fijo
                        if not estacion:
                            cursor.execute(f"SELECT id_fijo, nombre, url FROM {tabla} WHERE id_fijo = ? LIMIT 1", (int(identificador),))
                            estacion = cursor.fetchone()
                    else:
                        nombre_normalizado = normalizar_nombre(identificador)
                        cursor.execute(f"SELECT id_fijo, nombre, url FROM {tabla} WHERE lower(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, 'á', 'a'), 'é', 'e'), 'Ã­', 'i'), 'ó', 'o'), 'ú', 'u'), 'Ã¼', 'u'), 'ñ', 'n')) LIKE ? LIMIT 1", (f'%{nombre_normalizado}%',))
                        estacion = cursor.fetchone()
                    
                    if estacion:
                        print(f"--- REALTIME_API: Encontrada en {tabla}: {estacion} ---")
                        # Obtener id_modal y linea de estaciones_relacional.db si existe
                        conn2 = sqlite3.connect('db/estaciones_relacional.db')
                        cursor2 = conn2.cursor()
                        cursor2.execute("SELECT id_modal, linea FROM estaciones WHERE id_fijo = ? LIMIT 1", (estacion[0],))
                        modal_result = cursor2.fetchone()
                        id_modal = modal_result[0] if modal_result else None
                        linea = modal_result[1] if modal_result else tabla.replace('linea_', '')
                        conn2.close()
                        
                        estacion = (estacion[0], estacion[1], id_modal, linea, estacion[2])
                        break
                except Exception as e:
                    print(f"--- REALTIME_API: Error en tabla {tabla}: {e} ---")
                    continue
            
            conn.close()
        
        if not estacion:
            print(f"--- REALTIME_API: Estación no encontrada en ninguna base de datos ---")
            return jsonify({'error': f'Estación no encontrada: {identificador}'}), 404
        
        print(f"--- REALTIME_API: Estación encontrada: {estacion} ---")
        id_fijo, nombre_estacion, id_modal, linea, url = estacion
        
        # Mapear línea para usar las tablas correctas
        linea_mapped = linea
        if linea == 'linea_8':
            linea_mapped = '8'
        elif linea.startswith('linea_'):
            linea_mapped = linea.replace('linea_', '')
        
        # 1. Obtener próximos trenes (scraper Ninja)
        proximos_trenes_html = '<div class="no-data">No disponible</div>'
        if id_modal:
            try:
                # Usar el scraper Ninja para obtener datos en tiempo real
                from herramientas.scraper_ninja_tiempo_real import ScraperNinjaTiempoReal
                scraper = ScraperNinjaTiempoReal()
                url_proximos_trenes = f"https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}"
                ninja_data = scraper.scrape_estacion_tiempo_real(url_proximos_trenes)
                proximos_trenes_html = ninja_data.get('proximos_trenes_html', '<div class="no-data">No disponible</div>') if ninja_data else '<div class="no-data">No disponible</div>'
                print(f"--- REALTIME_API: Datos Ninja obtenidos para ID {id_modal} ---")
            except Exception as e:
                print(f"--- REALTIME_API: Error Ninja: {e} ---")
        else:
            # Si no hay id_modal, intentar con el nombre de la estación
            try:
                from herramientas.scraper_ninja_tiempo_real import ScraperNinjaTiempoReal
                scraper = ScraperNinjaTiempoReal()
                ninja_data = scraper.scrape_estacion_tiempo_real(nombre_estacion)
                if ninja_data and 'proximos_trenes_html' in ninja_data:
                    proximos_trenes_html = ninja_data['proximos_trenes_html']
                    print(f"--- REALTIME_API: Datos Ninja obtenidos por nombre: {nombre_estacion} ---")
            except Exception as e:
                print(f"--- REALTIME_API: Error Ninja por nombre: {e} ---")
        
        # 2. Obtener datos estáticos de la base de datos
        detalles_scrapeados = {
            'estado_ascensores': 'No disponible',
            'estado_escaleras': 'No disponible',
            'last_update': 'No disponible',
            'linea': linea_mapped,
            'proximos_trenes_html': proximos_trenes_html
        }
        
        # 3. Obtener datos guardados de la base de datos
        datos_guardados = []
        try:
            conn = sqlite3.connect('db/estaciones_relacional.db')
            cursor = conn.cursor()
            
            # Buscar en la tabla de datos guardados
            cursor.execute("""
                SELECT nombre, linea, zona_tarifaria, accesible, elevators, escalators, 
                       defibrillator, mobileCoverage, shops, historical, ultima_actualizacion
                FROM estaciones 
                WHERE id_fijo = ?
            """, (id_fijo,))
            
            row = cursor.fetchone()
            if row:
                servicios_list = []
                if row[3]:  # accesible
                    servicios_list.append('Accesible')
                if row[4]:  # elevators
                    servicios_list.append('Ascensores')
                if row[5]:  # escalators
                    servicios_list.append('Escaleras')
                if row[6]:  # defibrillator
                    servicios_list.append('Desfibrilador')
                if row[7]:  # mobileCoverage
                    servicios_list.append('Cobertura móvil')
                if row[8]:  # shops
                    servicios_list.append('Tiendas')
                if row[9]:  # historical
                    servicios_list.append('Histórica')
                
                accesos_list = []
                if row[4]:  # elevators
                    accesos_list.append('Ascensores')
                if row[5]:  # escalators
                    accesos_list.append('Escaleras mecánicas')
                
                datos_formateados = {
                    'nombre': row[0],
                    'linea': row[1],
                    'zona_tarifaria': row[2] or 'No especificada',
                    'servicios': '; '.join(servicios_list) if servicios_list else '',
                    'accesos': '; '.join(accesos_list) if accesos_list else ''
                }
                datos_guardados.append(datos_formateados)
            
            conn.close()
        except Exception as e:
            print(f"--- REALTIME_API: Error obteniendo datos guardados: {e} ---")
        
        print(f"--- REALTIME_API: Devolviendo datos para '{identificador}' ---")
        return jsonify({
            'next_trains_html': proximos_trenes_html,
            'details': detalles_scrapeados,
            'stored_data': datos_guardados,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[REALTIME_API] Error: {e}")
        return jsonify({'error': f'Error obteniendo datos: {str(e)}'}), 500

@app.route('/api/station/elevators/<identificador>')
def get_station_elevators(identificador):
    """Endpoint que devuelve el estado de ascensores de una estación"""
    try:
        print(f"[ELEVATORS] Obteniendo estado de ascensores para: {identificador}")
        
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Buscar por id_fijo si es número
        if identificador.isdigit():
            cursor.execute("SELECT id_fijo, nombre, linea, ascensores, escaleras_mecanicas FROM estaciones_completas WHERE id_fijo = ? LIMIT 1", (int(identificador),))
        else:
            nombre_normalizado = normalizar_nombre(identificador)
            cursor.execute("SELECT id_fijo, nombre, linea, ascensores, escaleras_mecanicas FROM estaciones_completas WHERE lower(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(nombre, 'á', 'a'), 'é', 'e'), 'Ã­', 'i'), 'ó', 'o'), 'ú', 'u'), 'Ã¼', 'u'), 'ñ', 'n')) LIKE ? LIMIT 1", (f'%{nombre_normalizado}%',))
        
        estacion = cursor.fetchone()
        conn.close()
        
        if not estacion:
            return jsonify({'error': f'No se encontró la estación: {identificador}'}), 404
        
        id_fijo, nombre_estacion, linea, ascensores_raw, escaleras_raw = estacion
        
        # Construir URL de la estación para el scraper
        linea_mapped = linea
        if linea == 'Ramal':
            linea_mapped = 'R'
        
        url_estacion = f'https://www.metromadrid.es/es/linea/linea-{linea_mapped}#estacion-{id_fijo}'
        
        # Intentar obtener datos en tiempo real primero (más preciso)
        estado_ascensores = "No disponible"
        estado_escaleras = "No disponible"
        ultima_actualizacion = datetime.now().strftime("%H:%M")
        fuente_datos = "Base de datos"
        
        try:
            if NINJA_SCRAPER_AVAILABLE:
                print(f"[ELEVATORS] Intentando obtener datos en tiempo real para: {nombre_estacion}")
                print(f"[ELEVATORS] URL de la línea: {url_estacion}")
                scraper = ScraperNinjaTiempoReal()
                estado_ascensores, estado_escaleras = scraper.obtener_estado_servicios(url_estacion, id_modal=str(id_fijo))
                
                if estado_ascensores and estado_ascensores != "No disponible":
                    ultima_actualizacion = "Ahora"
                    fuente_datos = "Tiempo real"
                    print(f"[ELEVATORS] Datos en tiempo real obtenidos: {estado_ascensores}")
                else:
                    print(f"[ELEVATORS] No se pudieron obtener datos en tiempo real")
        except Exception as e:
            print(f"[ELEVATORS] Error obteniendo datos en tiempo real: {e}")
        
        # Si no hay datos en tiempo real, usar datos de la base de datos
        if estado_ascensores == "No disponible":
            # Determinar estado de ascensores desde la base de datos
            if ascensores_raw and ascensores_raw.strip():
                if ascensores_raw == 'Sí':
                    estado_ascensores = "Operativo"
                elif ascensores_raw == 'No':
                    estado_ascensores = "No disponible"
                else:
                    estado_ascensores = ascensores_raw
            else:
                # Si no hay datos, intentar inferir basándose en el nombre de la estación
                # Algunas estaciones conocidas que NO tienen ascensores
                estaciones_sin_ascensor = [
                    'estrecho', 'alvarado', 'cuatro caminos', 'rios rosas', 
                    'iglesia', 'bilbao', 'tribunal', 'callao', 'gran vía'
                ]
                nombre_lower = nombre_estacion.lower()
                if any(estacion in nombre_lower for estacion in estaciones_sin_ascensor):
                    estado_ascensores = "No disponible"
                else:
                    estado_ascensores = "Información no disponible"
        
        # Determinar estado de escaleras
        if estado_escaleras == "No disponible":
            if escaleras_raw and escaleras_raw.strip():
                if escaleras_raw == 'Sí':
                    estado_escaleras = "Operativo"
                elif escaleras_raw == 'No':
                    estado_escaleras = "No disponible"
                else:
                    estado_escaleras = escaleras_raw
            else:
                estado_escaleras = "Información no disponible"
        
        # Determinar si está operativo
        def is_operativo(estado):
            if not estado or estado == "No disponible" or estado == "Información no disponible":
                return False
            return 'operativo' in estado.lower() or 'correctamente' in estado.lower() or 'funciona' in estado.lower()
        
        return jsonify({
            'estacion': {
                'nombre': nombre_estacion,
                'id_fijo': id_fijo,
                'linea': linea
            },
            'ascensores': {
                'estado': estado_ascensores,
                'operativo': is_operativo(estado_ascensores),
                'escaleras': estado_escaleras,
                'escaleras_operativo': is_operativo(estado_escaleras)
            },
            'ultima_actualizacion': ultima_actualizacion,
            'fuente_datos': fuente_datos,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ELEVATORS] Error: {e}")
        return jsonify({'error': f'Error obteniendo estado de ascensores: {str(e)}'}), 500

# ============================================================================
# FUNCIONES DE USUARIOS
# ============================================================================

@app.route('/api/station/detailed/<int:station_id>')
def get_detailed_station_by_id(station_id):
    """API para obtener datos detallados de una estación por ID fijo"""
    try:
        estacion = buscar_estacion_por_id(station_id)
        if not estacion:
            return jsonify({'error': 'Estación no encontrada'}), 404
        
        return jsonify(estacion)
    except Exception as e:
        print(f"Error obteniendo datos de estación {station_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/station/id-modal/<int:id_modal>/name')
def get_station_name_by_id_modal(id_modal):
    """Convierte id_modal en nombre de estación"""
    try:
        import pandas as pd
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        # Buscar la estación por id_modal
        station = df[df['id_modal'] == float(id_modal)]
        
        if station.empty:
            return jsonify({'error': f'Estación no encontrada para id_modal: {id_modal}'}), 404
        
        station_name = station.iloc[0]['nombre']
        
        return jsonify({
            'success': True,
            'id_modal': id_modal,
            'station_name': station_name,
            'linea': station.iloc[0]['linea']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo nombre: {str(e)}'}), 500

# ============================================================================
# SISTEMA DE FAVORITOS
# ============================================================================

def get_user_favorite_lines(user_id):
    """Obtiene las líneas favoritas de un usuario"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fl.line_id
            FROM favorite_lines fl
            WHERE fl.user_id = ?
            ORDER BY fl.id DESC
        """, (user_id,))
        
        favorite_lines = []
        for row in cursor.fetchall():
            line_id = row[0]
            if line_id in LINEAS_CONFIG:
                line_config = LINEAS_CONFIG[line_id]
                favorite_lines.append({
                    'id': line_id,
                    'name': line_config['name'],
                    'color': line_config['color'],
                    'color_secondary': line_config['color_secondary'],
                    'text_color': line_config['text_color']
                })
        
        conn.close()
        return favorite_lines
    except Exception as e:
        print(f"Error obteniendo líneas favoritas: {e}")
        return []

def get_user_favorite_stations(user_id):
    """Obtiene las estaciones favoritas de un usuario agrupadas por nombre"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fs.station_id, fs.line_id, fs.station_name, fs.created_at
            FROM favorite_stations fs
            WHERE fs.user_id = ?
            ORDER BY fs.station_name, fs.created_at DESC
        """, (user_id,))
        
        # Agrupar estaciones por nombre
        stations_by_name = {}
        for row in cursor.fetchall():
            station_id, line_id, station_name, created_at = row
            line_config = LINEAS_CONFIG.get(line_id, {'name': f'Línea {line_id}', 'color': '#666'})
            
            station_data = {
                'station_id': station_id,
                'line_id': line_id,
                'line_name': line_config['name'],
                'line_color': line_config['color'],
                'added_at': created_at
            }
            
            if station_name not in stations_by_name:
                stations_by_name[station_name] = {
                    'station_name': station_name,
                    'lines': [],
                    'first_added': created_at
                }
            
            stations_by_name[station_name]['lines'].append(station_data)
            # Mantener la fecha más antigua
            if created_at < stations_by_name[station_name]['first_added']:
                stations_by_name[station_name]['first_added'] = created_at
        
        # Convertir a lista ordenada por fecha
        favorite_stations = []
        for station_name, station_group in stations_by_name.items():
            # Para retrocompatibilidad, incluir datos de la primera línea
            primary_line = station_group['lines'][0]
            favorite_stations.append({
                'station_name': station_name,
                'station_id': primary_line['station_id'],
                'line_id': primary_line['line_id'],
                'line_name': primary_line['line_name'],
                'line_color': primary_line['line_color'],
                'added_at': station_group['first_added'],
                'all_lines': station_group['lines'],  # Todas las líneas para esta estación
                'lines_count': len(station_group['lines'])
            })
        
        # Ordenar por fecha de primera adición
        favorite_stations.sort(key=lambda x: x['added_at'], reverse=True)
        
        conn.close()
        return favorite_stations
    except Exception as e:
        print(f"Error obteniendo estaciones favoritas: {e}")
        return []

@app.route('/api/favorites/lines', methods=['GET'])
@login_required
def get_favorite_lines():
    """API para obtener líneas favoritas del usuario actual"""
    favorite_lines = get_user_favorite_lines(current_user.id)
    return jsonify({
        'favorite_lines': favorite_lines,
        'total': len(favorite_lines)
    })

@app.route('/api/favorites/stations', methods=['GET'])
@login_required
def get_favorite_stations():
    """API para obtener estaciones favoritas del usuario actual"""
    favorite_stations = get_user_favorite_stations(current_user.id)
    return jsonify({
        'favorite_stations': favorite_stations,
        'total': len(favorite_stations)
    })

@app.route('/api/favorites/lines/<line_id>', methods=['POST'])
@login_required
def add_favorite_line(line_id):
    """Añade una línea a favoritos"""
    try:
        if line_id not in LINEAS_CONFIG:
            return jsonify({'error': 'Línea no válida'}), 400
        
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar si ya está en favoritos
        cursor.execute("SELECT id FROM favorite_lines WHERE user_id = ? AND line_id = ?", 
                      (current_user.id, line_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'message': 'La línea ya está en favoritos'}), 200
        
        # Añadir a favoritos
        cursor.execute("""
            INSERT INTO favorite_lines (user_id, line_id)
            VALUES (?, ?)
        """, (current_user.id, line_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Línea {line_id} añadida a favoritos', 'success': True})
    except Exception as e:
        return jsonify({'error': f'Error añadiendo línea a favoritos: {str(e)}'}), 500

@app.route('/api/favorites/lines/<line_id>', methods=['DELETE'])
@login_required
def remove_favorite_line(line_id):
    """Elimina una línea de favoritos"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM favorite_lines WHERE user_id = ? AND line_id = ?", 
                      (current_user.id, line_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'La línea no estaba en favoritos'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Línea {line_id} eliminada de favoritos', 'success': True})
    except Exception as e:
        return jsonify({'error': f'Error eliminando línea de favoritos: {str(e)}'}), 500

@app.route('/api/favorites/stations', methods=['POST'])
@login_required
def add_favorite_station():
    """Añade una estación a favoritos"""
    try:
        data = request.get_json()
        station_id = data.get('station_id')
        line_id = data.get('line_id')
        station_name = data.get('station_name')
        
        if not all([station_id, line_id, station_name]):
            return jsonify({'error': 'Faltan datos obligatorios'}), 400
        
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar si ya está en favoritos
        cursor.execute("SELECT id FROM favorite_stations WHERE user_id = ? AND station_id = ? AND line_id = ?", 
                      (current_user.id, station_id, line_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'message': 'La estación ya está en favoritos'}), 200
        
        # Añadir a favoritos
        cursor.execute("""
            INSERT INTO favorite_stations (user_id, station_id, line_id, station_name)
            VALUES (?, ?, ?, ?)
        """, (current_user.id, station_id, line_id, station_name))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Estación {station_name} añadida a favoritos', 'success': True})
    except Exception as e:
        return jsonify({'error': f'Error añadiendo estación a favoritos: {str(e)}'}), 500

@app.route('/api/favorites/stations/<int:station_id>/<line_id>', methods=['DELETE'])
@login_required
def remove_favorite_station(station_id, line_id):
    """Elimina una estación de favoritos"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM favorite_stations WHERE user_id = ? AND station_id = ? AND line_id = ?", 
                      (current_user.id, station_id, line_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'La estación no estaba en favoritos'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Estación eliminada de favoritos', 'success': True})
    except Exception as e:
        return jsonify({'error': f'Error eliminando estación de favoritos: {str(e)}'}), 500

@app.route('/api/favorites/check/line/<line_id>', methods=['GET'])
@login_required
def check_favorite_line(line_id):
    """Verifica si una línea está en favoritos"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM favorite_lines WHERE user_id = ? AND line_id = ?", 
                      (current_user.id, line_id))
        is_favorite = cursor.fetchone() is not None
        
        conn.close()
        return jsonify({'is_favorite': is_favorite})
    except Exception as e:
        return jsonify({'error': f'Error verificando favorito: {str(e)}'}), 500

@app.route('/api/favorites/check/station/<int:station_id>/<line_id>', methods=['GET'])
@login_required
def check_favorite_station(station_id, line_id):
    """Verifica si una estación está en favoritos"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM favorite_stations WHERE user_id = ? AND station_id = ? AND line_id = ?", 
                      (current_user.id, station_id, line_id))
        is_favorite = cursor.fetchone() is not None
        
        conn.close()
        return jsonify({'is_favorite': is_favorite})
    except Exception as e:
        return jsonify({'error': f'Error verificando favorito: {str(e)}'}), 500

@app.route('/api/favorites/stations/by-name/<station_name>', methods=['DELETE'])
@login_required
def remove_favorite_station_by_name(station_name):
    """Elimina todas las líneas de una estación de favoritos por nombre"""
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM favorite_stations WHERE user_id = ? AND station_name = ?", 
                      (current_user.id, station_name))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'La estación no estaba en favoritos'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Todas las líneas de {station_name} eliminadas de favoritos', 'success': True})
    except Exception as e:
        return jsonify({'error': f'Error eliminando estación de favoritos: {str(e)}'}), 500

@app.route('/api/stations/nearby', methods=['POST'])
def get_nearby_stations():
    """Obtiene estaciones cercanas a una ubicación específica"""
    try:
        data = request.get_json()
        user_lat = float(data.get('lat'))
        user_lon = float(data.get('lon'))
        radius_km = float(data.get('radius', 1.0))  # Radio por defecto: 1km
        limit = int(data.get('limit', 10))  # Límite por defecto: 10 estaciones
        
        # Usar la función existente para obtener todas las estaciones con coordenadas
        from flask import current_app
        
        # Obtener estaciones desde la API existente
        with current_app.test_request_context():
            stations_response = get_all_stations()
            stations_data = stations_response.get_json()
        
        if not isinstance(stations_data, list):
            return jsonify({
                'success': False,
                'error': 'No se pudieron cargar los datos de estaciones'
            }), 500
        
        # Función para calcular distancia usando fórmula de Haversine
        def haversine_distance(lat1, lon1, lat2, lon2):
            from math import radians, cos, sin, asin, sqrt
            
            # Convertir grados a radianes
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Fórmula de Haversine
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            
            # Radio de la Tierra en kilómetros
            r = 6371
            return c * r
        
        # Calcular distancias para todas las estaciones
        nearby_stations = []
        
        for station in stations_data:
            if station.get('lat') and station.get('lon'):
                try:
                    station_lat = float(station['lat'])
                    station_lon = float(station['lon'])
                    
                    distance = haversine_distance(
                        user_lat, user_lon,
                        station_lat, station_lon
                    )
                    
                    if distance <= radius_km:
                        # Obtener configuración de línea
                        line_config = LINEAS_CONFIG.get(str(station.get('line', '')), {
                            'name': f'Línea {station.get("line", "?")}',
                            'color': '#666666'
                        })
                        
                        nearby_stations.append({
                            'id_fijo': station.get('id', 0),
                            'nombre': station.get('name', 'Estación desconocida'),
                            'linea': str(station.get('line', '')),
                            'linea_nombre': line_config['name'],
                            'linea_color': line_config['color'],
                            'lat': station_lat,
                            'lon': station_lon,
                            'distancia_km': round(distance, 3),
                            'distancia_metros': round(distance * 1000),
                            'zona': station.get('zona', 'A'),
                            'accesibilidad': station.get('accesibilidad', 'No disponible')
                        })
                except (ValueError, TypeError):
                    continue  # Saltar estaciones con coordenadas inválidas
        
        # Ordenar por distancia
        nearby_stations.sort(key=lambda x: x['distancia_km'])
        
        # Limitar resultados
        nearby_stations = nearby_stations[:limit]
        
        return jsonify({
            'success': True,
            'user_location': {
                'lat': user_lat,
                'lon': user_lon
            },
            'search_radius_km': radius_km,
            'total_found': len(nearby_stations),
            'stations': nearby_stations
        })
        
    except Exception as e:
        print(f"Error buscando estaciones cercanas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/location/nearest-station', methods=['POST'])
def get_nearest_station():
    """Obtiene la estación más cercana usando el endpoint de estaciones cercanas con limit=1"""
    try:
        data = request.get_json()
        user_lat = float(data.get('lat'))
        user_lon = float(data.get('lon'))
        
        # Simplemente usar el endpoint de estaciones cercanas con límite 1 y radio amplio
        from flask import current_app
        
        # Crear una nueva request simulada para el endpoint nearby
        with current_app.test_request_context(
            '/api/stations/nearby', 
            method='POST',
            json={'lat': user_lat, 'lon': user_lon, 'radius': 10.0, 'limit': 1}
        ):
            nearby_response = get_nearby_stations()
            nearby_data = nearby_response.get_json()
        
        if nearby_data.get('success') and nearby_data.get('stations'):
            nearest_station = nearby_data['stations'][0]
            # Añadir tiempo de caminata
            nearest_station['walking_time_minutes'] = max(1, round(nearest_station['distancia_km'] * 12))
            
            return jsonify({
                'success': True,
                'nearest_station': nearest_station
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontraron estaciones cercanas'
            }), 404
            
    except Exception as e:
        print(f"Error obteniendo estación más cercana: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-js')
def test_js():
    """Ruta de prueba para verificar si JavaScript funciona"""
    return send_file('test_js.html')

@app.route('/test-station-js')
def test_station_js():
    """Ruta de prueba para verificar JavaScript específico de station.html"""
    try:
        return send_file('test_station_js.html')
    except Exception as e:
        return f"Error cargando archivo: {e}"





@app.route('/mapa-v5')
def mapa_interactivo_v5():
    """Mapa interactivo del Metro Madrid v5.0"""
    return render_template('mapa_rutas_v5.html')

@app.route('/mapa-metro')
def mapa_metro_publico():
    """Acceso público al mapa interactivo"""
    return render_template('mapa_rutas_v5.html')

@app.route('/metro-mapa')
def metro_mapa_directo():
    """Ruta directa al mapa del metro"""
    return render_template('mapa_rutas_v5.html')


# ============================================================================
# API v5.0 - SISTEMA AVANZADO DE RUTAS
# ============================================================================

@app.route('/api/v5/route')
def calculate_route_v5():
    """API v5.0 para calcular rutas con algoritmos avanzados"""
    try:
        # Obtener parámetros
        origen = request.args.get('origen', '').strip().upper()
        destino = request.args.get('destino', '').strip().upper()
        algoritmo = request.args.get('algoritmo', 'dijkstra_bidirectional')
        optimizacion = request.args.get('optimizacion', 'min_time')
        
        # Validar parámetros obligatorios
        if not origen or not destino:
            return jsonify({
                'success': False,
                'error': 'Parámetros origen y destino son obligatorios',
                'ejemplo': '/api/v5/route?origen=SOL&destino=CALLAO'
            }), 400
        
        if origen == destino:
            return jsonify({
                'success': False,
                'error': 'Las estaciones de origen y destino no pueden ser iguales'
            }), 400
        
        # Cargar sistema v5.0
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado',
                'solucion': 'Ejecuta: python generar_timing_avanzado.py'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        # Buscar IDs de estaciones
        origen_id = None
        destino_id = None
        
        for station_id, station_data in metro_data['stations'].items():
            if station_data['nombre'] == origen:
                origen_id = station_id
            if station_data['nombre'] == destino:
                destino_id = station_id
        
        if not origen_id:
            return jsonify({
                'success': False,
                'error': f'Estación de origen "{origen}" no encontrada',
                'sugerencia': 'Verifica el nombre exacto de la estación'
            }), 404
        
        if not destino_id:
            return jsonify({
                'success': False,
                'error': f'Estación de destino "{destino}" no encontrada',
                'sugerencia': 'Verifica el nombre exacto de la estación'
            }), 404
        
        # Crear grafo y calcular ruta
        from collections import defaultdict
        import heapq
        
        # Crear grafo simplificado
        grafo = defaultdict(list)
        edges_dict = {}
        
        for edge in metro_data['edges']:
            from_id = edge['from_id']
            to_id = edge['to_id']
            
            grafo[from_id].append(to_id)
            edges_dict[(from_id, to_id)] = edge
        
        # Algoritmo Dijkstra simplificado
        def dijkstra_simple(start, end):
            distances = {start: 0}
            previous = {}
            unvisited = set(metro_data['stations'].keys())
            
            while unvisited:
                current = min(unvisited, key=lambda x: distances.get(x, float('inf')))
                
                if distances.get(current, float('inf')) == float('inf'):
                    break
                    
                if current == end:
                    break
                    
                unvisited.remove(current)
                
                for neighbor in grafo[current]:
                    if neighbor in unvisited:
                        edge = edges_dict.get((current, neighbor))
                        if edge:
                            # Calcular coste según optimización
                            if optimizacion == 'min_time':
                                coste = edge['time'] + edge['transfer_penalty']
                            elif optimizacion == 'min_transfers':
                                coste = edge['time'] + (edge['transfer_penalty'] * 5)
                            elif optimizacion == 'min_distance':
                                coste = edge['distance']
                            else:
                                coste = edge['time']
                            
                            new_distance = distances[current] + coste
                            
                            if new_distance < distances.get(neighbor, float('inf')):
                                distances[neighbor] = new_distance
                                previous[neighbor] = current
            
            # Reconstruir path
            if end not in previous and end != start:
                return None
            
            path = []
            current = end
            while current is not None:
                path.append(current)
                current = previous.get(current)
            path.reverse()
            
            return {
                'path': path,
                'total_time': distances.get(end, 0),
                'algorithm': algoritmo
            }
        
        # Calcular ruta
        resultado = dijkstra_simple(origen_id, destino_id)
        
        if not resultado:
            return jsonify({
                'success': False,
                'error': 'No se encontró ruta entre las estaciones',
                'origen': origen,
                'destino': destino
            }), 404
        
        # Contar transbordos
        transbordos = 0
        linea_actual = None
        
        path_detallado = []
        for i, station_id in enumerate(resultado['path']):
            station_info = metro_data['stations'][station_id]
            
            # Determinar línea actual
            if i < len(resultado['path']) - 1:
                next_station = resultado['path'][i + 1]
                edge = edges_dict.get((station_id, next_station))
                if edge:
                    if linea_actual is None:
                        linea_actual = edge['line']
                    elif linea_actual != edge['line']:
                        transbordos += 1
                        linea_actual = edge['line']
            
            path_detallado.append({
                'id': station_id,
                'nombre': station_info['nombre'],
                'lineas': station_info['lineas'],
                'es_transbordo': len(station_info['lineas']) > 1 and i > 0 and i < len(resultado['path']) - 1
            })
        
        # Respuesta exitosa
        return jsonify({
            'success': True,
            'data': {
                'origen': {
                    'id': origen_id,
                    'nombre': origen
                },
                'destino': {
                    'id': destino_id,
                    'nombre': destino
                },
                'ruta': {
                    'tiempo_total': round(resultado['total_time'], 1),
                    'transbordos': transbordos,
                    'estaciones': len(resultado['path']),
                    'algoritmo': algoritmo,
                    'optimizacion': optimizacion,
                    'path': path_detallado
                }
            },
            'meta': {
                'version': '5.0.0',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error en API v5 route: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'version': '5.0.0'
        }), 500

@app.route('/api/v5/stations')
def get_stations_v5():
    """API v5.0 para obtener todas las estaciones disponibles"""
    try:
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        estaciones = []
        for station_id, station_data in metro_data['stations'].items():
            estaciones.append({
                'id': station_id,
                'nombre': station_data['nombre'],
                'lineas': station_data['lineas'],
                'correspondencias': station_data.get('correspondencias', [])
            })
        
        # Ordenar por nombre
        estaciones.sort(key=lambda x: x['nombre'])
        
        return jsonify({
            'success': True,
            'data': estaciones,
            'total': len(estaciones),
            'meta': {
                'version': '5.0.0',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v5/info')
def get_info_v5():
    """API v5.0 información del sistema"""
    try:
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': {
                'meta': metro_data['meta'],
                'statistics': metro_data['statistics'],
                'algorithms': metro_data['algorithms'],
                'endpoints': {
                    'route': '/api/v5/route?origen=SOL&destino=CALLAO',
                    'stations': '/api/v5/stations',
                    'info': '/api/v5/info'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    inicializar_aplicacion()
    app.run(host='0.0.0.0', port=5000, debug=True)


# ============================================================================
# RUTAS FALTANTES AÑADIDAS TEMPORALMENTE
# ============================================================================

@app.route('/map/routes')
def map_routes_view_fixed():
    """Página del mapa con calculadora de rutas inteligente - VERSIÓN FIJA"""
    return render_template('map_routes.html')

@app.route('/api/routes')
def get_routes_fixed():
    """Endpoint para obtener las rutas del metro para el mapa - VERSIÓN FIJA"""
    try:
        # Intentar cargar el archivo de rutas JSON con manejo de errores mejorado
        import os
        routes_file = 'static/data/metro_routes.json'
        
        if os.path.exists(routes_file):
            try:
                # Verificar el tamaño del archivo
                file_size = os.path.getsize(routes_file)
                print(f"Cargando archivo de rutas: {file_size} bytes")
                
                # Si el archivo es muy grande (>10MB), usar fallback
                if file_size > 10 * 1024 * 1024:  # 10MB
                    print("Archivo demasiado grande, usando datos básicos")
                    raise Exception("Archivo demasiado grande")
                
                with open(routes_file, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                print("Archivo de rutas cargado exitosamente")
                return jsonify(routes_data)
                
            except Exception as file_error:
                print(f"Error cargando archivo JSON: {file_error}")
                # Fallback a datos básicos
                pass
        
        # Fallback: generar datos básicos desde la configuración
        print("Generando datos básicos de rutas")
        lines = []
        for line_id, config in LINEAS_CONFIG.items():
            lines.append({
                'line': line_id,
                'name': config['name'],
                'color': config['color'],
                'paths': []  # Sin rutas geográficas por ahora
            })
        
        return jsonify({
            'success': True,
            'lines': lines,
            'total': len(lines)
        })
            
    except Exception as e:
        print(f"Error en /api/routes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/test')
def test_api_fixed():
    """Ruta de prueba para verificar que el servidor responde - VERSIÓN FIJA"""
    return jsonify({
        'message': 'API funcionando correctamente - VERSIÓN FIJA',
        'timestamp': datetime.now().isoformat(),
        'success': True
    })


# ============================================================================
# IMPORTACIÓN DE RUTAS FALTANTES (MÓDULO SEPARADO)
# ============================================================================

try:
    from routes_missing import register_missing_routes
    register_missing_routes(app)
    print("✅ Rutas faltantes cargadas desde módulo separado")
except Exception as e:
    print(f"⚠️ Error cargando rutas faltantes: {e}")


# ============================================================================
# RUTA ALTERNATIVA PARA CALCULADORA (FUNCIONA INMEDIATAMENTE)
# ============================================================================

@app.route('/calculadora')
def calculadora_rutas():
    """Calculadora de rutas - RUTA ALTERNATIVA QUE FUNCIONA"""
    return render_template('map_routes.html')

@app.route('/calc')
def calc_rutas():
    """Calculadora de rutas - RUTA CORTA QUE FUNCIONA"""
    return render_template('map_routes.html')

@app.route('/rutas')
def rutas_metro():
    """Calculadora de rutas - RUTA SIMPLE QUE FUNCIONA"""
    return render_template('map_routes.html')


# ============================================================================
# RUTA PÚBLICA PARA CALCULADORA (SIN LOGIN REQUERIDO)
# ============================================================================

@app.route('/metro-rutas')
def metro_rutas_publico():
    """Calculadora de rutas - RUTA PÚBLICA SIN LOGIN"""
    return render_template('map_routes.html')

@app.route('/mapa-rutas')
def mapa_rutas_publico():
    """Calculadora de rutas - RUTA PÚBLICA ALTERNATIVA"""
    return render_template('map_routes.html')

@app.route('/calculadora-metro')
def calculadora_metro_publico():
    """Calculadora de rutas - RUTA PÚBLICA DESCRIPTIVA"""
    return render_template('map_routes.html')


# ============================================================================
# RUTA SIMPLE PARA CALCULADORA DE METRO
# ============================================================================

@app.route('/calculadora-simple')
def calculadora_simple():
    """Calculadora simple de rutas - PÁGINA INDEPENDIENTE"""
    try:
        with open('calculadora_metro.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "Archivo calculadora_metro.html no encontrado", 404

@app.route('/calc-simple')
def calc_simple():
    """Calculadora simple - RUTA CORTA"""
    return calculadora_simple()

@app.route('/metro-calc')
def metro_calc():
    """Calculadora metro - RUTA ALTERNATIVA"""
    return calculadora_simple()


# ============================================================================
# RUTA ESPECÍFICA PARA CALCULADORA DE RUTAS (SIN LOGIN)
# ============================================================================

@app.route('/calculadora-rutas')
def calculadora_rutas_metro():
    """Calculadora de rutas del metro - SIN LOGIN REQUERIDO"""
    return render_template('map_routes.html')

@app.route('/calc-metro')
def calc_metro_simple():
    """Calculadora simple del metro - RUTA ALTERNATIVA"""
    return render_template('map_routes.html')

@app.route('/rutas-metro')
def rutas_metro_madrid():
    """Rutas del Metro de Madrid - ACCESO PÚBLICO"""
    return render_template('map_routes.html')
