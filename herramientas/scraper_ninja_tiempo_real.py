#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time

class ScraperNinjaTiempoReal:
    """Scraper Ninja para obtener datos dinámicos en tiempo real"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xxml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def obtener_proximos_trenes(self, url_estacion):
        """Obtiene los próximos trenes de una estación"""
        try:
            print(f"[NINJA] Obteniendo próximos trenes de: {url_estacion}")
            
            response = self.session.get(url_estacion, timeout=10)
            if response.status_code != 200:
                print(f"[NINJA] Error HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar sección de próximos trenes
            proximos_trenes_html = ""
            
            # Buscar por diferentes selectores comunes
            selectors_proximos = [
                '.proximos-trenes',
                '.tiempo-espera',
                '.next-trains',
                '.train-times',
                '.horarios',
                '.schedules',
                '[data-section="proximos-trenes"]',
                '.estacion-horarios',
                '.station-times'
            ]
            
            for selector in selectors_proximos:
                elementos = soup.select(selector)
                if elementos:
                    proximos_trenes_html = str(elementos[0])
                    print(f"[NINJA] Encontrados próximos trenes con selector: {selector}")
                    break
            
            # Si no se encuentra con selectores específicos, buscar por texto
            if not proximos_trenes_html:
                elementos_con_texto = soup.find_all(text=re.compile(r'próximos|trenes|tiempo|espera', re.IGNORECASE))
                for elemento in elementos_con_texto:
                    if elemento.parent:
                        # Buscar el contenedor padre que contenga la información
                        contenedor = elemento.find_parent(['div', 'section', 'article'])
                        if contenedor:
                            proximos_trenes_html = str(contenedor)
                            print(f"[NINJA] Encontrados próximos trenes por texto")
                            break
            
            return proximos_trenes_html
            
        except Exception as e:
            print(f"[NINJA] Error obteniendo próximos trenes: {e}")
            return None
    
    def obtener_estado_servicios(self, url_estacion, id_modal=None):
        """Obtiene el estado de ascensores y escaleras mecánicas SOLO del bloque de la estación correspondiente."""
        try:
            print(f"[NINJA] Obteniendo estado de servicios de: {url_estacion}")
            response = self.session.get(url_estacion, timeout=10)
            if response.status_code != 200:
                print(f"[NINJA] Error HTTP {response.status_code}")
                return "No disponible", "No disponible"
            soup = BeautifulSoup(response.content, 'html.parser')

            # 1. Deducir el id del bloque de la estación (ej: estacion-418)
            match = re.search(r'estacion-(\d+)', url_estacion)
            if not match:
                print("[NINJA] No se pudo deducir el id de estación del URL")
                return "No disponible", "No disponible"
            id_estacion = match.group(1)
            bloque_id = f"estacion-{id_estacion}"
            print(f"[NINJA] Buscando bloque con id: {bloque_id}")

            # 2. Buscar el bloque de la estación
            bloque_estacion = soup.find(id=bloque_id)
            if not bloque_estacion:
                print(f"[NINJA] No se encontró el bloque de la estación {bloque_id}")
                return "No disponible", "No disponible"

            # 3. Buscar el texto de estado de ascensores/escaleras dentro del bloque
            estado_p = bloque_estacion.find('p', class_='text__info-estacion--tit-inc')
            if not estado_p:
                print(f"[NINJA] No se encontró el texto de estado en el bloque de la estación {bloque_id}")
                return "No disponible", "No disponible"
            texto_estado = estado_p.get_text(strip=True).lower()
            print(f"[NINJA] Texto de estado encontrado: {texto_estado}")

            # 4. Analizar el texto específico
            if 'funcionan correctamente' in texto_estado:
                return "Operativo", "Operativo"
            elif 'alteraciones' in texto_estado or 'fuera de servicio' in texto_estado or 'avería' in texto_estado:
                return "Fuera de servicio", "Fuera de servicio"
            elif 'mantenimiento' in texto_estado:
                return "En mantenimiento", "En mantenimiento"
            else:
                # Si no hay palabras clave específicas, devolver el texto original
                return texto_estado, texto_estado

        except Exception as e:
            print(f"[NINJA] Error al obtener estado de servicios: {e}")
            return "No disponible", "No disponible"
    
    def obtener_ultima_actualizacion(self, url_estacion):
        """Obtiene la última actualización de los datos"""
        try:
            response = self.session.get(url_estacion, timeout=10)
            if response.status_code != 200:
                return "No disponible"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar patrones de última actualización
            patrones_actualizacion = [
                r'última actualización[^:]*:?\s*([^.\n]+)',
                r'actualizado[^:]*:?\s*([^.\n]+)',
                r'última actualización[^:]*:?\s*hace\s+([^.\n]+)',
                r'actualizado[^:]*:?\s*hace\s+([^.\n]+)',
            ]
            
            texto_completo = soup.get_text()
            
            for patron in patrones_actualizacion:
                match = re.search(patron, texto_completo, re.IGNORECASE)
                if match:
                    ultima_act = match.group(1).strip()
                    print(f"[NINJA] Última actualización encontrada: {ultima_act}")
                    return ultima_act
            
            return "No disponible"
            
        except Exception as e:
            print(f"[NINJA] Error obteniendo última actualización: {e}")
            return "No disponible"
    
    def obtener_ultima_actualizacion_ascensores(self, url_estacion):
        """Obtiene la última actualización específica del estado de ascensores y escaleras"""
        try:
            print(f"[NINJA] Obteniendo última actualización de ascensores de: {url_estacion}")
            
            response = self.session.get(url_estacion, timeout=10)
            if response.status_code != 200:
                print(f"[NINJA] Error HTTP {response.status_code}")
                return "No disponible"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar todos los enlaces de próximos trenes para encontrar el ID modal
            modal_links = soup.find_all('a', href=re.compile(r'/es/metro_next_trains/modal/\d+'))
            
            print(f"[NINJA] Encontrados {len(modal_links)} enlaces de modal para actualización")
            
            # Si hay al menos 2 enlaces, usar el segundo (que suele ser para estado de accesibilidad)
            if len(modal_links) >= 2:
                target_link = modal_links[1]  # Segunda aparición
                print(f"[NINJA] Usando segunda aparición del enlace modal para actualización")
            elif len(modal_links) == 1:
                target_link = modal_links[0]  # Solo hay uno, usarlo
                print(f"[NINJA] Solo hay una aparición del enlace modal para actualización, usándola")
            else:
                print(f"[NINJA] No se encontraron enlaces de modal para actualización")
                return "No disponible"
            
            # Buscar la última actualización justo después de este enlace específico
            current_element = target_link
            found_update = False
            
            # Buscar en los siguientes elementos hermanos
            while current_element and not found_update:
                current_element = current_element.find_next_sibling()
                if not current_element:
                    break
                
                # Buscar el texto de última actualización
                update_text = current_element.find('p', class_='text_act--escaleras')
                if update_text:
                    texto_actualizacion = update_text.get_text(strip=True)
                    print(f"[NINJA] Última actualización encontrada: {texto_actualizacion}")
                    
                    # Extraer solo la parte de tiempo
                    if 'última actualización:' in texto_actualizacion.lower():
                        # Extraer la parte después de "Última actualización:"
                        tiempo_actualizacion = texto_actualizacion.split(':', 1)[1].strip()
                        print(f"[NINJA] Tiempo de actualización extraído: {tiempo_actualizacion}")
                        return tiempo_actualizacion
                    else:
                        # Si no tiene el formato esperado, devolver el texto completo
                        return texto_actualizacion
                
                # Si encontramos otro enlace de modal, parar la búsqueda
                if current_element.find('a', href=re.compile(r'/es/metro_next_trains/modal/\d+')):
                    print(f"[NINJA] Encontrado otro enlace modal, parando búsqueda de actualización")
                    break
            
            # Si no se encontró con el método específico, intentar búsqueda alternativa
            print(f"[NINJA] Intentando búsqueda alternativa de última actualización...")
            
            # Buscar directamente por texto en toda la página
            update_patterns = [
                r'última actualización:\s*([^.\n]+)',
                r'actualizado:\s*([^.\n]+)',
                r'última actualización[^:]*:?\s*hace\s+([^.\n]+)',
                r'actualizado[^:]*:?\s*hace\s+([^.\n]+)',
            ]
            
            texto_completo = soup.get_text()
            
            for pattern in update_patterns:
                match = re.search(pattern, texto_completo, re.IGNORECASE)
                if match:
                    ultima_act = match.group(1).strip()
                    print(f"[NINJA] Última actualización encontrada por búsqueda alternativa: {ultima_act}")
                    return ultima_act
            
            print(f"[NINJA] No se encontró información de última actualización")
            return "No disponible"
            
        except Exception as e:
            print(f"[NINJA] Error obteniendo última actualización de ascensores: {e}")
            return "No disponible"
    
    def scrape_estacion_tiempo_real(self, url_estacion):
        """Ejecuta el scraper completo para una estación en tiempo real"""
        try:
            print(f"[NINJA] Iniciando scraper tiempo real para: {url_estacion}")
            
            # Obtener todos los datos
            proximos_trenes_html = self.obtener_proximos_trenes(url_estacion)
            estado_ascensores, estado_escaleras = self.obtener_estado_servicios(url_estacion)
            ultima_actualizacion_ascensores = self.obtener_ultima_actualizacion_ascensores(url_estacion)
            ultima_actualizacion_general = self.obtener_ultima_actualizacion(url_estacion)
            
            # Usar la actualización específica de ascensores si está disponible, sino la general
            ultima_actualizacion = ultima_actualizacion_ascensores if ultima_actualizacion_ascensores != "No disponible" else ultima_actualizacion_general
            
            # Crear resultado
            resultado = {
                'proximos_trenes_html': proximos_trenes_html or '<p>No se pudieron obtener los próximos trenes</p>',
                'estado_ascensores': estado_ascensores,
                'estado_escaleras': estado_escaleras,
                'ultima_actualizacion': ultima_actualizacion,
                'ultima_actualizacion_ascensores': ultima_actualizacion_ascensores,
                'ultima_actualizacion_general': ultima_actualizacion_general,
                'timestamp_scraping': datetime.now().isoformat(),
                'url_estacion': url_estacion
            }
            
            print(f"[NINJA] Scraping completado exitosamente")
            return resultado
            
        except Exception as e:
            print(f"[NINJA] Error en scraping tiempo real: {e}")
            return {
                'proximos_trenes_html': '<p>Error obteniendo datos</p>',
                'estado_ascensores': 'Error',
                'estado_escaleras': 'Error',
                'ultima_actualizacion': 'Error',
                'ultima_actualizacion_ascensores': 'Error',
                'ultima_actualizacion_general': 'Error',
                'timestamp_scraping': datetime.now().isoformat(),
                'url_estacion': url_estacion,
                'error': str(e)
            }

    def obtener_estado_servicios_por_estacion(self, url_linea, nombre_estacion):
        """Obtiene el estado de ascensores para una estación específica"""
        try:
            print(f"[NINJA] Obteniendo estado de servicios para {nombre_estacion} en {url_linea}")
            
            response = self.session.get(url_linea, timeout=10)
            if response.status_code != 200:
                print(f"[NINJA] Error HTTP {response.status_code}")
                return "No disponible", "No disponible"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la estación por nombre en la página
            # Las estaciones suelen estar en elementos con el nombre
            estacion_elements = soup.find_all(text=re.compile(re.escape(nombre_estacion), re.IGNORECASE))
            
            for element in estacion_elements:
                # Buscar el contenedor padre que contenga el enlace de modal
                parent = element.find_parent()
                if parent:
                    # Buscar todos los enlaces de modal en este contenedor
                    modal_links = parent.find_all('a', href=re.compile(r'/es/metro_next_trains/modal/\d+'))
                    
                    if len(modal_links) >= 2:
                        # Usar la segunda aparición (estado de accesibilidad)
                        target_link = modal_links[1]
                        print(f"[NINJA] Encontrada segunda aparición del enlace modal para {nombre_estacion}")
                    elif len(modal_links) == 1:
                        # Solo hay uno, usarlo
                        target_link = modal_links[0]
                        print(f"[NINJA] Encontrada única aparición del enlace modal para {nombre_estacion}")
                    else:
                        continue  # No hay enlaces de modal, buscar en el siguiente elemento
                    
                    # Obtener el ID modal
                    href = target_link.get('href', '')
                    modal_id = re.search(r'/modal/(\d+)', href)
                    if modal_id:
                        modal_id = modal_id.group(1)
                        print(f"[NINJA] Encontrado modal ID para {nombre_estacion}: {modal_id}")
                        
                        # Buscar el estado justo después de este enlace específico
                        current_element = target_link
                        found_status = False
                        
                        while current_element and not found_status:
                            current_element = current_element.find_next_sibling()
                            if not current_element:
                                break
                            
                            # Buscar el texto de estado
                            estado_text = current_element.find('p', class_='text__info-estacion--tit-inc')
                            if estado_text:
                                texto_estado = estado_text.get_text(strip=True)
                                print(f"[NINJA] Estado encontrado para {nombre_estacion}: {texto_estado}")
                                
                                # Determinar el estado
                                if 'funcionan correctamente' in texto_estado.lower():
                                    return "Operativo", "Operativo"
                                elif 'no dispone de escaleras mecánicas ni ascensores' in texto_estado.lower():
                                    return "No disponible", "No disponible"
                                elif 'fuera de servicio' in texto_estado.lower() or 'averiado' in texto_estado.lower():
                                    return "Fuera de servicio", "Fuera de servicio"
                                elif 'mantenimiento' in texto_estado.lower():
                                    return "En mantenimiento", "En mantenimiento"
                                else:
                                    # Estado no reconocido
                                    print(f"[NINJA] Estado no reconocido para {nombre_estacion}: {texto_estado}")
                                    return "Estado desconocido", "Estado desconocido"
                            
                            # Si encontramos otro enlace de modal, parar
                            if current_element.find('a', href=re.compile(r'/es/metro_next_trains/modal/\d+')):
                                print(f"[NINJA] Encontrado otro enlace modal para {nombre_estacion}, parando búsqueda")
                                break
                        
                        if not found_status:
                            print(f"[NINJA] No se encontró estado específico para {nombre_estacion} después del enlace modal {modal_id}")
            
            # Si no se encontró estado con el método anterior, intentar búsqueda alternativa
            print(f"[NINJA] Intentando búsqueda alternativa de estado para {nombre_estacion}...")
            
            # Buscar directamente por texto en toda la página
            estado_patterns = [
                r'todas las escaleras mecánicas y/o ascensores funcionan correctamente',
                r'funcionan correctamente',
                r'fuera de servicio',
                r'averiado',
                r'mantenimiento',
                r'no dispone de escaleras mecánicas ni ascensores'
            ]
            
            texto_completo = soup.get_text().lower()
            for pattern in estado_patterns:
                if re.search(pattern, texto_completo):
                    if 'funcionan correctamente' in pattern:
                        print(f"[NINJA] Estado encontrado por búsqueda alternativa para {nombre_estacion}: Operativo")
                        return "Operativo", "Operativo"
                    elif 'no dispone' in pattern:
                        print(f"[NINJA] Estado encontrado por búsqueda alternativa para {nombre_estacion}: No disponible")
                        return "No disponible", "No disponible"
                    elif 'fuera de servicio' in pattern or 'averiado' in pattern:
                        print(f"[NINJA] Estado encontrado por búsqueda alternativa para {nombre_estacion}: Fuera de servicio")
                        return "Fuera de servicio", "Fuera de servicio"
                    elif 'mantenimiento' in pattern:
                        print(f"[NINJA] Estado encontrado por búsqueda alternativa para {nombre_estacion}: En mantenimiento")
                        return "En mantenimiento", "En mantenimiento"
            
            print(f"[NINJA] No se encontró estado para {nombre_estacion}")
            return "No disponible", "No disponible"
            
        except Exception as e:
            print(f"[NINJA] Error obteniendo estado de servicios para {nombre_estacion}: {e}")
            return "Error", "Error"

def test_scraper_ninja():
    """Prueba el scraper Ninja con algunas estaciones"""
    scraper = ScraperNinjaTiempoReal()
    
    # URLs de prueba - estaciones con diferentes configuraciones
    urls_prueba = [
        'https://www.metromadrid.es/es/linea/linea-1#estacion-152',  # Bambú
        'https://www.metromadrid.es/es/linea/linea-1#estacion-106',  # Cuatro Caminos
        'https://www.metromadrid.es/es/linea/linea-4#estacion-411',  # Avenida de América
        'https://www.metromadrid.es/es/linea/linea-6#estacion-601',  # Laguna
    ]
    
    for i, url in enumerate(urls_prueba, 1):
        print(f"\n{'='*80}")
        print(f"🔍 PROBANDO NINJA SCRAPER #{i}: {url}")
        print(f"{'='*80}")
        
        # Probar función específica de estado de servicios
        print(f"\n📊 Probando obtener_estado_servicios...")
        estado_asc, estado_esc = scraper.obtener_estado_servicios(url)
        print(f"✅ Estado ascensores: {estado_asc}")
        print(f"✅ Estado escaleras: {estado_esc}")
        
        # Probar función específica de última actualización de ascensores
        print(f"\n📊 Probando obtener_ultima_actualizacion_ascensores...")
        ultima_act_asc = scraper.obtener_ultima_actualizacion_ascensores(url)
        print(f"✅ Última actualización ascensores: {ultima_act_asc}")
        
        # Probar función completa
        print(f"\n📊 Probando scrape_estacion_tiempo_real...")
        resultado = scraper.scrape_estacion_tiempo_real(url)
        
        print(f"✅ Próximos trenes HTML: {len(resultado['proximos_trenes_html'])} caracteres")
        print(f"✅ Estado ascensores: {resultado['estado_ascensores']}")
        print(f"✅ Estado escaleras: {resultado['estado_escaleras']}")
        print(f"✅ Última actualización: {resultado['ultima_actualizacion']}")
        print(f"✅ Última actualización ascensores: {resultado['ultima_actualizacion_ascensores']}")
        print(f"✅ Última actualización general: {resultado['ultima_actualizacion_general']}")
        print(f"✅ Timestamp: {resultado['timestamp_scraping']}")
        
        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
        
        # Pausa entre requests para no sobrecargar el servidor
        if i < len(urls_prueba):
            print(f"\n⏳ Esperando 3 segundos antes de la siguiente prueba...")
            time.sleep(3)

def test_scraper_ninja_simple():
    """Prueba simple del scraper Ninja con una sola estación"""
    scraper = ScraperNinjaTiempoReal()
    
    # URL de prueba simple
    url_prueba = 'https://www.metromadrid.es/es/linea/linea-1#estacion-152'  # Bambú
    
    print(f"\n{'='*80}")
    print(f"🔍 PRUEBA SIMPLE NINJA SCRAPER: {url_prueba}")
    print(f"{'='*80}")
    
    resultado = scraper.scrape_estacion_tiempo_real(url_prueba)
    
    print(f"✅ Próximos trenes HTML: {len(resultado['proximos_trenes_html'])} caracteres")
    print(f"✅ Estado ascensores: {resultado['estado_ascensores']}")
    print(f"✅ Estado escaleras: {resultado['estado_escaleras']}")
    print(f"✅ Última actualización: {resultado['ultima_actualizacion']}")
    print(f"✅ Timestamp: {resultado['timestamp_scraping']}")
    
    if 'error' in resultado:
        print(f"❌ Error: {resultado['error']}")

if __name__ == "__main__":
    # Usar la prueba simple por defecto
    test_scraper_ninja_simple()
    
    # Descomentar para usar la prueba completa
    # test_scraper_ninja() 