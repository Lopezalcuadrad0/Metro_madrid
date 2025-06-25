#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Scraper Integrado para Metro de Madrid
Combina auto-updater de estado de estaciones + scraper de estado de líneas
- Cada 4 minutos: 5 estaciones aleatorias (considerando última actualización)
- Si detecta cambios: ejecuta scraper completo de todas las líneas
- Control de inicio/parada desde el menú principal
"""

import time
import schedule
import logging
import threading
import sqlite3
import random
import json
from datetime import datetime, timedelta
import os
import sys

# Añadir el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el scraper de estado de líneas
from scraper_estado_lineas import ScraperEstadoLineas

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_scraper_integrado.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AutoScraperIntegrado:
    def __init__(self):
        self.is_running = False
        self.update_thread = None
        self.last_update = None
        self.stations_updated = 0
        self.lines_updated = 0
        self.changes_detected = 0
        
        # Scrapers
        self.scraper_estado = ScraperEstadoLineas()
        
        # Configuración
        self.interval_minutes = 4
        self.stations_per_update = 5
        
        # Historial de actualizaciones por estación
        self.station_update_history = {}
        
        logging.info("🚇 Auto Scraper Integrado inicializado")
    
    def get_stations_with_update_history(self):
        """Obtiene estaciones con información de última actualización"""
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Obtener estaciones de todas las líneas con información de última actualización
            lineas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'Ramal']
            all_stations = []
            
            for linea in lineas:
                tabla_nombre = f'linea_{linea}'
                try:
                    cursor.execute(f"""
                        SELECT id_fijo, nombre, id_modal, 
                               (SELECT MAX(timestamp) FROM station_status WHERE station_id = id_fijo) as last_update
                        FROM {tabla_nombre} 
                        WHERE id_modal IS NOT NULL
                    """)
                    
                    line_stations = cursor.fetchall()
                    for row in line_stations:
                        last_update = row[3] if row[3] else None
                        all_stations.append({
                            'id_estacion': row[0],
                            'nombre': row[1],
                            'id_modal': row[2],
                            'linea': linea,
                            'last_update': last_update
                        })
                        
                except Exception as e:
                    logging.warning(f"⚠️ Error en tabla {tabla_nombre}: {e}")
                    continue
            
            conn.close()
            return all_stations
            
        except Exception as e:
            logging.error(f"❌ Error obteniendo estaciones con historial: {e}")
            return []
    
    def select_stations_for_update(self):
        """Selecciona estaciones para actualizar basándose en la última actualización"""
        all_stations = self.get_stations_with_update_history()
        
        if not all_stations:
            logging.warning("⚠️ No se pudieron obtener estaciones")
            return []
        
        # Ordenar por última actualización (las más antiguas primero)
        now = datetime.now()
        for station in all_stations:
            if station['last_update']:
                try:
                    last_update = datetime.fromisoformat(station['last_update'].replace('Z', '+00:00'))
                    station['hours_since_update'] = (now - last_update).total_seconds() / 3600
                except:
                    station['hours_since_update'] = 999  # Muchas horas si no se puede parsear
            else:
                station['hours_since_update'] = 999  # Nunca actualizada
        
        # Ordenar por tiempo desde última actualización (más antiguas primero)
        all_stations.sort(key=lambda x: x['hours_since_update'], reverse=True)
        
        # Seleccionar las primeras 5 (las más antiguas)
        selected_stations = all_stations[:self.stations_per_update]
        
        logging.info(f"📊 Seleccionadas {len(selected_stations)} estaciones para actualizar:")
        for station in selected_stations:
            hours = station['hours_since_update']
            if hours == 999:
                logging.info(f"  - {station['nombre']} (Línea {station['linea']}): Nunca actualizada")
            else:
                logging.info(f"  - {station['nombre']} (Línea {station['linea']}): {hours:.1f} horas sin actualizar")
        
        return selected_stations
    
    def check_for_changes(self, station_data, scraped_data):
        """Verifica si hay cambios en los datos de la estación"""
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Obtener datos actuales de la estación
            cursor.execute("""
                SELECT estado_ascensores, estado_escaleras, alertas, accesos, servicios
                FROM station_status 
                WHERE station_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (station_data['id_estacion'],))
            
            current_data = cursor.fetchone()
            conn.close()
            
            if not current_data:
                # No hay datos previos, considerar como cambio
                return True
            
            # Comparar datos actuales con nuevos datos
            current_ascensores = current_data[0] or 'Desconocido'
            current_escaleras = current_data[1] or 'Desconocido'
            current_alertas = current_data[2] or 'Sin alertas'
            
            # Extraer nuevos datos
            new_ascensores = 'Desconocido'
            new_escaleras = 'Desconocido'
            new_alertas = 'Sin alertas'
            
            if 'resultados' in scraped_data:
                for resultado in scraped_data['resultados']:
                    if 'estado_ascensores' in resultado:
                        new_ascensores = resultado['estado_ascensores'] or 'Desconocido'
                    if 'estado_escaleras' in resultado:
                        new_escaleras = resultado['estado_escaleras'] or 'Desconocido'
            
            # Verificar cambios
            changes = (
                current_ascensores != new_ascensores or
                current_escaleras != new_escaleras or
                current_alertas != new_alertas
            )
            
            if changes:
                logging.info(f"🔄 Cambios detectados en {station_data['nombre']}:")
                logging.info(f"  Ascensores: {current_ascensores} → {new_ascensores}")
                logging.info(f"  Escaleras: {current_escaleras} → {new_escaleras}")
                logging.info(f"  Alertas: {current_alertas} → {new_alertas}")
            
            return changes
            
        except Exception as e:
            logging.error(f"❌ Error verificando cambios: {e}")
            return False
    
    def update_station_status(self, station_data):
        """Actualiza el estado de una estación específica"""
        try:
            nombre = station_data['nombre']
            linea = station_data['linea']
            id_estacion = station_data['id_estacion']
            
            logging.info(f"🔄 Actualizando estado: {nombre} (Línea {linea})")
            
            # Importar el scraper de datos detallados
            from scraper_datos_detallados import MetroDetailedScraper
            scraper = MetroDetailedScraper()
            
            # Hacer scraping de datos de estado
            result = scraper.scrape_station_details(nombre)
            
            if 'error' not in result:
                # Verificar si hay cambios
                has_changes = self.check_for_changes(station_data, result)
                
                # Guardar datos de estado en la base de datos
                self.save_status_to_db(station_data, result)
                
                if has_changes:
                    self.changes_detected += 1
                    logging.info(f"✅ Cambios detectados y guardados: {nombre}")
                else:
                    logging.info(f"✅ Estado actualizado (sin cambios): {nombre}")
                
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
    
    def run_station_updates(self):
        """Ejecuta actualización de estaciones seleccionadas"""
        try:
            logging.info("🔄 Iniciando actualización automática de estaciones")
            
            # Seleccionar estaciones basándose en última actualización
            stations = self.select_stations_for_update()
            
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
            
            logging.info(f"✅ Actualización de estaciones completada: {updated_count}/{total_stations} estaciones actualizadas")
            
            # Si se detectaron cambios, ejecutar scraper completo de líneas
            if self.changes_detected > 0:
                logging.info(f"🔄 Cambios detectados ({self.changes_detected}), ejecutando scraper completo de líneas...")
                self.run_complete_lines_update()
            
        except Exception as e:
            logging.error(f"❌ Error en actualización automática: {e}")
    
    def run_complete_lines_update(self):
        """Ejecuta el scraper completo de todas las líneas"""
        try:
            logging.info("🔄 Ejecutando scraper completo de estado de líneas...")
            
            resultados = self.scraper_estado.obtener_estado_todas_lineas()
            
            if resultados:
                self.lines_updated = len(resultados)
                logging.info(f"✅ Scraper completo completado: {len(resultados)} líneas actualizadas")
            else:
                logging.warning("⚠️ No se obtuvieron resultados del scraper completo")
            
        except Exception as e:
            logging.error(f"❌ Error en scraper completo: {e}")
    
    def start_background_updates(self):
        """Inicia las actualizaciones en segundo plano"""
        if self.is_running:
            logging.warning("Auto scraper integrado ya está ejecutándose")
            return
        
        self.is_running = True
        logging.info(f"🚇 Iniciando Auto Scraper Integrado en segundo plano... (cada {self.interval_minutes} minutos)")
        
        # Programar actualización cada X minutos
        schedule.every(self.interval_minutes).minutes.do(self.run_station_updates)
        
        # Ejecutar una actualización inicial
        logging.info("🔄 Ejecutando actualización inicial...")
        self.run_station_updates()
        
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
        
        logging.info("✅ Auto scraper integrado iniciado en segundo plano")
    
    def stop_updates(self):
        """Detiene las actualizaciones"""
        if not self.is_running:
            logging.warning("Auto scraper integrado no está ejecutándose")
            return
        
        self.is_running = False
        schedule.clear()
        logging.info("🛑 Auto scraper integrado detenido")
    
    def get_status(self):
        """Obtiene el estado del auto scraper"""
        return {
            'is_running': self.is_running,
            'next_update': schedule.next_run() if schedule.jobs else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'stations_updated': self.stations_updated,
            'lines_updated': self.lines_updated,
            'changes_detected': self.changes_detected,
            'interval_minutes': self.interval_minutes,
            'stations_per_update': self.stations_per_update
        }

# Instancia global del auto scraper
auto_scraper = AutoScraperIntegrado()

def start_auto_scraper():
    """Función para iniciar el auto scraper desde la app Flask"""
    auto_scraper.start_background_updates()

def stop_auto_scraper():
    """Función para detener el auto scraper"""
    auto_scraper.stop_updates()

def get_scraper_status():
    """Función para obtener el estado del auto scraper"""
    return auto_scraper.get_status()

def main():
    """Función principal para ejecutar el auto scraper independientemente"""
    logging.info("🚇 Auto Scraper Integrado - Modo independiente")
    
    try:
        auto_scraper.start_background_updates()
        
        # Mantener el programa corriendo
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("🛑 Detención solicitada por el usuario")
        auto_scraper.stop_updates()
    except Exception as e:
        logging.error(f"❌ Error en modo independiente: {e}")
        auto_scraper.stop_updates()

if __name__ == "__main__":
    main() 