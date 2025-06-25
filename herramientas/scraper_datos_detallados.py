#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DATOS DETALLADOS - Metro de Madrid
==========================================

Scraper que obtiene datos detallados de las estaciones (dirección, calle, etc.)
una sola vez y los guarda en la base de datos fija.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import time
import re
from datetime import datetime
import unicodedata
import pandas as pd

class ScraperDatosDetallados:
    def __init__(self):
        """Inicializa el scraper con la base de datos"""
        try:
            # Conectar a la base de datos
            self.conn = sqlite3.connect('../db/estaciones_fijas_v2.db')
            self.cursor = self.conn.cursor()
            print("[INFO] Base de datos conectada correctamente")
            
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Lista de tablas de líneas
            self.lineas_tablas = [
                'linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5', 'linea_6',
                'linea_7', 'linea_8', 'linea_9', 'linea_10', 'linea_11', 'linea_12', 'linea_Ramal'
            ]
            
            # Inicializar base de datos
            self.init_database()
            
        except Exception as e:
            print(f"[ERROR] Error inicializando base de datos: {e}")
            raise
    
    def init_database(self):
        """Inicializa la base de datos y crea columnas para datos detallados si no existen"""
        try:
            cursor = self.cursor
            
            # Columnas a agregar para datos detallados
            columnas_detalladas = [
                'direccion_completa',
                'calle',
                'codigo_postal',
                'distrito',
                'barrio',
                'accesos',
                'servicios',
                'vestibulos',
                'nombres_acceso',
                'correspondencias',
                'ultima_actualizacion_detalles'
            ]
            
            for tabla in self.lineas_tablas:
                print(f"[INFO] Verificando columnas en {tabla}...")
                
                # Verificar columnas existentes
                cursor.execute(f"PRAGMA table_info({tabla})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Agregar columnas que no existen
                for columna in columnas_detalladas:
                    if columna not in columns:
                        print(f"  [+] Creando columna '{columna}' en {tabla}...")
                        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} TEXT")
                        print(f"  [OK] Columna '{columna}' creada en {tabla}")
                    else:
                        print(f"  [OK] Columna '{columna}' ya existe en {tabla}")
            
            self.conn.commit()
            self.conn.close()
            print("[OK] Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"[ERROR] Error inicializando base de datos: {e}")
            raise
    
    def scrape_estacion_detallada(self, url):
        """Scrapea datos detallados de una estación desde su URL"""
        try:
            print(f"[INFO] Consultando: {url}")
            
            resp = requests.get(url, headers=self.headers, timeout=15)
            
            if resp.status_code != 200:
                print(f"[ERROR] Error HTTP {resp.status_code}")
                return None
                
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extraer datos detallados
            datos = {
                'direccion_completa': None,
                'calle': None,
                'codigo_postal': None,
                'distrito': None,
                'barrio': None,
                'accesos': [],
                'servicios': [],
                'vestibulos': [],
                'nombres_acceso': [],
                'correspondencias': [],
                'ultima_actualizacion_detalles': datetime.now().isoformat()
            }
            
            # Extraer ID de estación de la URL
            estacion_id = None
            if '#estacion-' in url:
                estacion_id = url.split('#estacion-')[-1]
                print(f"    [INFO] Buscando datos para estación ID: {estacion_id}")
            
            # Buscar el bloque específico de la estación
            estacion_bloque = None
            
            # Método 1: Buscar por ID de estación en elementos
            if estacion_id:
                # Buscar elementos que contengan el ID de la estación
                elementos_estacion = soup.find_all(['div', 'section', 'article'], 
                                                 attrs={'id': lambda x: x and estacion_id in x})
                if elementos_estacion:
                    estacion_bloque = elementos_estacion[0]
                    print(f"    [INFO] Encontrado bloque por ID: {estacion_bloque.get('id', 'sin-id')}")
            
            # Método 2: Si no se encuentra por ID, buscar por el nombre de la estación en la URL
            if not estacion_bloque:
                # Extraer nombre de estación de la URL
                nombre_estacion = None
                if 'linea-1' in url and 'estacion-152' in url:
                    nombre_estacion = "Bambú"
                elif 'linea-1' in url and 'estacion-106' in url:
                    nombre_estacion = "Cuatro Caminos"
                # Añadir más mapeos según sea necesario
                
                if nombre_estacion:
                    # Buscar elementos que contengan el nombre de la estación
                    elementos_nombre = soup.find_all(text=re.compile(nombre_estacion, re.IGNORECASE))
                    if elementos_nombre:
                        # Buscar el contenedor padre más cercano que sea un bloque
                        for elemento in elementos_nombre:
                            bloque_padre = elemento.find_parent(['div', 'section', 'article'])
                            if bloque_padre:
                                estacion_bloque = bloque_padre
                                print(f"    [INFO] Encontrado bloque por nombre: {nombre_estacion}")
                                break
            
            # Método 3: Buscar por patrones específicos de la página
            if not estacion_bloque:
                # Buscar elementos que contengan información de estación
                elementos_estacion = soup.find_all(['div', 'section'], 
                                                 class_=re.compile(r'estacion|station|info', re.IGNORECASE))
                if elementos_estacion:
                    # Tomar el primer elemento que parezca ser de estación
                    estacion_bloque = elementos_estacion[0]
                    print(f"    [INFO] Encontrado bloque por clase: {estacion_bloque.get('class', [])}")
            
            # Si no se encuentra un bloque específico, usar toda la página pero con filtros más estrictos
            if not estacion_bloque:
                estacion_bloque = soup
                print(f"    [INFO] Usando toda la página (modo fallback)")
            
            # Buscar tabla de accesos SOLO en el bloque de la estación
            tablas_acceso = estacion_bloque.find_all('table')
            accesos_encontrados = 0
            
            for tabla in tablas_acceso:
                # Buscar tabla que contenga "VESTÍBULO" y "NOMBRE DE ACCESO"
                headers = tabla.find_all('th')
                if headers and any('VESTÍBULO' in h.get_text().upper() for h in headers):
                    print(f"    [INFO] Encontrada tabla de accesos en bloque de estación")
                    
                    # Extraer filas de la tabla
                    filas = tabla.find_all('tr')[1:]  # Saltar header
                    for fila in filas:
                        celdas = fila.find_all('td')
                        if len(celdas) >= 2:
                            vestibulo = celdas[0].get_text(strip=True)
                            nombre_acceso = celdas[1].get_text(strip=True)
                            
                            if vestibulo and nombre_acceso:
                                datos['vestibulos'].append(vestibulo)
                                datos['nombres_acceso'].append(nombre_acceso)
                                
                                # Buscar dirección en la siguiente fila o en la misma celda
                                direccion = ""
                                if len(celdas) > 2:
                                    direccion = celdas[2].get_text(strip=True)
                                else:
                                    # Buscar en la siguiente fila
                                    siguiente_fila = fila.find_next_sibling('tr')
                                    if siguiente_fila:
                                        celdas_sig = siguiente_fila.find_all('td')
                                        if celdas_sig:
                                            direccion = celdas_sig[0].get_text(strip=True)
                                            # Verificar si la siguiente fila es realmente una dirección
                                            # y no otra entrada de acceso
                                            if direccion and not any(palabra in direccion.upper() for palabra in ['VESTÍBULO', 'ACCESO', 'NOMBRE']):
                                                # Es una dirección válida
                                                pass
                                            else:
                                                # No es una dirección, buscar en la misma fila
                                                direccion = ""
                                
                                # Si no encontramos dirección en la siguiente fila, buscar en el texto de la celda actual
                                if not direccion:
                                    # Buscar dirección en el texto de la celda del nombre de acceso
                                    texto_celda = nombre_acceso
                                    # Buscar patrones de dirección
                                    patrones_direccion = [
                                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\d+)',  # Calle con número
                                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*\d+)',  # Calle, número
                                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+frente\s+al)',  # frente al
                                        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\([^)]+\))',  # con paréntesis
                                    ]
                                    
                                    for patron in patrones_direccion:
                                        match = re.search(patron, texto_celda)
                                        if match:
                                            direccion = match.group(1)
                                            break
                                
                                if direccion:
                                    acceso_completo = f"{vestibulo} - {nombre_acceso}: {direccion}"
                                    datos['accesos'].append(acceso_completo)
                                    accesos_encontrados += 1
                                    print(f"      [INFO] Acceso {accesos_encontrados}: {acceso_completo}")
                                else:
                                    # Si no hay dirección, crear acceso sin dirección
                                    acceso_completo = f"{vestibulo} - {nombre_acceso}"
                                    datos['accesos'].append(acceso_completo)
                                    accesos_encontrados += 1
                                    print(f"      [INFO] Acceso {accesos_encontrados}: {acceso_completo}")
            
            # Si no encontramos tabla, buscar en texto del bloque específico
            if not datos['accesos']:
                print(f"    [INFO] No se encontraron tablas, buscando en texto del bloque")
                # Buscar patrones de acceso en el texto del bloque
                texto_bloque = estacion_bloque.get_text()
                
                # Buscar patrones como "VESTÍBULO", "NOMBRE DE ACCESO"
                patrones_acceso = [
                    r'VESTÍBULO[:\s]*([^\n]+)',
                    r'NOMBRE DE ACCESO[:\s]*([^\n]+)',
                    r'Acceso[:\s]*([^\n]+)',
                    r'Entrada[:\s]*([^\n]+)'
                ]
                
                for patron in patrones_acceso:
                    matches = re.findall(patron, texto_bloque, re.IGNORECASE)
                    for match in matches:
                        if match.strip() and len(match.strip()) > 3:
                            datos['accesos'].append(match.strip())
            
            # Buscar dirección principal en el bloque específico
            direccion_selectors = [
                '.estacion-info .direccion',
                '.estacion-details .address',
                '.station-info .location',
                '.info-estacion .direccion',
                '.direccion-estacion',
                '.location-info',
                '.station-address'
            ]
            
            for selector in direccion_selectors:
                elemento = estacion_bloque.select_one(selector)
                if elemento:
                    datos['direccion_completa'] = elemento.get_text(strip=True)
                    break
            
            # Si no se encuentra con selectores específicos, buscar en el texto del bloque
            if not datos['direccion_completa']:
                # Buscar patrones de dirección en el bloque específico
                patrones_direccion = [
                    r'Dirección[:\s]*([^\n]+)',
                    r'Calle[:\s]*([^\n]+)',
                    r'Avenida[:\s]*([^\n]+)',
                    r'Plaza[:\s]*([^\n]+)'
                ]
                
                texto_bloque = estacion_bloque.get_text()
                for patron in patrones_direccion:
                    match = re.search(patron, texto_bloque, re.IGNORECASE)
                    if match:
                        datos['direccion_completa'] = match.group(1).strip()
                        break
            
            # Extraer calle de la dirección completa
            if datos['direccion_completa']:
                # Buscar patrones de calle
                calle_patterns = [
                    r'(Calle|Avenida|Plaza|Paseo|Camino)\s+[^,]+',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                ]
                
                for pattern in calle_patterns:
                    match = re.search(pattern, datos['direccion_completa'])
                    if match:
                        datos['calle'] = match.group(0)
                        break
            
            # Buscar código postal
            cp_match = re.search(r'\b\d{5}\b', resp.text)
            if cp_match:
                datos['codigo_postal'] = cp_match.group(0)
            
            # Buscar distrito y barrio en el bloque específico
            distrito_selectors = [
                '.distrito',
                '.barrio',
                '.location-info .district',
                '.estacion-info .district'
            ]
            
            for selector in distrito_selectors:
                elemento = estacion_bloque.select_one(selector)
                if elemento:
                    texto = elemento.get_text(strip=True)
                    if 'Distrito' in texto:
                        datos['distrito'] = texto.replace('Distrito:', '').strip()
                    elif 'Barrio' in texto:
                        datos['barrio'] = texto.replace('Barrio:', '').strip()
            
            # Buscar servicios en el bloque específico
            servicios_extraidos = set()
            
            # Buscar en la estructura específica de servicios de Metro Madrid
            # 1. Buscar elementos con clase box__icon
            elementos_iconos = estacion_bloque.find_all('div', class_='box__icon')
            for elemento in elementos_iconos:
                # Buscar imagen dentro del box__icon
                img = elemento.find('img')
                if img:
                    alt_text = img.get('alt', '')
                    if alt_text and 'icono' in alt_text.lower():
                        # Extraer el nombre del servicio del alt
                        servicio = alt_text.replace('icono', '').strip()
                        if servicio:
                            servicios_extraidos.add(servicio)
            
            # 2. Buscar elementos con clase tiempo-espera__minutos
            elementos_texto = estacion_bloque.find_all('span', class_='tiempo-espera__minutos')
            for elemento in elementos_texto:
                texto = elemento.get_text(strip=True)
                if texto and len(texto) > 2:
                    servicios_extraidos.add(texto)
            
            # 3. Buscar en elementos con clase text__info-estacion--tit-icon
            elementos_info = estacion_bloque.find_all('div', class_='text__info-estacion--tit-icon')
            for elemento in elementos_info:
                texto = elemento.get_text(strip=True)
                if texto and len(texto) > 2:
                    servicios_extraidos.add(texto)
            
            # 4. Buscar en la estructura completa de servicios
            servicios_selectors = [
                '.box__info-linea--estaciones',
                '.servicios',
                '.services',
                '.estacion-servicios',
                '.station-services',
                '.facilities',
                '.amenities'
            ]
            
            for selector in servicios_selectors:
                elementos = estacion_bloque.select(selector)
                for elemento in elementos:
                    # Buscar iconos con alt o title
                    iconos = elemento.find_all(['img', 'span', 'i', 'svg'])
                    for icono in iconos:
                        texto_icono = icono.get('alt') or icono.get('title') or icono.get_text(strip=True)
                        if texto_icono and len(texto_icono) > 2:
                            servicios_extraidos.add(texto_icono)
                    # Buscar textos directos
                    textos = elemento.stripped_strings
                    for texto in textos:
                        if texto and len(texto) > 2:
                            servicios_extraidos.add(texto)
            
            # Limpiar y filtrar duplicados
            servicios_limpios = set()
            servicios_finales = set()
            
            # Textos a excluir
            textos_excluir = [
                'ir a', 'Ir a', 'IR A',
                'linea-', 'línea-', 'Línea-',
                'autobuses-', 'Autobuses-',
                'metro-', 'Metro-',
                'linea-1', 'linea-2', 'linea-3', 'linea-4', 'linea-5', 'linea-6', 'linea-7', 'linea-8', 'linea-9', 'linea-10', 'linea-11', 'linea-12',
                'línea-1', 'línea-2', 'línea-3', 'línea-4', 'línea-5', 'línea-6', 'línea-7', 'línea-8', 'línea-9', 'línea-10', 'línea-11', 'línea-12',
                'autobuses-interurbanos', 'autobuses-de-largo-recorrido',
                'metro-circular', 'metro-ramal'
            ]
            
            # Servicios reales (para validar)
            servicios_validos = [
                'Ascensores', 'Escaleras mecánicas', 'Estación accesible', 'Cobertura móvil', 'Desfibrilador',
                'Oficina de gestión TTP', 'Parking disuasorio de pago', 'Quioscos ONCE', 'adaptada para discapacitados',
                'escaleras', 'ascensor', 'accesible', 'móvil', 'desfibrilador', 'parking', 'quioscos', 'oficina'
            ]
            
            for s in servicios_extraidos:
                s_limpio = s.replace('icono', '').replace('Icono', '').strip()
                if s_limpio and len(s_limpio) > 2:
                    # Verificar si contiene textos a excluir
                    debe_excluir = False
                    for texto_excluir in textos_excluir:
                        if texto_excluir.lower() in s_limpio.lower():
                            debe_excluir = True
                            break
                    
                    if not debe_excluir:
                        servicios_limpios.add(s_limpio)
            
            # Filtrar y limpiar servicios finales
            for servicio in servicios_limpios:
                # Limpiar textos adicionales
                servicio_limpio = servicio
                
                # Remover textos como "Ir a X"
                if 'Ir a ' in servicio_limpio:
                    servicio_limpio = servicio_limpio.split('Ir a ')[0].strip()
                
                # Remover textos como "Ir a X" al final
                if servicio_limpio.endswith('Ir a Alsa') or servicio_limpio.endswith('Ir a Consorcio'):
                    servicio_limpio = servicio_limpio.replace('Ir a Alsa', '').replace('Ir a Consorcio', '').strip()
                
                # Verificar si es un servicio válido
                es_servicio_valido = False
                for servicio_valido in servicios_validos:
                    if servicio_valido.lower() in servicio_limpio.lower():
                        es_servicio_valido = True
                        break
                
                # Si no es un servicio válido, verificar si contiene palabras clave
                if not es_servicio_valido:
                    palabras_clave = ['ascensor', 'escalera', 'accesible', 'móvil', 'desfibrilador', 'parking', 'quiosco', 'oficina', 'cobertura']
                    for palabra in palabras_clave:
                        if palabra.lower() in servicio_limpio.lower():
                            es_servicio_valido = True
                            break
                
                if es_servicio_valido and servicio_limpio and len(servicio_limpio) > 2:
                    servicios_finales.add(servicio_limpio)
            
            if servicios_finales:
                datos['servicios'] = '; '.join(sorted(servicios_finales))
                print(f"    [INFO] Servicios encontrados: {len(servicios_finales)}")
                for servicio in sorted(servicios_finales):
                    print(f"      [INFO] Servicio: {servicio}")
            else:
                print(f"    [INFO] No se encontraron servicios válidos")
            
            # Extraer conexiones (correspondencias) en el bloque específico
            conexiones_extraidas = set()
            
            # Buscar elementos que indiquen conexiones
            # 1. Buscar elementos con clase que contenga "conexion", "correspondencia", "intercambio"
            selectors_conexiones = [
                '.conexion', '.conexiones', '.correspondencia', '.correspondencias',
                '.intercambio', '.intercambios', '.transfer', '.transfers',
                '.connection', '.connections', '.linea-conexion', '.linea-correspondencia'
            ]
            
            for selector in selectors_conexiones:
                elementos = estacion_bloque.select(selector)
                for elemento in elementos:
                    texto = elemento.get_text(strip=True)
                    if texto and len(texto) > 2:
                        conexiones_extraidas.add(texto)
            
            # 2. Buscar elementos con imágenes de líneas de metro (indicador de conexión)
            elementos_lineas = estacion_bloque.find_all('img', alt=re.compile(r'linea|metro|autobús|bus', re.IGNORECASE))
            for elemento in elementos_lineas:
                alt_text = elemento.get('alt', '')
                if alt_text:
                    # Extraer información de la línea del alt
                    if 'linea' in alt_text.lower():
                        # Buscar el número de línea
                        match = re.search(r'linea[-\s]*(\d+)', alt_text, re.IGNORECASE)
                        if match:
                            num_linea = match.group(1)
                            conexiones_extraidas.add(f"Línea {num_linea}")
                        else:
                            conexiones_extraidas.add(alt_text)
                    elif 'autobús' in alt_text.lower() or 'bus' in alt_text.lower():
                        conexiones_extraidas.add("Autobuses")
            
            # 3. Buscar elementos con clase que contenga "linea" y que no sean de la línea actual
            elementos_lineas_clase = estacion_bloque.find_all(class_=re.compile(r'linea', re.IGNORECASE))
            for elemento in elementos_lineas_clase:
                # Obtener el texto del elemento
                texto = elemento.get_text(strip=True)
                if texto and len(texto) > 2:
                    # Verificar si es una línea de metro (contiene "Línea" o "L")
                    if 'línea' in texto.lower() or re.search(r'\bL\d+\b', texto):
                        conexiones_extraidas.add(texto)
            
            # 4. Buscar en el texto del bloque patrones de conexión
            texto_bloque = estacion_bloque.get_text()
            
            # Patrones para encontrar conexiones
            patrones_conexion = [
                r'Conexión con Línea (\d+)',
                r'Correspondencia con Línea (\d+)',
                r'Intercambio con Línea (\d+)',
                r'Línea (\d+)',
                r'Autobuses?',
                r'Cercanías',
                r'Renfe',
                r'Intercambiador',
                r'Estación de autobuses',
                r'Parada de autobús'
            ]
            
            for patron in patrones_conexion:
                matches = re.findall(patron, texto_bloque, re.IGNORECASE)
                for match in matches:
                    if patron == r'Conexión con Línea (\d+)':
                        conexiones_extraidas.add(f"Conexión con Línea {match}")
                    elif patron == r'Correspondencia con Línea (\d+)':
                        conexiones_extraidas.add(f"Correspondencia con Línea {match}")
                    elif patron == r'Intercambio con Línea (\d+)':
                        conexiones_extraidas.add(f"Intercambio con Línea {match}")
                    elif patron == r'Línea (\d+)':
                        conexiones_extraidas.add(f"Línea {match}")
                    else:
                        conexiones_extraidas.add(match)
            
            # 5. Buscar elementos específicos de Metro Madrid que indiquen conexiones
            elementos_metro = estacion_bloque.find_all(['div', 'span', 'p'], 
                                                     text=re.compile(r'conexión|correspondencia|intercambio|autobús|bus|cercanías', re.IGNORECASE))
            for elemento in elementos_metro:
                texto = elemento.get_text(strip=True)
                if texto and len(texto) > 5:  # Filtrar textos muy cortos
                    # Extraer solo la parte relevante
                    if 'conexión' in texto.lower():
                        conexiones_extraidas.add("Conexión disponible")
                    elif 'correspondencia' in texto.lower():
                        conexiones_extraidas.add("Correspondencia disponible")
                    elif 'intercambio' in texto.lower():
                        conexiones_extraidas.add("Intercambio disponible")
                    elif 'autobús' in texto.lower() or 'bus' in texto.lower():
                        conexiones_extraidas.add("Autobuses")
                    elif 'cercanías' in texto.lower():
                        conexiones_extraidas.add("Cercanías")
            
            # Limpiar y filtrar conexiones
            conexiones_limpias = set()
            for conexion in conexiones_extraidas:
                conexion_limpia = conexion.strip()
                if conexion_limpia and len(conexion_limpia) > 2:
                    # Remover duplicados y variaciones
                    conexion_normalizada = conexion_limpia.lower()
                    if conexion_normalizada not in [c.lower() for c in conexiones_limpias]:
                        conexiones_limpias.add(conexion_limpia)
            
            if conexiones_limpias:
                datos['correspondencias'] = list(conexiones_limpias)
                print(f"    [INFO] Conexiones encontradas: {len(conexiones_limpias)}")
                for conexion in sorted(conexiones_limpias):
                    print(f"      [INFO] Conexión: {conexion}")
            else:
                print(f"    [INFO] No se encontraron conexiones")
            
            # Guardar la última actualización
            datos['ultima_actualizacion_detalles'] = datetime.now().isoformat()
            
            # Convertir listas a texto
            datos['accesos'] = '; '.join(datos['accesos']) if datos['accesos'] else None
            datos['vestibulos'] = '; '.join(set(datos['vestibulos'])) if datos['vestibulos'] else None
            datos['nombres_acceso'] = '; '.join(set(datos['nombres_acceso'])) if datos['nombres_acceso'] else None
            
            # Resumen de datos extraídos
            resumen = []
            if datos['direccion_completa']:
                resumen.append(f"Dir: {datos['direccion_completa']}")
            if datos['accesos']:
                num_accesos = len(datos['accesos'].split(';'))
                resumen.append(f"Accesos: {num_accesos}")
            if datos['vestibulos']:
                num_vestibulos = len(datos['vestibulos'].split(';'))
                resumen.append(f"Vestíbulos: {num_vestibulos}")
            if datos['correspondencias']:
                num_conexiones = len(datos['correspondencias'])
                resumen.append(f"Conexiones: {num_conexiones}")
            
            print(f"[OK] Datos extraídos: {' | '.join(resumen) if resumen else 'Sin datos específicos'}")
            return datos
            
        except Exception as e:
            print(f"[ERROR] Error scrapeando estación: {e}")
            return None
    
    def actualizar_estacion_detallada(self, tabla, id_fijo, datos):
        """Actualiza los datos detallados de una estación en la base de datos"""
        try:
            cursor = self.cursor
            
            query = f"""
            UPDATE {tabla} 
            SET 
                direccion_completa = ?,
                calle = ?,
                codigo_postal = ?,
                distrito = ?,
                barrio = ?,
                accesos = ?,
                servicios = ?,
                vestibulos = ?,
                nombres_acceso = ?,
                correspondencias = ?,
                ultima_actualizacion_detalles = ?
            WHERE id_fijo = ?
            """
            
            cursor.execute(query, (
                datos['direccion_completa'],
                datos['calle'],
                datos['codigo_postal'],
                datos['distrito'],
                datos['barrio'],
                datos['accesos'],
                datos['servicios'],
                datos['vestibulos'],
                datos['nombres_acceso'],
                '; '.join(datos['correspondencias']) if datos['correspondencias'] else None,
                datos['ultima_actualizacion_detalles'],
                id_fijo
            ))
            
            self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error actualizando estación {id_fijo} en {tabla}: {e}")
            return False
    
    def procesar_estaciones_detalladas(self):
        """Procesa todas las estaciones para obtener datos detallados"""
        print("🚇 INICIANDO SCRAPING DE DATOS DETALLADOS")
        print("=" * 50)
        
        try:
            total_procesadas = 0
            total_exitosas = 0
            
            for tabla in self.lineas_tablas:
                print(f"\n[INFO] Procesando {tabla}...")
                
                # Obtener estaciones con URL pero sin datos detallados
                query = f"""
                SELECT id_fijo, nombre, url 
                FROM {tabla} 
                WHERE url IS NOT NULL 
                AND url != '' 
                AND (direccion_completa IS NULL OR direccion_completa = '')
                ORDER BY orden_en_linea
                """
                
                df = pd.read_sql_query(query, self.conn)
                
                if df.empty:
                    print(f"  [INFO] No hay estaciones pendientes en {tabla}")
                    continue
                
                print(f"  [INFO] {len(df)} estaciones pendientes en {tabla}")
                
                for _, row in df.iterrows():
                    total_procesadas += 1
                    
                    print(f"\n  [INFO] Procesando: {row['nombre']} (ID: {row['id_fijo']})")
                    
                    # Scrapear datos detallados
                    datos = self.scrape_estacion_detallada(row['url'])
                    
                    if datos:
                        # Actualizar en la base de datos
                        if self.actualizar_estacion_detallada(tabla, row['id_fijo'], datos):
                            total_exitosas += 1
                            print(f"    [OK] Actualizada correctamente")
                        else:
                            print(f"    [ERROR] Error actualizando en BD")
                    else:
                        print(f"    [ERROR] Sin datos obtenidos")
                    
                    # Pausa entre requests
                    time.sleep(2)
            
            self.conn.close()
            
            print(f"\n[RESUMEN] SCRAPING COMPLETADO")
            print("=" * 30)
            print(f"[INFO] Total procesadas: {total_procesadas}")
            print(f"[OK] Exitosas: {total_exitosas}")
            print(f"[ERROR] Fallidas: {total_procesadas - total_exitosas}")
            print(f"[INFO] Tasa de éxito: {(total_exitosas/total_procesadas*100):.1f}%" if total_procesadas > 0 else "N/A")
            
            return total_exitosas > 0
            
        except Exception as e:
            print(f"[ERROR] Error en el procesamiento: {e}")
            return False
    
    def verificar_datos_detallados(self):
        """Verifica qué estaciones tienen datos detallados"""
        try:
            total_estaciones = 0
            total_con_datos = 0
            
            for tabla in self.lineas_tablas:
                # Contar estaciones totales y con datos detallados
                query_total = f"SELECT COUNT(*) as total FROM {tabla}"
                query_con_datos = f"""
                SELECT COUNT(*) as con_datos 
                FROM {tabla} 
                WHERE direccion_completa IS NOT NULL 
                AND direccion_completa != ''
                """
                
                total = pd.read_sql_query(query_total, self.conn).iloc[0]['total']
                con_datos = pd.read_sql_query(query_con_datos, self.conn).iloc[0]['con_datos']
                
                total_estaciones += total
                total_con_datos += con_datos
                
                print(f"[INFO] {tabla}: {con_datos}/{total} estaciones con datos detallados")
            
            self.conn.close()
            
            print(f"\n[RESUMEN] GENERAL:")
            print(f"  [INFO] Total estaciones: {total_estaciones}")
            print(f"  [OK] Con datos detallados: {total_con_datos}")
            print(f"  [ERROR] Sin datos detallados: {total_estaciones - total_con_datos}")
            print(f"  [INFO] Porcentaje: {(total_con_datos/total_estaciones*100):.1f}%" if total_estaciones > 0 else "N/A")
            
        except Exception as e:
            print(f"[ERROR] Error verificando datos: {e}")

def main():
    scraper = ScraperDatosDetallados()
    
    # Verificar estado actual
    scraper.verificar_datos_detallados()
    
    # Preguntar si continuar
    respuesta = input("\n¿Deseas ejecutar el scraping de datos detallados? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        # Ejecutar scraping
        if scraper.procesar_estaciones_detalladas():
            print("\n[OK] Scraping completado exitosamente")
        else:
            print("\n[ERROR] Error en el scraping")
        
        # Verificar resultado final
        scraper.verificar_datos_detallados()
    else:
        print("[INFO] Scraping cancelado")

if __name__ == "__main__":
    main() 