#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar los id_modal en la base de datos usando el CSV actualizado
"""

import pandas as pd
import sqlite3
import os

def actualizar_id_modales():
    """Actualiza los id_modal en la base de datos usando el CSV actualizado"""
    
    # Cargar el CSV actualizado
    csv_path = 'datos_clave_estaciones_actualizado.csv'
    if not os.path.exists(csv_path):
        print(f"❌ No se encontró el archivo: {csv_path}")
        return False
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ CSV cargado: {len(df)} estaciones")
        
        # Filtrar estaciones con id_modal
        estaciones_con_id = df[df['id_modal'].notna() & (df['id_modal'] != '')]
        print(f"✅ Estaciones con id_modal: {len(estaciones_con_id)}")
        
        # Conectar a la base de datos
        db_path = 'db/estaciones_fijas_v2.db'
        if not os.path.exists(db_path):
            print(f"❌ No se encontró la base de datos: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'linea_%'")
        tablas = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tablas encontradas: {tablas}")
        
        actualizaciones = 0
        
        # Actualizar cada estación
        for _, estacion in estaciones_con_id.iterrows():
            id_fijo = estacion['id_fijo']
            id_modal = estacion['id_modal']
            tabla_origen = estacion['tabla_origen']
            
            if pd.isna(id_modal) or id_modal == '':
                continue
                
            # Verificar que la tabla existe
            if tabla_origen not in tablas:
                print(f"⚠️  Tabla {tabla_origen} no encontrada para estación {estacion['nombre']}")
                continue
            
            # Actualizar el id_modal en la tabla correspondiente
            try:
                cursor.execute(f"""
                    UPDATE {tabla_origen} 
                    SET id_modal = ? 
                    WHERE id_fijo = ?
                """, (int(id_modal), id_fijo))
                
                if cursor.rowcount > 0:
                    actualizaciones += 1
                    print(f"✅ Actualizado: {estacion['nombre']} (ID: {id_fijo}) -> id_modal: {id_modal}")
                else:
                    print(f"⚠️  No se encontró la estación {estacion['nombre']} (ID: {id_fijo}) en {tabla_origen}")
                    
            except Exception as e:
                print(f"❌ Error actualizando {estacion['nombre']}: {e}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print(f"\n🎉 ACTUALIZACIÓN COMPLETADA")
        print(f"✅ Total de actualizaciones: {actualizaciones}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la actualización: {e}")
        return False

def verificar_actualizacion():
    """Verifica que la actualización se realizó correctamente"""
    print("\n🔍 Verificando actualización...")
    
    try:
        # Cargar CSV para comparar
        df_csv = pd.read_csv('datos_clave_estaciones_actualizado.csv')
        
        # Conectar a la base de datos
        conn = sqlite3.connect('db/estaciones_fijas_v2.db')
        
        # Verificar algunas estaciones que antes no tenían id_modal
        estaciones_problema = ['Laguna', 'Carpetana', 'Opañel', 'Usera', 'Arganzuela – Planetario']
        
        for nombre in estaciones_problema:
            # Buscar en CSV
            estacion_csv = df_csv[df_csv['nombre'] == nombre]
            if not estacion_csv.empty:
                id_modal_csv = estacion_csv.iloc[0]['id_modal']
                tabla_origen = estacion_csv.iloc[0]['tabla_origen']
                
                # Buscar en BD
                query = f"SELECT id_modal FROM {tabla_origen} WHERE nombre = ?"
                cursor = conn.execute(query, (nombre,))
                result = cursor.fetchone()
                
                if result:
                    id_modal_bd = result[0]
                    if id_modal_bd == id_modal_csv:
                        print(f"✅ {nombre}: id_modal = {id_modal_bd}")
                    else:
                        print(f"❌ {nombre}: CSV={id_modal_csv}, BD={id_modal_bd}")
                else:
                    print(f"⚠️  {nombre}: No encontrada en BD")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando actualización de id_modal...")
    
    if actualizar_id_modales():
        verificar_actualizacion()
    else:
        print("❌ La actualización falló") 