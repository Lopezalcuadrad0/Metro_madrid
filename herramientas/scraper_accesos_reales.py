#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DE ACCESOS REALES - METRO DE MADRID
===========================================

Scraper específico para extraer información real de accesos
desde la página web oficial de Metro de Madrid.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
import sqlite3
import os

class ScraperAccesosReales:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://www.metromadrid.es"
        
    def scrape_accesos_estacion(self, station_url):
        """
        Extrae los accesos reales de una estación desde la página web de Metro
        """
        try:
            print(f"🔍 Scraping accesos para: {station_url}")
            
            # Hacer la petición a la página de la estación
            response = self.session.get(station_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la sección de accesos
            accesos = self.extraer_accesos_desde_html(soup)
            
            return {
                'success': True,
                'accesos': accesos,
                'total_accesos': len(accesos),
                'timestamp': datetime.now().isoformat(),
                'url_origen': station_url
            }
            
        except Exception as e:
            print(f"❌ Error scraping accesos: {e}")
            return {
                'success': False,
                'error': str(e),
                'accesos': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def extraer_accesos_desde_html(self, soup):
        """
        Extrae los accesos desde el HTML usando las clases y atributos específicos
        """
        accesos = []
        
        # Buscar elementos con role="cell" y aria-label="ACCESS NAME"
        access_cells = soup.find_all('td', attrs={'role': 'cell', 'aria-label': 'ACCESS NAME'})
        
        print(f"🔍 Encontrados {len(access_cells)} elementos de acceso")
        
        for cell in access_cells:
            try:
                # Extraer el tipo de acceso (strong)
                tipo_acceso = cell.find('strong')
                tipo = tipo_acceso.get_text(strip=True) if tipo_acceso else "Acceso"
                
                # Extraer la dirección (p)
                direccion_elem = cell.find('p')
                direccion = direccion_elem.get_text(strip=True) if direccion_elem else ""
                
                # Extraer UUID si está disponible
                uuid = cell.get('data-insuit-uuid', '')
                
                # Crear objeto de acceso
                acceso = {
                    'tipo': tipo,
                    'direccion': direccion,
                    'uuid': uuid,
                    'vestibulo': self.determinar_vestibulo(tipo, direccion),
                    'nombre_acceso': tipo
                }
                
                accesos.append(acceso)
                print(f"  ✅ Acceso: {tipo} - {direccion}")
                
            except Exception as e:
                print(f"  ⚠️ Error procesando celda de acceso: {e}")
                continue
        
        # Si no se encontraron accesos con el método principal, intentar métodos alternativos
        if not accesos:
            accesos = self.extraer_accesos_alternativo(soup)
        
        return accesos
    
    def extraer_accesos_alternativo(self, soup):
        """
        Método alternativo para extraer accesos si el principal no funciona
        """
        accesos = []
        
        # Buscar tablas que contengan información de accesos
        tables = soup.find_all('table')
        
        for table in tables:
            # Buscar filas que contengan información de accesos
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                for cell in cells:
                    # Buscar texto que indique un acceso
                    cell_text = cell.get_text(strip=True).lower()
                    
                    if any(keyword in cell_text for keyword in ['ascensor', 'escalera', 'acceso', 'entrada', 'salida']):
                        # Extraer información del acceso
                        strong_elem = cell.find('strong')
                        p_elem = cell.find('p')
                        
                        if strong_elem or p_elem:
                            tipo = strong_elem.get_text(strip=True) if strong_elem else "Acceso"
                            direccion = p_elem.get_text(strip=True) if p_elem else ""
                            
                            acceso = {
                                'tipo': tipo,
                                'direccion': direccion,
                                'uuid': '',
                                'vestibulo': self.determinar_vestibulo(tipo, direccion),
                                'nombre_acceso': tipo
                            }
                            
                            accesos.append(acceso)
                            print(f"  ✅ Acceso (alt): {tipo} - {direccion}")
        
        return accesos
    
    def determinar_vestibulo(self, tipo_acceso, direccion):
        """
        Determina el vestíbulo basándose en el tipo de acceso y dirección
        """
        tipo_lower = tipo_acceso.lower()
        direccion_lower = direccion.lower()
        
        # Lógica para determinar vestíbulo
        if 'ascensor' in tipo_lower:
            return 'Vestíbulo Principal'
        elif 'escalera' in tipo_lower:
            return 'Vestíbulo Secundario'
        elif 'acceso' in tipo_lower:
            return 'Vestíbulo General'
        else:
            return 'Vestíbulo'
    
    def guardar_accesos_bd(self, station_id, accesos):
        """
        Guarda los accesos extraídos en la base de datos
        """
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
            cursor = conn.cursor()
            
            # Crear tabla de accesos si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accesos_reales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER,
                    tipo_acceso TEXT,
                    direccion TEXT,
                    vestibulo TEXT,
                    nombre_acceso TEXT,
                    uuid TEXT,
                    timestamp TEXT,
                    url_origen TEXT
                )
            ''')
            
            # Insertar accesos
            for acceso in accesos:
                cursor.execute('''
                    INSERT INTO accesos_reales 
                    (station_id, tipo_acceso, direccion, vestibulo, nombre_acceso, uuid, timestamp, url_origen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    station_id,
                    acceso['tipo'],
                    acceso['direccion'],
                    acceso['vestibulo'],
                    acceso['nombre_acceso'],
                    acceso['uuid'],
                    datetime.now().isoformat(),
                    acceso.get('url_origen', '')
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ {len(accesos)} accesos guardados en BD")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando accesos en BD: {e}")
            return False
    
    def obtener_accesos_estacion(self, station_name, station_url):
        """
        Función principal para obtener accesos de una estación
        """
        print(f"🚪 Obteniendo accesos reales para: {station_name}")
        
        # Hacer scraping de accesos
        resultado = self.scrape_accesos_estacion(station_url)
        
        if resultado['success'] and resultado['accesos']:
            print(f"✅ {len(resultado['accesos'])} accesos extraídos para {station_name}")
            
            # Guardar en BD si es necesario
            # self.guardar_accesos_bd(station_id, resultado['accesos'])
            
            return resultado
        else:
            print(f"❌ No se pudieron extraer accesos para {station_name}")
            return resultado
    
    def close(self):
        """Cierra la sesión"""
        self.session.close()

# Función de prueba
def test_scraper_accesos():
    """Función para probar el scraper de accesos"""
    scraper = ScraperAccesosReales()
    
    # URL real de la base de datos
    test_url = "https://www.metromadrid.es/es/linea/linea-4#estacion-113"  # Bilbao
    
    try:
        resultado = scraper.scrape_accesos_estacion(test_url)
        
        if resultado['success']:
            print(f"✅ Scraping exitoso: {resultado['total_accesos']} accesos")
            for acceso in resultado['accesos']:
                print(f"  - {acceso['tipo']}: {acceso['direccion']}")
        else:
            print(f"❌ Error en scraping: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_scraper_accesos() 