#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSPECTOR DE DATOS DE CERCANÍAS
===============================

Inspecciona la estructura del archivo cercanias_completo.json
"""

import json

def inspeccionar_cercanias():
    """Inspecciona el archivo de Cercanías"""
    
    print("🔍 INSPECCIONANDO ARCHIVO DE CERCANÍAS")
    print("=" * 50)
    
    try:
        print("📖 Cargando archivo...")
        with open('static/data/cercanias_completo.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ Archivo cargado exitosamente")
        print("📊 ESTRUCTURA GENERAL:")
        print(f"  Secciones: {list(data.keys())}")
        
        # Inspeccionar metadatos
        if 'metadatos' in data:
            meta = data['metadatos']
            print(f"\n📋 METADATOS:")
            for key, value in meta.items():
                print(f"  {key}: {value}")
        
        # Inspeccionar estaciones para encontrar campos disponibles
        if 'estaciones' in data:
            print(f"\n🚉 ESTACIONES:")
            print(f"  Líneas: {list(data['estaciones'].keys())}")
            
            # Buscar estaciones en cualquier línea que tenga datos
            sample_station = None
            for line_key, stations in data['estaciones'].items():
                if stations and len(stations) > 0:
                    sample_station = stations[0]
                    print(f"\n🔍 MUESTRA DE ESTACIÓN (de {line_key}):")
                    print(f"  Número de estaciones en {line_key}: {len(stations)}")
                    break
            
            if sample_station:
                props = sample_station.get('properties', {})
                print(f"\n📝 CAMPOS DISPONIBLES EN ESTACIONES:")
                for field, value in props.items():
                    print(f"  {field}: {value} (tipo: {type(value).__name__})")
            else:
                print("  ⚠️ No se encontraron estaciones con datos")
        
        # Inspeccionar tramos
        if 'tramos' in data:
            print(f"\n🛤️ TRAMOS:")
            print(f"  Líneas: {list(data['tramos'].keys())}")
            
            # Mostrar detalle de tramos por línea
            for line_key, tramos in data['tramos'].items():
                if tramos:
                    print(f"  {line_key}: {len(tramos)} tramos")
                    
                    # Mostrar campos de un tramo de ejemplo
                    if line_key != 'unknown' and tramos:
                        sample_tramo = tramos[0]
                        props = sample_tramo.get('properties', {})
                        print(f"    Campos en tramo de {line_key}: {list(props.keys())}")
                        
                        # Mostrar valores específicos del tramo
                        for field in ['NUMEROLINEAUSUARIO', 'CODIGOGESTIONLINEA', 'LINEA', 'DENOMINACION']:
                            if field in props:
                                print(f"      {field}: {props[field]}")
        
        # Inspeccionar andenes
        if 'andenes' in data:
            print(f"\n🚏 ANDENES:")
            print(f"  Líneas: {list(data['andenes'].keys())}")
            for line_key, andenes in data['andenes'].items():
                if andenes:
                    print(f"  {line_key}: {len(andenes)} andenes")
        
        print(f"\n✅ Inspección completada")
        
    except FileNotFoundError:
        print("❌ Error: Archivo cercanias_completo.json no encontrado")
        print("💡 Ejecute primero: python herramientas/generar_cercanias_completo.py")
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    inspeccionar_cercanias() 