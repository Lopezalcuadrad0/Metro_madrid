#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Updater 7 Minutos para Metro de Madrid
Actualiza solo datos de estado: escaleras, alertas, estado de vía, funcionamiento de líneas
"""

import time
import schedule
import logging
import threading
import sqlite3
import random
from datetime import datetime
from metro_detailed_scraper import MetroDetailedScraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_updater_7min.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MetroAutoUpdater:
    def __init__(self):
        self.is_running = False
        self.update_thread = None
        self.last_update = None
        self.scraper = MetroDetailedScraper()
        self.stations_updated = 0
        
    def get_random_stations(self, count=20):
        """Obtiene estaciones aleatorias de la base de datos"""
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Obtener estaciones de todas las líneas
            lineas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'Ramal']
            all_stations = []
            
            for linea in lineas:
                tabla_nombre = f'linea_{linea}'
                try:
                    cursor.execute(f"""
                        SELECT id_fijo, nombre, id_modal 
                        FROM {tabla_nombre} 
                        WHERE id_modal IS NOT NULL
                        ORDER BY RANDOM()
                        LIMIT 5
                    """)
                    
                    line_stations = cursor.fetchall()
                    for row in line_stations:
                        all_stations.append({
                            'id_estacion': row[0],
                            'nombre': row[1],
                            'id_modal': row[2],
                            'linea': linea
                        })
                        
                except Exception as e:
                    logging.warning(f"⚠️ Error en tabla {tabla_nombre}: {e}")
                    
                    continue
            
            conn.close()
            
            # Seleccionar estaciones aleatorias
            random.shuffle(all_stations)
            return all_stations[:count]
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo estaciones aleatorias: {e}")
            return []
    
    def update_station_status(self, station_data):
        """Actualiza el estado de una estación (escaleras, alertas, etc.)"""
        try:
            nombre = station_data['nombre']
            linea = station_data['linea']
            id_estacion = station_data['id_estacion']
            
            logging.info(f"🔄 Actualizando estado: {nombre} (Línea {linea})")
            
            # Hacer scraping de datos de estado
            result = self.scraper.scrape_station_details(nombre)
            
            if 'error' not in result:
                # Guardar datos de estado en la base de datos
                self.save_status_to_db(station_data, result)
                logging.info(f"✅ Estado actualizado: {nombre}")
                return True
            else:
                logging.warning(f"⚠️ Error actualizando {nombre}: {result['error']}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error actualizando estado de {station_data['nombre']}: {e}")
            return False
    
    def save_status_to_db(self, station_data, scraped_data):
        """Guarda los datos de estado en la base de datos"""
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Crear tabla de estado si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS station_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER,
                    station_name TEXT,
                    linea TEXT,
                    estado_ascensores TEXT,
                    estado_escaleras TEXT,
                    alertas TEXT,
                    funcionamiento_linea TEXT,
                    accesos TEXT,
                    calles TEXT,
                    servicios TEXT,
                    zona_tarifaria TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Extraer datos de estado del resultado del scraping
            status_data = {
                'estado_ascensores': 'Desconocido',
                'estado_escaleras': 'Desconocido',
                'alertas': 'Sin alertas',
                'funcionamiento_linea': 'Normal',
                'accesos': 'No disponible',
                'calles': 'No disponible',
                'servicios': 'No disponible',
                'zona_tarifaria': 'No disponible'
            }
            
            if 'resultados' in scraped_data:
                for resultado in scraped_data['resultados']:
                    # Estado de ascensores y escaleras
                    if 'estado_ascensores' in resultado:
                        status_data['estado_ascensores'] = resultado['estado_ascensores'] or 'Desconocido'
                    if 'estado_escaleras' in resultado:
                        status_data['estado_escaleras'] = resultado['estado_escaleras'] or 'Desconocido'
                    
                    # Accesos y calles
                    if 'accesos' in resultado and resultado['accesos']:
                        accesos_list = []
                        for acceso in resultado['accesos']:
                            if isinstance(acceso, dict):
                                accesos_list.append(f"{acceso.get('nombre', '')} - {acceso.get('direccion', '')}")
                            else:
                                accesos_list.append(str(acceso))
                        status_data['accesos'] = '; '.join(accesos_list) if accesos_list else 'No disponible'
                    
                    # Calles (extraer de accesos)
                    if 'accesos' in resultado and resultado['accesos']:
                        calles_list = []
                        for acceso in resultado['accesos']:
                            if isinstance(acceso, dict) and 'direccion' in acceso:
                                calles_list.append(acceso['direccion'])
                        status_data['calles'] = '; '.join(calles_list) if calles_list else 'No disponible'
                    
                    # Servicios
                    if 'servicios' in resultado and resultado['servicios']:
                        status_data['servicios'] = '; '.join(resultado['servicios'])
                    
                    # Zona tarifaria
                    if 'zona_tarifaria' in resultado and resultado['zona_tarifaria']:
                        status_data['zona_tarifaria'] = resultado['zona_tarifaria']
            
            # Insertar o actualizar estado
            cursor.execute("""
                INSERT OR REPLACE INTO station_status 
                (station_id, station_name, linea, estado_ascensores, estado_escaleras, alertas, funcionamiento_linea, accesos, calles, servicios, zona_tarifaria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                station_data['id_estacion'],
                station_data['nombre'],
                station_data['linea'],
                status_data['estado_ascensores'],
                status_data['estado_escaleras'],
                status_data['alertas'],
                status_data['funcionamiento_linea'],
                status_data['accesos'],
                status_data['calles'],
                status_data['servicios'],
                status_data['zona_tarifaria']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ Error guardando estado en BD: {e}")
    
    def run_update(self):
        """Ejecuta una actualización de estado de estaciones"""
        try:
            logging.info("🔄 Iniciando actualización automática de estado (7 min)")
            
            # Obtener 20 estaciones aleatorias
            stations = self.get_random_stations(20)
            
            if not stations:
                logging.warning("⚠️ No se pudieron obtener estaciones para actualizar")
                return
            
            logging.info(f"📊 Actualizando estado de {len(stations)} estaciones")
            
            updated_count = 0
            total_stations = len(stations)
            
            for i, station in enumerate(stations, 1):
                logging.info(f"🔄 [{i}/{total_stations}] Actualizando estado: {station['nombre']} (Línea {station['linea']})")
                
                if self.update_station_status(station):
                    updated_count += 1
                    logging.info(f"✅ [{i}/{total_stations}] Estado actualizado: {station['nombre']}")
                else:
                    logging.warning(f"⚠️ [{i}/{total_stations}] Error actualizando: {station['nombre']}")
                
                time.sleep(random.uniform(2, 5))  # Delay entre estaciones
            
            self.stations_updated = updated_count
            self.last_update = datetime.now()
            
            logging.info(f"✅ Actualización completada: {updated_count}/{total_stations} estaciones actualizadas")
            
        except Exception as e:
            logging.error(f"❌ Error en actualización automática: {e}")
    
    def start_background_updates(self):
        """Inicia las actualizaciones en segundo plano"""
        if self.is_running:
            logging.warning("Auto updater ya está ejecutándose")
            return
        
        self.is_running = True
        logging.info("🚇 Iniciando Auto Updater 7 Minutos (solo estado) en segundo plano...")
        
        # Programar actualización cada 7 minutos
        schedule.every(7).minutes.do(self.run_update)
        
        # Ejecutar una actualización inicial
        logging.info("🔄 Ejecutando actualización inicial de estado...")
        self.run_update()
        
        # Bucle principal en thread separado
        def update_loop():
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    logging.error(f"❌ Error en bucle de actualización: {e}")
                    time.sleep(60)  # Esperar 1 minuto antes de reintentar
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        logging.info("✅ Auto updater de estado iniciado en segundo plano")
    
    def stop_updates(self):
        """Detiene las actualizaciones"""
        if not self.is_running:
            logging.warning("Auto updater no está ejecutándose")
            return
        
        self.is_running = False
        schedule.clear()
        logging.info("🛑 Auto updater detenido")
    
    def get_status(self):
        """Obtiene el estado del auto updater"""
        return {
            'is_running': self.is_running,
            'next_update': schedule.next_run() if schedule.jobs else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'stations_updated': self.stations_updated
        }

# Instancia global del auto updater
auto_updater = MetroAutoUpdater()

def start_auto_updater():
    """Función para iniciar el auto updater desde la app Flask"""
    auto_updater.start_background_updates()

def stop_auto_updater():
    """Función para detener el auto updater"""
    auto_updater.stop_updates()

def get_updater_status():
    """Función para obtener el estado del auto updater"""
    return auto_updater.get_status()

def main():
    """Función principal para ejecutar el auto updater independientemente"""
    logging.info("🚇 Auto Updater 7 Minutos - Modo independiente (solo estado)")
    
    try:
        auto_updater.start_background_updates()
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("🛑 Detención solicitada por el usuario")
        auto_updater.stop_updates()
    except Exception as e:
        logging.error(f"❌ Error en modo independiente: {e}")
        auto_updater.stop_updates()

if __name__ == "__main__":
    main() 