#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DESCARGADOR DE MODELOS 3D DE ESTACIONES
========================================

Script para descargar automáticamente los modelos 3D de estaciones
desde http://estacions.albertguillaumes.cat/img/madrid/
"""

import os
import requests
import time
import json
from pathlib import Path
import pandas as pd
from urllib.parse import urljoin, quote

class DescargadorModelos3D:
    def __init__(self):
        self.base_url = "http://estacions.albertguillaumes.cat/img/madrid/"
        self.output_dir = Path("static/model_3D")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def normalizar_nombre_estacion(self, nombre):
        """Normaliza el nombre de la estación para el formato de URL"""
        if not nombre:
            return ""
        
        # Normalizar caracteres especiales
        nombre = nombre.lower()
        nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        nombre = nombre.replace('ü', 'u').replace('ç', 'c')
        
        # Eliminar caracteres especiales y espacios
        nombre = ''.join(c for c in nombre if c.isalnum() or c.isspace())
        nombre = nombre.replace(' ', '_')
        
        return nombre
    
    def obtener_estaciones_desde_csv(self):
        """Obtiene la lista de estaciones desde el CSV de datos clave"""
        try:
            df = pd.read_csv('datos_clave_estaciones.csv')
            estaciones = []
            
            for _, row in df.iterrows():
                estacion = {
                    'nombre': row['nombre'],
                    'linea': row['linea'],
                    'id_fijo': row['id_fijo']
                }
                estaciones.append(estacion)
            
            print(f"✅ Cargadas {len(estaciones)} estaciones desde CSV")
            return estaciones
            
        except Exception as e:
            print(f"❌ Error cargando CSV: {e}")
            return []
    
    def crear_directorios_linea(self, linea):
        """Crea el directorio para una línea específica"""
        linea_dir = self.output_dir / f"linea_{linea}"
        linea_dir.mkdir(parents=True, exist_ok=True)
        return linea_dir
    
    def descargar_imagen(self, url, output_path):
        """Descarga una imagen desde la URL"""
        try:
            print(f"🔍 Descargando: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Descargada: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error descargando {url}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error guardando {output_path}: {e}")
            return False
    
    def descargar_modelo_estacion(self, estacion):
        """Descarga el modelo 3D de una estación específica"""
        nombre = estacion['nombre']
        linea = estacion['linea']
        
        # Normalizar nombre para URL
        nombre_normalizado = self.normalizar_nombre_estacion(nombre)
        if not nombre_normalizado:
            print(f"⚠️ Nombre de estación inválido: {nombre}")
            return False
        
        # Crear directorio de línea
        linea_dir = self.crear_directorios_linea(linea)
        
        # Construir URL y ruta de salida
        url = urljoin(self.base_url, f"{nombre_normalizado}.png")
        output_path = linea_dir / f"{nombre_normalizado}.png"
        
        # Verificar si ya existe
        if output_path.exists():
            print(f"⏭️ Ya existe: {output_path}")
            return True
        
        # Descargar imagen
        success = self.descargar_imagen(url, output_path)
        
        # Pausa para no sobrecargar el servidor
        time.sleep(0.5)
        
        return success
    
    def descargar_todos_los_modelos(self):
        """Descarga todos los modelos 3D disponibles"""
        print("🚀 Iniciando descarga de modelos 3D...")
        print(f"📁 Directorio de salida: {self.output_dir}")
        
        # Obtener estaciones
        estaciones = self.obtener_estaciones_desde_csv()
        if not estaciones:
            print("❌ No se pudieron obtener las estaciones")
            return
        
        # Estadísticas
        total_estaciones = len(estaciones)
        descargadas = 0
        errores = 0
        
        print(f"📊 Total de estaciones a procesar: {total_estaciones}")
        
        # Procesar cada estación
        for i, estacion in enumerate(estaciones, 1):
            print(f"\n[{i}/{total_estaciones}] Procesando: {estacion['nombre']} (Línea {estacion['linea']})")
            
            if self.descargar_modelo_estacion(estacion):
                descargadas += 1
            else:
                errores += 1
        
        # Resumen final
        print(f"\n🎉 Descarga completada!")
        print(f"📊 Resumen:")
        print(f"   - Total procesadas: {total_estaciones}")
        print(f"   - Descargadas: {descargadas}")
        print(f"   - Errores: {errores}")
        print(f"   - Tasa de éxito: {(descargadas/total_estaciones)*100:.1f}%")
    
    def descargar_estaciones_especificas(self, nombres_estaciones):
        """Descarga modelos 3D de estaciones específicas"""
        print(f"🎯 Descargando estaciones específicas: {nombres_estaciones}")
        
        estaciones = self.obtener_estaciones_desde_csv()
        estaciones_filtradas = []
        
        for estacion in estaciones:
            if estacion['nombre'].lower() in [n.lower() for n in nombres_estaciones]:
                estaciones_filtradas.append(estacion)
        
        if not estaciones_filtradas:
            print("❌ No se encontraron las estaciones especificadas")
            return
        
        print(f"📊 Estaciones encontradas: {len(estaciones_filtradas)}")
        
        for estacion in estaciones_filtradas:
            print(f"\n🎯 Descargando: {estacion['nombre']} (Línea {estacion['linea']})")
            self.descargar_modelo_estacion(estacion)
    
    def verificar_modelos_existentes(self):
        """Verifica qué modelos 3D ya están descargados"""
        print("🔍 Verificando modelos 3D existentes...")
        
        estaciones = self.obtener_estaciones_desde_csv()
        existentes = 0
        faltantes = 0
        
        for estacion in estaciones:
            nombre_normalizado = self.normalizar_nombre_estacion(estacion['nombre'])
            linea_dir = self.output_dir / f"linea_{estacion['linea']}"
            modelo_path = linea_dir / f"{nombre_normalizado}.png"
            
            if modelo_path.exists():
                existentes += 1
                print(f"✅ {estacion['nombre']} (Línea {estacion['linea']})")
            else:
                faltantes += 1
                print(f"❌ {estacion['nombre']} (Línea {estacion['linea']}) - FALTANTE")
        
        print(f"\n📊 Resumen de verificación:")
        print(f"   - Modelos existentes: {existentes}")
        print(f"   - Modelos faltantes: {faltantes}")
        print(f"   - Total: {existentes + faltantes}")

def main():
    """Función principal"""
    descargador = DescargadorModelos3D()
    
    print("🏗️ DESCARGADOR DE MODELOS 3D DE ESTACIONES")
    print("=" * 50)
    
    while True:
        print("\n📋 Opciones disponibles:")
        print("1. Descargar todos los modelos 3D")
        print("2. Descargar estaciones específicas")
        print("3. Verificar modelos existentes")
        print("4. Salir")
        
        opcion = input("\n🎯 Selecciona una opción (1-4): ").strip()
        
        if opcion == "1":
            descargador.descargar_todos_los_modelos()
        elif opcion == "2":
            nombres = input("📝 Introduce nombres de estaciones separados por comas: ").strip()
            if nombres:
                estaciones_list = [n.strip() for n in nombres.split(",")]
                descargador.descargar_estaciones_especificas(estaciones_list)
        elif opcion == "3":
            descargador.verificar_modelos_existentes()
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida. Inténtalo de nuevo.")

if __name__ == "__main__":
    main() 