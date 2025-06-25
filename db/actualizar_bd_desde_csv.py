#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar la base de datos con los datos corregidos del CSV
"""

import sqlite3
import pandas as pd
import re
from datetime import datetime

def limpiar_nombre(nombre):
    """Limpia el nombre de la estación para hacerlo compatible con la base de datos"""
    # Eliminar caracteres especiales y normalizar
    nombre_limpio = re.sub(r'[^\w\s]', '', nombre)
    nombre_limpio = nombre_limpio.strip()
    return nombre_limpio

def actualizar_base_datos_desde_csv():
    """Actualiza la base de datos desde el archivo CSV definitivo"""
    
    # Conectar a la base de datos
    conn = sqlite3.connect('db/estaciones_fijas_v2.db')
    cursor = conn.cursor()
    
    try:
        # Leer el archivo CSV definitivo
        print("📖 Leyendo archivo datos_clave_estaciones_definitivo.csv...")
        df = pd.read_csv('datos_clave_estaciones_definitivo.csv')
        
        print(f"📊 Total estaciones en CSV: {len(df)}")
        
        # Verificar que tenemos las columnas necesarias
        columnas_requeridas = ['id_fijo', 'nombre', 'orden', 'linea']
        for col in columnas_requeridas:
            if col not in df.columns:
                print(f"❌ Error: Falta la columna '{col}' en el CSV")
                return
        
        # Obtener lista de tablas de líneas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
        tablas_lineas = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Tablas de líneas encontradas: {len(tablas_lineas)}")
        
        # Estadísticas por línea
        print("\n📈 Estadísticas por línea:")
        for linea in sorted(df['linea'].unique()):
            count = len(df[df['linea'] == linea])
            print(f"🚇 Línea {linea}: {count} estaciones")
        
        # Procesar cada línea
        total_actualizadas = 0
        total_errores = 0
        
        for linea in sorted(df['linea'].unique()):
            if linea == 'nan' or linea == '':
                continue
                
            print(f"\n🔄 Procesando Línea {linea}...")
            
            # Obtener estaciones de esta línea
            estaciones_linea = df[df['linea'] == linea].copy()
            
            # Buscar la tabla correspondiente
            tabla_linea = f"linea_{linea}"
            if tabla_linea not in tablas_lineas:
                print(f"⚠️ Tabla {tabla_linea} no encontrada, saltando...")
                continue
            
            # Verificar estructura de la tabla
            cursor.execute(f"PRAGMA table_info({tabla_linea})")
            columnas_tabla = [row[1] for row in cursor.fetchall()]
            
            print(f"📋 Columnas en {tabla_linea}: {columnas_tabla}")
            
            # Actualizar cada estación de esta línea
            for idx, estacion in estaciones_linea.iterrows():
                try:
                    id_fijo = estacion['id_fijo']
                    nombre = estacion['nombre']
                    orden = estacion['orden']
                    
                    # Limpiar nombre para búsqueda
                    nombre_limpio = limpiar_nombre(nombre)
                    
                    # Buscar la estación en la tabla
                    if 'nombre_limpio' in columnas_tabla:
                        # Si existe la columna nombre_limpio, usarla
                        cursor.execute(f"""
                            UPDATE {tabla_linea} 
                            SET orden_en_linea = ?, id_fijo = ?
                            WHERE nombre_limpio = ?
                        """, (orden, id_fijo, nombre_limpio))
                    else:
                        # Si no existe, usar nombre directamente
                        cursor.execute(f"""
                            UPDATE {tabla_linea} 
                            SET orden_en_linea = ?, id_fijo = ?
                            WHERE nombre = ?
                        """, (orden, id_fijo, nombre))
                    
                    filas_afectadas = cursor.rowcount
                    if filas_afectadas > 0:
                        total_actualizadas += 1
                        print(f"✅ {nombre} (ID: {id_fijo}) - Orden: {orden}")
                    else:
                        total_errores += 1
                        print(f"❌ No se encontró: {nombre} (ID: {id_fijo})")
                        
                except Exception as e:
                    total_errores += 1
                    print(f"❌ Error actualizando {nombre}: {str(e)}")
            
            # Commit después de cada línea
            conn.commit()
        
        # Estadísticas finales
        print(f"\n{'='*60}")
        print("📊 ESTADÍSTICAS FINALES")
        print(f"{'='*60}")
        print(f"✅ Estaciones actualizadas: {total_actualizadas}")
        print(f"❌ Errores: {total_errores}")
        print(f"📋 Total procesadas: {len(df)}")
        
        # Verificar algunas actualizaciones específicas
        print(f"\n🔍 Verificando actualizaciones específicas:")
        
        # Verificar Línea 1
        cursor.execute("SELECT nombre, orden_en_linea, id_fijo FROM linea_1 WHERE nombre IN ('Alto del Arenal', 'Portazgo', 'Puente de Vallecas')")
        resultados_l1 = cursor.fetchall()
        for nombre, orden, id_fijo in resultados_l1:
            print(f"✅ L1 - {nombre}: orden {orden}, ID {id_fijo}")
        
        # Verificar Línea 3
        cursor.execute("SELECT nombre, orden_en_linea, id_fijo FROM linea_3 WHERE nombre IN ('Callao', 'Sol')")
        resultados_l3 = cursor.fetchall()
        for nombre, orden, id_fijo in resultados_l3:
            print(f"✅ L3 - {nombre}: orden {orden}, ID {id_fijo}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando actualización de base de datos desde CSV...")
    print(f"⏰ Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    actualizar_base_datos_desde_csv()
    
    print("=" * 60)
    print("🏁 Proceso completado!") 