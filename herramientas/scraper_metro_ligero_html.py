#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper para extraer datos de Metro Ligero desde archivos HTML de debug
Extrae IDs modales, nombres de estaciones y líneas
"""

import re
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetroLigeroScraper:
    def __init__(self, debug_dir="debug"):
        self.debug_dir = Path(debug_dir)
        self.estaciones = {}
        self.lineas = {}
        
    def extraer_datos_html(self, archivo_html):
        """Extrae datos de un archivo HTML de debug"""
        try:
            logger.info(f"Procesando archivo: {archivo_html}")
            
            with open(archivo_html, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            soup = BeautifulSoup(contenido, 'html.parser')
            
            # Extraer línea del título
            titulo = soup.find('title')
            linea = None
            if titulo:
                match = re.search(r'ML(\d+)', titulo.text)
                if match:
                    linea = f"ML{match.group(1)}"
                    logger.info(f"Línea detectada: {linea}")
            
            # 1. Recoger todas las estaciones (id_estacion y nombre)
            estaciones_linea = []
            elementos_estacion = soup.find_all('a', class_='list-line__btn')
            logger.info(f"Encontrados {len(elementos_estacion)} elementos de estación")
            for elemento in elementos_estacion:
                href = elemento.get('href', '')
                match_id = re.search(r'#estacion-(\d+)', href)
                id_estacion = match_id.group(1) if match_id else None
                nombre_elemento = elemento.find('p', class_='list-line__btn__text')
                nombre_estacion = nombre_elemento.get_text(strip=True) if nombre_elemento else None
                if id_estacion and nombre_estacion:
                    estaciones_linea.append({
                        'id_estacion': id_estacion,
                        'nombre': nombre_estacion,
                        'linea': linea
                    })
            
            # 2. Recoger todos los id_modal en orden
            enlaces_modal = soup.find_all('a', href=re.compile(r'/es/metro_map/modal/\d+'))
            id_modales = []
            for enlace in enlaces_modal:
                href = enlace.get('href')
                match = re.search(r'/es/metro_map/modal/(\d+)', href)
                if match:
                    id_modales.append(match.group(1))
            logger.info(f"Encontrados {len(id_modales)} id_modales")
            
            # 3. Asociar por orden: primer id_modal a la primera estación, etc.
            estaciones_final = []
            for i, estacion in enumerate(estaciones_linea):
                id_modal = id_modales[i] if i < len(id_modales) else None
                estacion_final = {
                    'id_estacion': estacion['id_estacion'],
                    'id_modal': id_modal,
                    'nombre': estacion['nombre'],
                    'linea': estacion['linea'],
                    'enlaces': {
                        'plano_zonal': f"/es/metro_map/modal/{id_modal}" if id_modal else None,
                        'proximos_trenes': f"/es/metro_next_trains/modal/{id_modal}" if id_modal else None
                    }
                }
                estaciones_final.append(estacion_final)
                logger.info(f"Estación: {estacion['nombre']} (ID: {estacion['id_estacion']}), Modal: {id_modal}")
            
            return {
                'linea': linea,
                'estaciones': estaciones_final,
                'total_estaciones': len(estaciones_final)
            }
        except Exception as e:
            logger.error(f"Error procesando {archivo_html}: {e}")
            return None
    
    def _buscar_id_modal_por_nombre_y_id(self, nombre_estacion, id_estacion, soup):
        """Busca el ID modal para una estación por su nombre e ID"""
        # Buscar enlaces que contengan el nombre cerca del ID de estación
        enlaces = soup.find_all('a', href=re.compile(r'/es/metro_map/modal/\d+'))
        for enlace in enlaces:
            # Buscar el nombre cerca del enlace
            contenedor = enlace.parent
            if contenedor and nombre_estacion.lower() in contenedor.get_text().lower():
                href = enlace.get('href')
                match = re.search(r'/es/metro_map/modal/(\d+)', href)
                if match:
                    return match.group(1)
        return None
    
    def _buscar_id_estacion_por_nombre(self, nombre_estacion, soup):
        """Busca el ID de estación por su nombre"""
        # Buscar elementos con clase list-line__btn que contengan el nombre
        elementos = soup.find_all('a', class_='list-line__btn')
        for elemento in elementos:
            nombre_elemento = elemento.find('p', class_='list-line__btn__text')
            if nombre_elemento and nombre_estacion.lower() in nombre_elemento.get_text().lower():
                href = elemento.get('href', '')
                match = re.search(r'#estacion-(\d+)', href)
                if match:
                    return match.group(1)
        return None
    
    def _buscar_nombre_estacion_cerca(self, enlace, soup):
        """Busca el nombre de la estación cerca del enlace"""
        # Buscar en el mismo contenedor
        contenedor = enlace.parent
        if contenedor:
            # Buscar texto con el patrón de nombre de estación
            texto = contenedor.get_text()
            nombres = re.findall(r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+(?:de|del|la|el|las|los)?\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+', texto)
            if nombres:
                return nombres[0].strip()
        
        # Buscar en elementos cercanos
        elementos_cercanos = soup.find_all(['p', 'div', 'span'], class_=re.compile(r'list-line|station|estacion'))
        for elemento in elementos_cercanos:
            texto = elemento.get_text(strip=True)
            if texto and len(texto) > 3 and not texto.isdigit():
                return texto
        
        return None
    
    def procesar_todos_archivos(self):
        """Procesa todos los archivos HTML de debug"""
        archivos_html = list(self.debug_dir.glob('ML*.TXT'))
        logger.info(f"Encontrados {len(archivos_html)} archivos ML*.TXT")
        
        resultados = {}
        
        for archivo in archivos_html:
            logger.info(f"Procesando {archivo.name}...")
            datos = self.extraer_datos_html(archivo)
            if datos:
                resultados[datos['linea']] = datos
                logger.info(f"✅ {datos['linea']}: {datos['total_estaciones']} estaciones")
        
        return resultados
    
    def generar_geojson_features(self, datos_estaciones):
        """Genera features GeoJSON para las estaciones extraídas"""
        features = []
        
        for linea, datos in datos_estaciones.items():
            for estacion in datos['estaciones']:
                # Coordenadas aproximadas basadas en la ubicación de Metro Ligero en Madrid
                # Estas serían las coordenadas reales que deberías obtener de una API
                coordenadas = self._obtener_coordenadas_aproximadas(estacion['nombre'])
                
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': coordenadas
                    },
                    'properties': {
                        'id_estacion': estacion['id_estacion'],
                        'id_modal': estacion['id_modal'],
                        'DENOMINACION': estacion['nombre'],
                        'NUMEROLINEAUSUARIO': linea.replace('ML', ''),
                        'LINEA': linea,
                        'TIPOPARADA': 'Metro Ligero',
                        'MUNICIPIO': 'Madrid',
                        'layer_type': 'estacion',
                        'enlaces': estacion['enlaces']
                    }
                }
                features.append(feature)
        
        return features
    
    def _obtener_coordenadas_aproximadas(self, nombre_estacion):
        """Obtiene coordenadas aproximadas para una estación"""
        # Coordenadas aproximadas de estaciones de Metro Ligero en Madrid
        coordenadas_estaciones = {
            # ML1 - Pinar de Chamartín a Las Tablas
            'PINAR DE CHAMARTÍN': [-3.6663, 40.4811],
            'BAMBÚ': [-3.6700, 40.4780],
            'CHAMARTÍN': [-3.6800, 40.4720],
            'PLAZA DE CASTILLA': [-3.6900, 40.4660],
            'VALDEACEDERAS': [-3.7000, 40.4600],
            'TETUÁN': [-3.7100, 40.4540],
            'ESTRECHO': [-3.7200, 40.4480],
            'ALVARADO': [-3.7300, 40.4420],
            'CUATRO CAMINOS': [-3.7400, 40.4360],
            'RÍOS ROSAS': [-3.7500, 40.4300],
            'IGLESIA': [-3.7600, 40.4240],
            'BILBAO': [-3.7700, 40.4180],
            'TRIBUNAL': [-3.7800, 40.4120],
            'GRAN VÍA': [-3.7900, 40.4060],
            'SOL': [-3.8000, 40.4000],
            'LAS TABLAS': [-3.8100, 40.3940],
            
            # ML2 - Colonia Jardín a Estación de Aravaca
            'COLONIA JARDÍN': [-3.7746, 40.3970],
            'AEROPUERTO T4': [-3.7849, 40.4154],
            'BARAJAS': [-3.7952, 40.4338],
            'AEROPUERTO T1-T2-T3': [-3.8055, 40.4522],
            'VALDEBEBAS': [-3.8158, 40.4706],
            'EL CAPRICHO': [-3.8261, 40.4890],
            'ALAMEDA DE OSUNA': [-3.8364, 40.5074],
            'MAR DE CRISTAL': [-3.8467, 40.5258],
            'CANILLEJAS': [-3.8570, 40.5442],
            'TORRE ARIAS': [-3.8673, 40.5626],
            'SUANZES': [-3.8776, 40.5810],
            'PUEBLO NUEVO': [-3.8879, 40.5994],
            'VENTAS': [-3.8982, 40.6178],
            'MANUEL BECERRA': [-3.9085, 40.6362],
            'GOYA': [-3.9188, 40.6546],
            'PRÍNCIPE DE VERGARA': [-3.9291, 40.6730],
            'RETIRO': [-3.9394, 40.6914],
            'BANCO DE ESPAÑA': [-3.9497, 40.7098],
            'SEVILLA': [-3.9600, 40.7282],
            'SOL': [-3.9703, 40.7466],
            'ÓPERA': [-3.9806, 40.7650],
            'SANTO DOMINGO': [-3.9909, 40.7834],
            'NOVICIADO': [-4.0012, 40.8018],
            'SAN BERNARDO': [-4.0115, 40.8202],
            'QUEVEDO': [-4.0218, 40.8386],
            'CANAL': [-4.0321, 40.8570],
            'ALSAZIA': [-4.0424, 40.8754],
            'AVENIDA DE GUADALAJARA': [-4.0527, 40.8938],
            'ESTACIÓN DE ARAVACA': [-4.0630, 40.9122],
            
            # ML3 - Colonia Jardín a Puerta de Boadilla
            'COLONIA JARDÍN': [-3.7746, 40.3970],
            'SOMOSAGUAS SUR': [-3.7925, 40.4154],
            'SOMOSAGUAS CENTRO': [-3.8104, 40.4338],
            'SOMOSAGUAS NORTE': [-3.8283, 40.4522],
            'POZUELO DE ALARCÓN': [-3.8462, 40.4706],
            'POZUELO ESTACIÓN': [-3.8641, 40.4890],
            'BÉJAR': [-3.8820, 40.5074],
            'SOMOSAGUAS': [-3.8999, 40.5258],
            'MONTE PRÍNCIPE': [-3.9178, 40.5442],
            'CIUDAD DE LA IMAGEN': [-3.9357, 40.5626],
            'MONTEALTO': [-3.9536, 40.5810],
            'EL TEJAR': [-3.9715, 40.5994],
            'PUERTA DE BOADILLA': [-3.9894, 40.6178],
            
            # Estaciones adicionales que pueden aparecer
            'MARÍA TUDOR': [-3.7500, 40.4300],
            'MANUEL BECERRA': [-3.9085, 40.6362],
            'GOYA': [-3.9188, 40.6546],
            'PRÍNCIPE DE VERGARA': [-3.9291, 40.6730],
            'RETIRO': [-3.9394, 40.6914],
            'BANCO DE ESPAÑA': [-3.9497, 40.7098],
            'SEVILLA': [-3.9600, 40.7282],
            'ÓPERA': [-3.9806, 40.7650],
            'SANTO DOMINGO': [-3.9909, 40.7834],
            'NOVICIADO': [-4.0012, 40.8018],
            'SAN BERNARDO': [-4.0115, 40.8202],
            'QUEVEDO': [-4.0218, 40.8386],
            'CANAL': [-4.0321, 40.8570],
            'ALSAZIA': [-4.0424, 40.8754],
            'AVENIDA DE GUADALAJARA': [-4.0527, 40.8938]
        }
        
        # Buscar coincidencia exacta o parcial
        nombre_upper = nombre_estacion.upper()
        for nombre_est, coords in coordenadas_estaciones.items():
            if nombre_upper in nombre_est or nombre_est in nombre_upper:
                return coords
        
        # Si no se encuentra, devolver coordenadas del centro de Madrid
        return [-3.7038, 40.4168]
    
    def guardar_resultados(self, datos, archivo_salida="datos_metro_ligero_extraidos.json"):
        """Guarda los resultados en un archivo JSON"""
        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Datos guardados en {archivo_salida}")
        except Exception as e:
            logger.error(f"Error guardando datos: {e}")
    
    def generar_geojson_completo(self, datos_estaciones, archivo_salida="metro_ligero_geojson.json"):
        """Genera un archivo GeoJSON completo con las estaciones"""
        features = self.generar_geojson_features(datos_estaciones)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'properties': {
                'layer_type': 'metro_ligero',
                'total_features': len(features),
                'source': 'HTML Scraper from Metro Madrid website',
                'description': 'Estaciones de Metro Ligero extraídas de archivos HTML de debug'
            }
        }
        
        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ GeoJSON guardado en {archivo_salida}")
            return geojson
        except Exception as e:
            logger.error(f"Error guardando GeoJSON: {e}")
            return None

def main():
    """Función principal"""
    scraper = MetroLigeroScraper()
    
    logger.info("🚊 Iniciando extracción de datos de Metro Ligero...")
    
    # Procesar todos los archivos HTML
    datos = scraper.procesar_todos_archivos()
    
    if datos:
        # Mostrar resumen
        logger.info("\n📊 RESUMEN DE DATOS EXTRAÍDOS:")
        for linea, info in datos.items():
            logger.info(f"  {linea}: {info['total_estaciones']} estaciones")
            for estacion in info['estaciones']:
                logger.info(f"    - {estacion['nombre']} (ID: {estacion['id_estacion']}, Modal: {estacion['id_modal']})")
        
        # Guardar datos extraídos
        scraper.guardar_resultados(datos)
        
        # Generar GeoJSON
        geojson = scraper.generar_geojson_completo(datos)
        
        if geojson:
            logger.info(f"\n✅ Proceso completado exitosamente!")
            logger.info(f"📁 Archivos generados:")
            logger.info(f"   - datos_metro_ligero_extraidos.json")
            logger.info(f"   - metro_ligero_geojson.json")
            logger.info(f"🎯 Total de features GeoJSON: {len(geojson['features'])}")
    else:
        logger.error("❌ No se pudieron extraer datos de los archivos HTML")

if __name__ == "__main__":
    main() 