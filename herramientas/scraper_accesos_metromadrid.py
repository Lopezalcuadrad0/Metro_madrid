#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER ACCESOS METROMADRID.ES
==============================

Extrae accesos de la web oficial de Metro de Madrid usando el id de estación.
"""
import requests
from bs4 import BeautifulSoup
import sys
import json
import re

# URLs base para diferentes líneas
LINE_URLS = {
    '1': "https://www.metromadrid.es/es/linea/linea-1#estacion-{}",
    '2': "https://www.metromadrid.es/es/linea/linea-2#estacion-{}",
    '3': "https://www.metromadrid.es/es/linea/linea-3#estacion-{}",
    '4': "https://www.metromadrid.es/es/linea/linea-4#estacion-{}",
    '5': "https://www.metromadrid.es/es/linea/linea-5#estacion-{}",
    '6': "https://www.metromadrid.es/es/linea/linea-6#estacion-{}",
    '7': "https://www.metromadrid.es/es/linea/linea-7#estacion-{}",
    '8': "https://www.metromadrid.es/es/linea/linea-8#estacion-{}",
    '9': "https://www.metromadrid.es/es/linea/linea-9#estacion-{}",
    '10': "https://www.metromadrid.es/es/linea/linea-10#estacion-{}",
    '11': "https://www.metromadrid.es/es/linea/linea-11#estacion-{}",
    '12': "https://www.metromadrid.es/es/linea/linea-12#estacion-{}",
    'R': "https://www.metromadrid.es/es/linea/ramal#estacion-{}"
}


def extraer_accesos_metromadrid(id_estacion, linea=None):
    """
    Extrae accesos de MetroMadrid para una estación específica.
    
    Args:
        id_estacion: ID de la estación
        linea: Línea específica (opcional). Si no se proporciona, intentará detectarla.
    """
    
    # Si no se especifica línea, intentar detectarla
    if not linea:
        linea = detectar_linea_por_id(id_estacion)
    
    if not linea:
        print(f"❌ No se pudo determinar la línea para el ID {id_estacion}")
        return []
    
    url = LINE_URLS.get(linea, LINE_URLS['10']).format(id_estacion)
    print(f"🔗 Accediendo a: {url}")
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Buscar la tabla de accesos
        tabla = soup.find('div', class_='box__info-linea--accesos')
        if not tabla:
            print("❌ No se encontró la tabla de accesos.")
            return []
        table = tabla.find('table')
        if not table:
            print("❌ No se encontró la tabla dentro del div.")
            return []
        
        accesos = []
        tbody = table.find('tbody')
        if not tbody:
            print("❌ No se encontró el tbody de la tabla.")
            return []
        
        for row in tbody.find_all('tr'):
            celdas = row.find_all('td')
            if len(celdas) != 2:
                continue
            
            # Extraer vestíbulo
            vestibulo = celdas[0].get_text(strip=True)
            
            # Extraer información del acceso desde la segunda celda
            acceso_celda = celdas[1]
            
            # Buscar el nombre del acceso (strong)
            acceso_nombre_elem = acceso_celda.find('strong')
            acceso_nombre = acceso_nombre_elem.get_text(strip=True) if acceso_nombre_elem else ''
            
            # Buscar la dirección (p)
            direccion_elem = acceso_celda.find('p')
            direccion = direccion_elem.get_text(strip=True) if direccion_elem else ''
            
            # Si no hay strong, intentar extraer del texto completo
            if not acceso_nombre:
                texto_completo = acceso_celda.get_text(strip=True)
                # Intentar separar nombre y dirección si hay un patrón
                if direccion and direccion in texto_completo:
                    acceso_nombre = texto_completo.replace(direccion, '').strip()
                else:
                    acceso_nombre = texto_completo
            
            # Limpiar y validar datos
            vestibulo = limpiar_texto(vestibulo)
            acceso_nombre = limpiar_texto(acceso_nombre)
            direccion = limpiar_texto(direccion)
            
            # Solo agregar si hay información válida
            if vestibulo or acceso_nombre or direccion:
                accesos.append({
                    'vestibulo': vestibulo,
                    'acceso': acceso_nombre,
                    'direccion': direccion
                })
                print(f"✅ Acceso encontrado: {vestibulo} - {acceso_nombre} - {direccion}")
        
        return accesos
        
    except Exception as e:
        print(f"❌ Error accediendo a {url}: {e}")
        return []


def detectar_linea_por_id(id_estacion):
    """
    Intenta detectar la línea basándose en el ID de la estación.
    Esta es una aproximación basada en patrones conocidos.
    """
    # Mapeo aproximado de IDs a líneas (esto debería mejorarse con una base de datos)
    id_linea_mapping = {
        # Línea 1
        1001: '1', 1010: '1', 1020: '1', 1030: '1', 1040: '1', 1050: '1',
        # Línea 9
        9001: '9', 9010: '9', 9020: '9', 9030: '9', 9040: '9', 9050: '9',
        # Línea 10
        10001: '10', 10010: '10', 10020: '10', 10030: '10', 10040: '10', 10050: '10',
        # Plaza de Castilla específicamente
        189: '1',  # Probablemente línea 1
    }
    
    # Buscar en el mapeo
    if id_estacion in id_linea_mapping:
        return id_linea_mapping[id_estacion]
    
    # Si no está en el mapeo, intentar deducir por rangos
    if 1000 <= id_estacion <= 1999:
        return '1'
    elif 9000 <= id_estacion <= 9999:
        return '9'
    elif 10000 <= id_estacion <= 10999:
        return '10'
    
    # Por defecto, intentar línea 1
    return '1'


def limpiar_texto(texto):
    """Limpia y normaliza el texto extraído"""
    if not texto:
        return ""
    
    # Eliminar espacios extra y caracteres especiales
    texto = re.sub(r'\s+', ' ', texto.strip())
    
    # Eliminar caracteres de control
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)
    
    return texto


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scraper_accesos_metromadrid.py <id_estacion> [linea]")
        sys.exit(1)
    id_estacion = sys.argv[1]
    linea = sys.argv[2] if len(sys.argv) > 2 else None
    resultado = extraer_accesos_metromadrid(id_estacion, linea)
    print(json.dumps(resultado, indent=2, ensure_ascii=False)) 