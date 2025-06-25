#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def verificar_columnas_bd():
    """Verifica qué columnas existen en las tablas de la base de datos actual"""
    print("=== VERIFICANDO COLUMNAS DE LA BASE DE DATOS ACTUAL ===")
    
    conn = sqlite3.connect('../db/estaciones_fijas_v2.db')
    cursor = conn.cursor()
    
    # Obtener todas las tablas de líneas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
    lineas = [row[0] for row in cursor.fetchall()]
    
    print(f"Tablas encontradas: {len(lineas)}")
    
    # Verificar columnas de la primera tabla para ver la estructura
    if lineas:
        primera_linea = lineas[0]
        print(f"\n📋 Estructura de {primera_linea}:")
        
        cursor.execute(f"PRAGMA table_info({primera_linea})")
        columnas = cursor.fetchall()
        
        for col in columnas:
            cid, nombre, tipo, not_null, default_value, pk = col
            print(f"  - {nombre} ({tipo}) {'PRIMARY KEY' if pk else ''}")
        
        # Verificar si existen columnas específicas
        nombres_columnas = [col[1] for col in columnas]
        
        print(f"\n🔍 Verificación de columnas específicas:")
        columnas_importantes = ['id_fijo', 'id_modal', 'nombre', 'url', 'latitud', 'longitud', 
                               'orden', 'ultima_actualizacion', 'accesos', 'servicios', 
                               'correspondencias', 'direccion_completa']
        
        for col in columnas_importantes:
            existe = col in nombres_columnas
            print(f"  - {col}: {'✅' if existe else '❌'}")
        
        # Mostrar algunos datos de ejemplo
        print(f"\n📊 Datos de ejemplo de {primera_linea}:")
        cursor.execute(f"SELECT * FROM {primera_linea} LIMIT 1")
        ejemplo = cursor.fetchone()
        
        if ejemplo:
            for i, valor in enumerate(ejemplo):
                nombre_col = columnas[i][1] if i < len(columnas) else f"col_{i}"
                print(f"  - {nombre_col}: {valor}")
    
    conn.close()

if __name__ == "__main__":
    verificar_columnas_bd() 