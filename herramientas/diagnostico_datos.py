#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO DE DATOS - Metro de Madrid
======================================

Diagnostica el estado de los datos en la base de datos fija.
Verifica qué estaciones tienen datos detallados y cuáles faltan.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import os

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'estaciones_fijas_v2.db')

def diagnosticar_estacion_ejemplo():
    """Diagnostica una estación específica como ejemplo"""
    print("DIAGNOSTICO DE ESTACION EJEMPLO")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Buscar una estación con datos
        query = """
        SELECT 
            id_fijo, nombre, direccion_completa, accesos, servicios, vestibulos, ultima_actualizacion_detalles
        FROM linea_1 
        WHERE direccion_completa IS NOT NULL 
        LIMIT 1
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            estacion = df.iloc[0]
            print(f"Estacion: {estacion['nombre']}")
            print(f"ID: {estacion['id_fijo']}")
            print(f"Direccion completa: {estacion['direccion_completa']}")
            print(f"Accesos: {estacion['accesos']}")
            print(f"Servicios: {estacion['servicios']}")
            print(f"Vestibulos: {estacion['vestibulos']}")
            print(f"Ultima actualizacion: {estacion['ultima_actualizacion_detalles']}")
            
            # Análisis de campos
            print(f"\nANALISIS DE CAMPOS:")
            print(f"  direccion_completa es NULL: {estacion['direccion_completa'] is None}")
            print(f"  direccion_completa esta vacio: {estacion['direccion_completa'] == ''}")
            print(f"  accesos es NULL: {estacion['accesos'] is None}")
            print(f"  accesos esta vacio: {estacion['accesos'] == ''}")
            print(f"  servicios es NULL: {estacion['servicios'] is None}")
            print(f"  servicios esta vacio: {estacion['servicios'] == ''}")
            
        else:
            print("No se encontro la estacion Pinar de Chamartin")
            
        conn.close()
        
    except Exception as e:
        print(f"ERROR en diagnostico: {e}")

def verificar_consultas():
    """Verifica diferentes consultas para entender el estado de los datos"""
    print("\nVERIFICACION DE CONSULTAS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Consulta 1: Solo direccion_completa
        query1 = """
        SELECT COUNT(*) as total
        FROM (
            SELECT id_fijo FROM linea_1 WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
            UNION ALL
            SELECT id_fijo FROM linea_2 WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
            UNION ALL
            SELECT id_fijo FROM linea_3 WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
            UNION ALL
            SELECT id_fijo FROM linea_4 WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
            UNION ALL
            SELECT id_fijo FROM linea_5 WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
        )
        """
        
        # Consulta 2: Datos completos
        query2 = """
        SELECT COUNT(*) as total
        FROM (
            SELECT id_fijo FROM linea_1 WHERE direccion_completa IS NOT NULL AND direccion_completa != '' AND accesos IS NOT NULL AND accesos != ''
            UNION ALL
            SELECT id_fijo FROM linea_2 WHERE direccion_completa IS NOT NULL AND direccion_completa != '' AND accesos IS NOT NULL AND accesos != ''
            UNION ALL
            SELECT id_fijo FROM linea_3 WHERE direccion_completa IS NOT NULL AND direccion_completa != '' AND accesos IS NOT NULL AND accesos != ''
            UNION ALL
            SELECT id_fijo FROM linea_4 WHERE direccion_completa IS NOT NULL AND direccion_completa != '' AND accesos IS NOT NULL AND accesos != ''
            UNION ALL
            SELECT id_fijo FROM linea_5 WHERE direccion_completa IS NOT NULL AND direccion_completa != '' AND accesos IS NOT NULL AND accesos != ''
        )
        """
        
        # Consulta 3: Cualquier dato
        query3 = """
        SELECT COUNT(*) as total
        FROM (
            SELECT id_fijo FROM linea_1 WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
            UNION ALL
            SELECT id_fijo FROM linea_2 WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
            UNION ALL
            SELECT id_fijo FROM linea_3 WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
            UNION ALL
            SELECT id_fijo FROM linea_4 WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
            UNION ALL
            SELECT id_fijo FROM linea_5 WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
        )
        """
        
        # Ejecutar consultas
        cursor = conn.cursor()
        
        cursor.execute(query1)
        consulta1 = cursor.fetchone()[0]
        
        cursor.execute(query2)
        consulta2 = cursor.fetchone()[0]
        
        cursor.execute(query3)
        consulta3 = cursor.fetchone()[0]
        
        print(f"Consulta 1 (solo direccion_completa): {consulta1} estaciones")
        print(f"Consulta 2 (datos completos): {consulta2} estaciones")
        print(f"Consulta 3 (cualquier dato): {consulta3} estaciones")
        
        # Mostrar ejemplos de estaciones con datos
        print(f"\nEJEMPLOS DE ESTACIONES CON DATOS:")
        
        # Ejemplo consulta 1
        print(f"\nSegun consulta 1 (solo direccion_completa):")
        ejemplo1 = pd.read_sql_query("""
            SELECT nombre, direccion_completa, accesos, servicios 
            FROM linea_1 
            WHERE direccion_completa IS NOT NULL AND direccion_completa != ''
            LIMIT 3
        """, conn)
        
        for _, row in ejemplo1.iterrows():
            print(f"  - {row['nombre']}: dir='{row['direccion_completa']}', accesos='{row['accesos']}', servicios='{row['servicios']}'")
        
        # Ejemplo consulta 3
        print(f"\nSegun consulta 3 (cualquier dato):")
        ejemplo3 = pd.read_sql_query("""
            SELECT nombre, direccion_completa, accesos, servicios 
            FROM linea_1 
            WHERE direccion_completa IS NOT NULL OR accesos IS NOT NULL OR servicios IS NOT NULL
            LIMIT 3
        """, conn)
        
        for _, row in ejemplo3.iterrows():
            print(f"  - {row['nombre']}: dir='{row['direccion_completa']}', accesos='{row['accesos']}', servicios='{row['servicios']}'")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR verificando consultas: {e}")

def verificar_actualizaciones_recientes():
    """Verifica las últimas actualizaciones de datos"""
    print("\nVERIFICACION DE ACTUALIZACIONES RECIENTES")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Buscar estaciones actualizadas recientemente
        query = """
        SELECT 
            nombre, ultima_actualizacion_detalles, direccion_completa, accesos, servicios
        FROM linea_1 
        WHERE ultima_actualizacion_detalles IS NOT NULL
        ORDER BY ultima_actualizacion_detalles DESC
        LIMIT 5
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            print("Ultimas 5 estaciones actualizadas:")
            for _, row in df.iterrows():
                print(f"  - {row['nombre']}: {row['ultima_actualizacion_detalles']}")
                print(f"    Direccion: '{row['direccion_completa']}'")
                print(f"    Accesos: '{row['accesos']}'")
                print(f"    Servicios: '{row['servicios']}'")
                print()
        else:
            print("No se encontraron estaciones con actualizaciones")
            
        conn.close()
        
    except Exception as e:
        print(f"ERROR verificando actualizaciones: {e}")

def check_database_completeness():
    """
    Analiza la base de datos para encontrar estaciones con datos incompletos
    en las columnas de servicios, accesos o correspondencias.
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró la base de datos en '{DB_PATH}'")
        return

    print(f"✅ Conectando a la base de datos en: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener la lista de todas las tablas de líneas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
    line_tables = [row[0] for row in cursor.fetchall()]

    if not line_tables:
        print("❌ Error: No se encontraron tablas de líneas ('linea_...').")
        conn.close()
        return

    print(f"🔎 Encontradas {len(line_tables)} tablas de líneas. Analizando estaciones...")
    print("-" * 50)

    stations_with_missing_info = {}

    for table in line_tables:
        try:
            cursor.execute(f"SELECT nombre, servicios, accesos, correspondencias FROM {table}")
            stations = cursor.fetchall()
            
            for station in stations:
                nombre, servicios_json, accesos_json, correspondencias_json = station
                
                missing_fields = []
                
                # Chequear 'servicios'
                if not servicios_json or servicios_json.strip() in ('', '[]', '{}', 'null'):
                    missing_fields.append("Servicios")
                    
                # Chequear 'accesos'
                if not accesos_json or accesos_json.strip() in ('', '[]', '{}', 'null'):
                    missing_fields.append("Accesos")

                # Chequear 'correspondencias'
                if not correspondencias_json or correspondencias_json.strip() in ('', '[]', '{}', 'null'):
                    missing_fields.append("Conexiones")
                
                # Si faltan todos, la añadimos a la lista
                if len(missing_fields) == 3:
                    if nombre not in stations_with_missing_info:
                        stations_with_missing_info[nombre] = []
                    stations_with_missing_info[nombre].append(table)

        except sqlite3.OperationalError as e:
            print(f"⚠️  Aviso: La tabla '{table}' podría no tener las columnas esperadas. {e}")

    conn.close()

    # --- Imprimir Resultados ---
    if not stations_with_missing_info:
        print("\n🎉 ¡Enhorabuena! Todas las estaciones en la base de datos tienen datos de servicios, accesos y conexiones.")
    else:
        print(f"\n🚨 Se encontraron {len(stations_with_missing_info)} estaciones a las que les faltan TODOS los datos (Servicios, Accesos y Conexiones):\n")
        
        # Ordenar por nombre de estación
        sorted_stations = sorted(stations_with_missing_info.items())
        
        for station_name, tables in sorted_stations:
            # Extraer solo el número de línea de las tablas
            line_numbers = [t.replace('linea_', 'L') for t in tables]
            print(f"  - {station_name} (En: {', '.join(line_numbers)})")
            
        print("\n--- Fin del Diagnóstico ---")

def check_data_content():
    """
    Analiza el contenido real de los datos en la base de datos.
    Verifica si las columnas tienen datos reales o están vacías.
    """
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró la base de datos en '{DB_PATH}'")
        return

    print(f"✅ Conectando a la base de datos en: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener la lista de todas las tablas de líneas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
    line_tables = [row[0] for row in cursor.fetchall()]

    if not line_tables:
        print("❌ Error: No se encontraron tablas de líneas ('linea_...').")
        conn.close()
        return

    print(f"🔎 Analizando contenido de datos en {len(line_tables)} tablas de líneas...")
    print("=" * 80)

    # Estadísticas globales
    total_stations = 0
    stations_with_services = 0
    stations_with_accesses = 0
    stations_with_connections = 0
    stations_with_all_data = 0
    stations_with_no_data = 0

    # Detalles por tabla
    table_details = {}

    for table in line_tables:
        try:
            cursor.execute(f"SELECT nombre, servicios, accesos, correspondencias FROM {table}")
            stations = cursor.fetchall()
            
            table_stats = {
                'total': len(stations),
                'with_services': 0,
                'with_accesses': 0,
                'with_connections': 0,
                'with_all': 0,
                'with_none': 0,
                'empty_stations': []
            }
            
            for station in stations:
                nombre, servicios_json, accesos_json, correspondencias_json = station
                total_stations += 1
                
                # Verificar si tienen datos reales (no vacíos, no arrays vacíos, no null)
                has_services = servicios_json and servicios_json.strip() not in ('', '[]', '{}', 'null', "'[]'")
                has_accesses = accesos_json and accesos_json.strip() not in ('', '[]', '{}', 'null', "'[]'")
                has_connections = correspondencias_json and correspondencias_json.strip() not in ('', '[]', '{}', 'null', "'[]'")
                
                if has_services:
                    table_stats['with_services'] += 1
                    stations_with_services += 1
                    
                if has_accesses:
                    table_stats['with_accesses'] += 1
                    stations_with_accesses += 1
                    
                if has_connections:
                    table_stats['with_connections'] += 1
                    stations_with_connections += 1
                
                if has_services and has_accesses and has_connections:
                    table_stats['with_all'] += 1
                    stations_with_all_data += 1
                elif not has_services and not has_accesses and not has_connections:
                    table_stats['with_none'] += 1
                    stations_with_no_data += 1
                    table_stats['empty_stations'].append(nombre)

            table_details[table] = table_stats

        except sqlite3.OperationalError as e:
            print(f"⚠️  Error en tabla '{table}': {e}")

    conn.close()

    # --- Imprimir Reporte Detallado ---
    print("\n📊 REPORTE DETALLADO DE CONTENIDO DE DATOS")
    print("=" * 80)
    
    # Estadísticas globales
    print(f"\n🌍 ESTADÍSTICAS GLOBALES:")
    print(f"  • Total de estaciones analizadas: {total_stations}")
    print(f"  • Estaciones con servicios: {stations_with_services} ({stations_with_services/total_stations*100:.1f}%)")
    print(f"  • Estaciones con accesos: {stations_with_accesses} ({stations_with_accesses/total_stations*100:.1f}%)")
    print(f"  • Estaciones con conexiones: {stations_with_connections} ({stations_with_connections/total_stations*100:.1f}%)")
    print(f"  • Estaciones con TODOS los datos: {stations_with_all_data} ({stations_with_all_data/total_stations*100:.1f}%)")
    print(f"  • Estaciones SIN datos: {stations_with_no_data} ({stations_with_no_data/total_stations*100:.1f}%)")
    
    # Detalles por tabla
    print(f"\n📋 DETALLES POR TABLA:")
    for table, stats in sorted(table_details.items()):
        line_name = table.replace('linea_', 'Línea ')
        print(f"\n  {line_name} ({stats['total']} estaciones):")
        print(f"    • Con servicios: {stats['with_services']}/{stats['total']} ({stats['with_services']/stats['total']*100:.1f}%)")
        print(f"    • Con accesos: {stats['with_accesses']}/{stats['total']} ({stats['with_accesses']/stats['total']*100:.1f}%)")
        print(f"    • Con conexiones: {stats['with_connections']}/{stats['total']} ({stats['with_connections']/stats['total']*100:.1f}%)")
        print(f"    • Con todos los datos: {stats['with_all']}/{stats['total']} ({stats['with_all']/stats['total']*100:.1f}%)")
        print(f"    • Sin datos: {stats['with_none']}/{stats['total']} ({stats['with_none']/stats['total']*100:.1f}%)")
        
        if stats['empty_stations']:
            print(f"    • Estaciones vacías: {', '.join(stats['empty_stations'])}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if stations_with_no_data > 0:
        print(f"  ⚠️  Hay {stations_with_no_data} estaciones sin datos. Necesitas ejecutar el scraper para poblarlas.")
    if stations_with_all_data < total_stations * 0.5:
        print(f"  ⚠️  Menos del 50% de las estaciones tienen datos completos. Considera ejecutar el scraper completo.")
    if stations_with_all_data == total_stations:
        print(f"  ✅ ¡Excelente! Todas las estaciones tienen datos completos.")
    
    print("\n" + "=" * 80)

def main():
    """Función principal de diagnóstico"""
    print("DIAGNOSTICO DE DATOS - METRO DE MADRID")
    print("=" * 60)
    
    # Diagnóstico de estación ejemplo
    diagnosticar_estacion_ejemplo()
    
    # Verificar consultas
    verificar_consultas()
    
    # Verificar actualizaciones recientes
    verificar_actualizaciones_recientes()
    
    # Verificar completitud de la base de datos
    check_database_completeness()
    
    # Verificar contenido de los datos
    check_data_content()
    
    print("\nRECOMENDACIONES:")
    print("1. Si los datos estan vacios, el scraper no esta extrayendo correctamente")
    print("2. Si los datos estan ahi pero no se detectan, hay un problema en las consultas")
    print("3. Si las actualizaciones son recientes, el scraper si esta funcionando")

if __name__ == "__main__":
    main() 