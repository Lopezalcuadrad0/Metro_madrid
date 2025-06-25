#!/usr/bin/env python3
import sqlite3

def check_modal_ids():
    """Verifica los id_modal en la base de datos"""
    conn = sqlite3.connect('db/estaciones_fijas_v2.db')
    cursor = conn.cursor()
    
    # Verificar algunas estaciones conocidas
    test_stations = [
        ('linea_1', 'Sol'),
        ('linea_2', 'Sol'),
        ('linea_3', 'Callao'),
        ('linea_4', 'Alonso Martínez'),
        ('linea_5', 'Callao')
    ]
    
    print("🔍 Verificando id_modal en la base de datos:")
    print("=" * 50)
    
    for tabla, nombre in test_stations:
        cursor.execute(f'SELECT id_fijo, nombre, id_modal FROM {tabla} WHERE nombre = ?', (nombre,))
        result = cursor.fetchone()
        
        if result:
            id_fijo, nombre, id_modal = result
            print(f"📍 {tabla}: {nombre}")
            print(f"   ID fijo: {id_fijo}")
            print(f"   ID modal: {id_modal}")
            print(f"   URL que se generaría: https://www.metromadrid.es/es/metro_next_trains/modal/{id_modal}")
            print()
        else:
            print(f"❌ {tabla}: {nombre} - NO ENCONTRADA")
            print()
    
    conn.close()

if __name__ == "__main__":
    check_modal_ids() 