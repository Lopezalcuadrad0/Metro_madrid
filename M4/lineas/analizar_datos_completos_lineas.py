#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALIZAR DATOS COMPLETOS DE TODAS LAS LÍNEAS - Metro de Madrid
============================================================

Analiza todos los archivos datosl*.txt y datosR.txt del directorio M4/lineas/
y extrae información completa de:
- Accesos y vestíbulos con direcciones
- Ascensores y escaleras mecánicas
- Conexiones (Cercanías, autobuses, etc.)
- Servicios disponibles
- Estado de equipos
- Zonas tarifarias
- Horarios de apertura
"""

import sqlite3
import os
import re
import json
import csv
from datetime import datetime
from pathlib import Path
import unicodedata

# Configuración CORREGIDA
DB_PATH = os.path.join(os.path.dirname(__file__),'..', 'db', 'estaciones_fijas_v2.db')
DATOS_LINEAS_PATH = os.path.join(os.path.dirname(__file__),'M4', 'lineas')

class AnalizadorCompletoLineas:
    def __init__(self):
        self.db_path = DB_PATH
        self.datos_path = DATOS_LINEAS_PATH
        self.datos_completos = {}
        
    def obtener_estaciones_reales_bd(self, linea):
        """Obtiene las estaciones reales de la base de datos para una línea"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener estaciones reales de la base de datos
            cursor.execute("""
                SELECT id, idmodal, nombre, linea 
                FROM estaciones 
                WHERE linea = ? 
                ORDER BY orden
            """, (linea,))
            
            estaciones = cursor.fetchall()
            conn.close()
            
            return [(row[0], row[1], row[2]) for row in estaciones]
            
        except Exception as e:
            print(f"❌ Error obteniendo estaciones de BD para línea {linea}: {e}")
            return []
    
    def extraer_seccion_estacion(self, contenido, nombre_estacion):
        """Extrae la sección completa de una estación del contenido"""
        # Buscar la estación con patrones más flexibles
        patrones = [
            rf"{re.escape(nombre_estacion)}\s*icono",
            rf"{re.escape(nombre_estacion)}\s*Zona tarifaria",
            rf"{re.escape(nombre_estacion)}\s*\n",
            rf"{re.escape(nombre_estacion)}\s*$",
            # Patrón más flexible para capturar variaciones
            rf"{re.escape(nombre_estacion)}\s+",
            rf"{re.escape(nombre_estacion)}\s*"
        ]
        
        inicio = -1
        for patron in patrones:
            match = re.search(patron, contenido, re.IGNORECASE)
            if match:
                inicio = match.start()
                break
        
        if inicio == -1:
            return ""
        
        # Buscar el final de la sección (siguiente estación o fin de archivo)
        # Buscar el siguiente patrón de estación que empiece con mayúscula
        siguiente_patron = r'\n[A-Z][^a-z].*?(?:icono|Zona tarifaria)'
        siguiente_match = re.search(siguiente_patron, contenido[inicio+len(nombre_estacion):])
        
        if siguiente_match:
            fin = inicio + len(nombre_estacion) + siguiente_match.start()
        else:
            fin = len(contenido)
        
        return contenido[inicio:fin]
    
    def extraer_accesos(self, seccion):
        """Extrae información detallada de accesos"""
        accesos = []
        # Buscar sección de accesos delimitada por 'Accesos:' y 'El horario de apertura al público es de'
        accesos_match = re.search(r'Accesos:(.*?)(El horario de apertura al público es de|$)', seccion, re.DOTALL)
        if not accesos_match:
            return accesos
        accesos_texto = accesos_match.group(1)
        # Quitar encabezados y líneas vacías
        lineas = [l.strip() for l in accesos_texto.strip().split('\n') if l.strip() and not l.strip().startswith('VESTÍBULO')]
        i = 0
        while i < len(lineas) - 1:
            linea = lineas[i]
            if '\t' in linea:
                partes = linea.split('\t')
                vestibulo = partes[0].strip()
                nombre_acceso = partes[1].strip()
                direccion = lineas[i+1].strip() if (i+1) < len(lineas) else ''
                accesos.append({
                    'vestibulo': vestibulo,
                    'nombre': nombre_acceso,
                    'direccion': direccion
                })
                i += 2
            else:
                i += 1
        return accesos
    
    def extraer_conexiones(self, seccion):
        """Extrae información de conexiones"""
        conexiones = []
        
        # Buscar sección de conexiones
        conexiones_match = re.search(r'Conexiones:(.*?)(?=\n[A-Z]|$)', seccion, re.DOTALL)
        if not conexiones_match:
            return conexiones
        
        conexiones_texto = conexiones_match.group(1)
        
        # Buscar tipos de conexiones por iconos
        tipos_conexion = {
            'cercanias-renfe': 'Cercanías Renfe',
            'estacion-de-tren': 'Estación de tren',
            'autobuses-interurbanos': 'Autobuses Interurbanos',
            'autobuses-de-largo-recorrido': 'Autobuses de largo recorrido',
            'terminal-autobuses-nocturnos': 'Terminal autobuses nocturnos',
            'cambio-de-tren': 'Cambio de tren'
        }
        
        for icono, nombre in tipos_conexion.items():
            if icono in conexiones_texto:
                conexiones.append({
                    'tipo': nombre,
                    'icono': icono
                })
        
        return conexiones
    
    def extraer_servicios(self, seccion):
        """Extrae información de servicios disponibles"""
        servicios = []
        
        # Buscar sección de servicios
        servicios_match = re.search(r'Servicios:(.*?)(?=\n[A-Z]|$)', seccion, re.DOTALL)
        if not servicios_match:
            return servicios
        
        servicios_texto = servicios_match.group(1)
        
        # Lista de servicios conocidos
        servicios_conocidos = [
            'Estación accesible', 'Ascensores', 'Escaleras mecánicas', 'Desfibrilador',
            'Cobertura móvil', 'Bibliometro', 'Tienda de Metro', 'Parking disuasorio',
            'Estacionamiento de bicicletas', 'Quioscos ONCE', 'Espacio histórico de Metro',
            'Atención al cliente', 'Oficina de gestión TTP', 'Oficina Objetos Perdidos',
            'Cafeterías', 'Tiendas', 'Pasillos rodantes', 'Teléfonos', 'Metroteca',
            'Parking disuasorio gratuito', 'Atención a la tarifa/Validación a la SALIDA'
        ]
        
        for servicio in servicios_conocidos:
            if servicio in servicios_texto:
                servicios.append(servicio)
        
        return servicios
    
    def extraer_estado_equipos(self, seccion):
        """Extrae estado de ascensores y escaleras mecánicas"""
        estado = {
            'ascensores': 'Desconocido',
            'escaleras': 'Desconocido',
            'alertas': []
        }
        
        # Buscar sección de estado
        estado_match = re.search(r'Estado de los ascensores y escaleras mecánicas(.*?)(?=\n[A-Z]|$)', seccion, re.DOTALL)
        if not estado_match:
            return estado
        
        estado_texto = estado_match.group(1)
        
        # Verificar si todo funciona correctamente
        if 'Todas las escaleras mecánicas y/o ascensores funcionan correctamente' in estado_texto:
            estado['ascensores'] = 'Funcionando correctamente'
            estado['escaleras'] = 'Funcionando correctamente'
            return estado
        
        # Buscar problemas específicos
        if 'Lamentamos informarle de alteraciones' in estado_texto:
            # Buscar problemas de ascensores
            problemas_ascensores = re.findall(r'ascensoresAscensores(.*?)(?=\n|$)', estado_texto, re.DOTALL)
            if problemas_ascensores:
                estado['ascensores'] = 'Problemas detectados'
                estado['alertas'].append('Problemas con ascensores')
            
            # Buscar problemas de escaleras
            problemas_escaleras = re.findall(r'escalerasEscaleras mecánicas(.*?)(?=\n|$)', estado_texto, re.DOTALL)
            if problemas_escaleras:
                estado['escaleras'] = 'Problemas detectados'
                estado['alertas'].append('Problemas con escaleras mecánicas')
        
        return estado
    
    def extraer_datos_estacion(self, contenido, nombre_estacion, id_estacion=None, idmodal_estacion=None):
        """Extrae todos los datos de una estación específica"""
        datos = {
            'id': id_estacion,
            'idmodal': idmodal_estacion,
            'nombre': nombre_estacion,
            'zona_tarifaria': '',
            'accesos': [],
            'conexiones': [],
            'servicios': [],
            'estado_equipos': {},
            'accesible': False,
            'horarios': '6:00 a.m. a 1:30 a.m.'
        }
        
        # Extraer sección de la estación
        seccion = self.extraer_seccion_estacion(contenido, nombre_estacion)
        if not seccion:
            return datos
        
        # Extraer zona tarifaria
        zona_match = re.search(r'Zona tarifaria:\s*([A-Z0-9]+)', seccion)
        if zona_match:
            datos['zona_tarifaria'] = zona_match.group(1)
        
        # Verificar accesibilidad
        if 'icono adaptada para discapacitados' in seccion or 'Estación accesible' in seccion:
            datos['accesible'] = True
        
        # Extraer accesos
        datos['accesos'] = self.extraer_accesos(seccion)
        
        # Extraer conexiones
        datos['conexiones'] = self.extraer_conexiones(seccion)
        
        # Extraer servicios
        datos['servicios'] = self.extraer_servicios(seccion)
        
        # Extraer estado de equipos
        datos['estado_equipos'] = self.extraer_estado_equipos(seccion)
        
        return datos
    
    def procesar_archivo_linea(self, archivo_path, numero_linea):
        """Procesa un archivo de datos de línea específica"""
        print(f"📋 Procesando {os.path.basename(archivo_path)}...")
        
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
        except Exception as e:
            print(f"❌ Error leyendo {archivo_path}: {e}")
            return {}
        
        # Lista de estaciones por línea (extraídas de los archivos)
        estaciones_por_linea = {
            '1': ['Pinar de Chamartín', 'Bambú', 'Chamartín', 'Plaza de Castilla', 'Valdeacederas', 
                  'Tetuán', 'Estrecho', 'Alvarado', 'Cuatro Caminos', 'Ríos Rosas', 'Iglesia', 
                  'Bilbao', 'Tribunal', 'Gran Vía', 'Sol', 'Tirso de Molina', 'Antón Martín', 
                  'Estación del Arte', 'Atocha', 'Menéndez Pelayo', 'Pacífico', 'Puente de Vallecas', 
                  'Nueva Numancia', 'Portazgo', 'Buenos Aires', 'Alto del Arenal', 'Miguel Hernández', 
                  'Sierra de Guadalupe', 'Villa de Vallecas', 'Congosto', 'La Gavia', 'Las Suertes', 'Valdecarros'],
            '2': ['Las Rosas', 'Avenida de Guadalajara', 'Alsacia', 'La Almudena', 'La Elipa', 
                  'Ventas', 'Manuel Becerra', 'Goya', 'Príncipe de Vergara', 'Retiro', 'Banco de España', 
                  'Sevilla', 'Sol', 'Ópera', 'Santo Domingo', 'Noviciado', 'San Bernardo', 'Quevedo', 'Canal', 'Cuatro Caminos'],
            '3': ['Villaverde Alto', 'San Cristóbal', 'Villaverde Bajo Cruce', 'Ciudad de los Ángeles', 
                  'San Fermín – Orcasur', 'Hospital 12 de Octubre', 'Almendrales', 'Legazpi', 'Delicias', 
                  'Palos de la Frontera', 'Embajadores', 'Lavapiés', 'Sol', 'Callao', 'Plaza de España', 
                  'Ventura Rodríguez', 'Argüelles', 'Moncloa'],
            '4': ['Argüelles', 'San Bernardo', 'Bilbao', 'Alonso Martínez', 'Colón', 'Serrano', 'Velázquez', 
                  'Goya', 'Lista', 'Diego de León', 'Avenida de América', 'Prosperidad', 'Alfonso XIII', 
                  'Avenida de la Paz', 'Arturo Soria', 'Esperanza', 'Canillas', 'Mar de Cristal', 
                  'San Lorenzo', 'Parque de Santa María', 'Hortaleza', 'Manoteras', 'Pinar de Chamartín'],
            '5': ['Alameda de Osuna', 'El Capricho', 'Canillejas', 'Torre Arias', 'Suanzes', 'Ciudad Lineal', 
                  'Pueblo Nuevo', 'Quintana', 'El Carmen', 'Ventas', 'Diego de León', 'Núñez de Balboa', 
                  'Rubén Darío', 'Alonso Martínez', 'Chueca', 'Gran Vía', 'Callao', 'Ópera', 'La Latina', 
                  'Puerta de Toledo', 'Acacias', 'Pirámides', 'Marqués de Vadillo', 'Urgel', 'Oporto', 
                  'Vista Alegre', 'Carabanchel', 'Eugenia de Montijo', 'Aluche', 'Empalme', 'Campamento', 'Casa de Campo'],
            '6': ['Laguna', 'Carpetana', 'Opañel', 'Plaza Elíptica', 'Usera', 'Legazpi', 'Arganzuela – Planetario', 
                  'Méndez Álvaro', 'Pacífico', 'Conde de Casal', 'Sainz de Baranda', 'O\'Donnell', 'Manuel Becerra', 
                  'Diego de León', 'Avenida de América', 'República Argentina', 'Nuevos Ministerios', 'Cuatro Caminos', 
                  'Guzmán el Bueno', 'Vicente Aleixandre', 'Ciudad Universitaria', 'Moncloa', 'Argüelles', 
                  'Príncipe Pío', 'Puerta del Ángel', 'Alto de Extremadura', 'Lucero'],
            '7': ['Hospital del Henares', 'Henares', 'Jarama', 'San Fernando', 'La Rambla', 'Coslada Central', 
                  'Barrio del Puerto', 'Estadio Metropolitano', 'Las Musas', 'San Blas', 'Simancas', 'García Noblejas', 
                  'Ascao', 'Pueblo Nuevo', 'Barrio de la Concepción', 'Quintana', 'El Carmen', 'Ventas', 
                  'Diego de León', 'Núñez de Balboa', 'Rubén Darío', 'Alonso Martínez', 'Chueca', 'Gran Vía', 
                  'Callao', 'Ópera', 'La Latina', 'Puerta de Toledo', 'Acacias', 'Pirámides', 'Marqués de Vadillo', 
                  'Urgel', 'Oporto', 'Vista Alegre', 'Carabanchel', 'Eugenia de Montijo', 'Aluche', 'Empalme', 
                  'Campamento', 'Casa de Campo'],
            '8': ['Aeropuerto T1-T2-T3', 'Aeropuerto T4', 'Barajas', 'Mar de Cristal', 'Pinar del Rey', 'Colombia', 
                  'Nuevos Ministerios', 'Gregorio Marañón', 'Alonso Martínez', 'Colón', 'Serrano', 'Velázquez', 
                  'Goya', 'Lista', 'Diego de León', 'Avenida de América', 'Prosperidad', 'Alfonso XIII', 
                  'Avenida de la Paz', 'Arturo Soria', 'Esperanza', 'Canillas', 'Mar de Cristal', 'San Lorenzo', 
                  'Parque de Santa María', 'Hortaleza', 'Manoteras', 'Pinar de Chamartín'],
            '9': ['Arganda del Rey', 'La Poveda', 'Rivas Vaciamadrid', 'Rivas Futura', 'Rivas Urbanizaciones', 
                   'Puerta de Arganda', 'San Cipriano', 'Vicálvaro', 'Valdebernardo', 'Pavones', 'Artilleros', 
                   'Vinateros', 'Estrella', 'Sainz de Baranda', 'Ibiza', 'Príncipe de Vergara', 'Núñez de Balboa', 
                   'Avenida de América', 'Cruz del Rayo', 'Concha Espina', 'Colombia', 'Pío XII', 'Duque de Pastrana', 
                   'Plaza de Castilla', 'Ventilla', 'Barrio del Pilar', 'Herrera Oria', 'Mirasierra', 'Paco de Lucía'],
            '10': ['Hospital Infanta Sofía', 'Reyes Católicos', 'Baunatal', 'Manuel de Falla', 'Marqués de la Valdavia', 
                   'La Moraleja', 'La Granja', 'Ronda de la Comunicación', 'Las Tablas', 'Montecarmelo', 'Tres Olivos', 
                   'Fuencarral', 'Begoña', 'Chamartín', 'Plaza de Castilla', 'Cuzco', 'Santiago Bernabéu', 
                   'Nuevos Ministerios', 'Gregorio Marañón', 'Alonso Martínez', 'Tribunal', 'Plaza de España', 
                   'Príncipe Pío', 'Lago', 'Batán', 'Casa de Campo', 'Colonia Jardín', 'Aviación Española', 
                   'Cuatro Vientos', 'Joaquín Vilumbrales', 'Puerta del Sur'],
            '11': ['Plaza Elíptica', 'Abrantes', 'Pan Bendito', 'San Francisco', 'Carabanchel Alto', 'La Peseta', 'La Fortuna'],
            '12': ['Puerta del Sur', 'Parque de Lisboa', 'Alcorcón Central', 'Parque Oeste', 'Universidad Rey Juan Carlos', 
                   'Móstoles Central', 'Pradillo', 'Hospital de Móstoles', 'Manuela Malasaña', 'Loranca', 
                   'Hospital de Fuenlabrada', 'Parque Europa', 'Fuenlabrada Central', 'Parque de los Estados', 
                   'Arroyo Culebro', 'Conservatorio', 'Alonso de Mendoza', 'Getafe Central', 'Juan de la Cierva', 
                   'El Casar', 'Los Espartales', 'El Bercial', 'El Carrascal', 'Julián Besteiro', 'Casa del Reloj', 
                   'Hospital Severo Ochoa', 'Leganés Central', 'San Nicasio'],
            'R': ['Ópera', 'Príncipe Pío']
        }
        
        estaciones_linea = estaciones_por_linea.get(numero_linea, [])
        datos_linea = {}
        
        for estacion in estaciones_linea:
            datos = self.extraer_datos_estacion(contenido, estacion)
            # Incluir todas las estaciones, no solo las que tienen datos
            datos_linea[estacion] = datos
            print(f"  ✅ {estacion}: {len(datos['accesos'])} accesos, {len(datos['conexiones'])} conexiones")
        
        return datos_linea
    
    def actualizar_base_datos(self, datos_completos):
        """Actualiza la base de datos con los datos extraídos"""
        print("\n🗄️ Actualizando base de datos...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla de datos detallados si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datos_detallados_estaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    linea TEXT NOT NULL,
                    nombre_estacion TEXT NOT NULL,
                    zona_tarifaria TEXT,
                    accesos_json TEXT,
                    conexiones_json TEXT,
                    servicios_json TEXT,
                    estado_equipos_json TEXT,
                    accesible BOOLEAN,
                    horarios TEXT,
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(linea, nombre_estacion)
                )
            """)
            
            # Limpiar datos anteriores
            cursor.execute("DELETE FROM datos_detallados_estaciones")
            
            # Insertar nuevos datos
            for linea, estaciones in datos_completos.items():
                for nombre_estacion, datos in estaciones.items():
                    cursor.execute("""
                        INSERT INTO datos_detallados_estaciones 
                        (linea, nombre_estacion, zona_tarifaria, accesos_json, conexiones_json, 
                         servicios_json, estado_equipos_json, accesible, horarios)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        linea,
                        nombre_estacion,
                        datos['zona_tarifaria'],
                        json.dumps(datos['accesos'], ensure_ascii=False),
                        json.dumps(datos['conexiones'], ensure_ascii=False),
                        json.dumps(datos['servicios'], ensure_ascii=False),
                        json.dumps(datos['estado_equipos'], ensure_ascii=False),
                        datos['accesible'],
                        datos['horarios']
                    ))
            
            conn.commit()
            print(f"✅ Base de datos actualizada con {len(datos_completos)} líneas")
            
            # Mostrar resumen
            cursor.execute("SELECT linea, COUNT(*) FROM datos_detallados_estaciones GROUP BY linea")
            resumen = cursor.fetchall()
            print("\n📊 Resumen de datos insertados:")
            for linea, count in resumen:
                print(f"  - Línea {linea}: {count} estaciones")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error actualizando base de datos: {e}")
    
    def generar_archivos_json(self, datos_completos):
        """Genera archivos JSON con los datos extraídos"""
        print("\n📄 Generando archivos JSON...")
        
        # Crear directorio de salida
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'datos_estaciones')
        os.makedirs(output_dir, exist_ok=True)
        
        # Archivo principal con todos los datos
        archivo_principal = os.path.join(output_dir, 'datos_completos_todas_lineas.json')
        with open(archivo_principal, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=2)
        print(f"✅ Archivo principal: {archivo_principal}")
        
        # Archivos individuales por línea
        for linea, estaciones in datos_completos.items():
            archivo_linea = os.path.join(output_dir, f'datos_linea_{linea}.json')
            with open(archivo_linea, 'w', encoding='utf-8') as f:
                json.dump(estaciones, f, ensure_ascii=False, indent=2)
            print(f"✅ Línea {linea}: {archivo_linea}")
        
        # Archivo de resumen estadístico
        resumen = {}
        for linea, estaciones in datos_completos.items():
            total_accesos = sum(len(est['accesos']) for est in estaciones.values())
            total_conexiones = sum(len(est['conexiones']) for est in estaciones.values())
            total_servicios = sum(len(est['servicios']) for est in estaciones.values())
            estaciones_accesibles = sum(1 for est in estaciones.values() if est['accesible'])
            
            resumen[linea] = {
                'total_estaciones': len(estaciones),
                'total_accesos': total_accesos,
                'total_conexiones': total_conexiones,
                'total_servicios': total_servicios,
                'estaciones_accesibles': estaciones_accesibles,
                'estaciones_con_problemas': sum(1 for est in estaciones.values() 
                                              if est['estado_equipos'].get('alertas'))
            }
        
        archivo_resumen = os.path.join(output_dir, 'resumen_completo_lineas.json')
        with open(archivo_resumen, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"✅ Resumen: {archivo_resumen}")
        
        # Generar archivo de texto con estadísticas
        archivo_stats = os.path.join(output_dir, 'estadisticas_lineas.txt')
        with open(archivo_stats, 'w', encoding='utf-8') as f:
            f.write("ESTADÍSTICAS COMPLETAS DEL METRO DE MADRID\n")
            f.write("=" * 50 + "\n\n")
            
            total_estaciones = sum(resumen[linea]['total_estaciones'] for linea in resumen)
            total_accesos = sum(resumen[linea]['total_accesos'] for linea in resumen)
            total_conexiones = sum(resumen[linea]['total_conexiones'] for linea in resumen)
            total_accesibles = sum(resumen[linea]['estaciones_accesibles'] for linea in resumen)
            
            f.write(f"RESUMEN GENERAL:\n")
            f.write(f"- Total de líneas: {len(resumen)}\n")
            f.write(f"- Total de estaciones: {total_estaciones}\n")
            f.write(f"- Total de accesos: {total_accesos}\n")
            f.write(f"- Total de conexiones: {total_conexiones}\n")
            f.write(f"- Estaciones accesibles: {total_accesibles}\n\n")
            
            f.write("DETALLE POR LÍNEA:\n")
            f.write("-" * 30 + "\n")
            for linea in sorted(resumen.keys()):
                stats = resumen[linea]
                f.write(f"Línea {linea}:\n")
                f.write(f"  - Estaciones: {stats['total_estaciones']}\n")
                f.write(f"  - Accesos: {stats['total_accesos']}\n")
                f.write(f"  - Conexiones: {stats['total_conexiones']}\n")
                f.write(f"  - Accesibles: {stats['estaciones_accesibles']}\n")
                f.write(f"  - Con problemas: {stats['estaciones_con_problemas']}\n\n")
        
        print(f"✅ Estadísticas: {archivo_stats}")
    
    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo de todos los archivos"""
        print("🚇 ANÁLISIS COMPLETO DE TODAS LAS LÍNEAS DEL METRO")
        print("=" * 60)
        
        if not os.path.exists(self.datos_path):
            print(f"❌ No se encuentra el directorio: {self.datos_path}")
            return
        
        # Buscar todos los archivos de datos
        archivos_datos = []
        for archivo in os.listdir(self.datos_path):
            if archivo.startswith('datosl') and archivo.endswith('.txt'):
                numero_linea = archivo[6:-4]  # Así obtienes '1', '2', ..., '10', '11', '12'
                archivos_datos.append((archivo, numero_linea))
            elif archivo == 'datosR.txt':
                archivos_datos.append((archivo, 'R'))
        
        print(f"📁 Encontrados {len(archivos_datos)} archivos de datos:")
        for archivo, linea in archivos_datos:
            print(f"  - {archivo} (Línea {linea})")
        
        datos_completos = {}
        
        # Procesar cada archivo
        for archivo, numero_linea in archivos_datos:
            archivo_path = os.path.join(self.datos_path, archivo)
            datos_linea = self.procesar_archivo_linea(archivo_path, numero_linea)
            if datos_linea:
                datos_completos[numero_linea] = datos_linea
        
        print(f"\n✅ Procesamiento completado: {len(datos_completos)} líneas analizadas")
        
        # Actualizar base de datos
        self.actualizar_base_datos(datos_completos)
        
        # Generar archivos JSON
        self.generar_archivos_json(datos_completos)
        
        print("\n🎉 Análisis completo finalizado!")
        print(f"📊 Se procesaron {len(datos_completos)} líneas con datos detallados")

def cargar_estaciones_desde_csv(csv_path):
    """Carga las estaciones desde el CSV definitivo con los IDs correctos"""
    estaciones_por_linea = {}
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            linea = row['linea']
            if linea.isdigit():
                linea = int(linea)
            # Si no es dígito, lo dejamos como string (por ejemplo, 'Ramal')
            if linea not in estaciones_por_linea:
                estaciones_por_linea[linea] = []
            
            estaciones_por_linea[linea].append({
                'station_name': row['nombre'],
                'station_id': int(row['id_fijo']),
                'id_modal': row['id_modal'] if row['id_modal'] else None,
                'url': row['url'],
                'zona': row['zona'],
                'accesible': row['accesible'] == '1' if row['accesible'] else False,
                'orden': int(row['orden'])
            })
    
    # Ordenar estaciones por orden dentro de cada línea
    for linea in estaciones_por_linea:
        estaciones_por_linea[linea].sort(key=lambda x: x['orden'])
    
    return estaciones_por_linea

def normalizar_nombre(nombre):
    """Normaliza un nombre para comparación flexible (sin tildes, minúsculas, sin espacios extras)"""
    nombre = nombre.lower().strip()
    nombre = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
    nombre = nombre.replace('  ', ' ')
    return nombre

def extraer_accesos_por_orden(contenido_archivo, estaciones):
    """Por orden de estaciones del CSV, cada "Accesos:" encontrado corresponde a la siguiente estación"""
    lineas = contenido_archivo.split('\n')
    accesos_por_estacion = []
    estacion_actual = 0
    
    i = 0
    while i < len(lineas) and estacion_actual < len(estaciones):
        linea = lineas[i].strip()
        
        if 'Accesos:' in linea:
            print(f"  📋 Encontrado 'Accesos:' para estación {estacion_actual + 1}: '{estaciones[estacion_actual]['station_name']}'")
            
            # Buscar la línea "VESTÍBULO\tNOMBRE DE ACCESO"
            j = i + 1
            while j < len(lineas) and not re.search(r'VESTÍBULO.*NOMBRE DE ACCESO', lineas[j].strip()):
                j += 1
            
            if j < len(lineas):
                # Extraer el bloque de accesos
                bloque = []
                while j < len(lineas):
                    linea_actual = lineas[j].strip()
                    bloque.append(linea_actual)
                    if 'El horario de apertura al público es de' in linea_actual:
                        break
                    j += 1
                
                if bloque:
                    accesos = procesar_bloque_accesos(bloque)
                    print(f"  ✅ Extraídos {len(accesos)} accesos")
                else:
                    accesos = []
                    print(f"  ⚠️  Bloque de accesos vacío")
            else:
                accesos = []
                print(f"  ⚠️  No se encontró 'VESTÍBULO\tNOMBRE DE ACCESO'")
            
            accesos_por_estacion.append(accesos)
            estacion_actual += 1
        
        i += 1
    
    # Si quedan estaciones sin accesos, añadir listas vacías
    while estacion_actual < len(estaciones):
        print(f"  ⚠️  Estación {estacion_actual + 1}: '{estaciones[estacion_actual]['station_name']}' sin sección de accesos")
        accesos_por_estacion.append([])
        estacion_actual += 1
    
    return accesos_por_estacion

def procesar_bloque_accesos(bloque):
    """Procesa un bloque de líneas para extraer accesos. Añade logs para debuggear."""
    accesos = []
    i = 0
    
    print(f"    🔍 Procesando bloque de {len(bloque)} líneas:")
    for idx, linea in enumerate(bloque):
        print(f"      [{idx}] {linea}")
    
    while i < len(bloque):
        linea = bloque[i].strip()
        
        # Buscar líneas que contengan tabulador (VESTÍBULO\tNOMBRE DE ACCESO)
        # PERO IGNORAR el encabezado "VESTÍBULO\tNOMBRE DE ACCESO"
        if '\t' in linea and not linea.startswith('VESTÍBULO\tNOMBRE DE ACCESO'):
            partes = linea.split('\t')
            if len(partes) >= 2:
                vestibulo = partes[0].strip()
                nombre_acceso = partes[1].strip()
                
                # Buscar la dirección en la siguiente línea
                direccion = ""
                if i + 1 < len(bloque):
                    siguiente_linea = bloque[i + 1].strip()
                    # Si la siguiente línea no tiene tabulador y no está vacía, es la dirección
                    if siguiente_linea and not '\t' in siguiente_linea and not siguiente_linea.startswith(('El horario', 'VESTÍBULO', 'NOMBRE DE ACCESO')):
                        direccion = siguiente_linea
                        i += 1  # Saltar la línea de dirección
                
                acceso = {
                    'vestibulo': vestibulo,
                    'nombre': nombre_acceso,
                    'direccion': direccion
                }
                accesos.append(acceso)
                print(f"    ✅ Acceso encontrado: {vestibulo} -> {nombre_acceso} -> {direccion}")
        
        i += 1
    
    print(f"    📊 Total accesos extraídos: {len(accesos)}")
    return accesos

def analizar_datos_completos():
    """Analiza todos los archivos de datos de líneas usando el CSV definitivo como base"""
    # Rutas
    base_path = Path(__file__).parent.parent  # Subir un nivel para llegar a la raíz del proyecto
    datos_path = base_path /  "lineas" /"M4"/ "lineas"
    csv_path = base_path.parent / "datos_clave_estaciones_definitivo.csv"  # CSV en la raíz del proyecto
    
    print(f"📁 Usando CSV: {csv_path}")
    print(f"📁 Datos de líneas: {datos_path}")
    
    if not csv_path.exists():
        print(f"❌ No se encuentra el CSV: {csv_path}")
        return
    
    # Cargar estaciones desde CSV definitivo
    estaciones_por_linea = cargar_estaciones_desde_csv(csv_path)
    
    resultado_completo = {}
    
    # Procesar cada línea
    for numero_linea, estaciones in estaciones_por_linea.items():
        print(f"\n🚇 Procesando línea {numero_linea} con {len(estaciones)} estaciones...")
        
        # Determinar nombre del archivo
        if numero_linea == 12:
            nombre_archivo = "datosl12.txt"
        elif numero_linea == "Ramal":
            nombre_archivo = "datosR.txt"
        else:
            nombre_archivo = f"datosl{numero_linea}.txt"
        
        archivo_path = datos_path / nombre_archivo
        
        if not archivo_path.exists():
            print(f"⚠️  Archivo {nombre_archivo} no encontrado en {archivo_path}")
            continue
        
        # Leer contenido del archivo
        try:
            with open(archivo_path, 'r', encoding='utf-8') as file:
                contenido = file.read()
        except Exception as e:
            print(f"❌ Error leyendo {nombre_archivo}: {e}")
            continue
        
        # Extraer accesos por orden
        accesos_por_estacion = extraer_accesos_por_orden(contenido, estaciones)
        
        # Crear estructura de datos para la línea
        datos_linea = {
            'numero_linea': numero_linea,
            'estaciones': []
        }
        
        # Asociar cada estación con sus accesos
        for i, estacion in enumerate(estaciones):
            datos_estacion = {
                'station_name': estacion['station_name'],
                'station_id': estacion['station_id'],
                'id_modal': estacion['id_modal'],
                'url': estacion['url'],
                'zona': estacion['zona'],
                'accesible': estacion['accesible'],
                'orden': estacion['orden'],
                'accesos': accesos_por_estacion[i] if i < len(accesos_por_estacion) else []
            }
            datos_linea['estaciones'].append(datos_estacion)
        
        resultado_completo[f"linea_{numero_linea}"] = datos_linea
        
        print(f"✅ Línea {numero_linea}: {len(estaciones)} estaciones procesadas")
    
    # Crear directorio de salida si no existe
    output_dir = base_path / "datos_estaciones"
    output_dir.mkdir(exist_ok=True)
    
    # Guardar resultado
    output_path = output_dir / "datos_completos_todas_lineas.json"
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(resultado_completo, file, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 Análisis completado. Resultado guardado en: {output_path}")
    
    # Generar también los CSV de accesos y conexiones
    generar_csv_accesos_conexiones(resultado_completo, output_dir)
    
    # Mostrar estadísticas
    total_estaciones = sum(len(estaciones) for estaciones in estaciones_por_linea.values())
    total_accesos = sum(
        len(estacion['accesos']) 
        for linea in resultado_completo.values() 
        for estacion in linea['estaciones']
    )
    
    print(f"\n📊 Estadísticas:")
    print(f"   - Total de líneas: {len(resultado_completo)}")
    print(f"   - Total de estaciones: {total_estaciones}")
    print(f"   - Total de accesos: {total_accesos}")

def generar_csv_accesos_conexiones(resultado_completo, output_dir):
    """Genera los CSV de accesos y conexiones desde los datos completos"""
    print("\n📄 Generando CSV de accesos y conexiones...")
    
    # CSV de accesos
    accesos_data = []
    for linea_key, datos_linea in resultado_completo.items():
        numero_linea = datos_linea['numero_linea']
        for estacion in datos_linea['estaciones']:
            for acceso in estacion['accesos']:
                accesos_data.append({
                    'id_estacion': estacion['station_id'],
                    'linea': numero_linea,
                    'nombre_estacion': estacion['station_name'],
                    'vestibulo': acceso['vestibulo'],
                    'nombre_acceso': acceso['nombre'],
                    'direccion': acceso['direccion']
                })
    
    accesos_path = output_dir / "accesos_completos.csv"
    with open(accesos_path, 'w', encoding='utf-8', newline='') as file:
        if accesos_data:
            fieldnames = accesos_data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(accesos_data)
    
    print(f"✅ Accesos: {accesos_path} ({len(accesos_data)} registros)")
    
    # CSV de conexiones (por ahora vacío, se puede expandir después)
    conexiones_data = []
    for linea_key, datos_linea in resultado_completo.items():
        numero_linea = datos_linea['numero_linea']
        for estacion in datos_linea['estaciones']:
            conexiones_data.append({
                'id_estacion': estacion['station_id'],
                'linea': numero_linea,
                'nombre_estacion': estacion['station_name'],
                'id_modal': estacion['id_modal'],
                'url': estacion['url'],
                'zona': estacion['zona'],
                'accesible': estacion['accesible']
            })
    
    conexiones_path = output_dir / "conexiones_completas.csv"
    with open(conexiones_path, 'w', encoding='utf-8', newline='') as file:
        if conexiones_data:
            fieldnames = conexiones_data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(conexiones_data)
    
    print(f"✅ Conexiones: {conexiones_path} ({len(conexiones_data)} registros)")

def main():
    """Función principal"""
    print("🚇 Iniciando análisis de datos completos del Metro de Madrid...")
    print("=" * 60)
    
    # Ejecutar el nuevo análisis basado en CSV
    analizar_datos_completos()
    
    print("\n" + "=" * 60)
    print("🎉 Proceso completado exitosamente!")

if __name__ == "__main__":
    main()