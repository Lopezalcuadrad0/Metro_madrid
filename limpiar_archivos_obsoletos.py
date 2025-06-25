#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

def limpiar_archivos_obsoletos():
    """Limpia archivos obsoletos después de crear el Sistema v5.0"""
    
    archivos_a_borrar = [
        # Sistemas antiguos
        "timing/timing_artificial_completo.json",
        "timing/timing_completo_v3.json", 
        "timing/timing_optimizado.json",
        "timing/datos_metro_completos_con_linea3_final.json",
        "timing/ids_y_lineas_estaciones.txt",
        "timing/tiempos_entre_estaciones.txt",
        
        # Archivos duplicados
        "ids_y_lineas_estaciones.txt",
        "tiempos_entre_estaciones.txt", 
        "nombres_estaciones.txt",
        
        # Scripts obsoletos
        "generar_timing_artificial.py",
        "generar_timing_completo.py",
        "crear_timing_optimizado.py",
        "calculadora_definitiva.py",
        "crear_calculadora_todas_estaciones.py",
        "crear_calculadora_completa.py", 
        "generar_calculadora_con_datos_reales.py",
        "anadir_estaciones_faltantes.py",
        
        # Calculadoras obsoletas
        "calculadora_metro_definitiva.html",
        "calculadora_metro_todas.html",
        "calculadora_metro_completa.html",
        "calculadora_metro_final.html", 
        "calculadora_metro_avanzada.html",
        "calculadora_metro.html",
        
        # Scripts de verificación
        "verificar_codigos_linea3.py",
        "verificar_estaciones_faltantes.py",
        "verificar_conexiones.py",
        "debug_conexiones.py",
        "analizar_trayectos.py",
        
        # Resultados de verificaciones
        "verificacion_codigos_linea3.txt",
        "verificacion_estaciones_faltantes.json",
        "resumen_estaciones_faltantes.txt",
        "linea3_completa_final.txt",
        "resumen_linea3_añadida.txt", 
        "tiempos_actualizados_con_linea3.txt",
        "resumen_datos_completos.txt",
        
        # Scripts de rutas fallidos
        "add_calc_route.py",
        "public_route_fix.py",
        "import_routes_fix.py", 
        "quick_route_fix.py",
        "simple_calc_route.py",
        "routes_missing.py",
        
        # Backups y archivos vacíos
        "app_backup_duplicated.py",
        "app_backup.py",
        "estaciones_fijas_v2.db",
        
        # Archivo gigante problemático
        "secuencia_estaciones.json"
    ]
    
    print("🧹 LIMPIANDO ARCHIVOS OBSOLETOS - Sistema Metro Madrid v5.0")
    print("=" * 70)
    
    total_size = 0
    files_deleted = 0
    files_not_found = 0
    
    for archivo in archivos_a_borrar:
        try:
            if os.path.exists(archivo):
                size = os.path.getsize(archivo)
                total_size += size
                os.remove(archivo)
                files_deleted += 1
                print(f"✅ Borrado: {archivo} ({size/1024:.1f} KB)")
            else:
                files_not_found += 1
                print(f"⚠️  No encontrado: {archivo}")
        except Exception as e:
            print(f"❌ Error borrando {archivo}: {e}")
    
    # Limpiar __pycache__ 
    try:
        if os.path.exists("__pycache__"):
            shutil.rmtree("__pycache__")
            print(f"✅ Borrado: __pycache__/ (directorio completo)")
            files_deleted += 1
    except Exception as e:
        print(f"❌ Error borrando __pycache__: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 RESUMEN DE LIMPIEZA:")
    print(f"🗑️  Archivos borrados: {files_deleted}")
    print(f"❓ Archivos no encontrados: {files_not_found}")
    print(f"💾 Espacio liberado: {total_size/1024/1024:.1f} MB")
    
    print(f"\n✨ ARCHIVOS MANTENIDOS (Sistema v5.0):")
    archivos_importantes = [
        "timing/metro_madrid_v5.json - Sistema principal v5.0",
        "generar_timing_avanzado.py - Generador v5.0", 
        "demo_algoritmos_v5.py - Demo y testing",
        "test_algoritmos_avanzados.py - Suite de testing",
        "calculadora_metro_v5.html - Calculadora moderna",
        "lectura/SISTEMA_V5_RESUMEN.md - Documentación",
        "datos_clave_estaciones_definitivo.csv - Datos base",
        "timing/periodos.csv - Horarios base",
        "app.py - Aplicación Flask principal"
    ]
    
    for archivo in archivos_importantes:
        print(f"   ✅ {archivo}")
    
    print(f"\n🎉 ¡LIMPIEZA COMPLETADA!")
    print(f"📁 Sistema consolidado en {files_deleted} archivos menos")
    print(f"🚀 Sistema Metro Madrid v5.0 optimizado y listo")

if __name__ == '__main__':
    respuesta = input("⚠️ ¿Confirmas borrar todos los archivos obsoletos? (s/N): ")
    if respuesta.lower() in ['s', 'si', 'sí', 'yes', 'y']:
        limpiar_archivos_obsoletos()
    else:
        print("❌ Operación cancelada. No se borraron archivos.") 