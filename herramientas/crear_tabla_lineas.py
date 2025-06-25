#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CREAR TABLA LINEAS - Metro de Madrid
====================================

Añade la tabla 'lineas' a la base de datos relacional para completar la estructura.
"""

import sqlite3
import os

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'estaciones_relacional.db')

def crear_tabla_lineas():
    """Crea la tabla lineas en la base de datos relacional"""
    
    print("🚇 CREANDO TABLA LINEAS EN BASE DE DATOS RELACIONAL")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Crear tabla lineas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lineas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_linea INTEGER UNIQUE NOT NULL,
                nombre_linea TEXT NOT NULL,
                color_linea TEXT,
                descripcion TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar datos de las líneas del Metro de Madrid
        lineas_data = [
            (1, 'Línea 1', '#1E3A8A', 'Pinar de Chamartín - Valdecarros'),
            (2, 'Línea 2', '#DC2626', 'Las Rosas - Cuatro Caminos'),
            (3, 'Línea 3', '#F59E0B', 'Villaverde Alto - Moncloa'),
            (4, 'Línea 4', '#7C3AED', 'Argüelles - Pinar de Chamartín'),
            (5, 'Línea 5', '#059669', 'Alameda de Osuna - Casa de Campo'),
            (6, 'Línea 6', '#0EA5E9', 'Circular'),
            (7, 'Línea 7', '#F97316', 'Hospital del Henares - Pitis'),
            (8, 'Línea 8', '#EC4899', 'Nuevos Ministerios - Aeropuerto T4'),
            (9, 'Línea 9', '#8B5CF6', 'Paco de Lucía - Arganda del Rey'),
            (10, 'Línea 10', '#06B6D4', 'Hospital Infanta Sofía - Puerta del Sur'),
            (11, 'Línea 11', '#84CC16', 'Plaza Elíptica - La Fortuna'),
            (12, 'Línea 12', '#F59E0B', 'MetroSur'),
            (13, 'Ramal', '#6B7280', 'Ópera - Príncipe Pío')
        ]
        
        for linea in lineas_data:
            cursor.execute('''
                INSERT OR REPLACE INTO lineas (numero_linea, nombre_linea, color_linea, descripcion)
                VALUES (?, ?, ?, ?)
            ''', linea)
        
        conn.commit()
        print("✅ Tabla 'lineas' creada y poblada correctamente")
        
        # Verificar que se creó correctamente
        cursor.execute("SELECT * FROM lineas ORDER BY numero_linea")
        lineas = cursor.fetchall()
        
        print(f"\n📊 LÍNEAS CREADAS ({len(lineas)}):")
        for linea in lineas:
            id, numero, nombre, color, desc, fecha = linea
            print(f"  - Línea {numero}: {nombre} ({color})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando tabla lineas: {e}")
        return False

def verificar_estructura_completa():
    """Verifica que la estructura de la base de datos esté completa"""
    print("\n🔍 VERIFICANDO ESTRUCTURA COMPLETA")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [row[0] for row in cursor.fetchall()]
        
        print("📋 Tablas encontradas:")
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"  - {tabla}: {count} registros")
        
        # Verificar relaciones
        print(f"\n🔗 Verificando relaciones:")
        
        # Estaciones por línea
        cursor.execute("""
            SELECT l.nombre_linea, COUNT(e.id_fijo) as num_estaciones
            FROM lineas l
            LEFT JOIN estaciones e ON l.numero_linea = CAST(e.linea AS INTEGER)
            GROUP BY l.numero_linea
            ORDER BY l.numero_linea
        """)
        
        relaciones = cursor.fetchall()
        print("  📍 Estaciones por línea:")
        for linea, count in relaciones:
            print(f"    - {linea}: {count} estaciones")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

if __name__ == "__main__":
    print("🚇 CREANDO TABLA LINEAS PARA BASE DE DATOS RELACIONAL")
    print("=" * 60)
    
    if crear_tabla_lineas():
        verificar_estructura_completa()
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Error en el proceso") 