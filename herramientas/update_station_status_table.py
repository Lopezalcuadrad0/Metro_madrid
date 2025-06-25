#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar la tabla station_status con las columnas que faltan
"""

import sqlite3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_station_status_table():
    """Actualiza la tabla station_status con las columnas que faltan"""
    
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='station_status'")
        if not cursor.fetchone():
            logging.info("📋 Creando tabla station_status...")
            cursor.execute("""
                CREATE TABLE station_status (
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
            logging.info("✅ Tabla station_status creada")
        else:
            logging.info("📋 Tabla station_status ya existe, verificando columnas...")
            
            # Obtener columnas existentes
            cursor.execute("PRAGMA table_info(station_status)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Columnas que deben existir
            required_columns = {
                'accesos': 'TEXT',
                'calles': 'TEXT', 
                'servicios': 'TEXT',
                'zona_tarifaria': 'TEXT'
            }
            
            # Agregar columnas que faltan
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    logging.info(f"➕ Agregando columna: {col_name}")
                    cursor.execute(f"ALTER TABLE station_status ADD COLUMN {col_name} {col_type}")
                else:
                    logging.info(f"✅ Columna {col_name} ya existe")
        
        conn.commit()
        conn.close()
        
        logging.info("✅ Tabla station_status actualizada correctamente")
        
        # Mostrar estructura final
        show_final_structure()
        
    except Exception as e:
        logging.error(f"❌ Error actualizando tabla: {e}")

def show_final_structure():
    """Muestra la estructura final de la tabla station_status"""
    
    try:
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(station_status)")
        columns = cursor.fetchall()
        
        print("\n📋 Estructura final de station_status:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Mostrar algunos registros de ejemplo
        cursor.execute("SELECT * FROM station_status ORDER BY timestamp DESC LIMIT 3")
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n📊 Últimos 3 registros:")
            for row in rows:
                print(f"  {row}")
        else:
            print("\n📊 No hay registros en la tabla station_status")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"❌ Error mostrando estructura: {e}")

if __name__ == "__main__":
    update_station_status_table() 