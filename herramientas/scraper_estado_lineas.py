#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper para obtener el estado de las líneas de Metro de Madrid
Obtiene información sobre circulación interrumpida, estaciones cerradas, etc.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time
import sqlite3
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScraperEstadoLineas:
    def __init__(self):
        self.session = requests.Session()
        # Usar los mismos headers que funcionan en el scraper de servicios
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # URLs de las líneas
        self.lineas_urls = {
            '1': 'https://www.metromadrid.es/es/linea/linea-1',
            '2': 'https://www.metromadrid.es/es/linea/linea-2',
            '3': 'https://www.metromadrid.es/es/linea/linea-3',
            '4': 'https://www.metromadrid.es/es/linea/linea-4',
            '5': 'https://www.metromadrid.es/es/linea/linea-5',
            '6': 'https://www.metromadrid.es/es/linea/linea-6',
            '7': 'https://www.metromadrid.es/es/linea/linea-7',
            '8': 'https://www.metromadrid.es/es/linea/linea-8',
            '9': 'https://www.metromadrid.es/es/linea/linea-9',
            '10': 'https://www.metromadrid.es/es/linea/linea-10',
            '11': 'https://www.metromadrid.es/es/linea/linea-11',
            '12': 'https://www.metromadrid.es/es/linea/linea-12-metrosur',
            'Ramal': 'https://www.metromadrid.es/es/linea/ramal'
        }
        
        # Crear carpeta de debug si no existe
        self.debug_folder = 'herramientas/debug'
        os.makedirs(self.debug_folder, exist_ok=True)
        
        # Posibles endpoints API para estado de líneas
        self.api_endpoints = {
            '1': 'https://www.metromadrid.es/es/api/linea/1/status',
            '2': 'https://www.metromadrid.es/es/api/linea/2/status',
            '3': 'https://www.metromadrid.es/es/api/linea/3/status',
            '4': 'https://www.metromadrid.es/es/api/linea/4/status',
            '5': 'https://www.metromadrid.es/es/api/linea/5/status',
            '6': 'https://www.metromadrid.es/es/api/linea/6/status',
            '7': 'https://www.metromadrid.es/es/api/linea/7/status',
            '8': 'https://www.metromadrid.es/es/api/linea/8/status',
            '9': 'https://www.metromadrid.es/es/api/linea/9/status',
            '10': 'https://www.metromadrid.es/es/api/linea/10/status',
            '11': 'https://www.metromadrid.es/es/api/linea/11/status',
            '12': 'https://www.metromadrid.es/es/api/linea/12/status',
            'Ramal': 'https://www.metromadrid.es/es/api/linea/ramal/status'
        }
    
    def obtener_estado_linea(self, numero_linea):
        """Obtiene el estado de una línea específica"""
        try:
            logger.info(f"[ESTADO_LINEA] Obteniendo estado de línea {numero_linea}")
            
            # 1. Intentar API primero (si existe)
            api_url = f"https://www.metromadrid.es/api/linea/{numero_linea}/estado"
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"[ESTADO_LINEA] API exitosa para línea {numero_linea}")
                    # Guardar respuesta API para inspección
                    api_filename = os.path.join(self.debug_folder, f"debug_linea_{numero_linea}_api.txt")
                    with open(api_filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"[ESTADO_LINEA] Respuesta API guardada en {api_filename}")
                    
                    # Procesar respuesta API
                    return self.procesar_respuesta_api(response, numero_linea, api_url)
            except Exception as e:
                logger.warning(f"[ESTADO_LINEA] API falló para línea {numero_linea}: {e}")
            
            # 2. Fallback a página web
            url = self.lineas_urls.get(numero_linea)
            if not url:
                logger.error(f"URL no encontrada para línea {numero_linea}")
                return None
            
            logger.info(f"[ESTADO_LINEA] Probando página web para línea {numero_linea}: {url}")
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                logger.error(f"[ESTADO_LINEA] Error HTTP {response.status_code} para línea {numero_linea}")
                return None
            
            # Guardar HTML para inspección
            html_filename = os.path.join(self.debug_folder, f"debug_linea_{numero_linea}_html.txt")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"[ESTADO_LINEA] HTML guardado en {html_filename}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el estado de la línea
            estado_linea = self.extraer_estado_linea(soup)
            
            # Buscar estaciones cerradas
            estaciones_cerradas, accesos_cerrados = self.extraer_estaciones_cerradas(soup, numero_linea)
            
            # Buscar incidencias
            incidencias = self.extraer_incidencias(soup)
            
            resultado = {
                'linea': numero_linea,
                'url': url,
                'estado_linea': estado_linea,
                'estaciones_cerradas': estaciones_cerradas,
                'accesos_cerrados': accesos_cerrados,
                'incidencias': incidencias,
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'html_file': html_filename,
                'fuente': 'pagina_web'
            }
            
            logger.info(f"[ESTADO_LINEA] Estado línea {numero_linea}: {estado_linea['estado']}")
            return resultado
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error obteniendo estado línea {numero_linea}: {e}")
            return None
    
    def procesar_respuesta_api(self, response, numero_linea, api_url):
        """Procesa la respuesta de la API de estado de líneas"""
        try:
            # Intentar parsear como JSON
            try:
                data = response.json()
                logger.info(f"[ESTADO_LINEA] Respuesta API JSON para línea {numero_linea}")
                
                # Procesar datos JSON según la estructura esperada
                estado_linea = {
                    'estado': data.get('estado', 'Normal'),
                    'clase': data.get('clase_css', 'state--normal'),
                    'descripcion': data.get('descripcion', ''),
                    'texto_original': data.get('estado', 'Normal')
                }
                
                estaciones_cerradas = data.get('estaciones_cerradas', [])
                accesos_cerrados = data.get('accesos_cerrados', [])
                incidencias = data.get('incidencias', [])
                
            except json.JSONDecodeError:
                # Si no es JSON, procesar como HTML
                logger.info(f"[ESTADO_LINEA] Respuesta API HTML para línea {numero_linea}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                estado_linea = self.extraer_estado_linea(soup)
                estaciones_cerradas, accesos_cerrados = self.extraer_estaciones_cerradas(soup, numero_linea)
                incidencias = self.extraer_incidencias(soup)
            
            return {
                'linea': numero_linea,
                'url': api_url,
                'estado_linea': estado_linea,
                'estaciones_cerradas': estaciones_cerradas,
                'accesos_cerrados': accesos_cerrados,
                'incidencias': incidencias,
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'fuente': 'api'
            }
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error procesando respuesta API: {e}")
            return None
    
    def extraer_estado_linea(self, soup):
        """Extrae el estado general de la línea"""
        try:
            # Buscar el div de estado de la línea (puede estar en diferentes lugares)
            estado_div = soup.find('div', class_='box__line-state')
            if not estado_div:
                # Buscar también en la sección de incidencias
                seccion_incidencias = soup.find('div', id='line-incidents')
                if seccion_incidencias:
                    estado_div = seccion_incidencias.find('div', class_='box__line-state')
            
            if not estado_div:
                return {'estado': 'Normal', 'clase': 'state--normal', 'descripcion': ''}
            
            # Buscar el título del estado (puede ser span o h3)
            titulo_estado = estado_div.find('span', class_='tit__line-state')
            if not titulo_estado:
                titulo_estado = estado_div.find('h3', class_='tit__line-state')
            
            if not titulo_estado:
                return {'estado': 'Normal', 'clase': 'state--normal', 'descripcion': ''}
            
            estado_texto = titulo_estado.get_text(strip=True)
            estado_clase = ' '.join(titulo_estado.get('class', []))
            
            # Buscar descripción adicional
            descripcion = estado_div.find('p', class_='text__line-state')
            descripcion_texto = descripcion.get_text(strip=True) if descripcion else ''
            
            # Determinar el estado basándose en la clase CSS y el texto
            if 'state--red' in estado_clase or 'circulación interrumpida' in estado_texto.lower():
                estado = 'Circulación interrumpida'
            elif 'state--orange' in estado_clase or 'circulación afectada' in estado_texto.lower():
                estado = 'Circulación afectada'
            elif 'state--yellow' in estado_clase or 'atención' in estado_texto.lower():
                estado = 'Atención'
            elif estado_texto:
                estado = estado_texto
            else:
                estado = 'Normal'
            
            logger.info(f"[ESTADO_LINEA] Texto encontrado: '{estado_texto}', Clase: '{estado_clase}', Estado final: '{estado}'")
            
            return {
                'estado': estado,
                'clase': estado_clase,
                'descripcion': descripcion_texto,
                'texto_original': estado_texto
            }
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo estado: {e}")
            return {'estado': 'Error', 'clase': 'state--error', 'descripcion': str(e)}
    
    def extraer_estaciones_cerradas(self, soup, numero_linea):
        """Extrae las estaciones cerradas de la línea (solo estaciones realmente cerradas)"""
        try:
            estaciones_cerradas = []
            accesos_cerrados = []

            # 1. Crear diccionario {id_estacion: nombre} desde la lista de acordeones
            id_nombre_estacion = {}
            for a in soup.select('a.list-line__btn.accordion-title'):
                href = a.get('href', '')
                if href.startswith('#estacion-'):
                    id_est = href.replace('#estacion-', '')
                    nombre_elem = a.find('p', class_='list-line__btn__text')
                    if nombre_elem:
                        nombre = nombre_elem.get_text(strip=True)
                        if nombre:
                            id_nombre_estacion[id_est] = nombre
                            logger.info(f"[ESTADO_LINEA] Estación encontrada: {nombre} (ID: {id_est})")

            # 2. Recorrer los bloques de detalles de estación
            bloques_estacion = soup.find_all('div', class_='accordion-content station-info')
            logger.info(f"[ESTADO_LINEA] Encontrados {len(bloques_estacion)} bloques de estación")
            
            for bloque in bloques_estacion:
                id_est = bloque.get('id', '').replace('estacion-', '')
                nombre_estacion = id_nombre_estacion.get(id_est, None)
                
                if not nombre_estacion:
                    logger.warning(f"[ESTADO_LINEA] No se encontró nombre para estación ID: {id_est}")
                    continue
                
                # Buscar <strong class="close--station">Estación Cerrada</strong>
                estacion_cerrada = bloque.find('strong', class_='close--station')
                if estacion_cerrada and 'Estación Cerrada' in estacion_cerrada.get_text():
                    logger.info(f"[ESTADO_LINEA] Estación cerrada detectada: {nombre_estacion} (ID: {id_est})")
                    
                    # Buscar el motivo en el párrafo padre
                    p_info = estacion_cerrada.find_parent('p', class_='text__info-estacion')
                    motivo = ""
                    if p_info:
                        # Obtener todo el texto del párrafo y limpiarlo
                        texto_completo = p_info.get_text(strip=True)
                        motivo = texto_completo.replace('Estación Cerrada', '').strip()
                        # Si no hay motivo específico, usar uno genérico
                        if not motivo:
                            motivo = "Estación cerrada temporalmente"
                    
                    estaciones_cerradas.append({
                        'nombre': nombre_estacion,
                        'id_estacion': id_est,
                        'motivo': motivo,
                        'tipo': 'estacion_cerrada'
                    })
                
                # Buscar accesos cerrados dentro del bloque
                accesos_estacion = self.extraer_accesos_cerrados(bloque)
                if accesos_estacion and nombre_estacion:
                    for acceso in accesos_estacion:
                        accesos_cerrados.append({
                            'estacion': nombre_estacion,
                            'acceso': acceso['nombre'],
                            'motivo': acceso['motivo'],
                            'tipo': 'acceso_cerrado'
                        })
            
            logger.info(f"[ESTADO_LINEA] Estaciones cerradas encontradas: {len(estaciones_cerradas)}")
            for est in estaciones_cerradas:
                logger.info(f"[ESTADO_LINEA] - {est['nombre']}: {est['motivo']}")
                
            return estaciones_cerradas, accesos_cerrados
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo estaciones cerradas: {e}")
            return [], []

    def extraer_accesos_cerrados(self, estacion_element):
        """Extrae los accesos cerrados de una estación específica"""
        try:
            accesos_cerrados = []
            
            # Buscar elementos que contengan información de accesos
            # Pueden estar en diferentes estructuras HTML
            elementos_acceso = estacion_element.find_all(['p', 'div', 'span'], string=re.compile(r'De .*?:.*?Cierre|acceso.*?Cierre|vestíbulo.*?Cierre'))
            
            for elemento in elementos_acceso:
                texto = elemento.get_text(strip=True)
                # Buscar patrones como "De acceso X: Cierre temporal" o "De vestíbulo a: Cierre temporal"
                match = re.search(r'De (.*?): (.*?Cierre.*?)(?:$|\s|\.)', texto)
                if match:
                    nombre_acceso = match.group(1).strip()
                    motivo = match.group(2).strip()
                    
                    accesos_cerrados.append({
                        'nombre': nombre_acceso,
                        'motivo': motivo
                    })
            
            return accesos_cerrados
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo accesos cerrados: {e}")
            return []
    
    def extraer_nombre_estacion(self, elemento_estacion):
        """Extrae el nombre de una estación de su elemento HTML"""
        try:
            # Buscar específicamente en el elemento que contiene el nombre de la estación
            nombre_elem = elemento_estacion.find('p', class_='list-line__btn__text')
            if nombre_elem:
                nombre = nombre_elem.get_text(strip=True)
                if nombre and len(nombre) > 2:
                    return nombre
            
            # Buscar en el elemento padre (el enlace) si no se encuentra el párrafo
            enlace = elemento_estacion.find('a', class_='list-line__btn')
            if enlace:
                nombre_elem = enlace.find('p', class_='list-line__btn__text')
                if nombre_elem:
                    nombre = nombre_elem.get_text(strip=True)
                    if nombre and len(nombre) > 2:
                        return nombre
            
            # Buscar en diferentes elementos como fallback
            selectores = [
                'h3', 'h4', 'h2', 'h5', 'h6',
                '.estacion-nombre', '.station-name', '.estacion-titulo',
                '.titulo-estacion', '.nombre-estacion', '.station-title',
                '[class*="estacion"]', '[class*="station"]',
                'strong', 'b', 'span[class*="nombre"]'
            ]
            
            for selector in selectores:
                elementos = elemento_estacion.find_all(selector)
                for elem in elementos:
                    texto = elem.get_text(strip=True)
                    if texto and len(texto) > 2 and len(texto) < 50:  # Texto razonable para un nombre
                        # Filtrar texto que no sea nombre de estación
                        if not any(palabra in texto.lower() for palabra in ['estación', 'cerrada', 'accesible', 'zona', 'plano', 'cierre', 'servicios']):
                            return texto
            
            return None
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo nombre estación: {e}")
            return None
    
    def extraer_motivo_cierre(self, elemento_estacion):
        """Extrae el motivo del cierre de una estación"""
        try:
            # Buscar texto que indique el motivo
            texto = elemento_estacion.get_text().lower()
            
            motivos = {
                'mantenimiento': 'Mantenimiento',
                'obras': 'Obras',
                'avería': 'Avería técnica',
                'incidencia': 'Incidencia',
                'interrumpida': 'Circulación interrumpida',
                'suspendida': 'Servicio suspendido'
            }
            
            for palabra, motivo in motivos.items():
                if palabra in texto:
                    return motivo
            
            return 'Cierre temporal'
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo motivo cierre: {e}")
            return 'Motivo no especificado'
    
    def extraer_incidencias(self, soup):
        """Extrae las incidencias de la línea"""
        try:
            incidencias = []
            
            # Buscar la sección de incidencias
            seccion_incidencias = soup.find('div', id='line-incidents')
            if not seccion_incidencias:
                return incidencias
            
            # Buscar elementos de incidencias específicos
            elementos_incidencias = seccion_incidencias.find_all('div', class_='box__incidencias-incidencia')
            
            for elemento in elementos_incidencias:
                incidencia = {
                    'titulo': '',
                    'descripcion': '',
                    'fecha': '',
                    'tipo': 'General'
                }
                
                # Extraer descripción de la incidencia
                desc_elem = elemento.find('div', class_='text__incidencia')
                if desc_elem:
                    # Buscar párrafos con información de estación
                    parrafos = desc_elem.find_all('p', class_='text__info-estacion')
                    if parrafos:
                        descripcion_texto = ' '.join([p.get_text(strip=True) for p in parrafos if p.get_text(strip=True)])
                        incidencia['descripcion'] = descripcion_texto
                
                # Si no hay descripción específica, buscar cualquier texto
                if not incidencia['descripcion']:
                    texto_general = elemento.get_text(strip=True)
                    if texto_general:
                        incidencia['descripcion'] = texto_general
                
                # Extraer título del estado si está disponible
                estado_div = elemento.find_previous('div', class_='box__line-state')
                if estado_div:
                    titulo_elem = estado_div.find(['h3', 'span'], class_='tit__line-state')
                    if titulo_elem:
                        incidencia['titulo'] = titulo_elem.get_text(strip=True)
                
                if incidencia['descripcion']:
                    incidencias.append(incidencia)
            
            # Si no se encontraron incidencias específicas, buscar en toda la sección
            if not incidencias:
                texto_completo = seccion_incidencias.get_text(strip=True)
                if texto_completo and len(texto_completo) > 50:  # Solo si hay texto significativo
                    incidencias.append({
                        'titulo': 'Información de incidencias',
                        'descripcion': texto_completo,
                        'fecha': '',
                        'tipo': 'General'
                    })
            
            logger.info(f"[ESTADO_LINEA] Encontradas {len(incidencias)} incidencias")
            return incidencias
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error extrayendo incidencias: {e}")
            return []
    
    def guardar_estado_linea(self, datos_estado):
        """Guarda el estado de la línea en la base de datos solo si hay cambios"""
        try:
            conn = sqlite3.connect('db/estaciones_fijas_v2.db')
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
            
            # Obtener el estado anterior más reciente
            cursor.execute('''
                SELECT estado, estaciones_cerradas, accesos_cerrados, incidencias, timestamp
                FROM estado_lineas 
                WHERE linea = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (datos_estado['linea'],))
            
            estado_anterior = cursor.fetchone()
            
            # Preparar datos del nuevo estado
            nuevo_estado = datos_estado['estado_linea']['estado']
            nuevas_estaciones_cerradas = json.dumps(datos_estado['estaciones_cerradas'], ensure_ascii=False)
            nuevos_accesos_cerrados = json.dumps(datos_estado['accesos_cerrados'], ensure_ascii=False)
            nuevas_incidencias = json.dumps(datos_estado['incidencias'], ensure_ascii=False)
            
            # Verificar si hay cambios significativos
            hay_cambios = True
            
            if estado_anterior:
                # estado_anterior es una tupla: (estado, estaciones_cerradas, accesos_cerrados, incidencias, timestamp)
                estado_anterior_estado = estado_anterior[0]
                estado_anterior_estaciones = estado_anterior[1]
                estado_anterior_accesos = estado_anterior[2]
                estado_anterior_incidencias = estado_anterior[3]
                
                # Comparar estado general
                if (estado_anterior_estado == nuevo_estado and
                    estado_anterior_estaciones == nuevas_estaciones_cerradas and
                    estado_anterior_accesos == nuevos_accesos_cerrados and
                    estado_anterior_incidencias == nuevas_incidencias):
                    
                    hay_cambios = False
                    logger.info(f"[ESTADO_LINEA] No hay cambios en línea {datos_estado['linea']}, no se actualiza BD")
            
            # Solo guardar si hay cambios
            if hay_cambios:
                cursor.execute('''
                    INSERT INTO estado_lineas 
                    (linea, estado, clase_css, descripcion, estaciones_cerradas, accesos_cerrados, incidencias, url_origen, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datos_estado['linea'],
                    datos_estado['estado_linea']['estado'],
                    datos_estado['estado_linea']['clase'],
                    datos_estado['estado_linea']['descripcion'],
                    nuevas_estaciones_cerradas,
                    nuevos_accesos_cerrados,
                    nuevas_incidencias,
                    datos_estado['url'],
                    datos_estado['timestamp']
                ))
                
                conn.commit()
                logger.info(f"[ESTADO_LINEA] Estado de línea {datos_estado['linea']} actualizado en BD (cambios detectados)")
            else:
                logger.info(f"[ESTADO_LINEA] Estado de línea {datos_estado['linea']} sin cambios, BD no actualizada")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"[ESTADO_LINEA] Error guardando estado de línea {datos_estado['linea']}: {e}")
            if 'conn' in locals():
                conn.close()
    
    def obtener_estado_todas_lineas(self):
        """Obtiene el estado de todas las líneas"""
        resultados = {}
        
        for numero_linea in self.lineas_urls.keys():
            logger.info(f"[ESTADO_LINEA] Procesando línea {numero_linea}")
            
            datos = self.obtener_estado_linea(numero_linea)
            if datos:
                self.guardar_estado_linea(datos)
                resultados[numero_linea] = datos
            
            # Pausa entre requests para no sobrecargar el servidor
            time.sleep(2)
        
        return resultados

def test_scraper_estado_lineas():
    """Función de prueba del scraper"""
    print("🔍 PROBANDO SCRAPER ESTADO LÍNEAS")
    print("=" * 50)
    
    scraper = ScraperEstadoLineas()
    
    # Ejecutar para todas las líneas
    print("📊 Obteniendo estado de todas las líneas...")
    resultados = scraper.obtener_estado_todas_lineas()
    
    print(f"\n✅ Procesadas {len(resultados)} líneas:")
    for linea_id, resultado in resultados.items():
        if resultado:
            print(f"\n🚇 Línea {linea_id}:")
            print(f"   Estado: {resultado['estado_linea']['estado']}")
            print(f"   Estaciones cerradas: {len(resultado['estaciones_cerradas'])}")
            for estacion in resultado['estaciones_cerradas']:
                print(f"     - {estacion['nombre']}: {estacion['motivo']}")
            print(f"   Accesos cerrados: {len(resultado['accesos_cerrados'])}")
            print(f"   Incidencias: {len(resultado['incidencias'])}")
        else:
            print(f"\n❌ Línea {linea_id}: Error al obtener datos")
    
    print(f"\n✅ Base de datos actualizada con estado de {len(resultados)} líneas")

if __name__ == "__main__":
    test_scraper_estado_lineas() 