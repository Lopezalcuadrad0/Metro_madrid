# 🚇 Herramientas para Datos del Metro de Madrid

## 📁 Estructura del Proyecto

### `/herramientas_csv/` - Scripts y herramientas
- **`csv_generator_tool.py`** - Herramienta interactiva principal para crear archivos CSV
- **`create_station_csv.py`** - Generador básico de archivos CSV
- **`create_linea_2_data.py`** - Datos específicos de la Línea 2
- **`scrape_metro_official_v2.py`** - Webscraper mejorado (requiere acceso web)
- **`scrape_metro_official.py`** - Webscraper básico
- **`scrape_stations.py`** - Scraper original
- **`create_station_data_from_html.py`** - Procesador de datos HTML
- **`generated_stations_data.py`** - Datos generados automáticamente

### `/datos_estaciones/` - Archivos de datos
- **`linea_1_estaciones.csv`** - Datos de ejemplo Línea 1
- **`linea_2_estaciones.csv`** - Datos completos Línea 2 (7 estaciones)
- **`linea_5_estaciones.csv`** - Datos de ejemplo Línea 5
- **`plantilla_estacion.csv`** - Plantilla para rellenar manualmente
- **`todas_estaciones_v2.json`** - Datos en formato JSON

## 🛠️ Cómo usar las herramientas

### 1. Herramienta Interactiva Principal
```bash
cd herramientas_csv
python csv_generator_tool.py
```

**Opciones disponibles:**
- **Opción 1:** Crear ejemplo Línea 1
- **Opción 2:** Crear ejemplo Línea 5  
- **Opción 3:** Crear datos interactivamente
- **Opción 4:** Ver archivos existentes
- **Opción 5:** Salir

### 2. Generar datos de una línea específica
```bash
cd herramientas_csv
python create_linea_2_data.py
```

### 3. Procesar datos HTML
```bash
cd herramientas_csv
python create_station_data_from_html.py
```

## 📊 Estructura de los archivos CSV

Cada archivo CSV contiene las siguientes columnas:

| Campo | Descripción |
|-------|-------------|
| `estacion_id` | ID único de la estación |
| `nombre` | Nombre de la estación |
| `correspondencias` | Otras líneas de metro (separadas por ;) |
| `conexiones` | Autobuses, cercanías, etc. |
| `servicios` | Ascensores, escaleras, etc. (separados por ;) |
| `accesos` | JSON con vestíbulo, nombre y dirección |
| `zona_tarifaria` | Zona A, B, etc. |
| `estado_ascensores` | Estado actual de ascensores/escaleras |
| `ultima_actualizacion` | Fecha/hora de última actualización |
| `horario` | Horario de apertura |

## 💡 Ejemplo de uso

1. **Ejecutar la herramienta principal:**
   ```bash
   python herramientas_csv/csv_generator_tool.py
   ```

2. **Seleccionar opción 3 (crear interactivamente)**

3. **Introducir datos de la estación:**
   - ID: `301`
   - Nombre: `Plaza de España`
   - Correspondencias: `Línea 3; Línea 10`
   - Servicios: `Estación accesible; Ascensores; Escaleras mecánicas`
   - Zona: `A`

4. **Añadir accesos:**
   - Vestíbulo: `Plaza de España`
   - Nombre: `Gran Vía`
   - Dirección: `Gran Vía, 1`

5. **El archivo se guardará como `linea_X_estaciones.csv`**

## 🔄 Integración con la aplicación Flask

Los archivos CSV generados se pueden usar en tu aplicación Flask:

```python
import csv
import json

def load_station_data(line_number):
    """Carga datos de estaciones desde CSV"""
    stations = []
    filename = f"datos_estaciones/linea_{line_number}_estaciones.csv"
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convertir JSON de accesos de vuelta a diccionario
            row['accesos'] = json.loads(row['accesos'])
            stations.append(row)
    
    return stations
```

## 📝 Notas importantes

- Los archivos CSV usan codificación UTF-8
- Los accesos se guardan en formato JSON dentro del CSV
- Todos los archivos incluyen encabezados
- La plantilla está disponible para rellenar manualmente
- Los datos se pueden abrir en Excel o Google Sheets

## 🎯 Próximos pasos

1. Usar la herramienta interactiva para crear datos de más líneas
2. Copiar información de la web oficial de Metro de Madrid
3. Generar archivos CSV para todas las líneas
4. Integrar los datos en la aplicación Flask 