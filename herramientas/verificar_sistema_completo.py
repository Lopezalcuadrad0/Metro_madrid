#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICAR SISTEMA COMPLETO - Metro de Madrid
============================================

Verifica que todos los componentes del sistema funcionen correctamente:
- Base de datos
- Scraper Ninja
- Aplicación Flask
- API NinjaScrap
- Búsqueda de estaciones
"""

import sqlite3
import requests
import sys
import os
from datetime import datetime

# Configuración
DB_PATH = 'db/estaciones_fijas_v2.db'
FLASK_URL = 'http://localhost:5000'
API_URL = 'http://localhost:5000/api/ninjascrap'

def verificar_base_datos():
    """Verifica que la base de datos esté accesible y tenga datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [row[0] for row in cursor.fetchall()]
        
        # Verificar que existan las tablas principales
        tablas_requeridas = ['linea_1', 'linea_2', 'linea_3', 'linea_4', 'linea_5']
        tablas_faltantes = [t for t in tablas_requeridas if t not in tablas]
        
        if tablas_faltantes:
            print(f"ERROR: Faltan tablas en la base de datos: {tablas_faltantes}")
            return False
        
        # Verificar datos en línea 1
        cursor.execute("SELECT COUNT(*) FROM linea_1")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("ERROR: La tabla linea_1 está vacía")
            return False
        
        print(f"OK: Base de datos accesible con {len(tablas)} tablas")
        print(f"OK: Línea 1 tiene {count} estaciones")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR verificando base de datos: {e}")
        return False

def verificar_scraper_ninja():
    """Verifica que el scraper Ninja se pueda importar y crear"""
    try:
        # Intentar importar el scraper
        sys.path.append('herramientas')
        from scraper_ninja_tiempo_real import NinjaScraper
        
        print("OK: Scraper Ninja importado correctamente")
        
        # Intentar crear una instancia
        scraper = NinjaScraper()
        print("OK: Instancia de scraper creada")
        
        return True
        
    except ImportError as e:
        print(f"ERROR importando scraper Ninja: {e}")
        return False
    except Exception as e:
        print(f"ERROR creando instancia de scraper: {e}")
        return False

def verificar_aplicacion_flask():
    """Verifica que la aplicación Flask esté funcionando"""
    try:
        response = requests.get(FLASK_URL, timeout=5)
        
        if response.status_code == 200:
            print("OK: Aplicacion Flask funcionando")
            return True
        else:
            print(f"ERROR: Aplicacion Flask respondio con codigo: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: No se puede conectar a la aplicacion Flask")
        print("Asegurate de que la aplicacion este ejecutandose en http://localhost:5000")
        return False
    except Exception as e:
        print(f"ERROR verificando aplicacion Flask: {e}")
        return False

def verificar_api_ninjascrap():
    """Verifica que la API NinjaScrap funcione"""
    try:
        # Probar con una estación conocida
        test_data = {
            'id_modal': '1_1',  # Plaza de Castilla
            'url': 'https://www.metromadrid.es/es/estacion/plaza-castilla'
        }
        
        response = requests.post(API_URL, json=test_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'proximos_trenes_html' in data:
                print("OK: API NinjaScrap funcionando")
                return True
            else:
                print(f"ERROR: API respondio con error: {response.text}")
                return False
        else:
            print(f"ERROR: API respondio con error: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR probando API NinjaScrap: {e}")
        return False

def verificar_busqueda_estaciones():
    """Verifica que la búsqueda de estaciones funcione"""
    try:
        # Probar búsqueda
        search_url = f"{FLASK_URL}/api/search"
        params = {'q': 'plaza'}
        
        response = requests.get(search_url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'estaciones' in data:
                print(f"OK: Busqueda funcionando - {len(data)} resultados encontrados")
                return True
            else:
                print(f"ERROR: Busqueda fallo: {response.text}")
                return False
        else:
            print(f"ERROR: Busqueda fallo: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR probando busqueda: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("VERIFICACION DEL SISTEMA COMPLETO - METRO DE MADRID")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar cada componente
    print("1. Verificando base de datos...")
    bd_ok = verificar_base_datos()
    print()
    
    print("2. Verificando scraper Ninja...")
    ninja_ok = verificar_scraper_ninja()
    print()
    
    print("3. Verificando aplicacion Flask...")
    flask_ok = verificar_aplicacion_flask()
    print()
    
    print("4. Verificando API NinjaScrap...")
    api_ok = verificar_api_ninjascrap()
    print()
    
    print("5. Verificando busqueda de estaciones...")
    busqueda_ok = verificar_busqueda_estaciones()
    print()
    
    # Resumen
    print("=" * 60)
    print("RESUMEN:")
    print(f"  Base de datos: {'OK' if bd_ok else 'ERROR'}")
    print(f"  Scraper Ninja: {'OK' if ninja_ok else 'ERROR'}")
    print(f"  Aplicacion Flask: {'OK' if flask_ok else 'ERROR'}")
    print(f"  API NinjaScrap: {'OK' if api_ok else 'ERROR'}")
    print(f"  Busqueda estaciones: {'OK' if busqueda_ok else 'ERROR'}")
    print("=" * 60)
    
    # Determinar estado general
    componentes_ok = sum([bd_ok, ninja_ok, flask_ok, api_ok, busqueda_ok])
    total_componentes = 5
    
    if componentes_ok == total_componentes:
        print("\nSISTEMA COMPLETAMENTE FUNCIONAL")
        print("Todos los componentes estan funcionando correctamente.")
    elif componentes_ok >= 3:
        print(f"\nSISTEMA PARCIALMENTE FUNCIONAL")
        print(f"{componentes_ok}/{total_componentes} componentes funcionando.")
        print("Algunas funciones pueden no estar disponibles.")
    else:
        print(f"\nSISTEMA CON PROBLEMAS")
        print(f"Solo {componentes_ok}/{total_componentes} componentes funcionando.")
        print("Se recomienda revisar la configuracion.")
    
    print("\nRecomendaciones:")
    if not bd_ok:
        print("- Ejecuta 'python herramientas/crear_tablas_fijas.py' para crear la base de datos")
    if not flask_ok:
        print("- Ejecuta 'python app.py' para iniciar la aplicacion Flask")
    if not ninja_ok:
        print("- Verifica que el scraper Ninja esté configurado correctamente")
    if not api_ok or not busqueda_ok:
        print("- Asegurate de que la aplicacion Flask esté ejecutandose")

if __name__ == "__main__":
    main() 