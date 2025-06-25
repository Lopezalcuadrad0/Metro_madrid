# 🚇 Sistema Inteligente de Web Scraping - Metro de Madrid

## 📋 Descripción

Sistema avanzado de web scraping en tiempo real para estaciones del Metro de Madrid que:

- **Carga datos automáticamente** al hacer clic en estaciones
- **Guarda información en cache** para evitar consultas repetidas
- **Diferenciación inteligente** entre datos estáticos y dinámicos
- **Actualización automática** de información que cambia frecuentemente
- **Integración completa** con la aplicación Flask

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **`IntelligentMetroScraper`** - Clase principal del scraper
2. **`MetroScraperAPI`** - API para integración con Flask
3. **`RealtimeMetroScraper`** - Cliente JavaScript para frontend
4. **Base de datos SQLite** - Cache inteligente
5. **Archivo CSV** - Almacenamiento persistente

### Flujo de Datos

```
Usuario hace clic → JavaScript detecta → API Flask → Verificar Cache → Scraping Web → Guardar Cache → Actualizar CSV → Mostrar datos
```

## 🚀 Características

### ✨ Funcionalidades Principales

- **Scraping en Tiempo Real**: Carga datos automáticamente al interactuar con estaciones
- **Cache Inteligente**: Evita consultas repetidas usando base de datos SQLite
- **Diferenciación de Datos**:
  - **Estáticos** (24h TTL): Nombre, accesos, correspondencias, servicios
  - **Dinámicos** (5min TTL): Estado ascensores, última actualización
- **Actualización Automática**: Solo actualiza datos que han cambiado
- **Procesamiento Asíncrono**: No bloquea la interfaz durante el scraping
- **Notificaciones en Tiempo Real**: Feedback visual del estado de las operaciones

### 📊 Datos Extraídos

#### Datos Estáticos
- Nombre de la estación
- Información de accesos (vestíbulo, dirección)
- Servicios disponibles
- Zona tarifaria
- Correspondencias con otras líneas
- Conexiones (Cercanías, autobuses, Metro Ligero)
- Horarios de servicio

#### Datos Dinámicos
- Estado de ascensores (funcionando/averiado/mantenimiento)
- Última actualización de información
- Timestamp de scraping

## 📁 Estructura de Archivos

```
herramientas_csv/
├── intelligent_scraper.py      # Sistema principal de scraping
├── generated_stations_data.py  # Datos fijos de estaciones
└── ...

static/
├── js/
│   └── realtime_scraper.js     # Cliente JavaScript
└── css/
    └── realtime_scraper.css    # Estilos del sistema

datos_estaciones/
├── scraper_cache.db           # Base de datos SQLite (cache)
├── estaciones_completas.csv   # Datos persistentes
└── ...

templates/
└── header.html                # Header con integración del sistema
```

## 🔧 Instalación y Configuración

### 1. Dependencias

```bash
pip install requests beautifulsoup4 sqlite3
```

### 2. Configuración Inicial

```python
from herramientas_csv.intelligent_scraper import IntelligentMetroScraper

# Inicializar scraper
scraper = IntelligentMetroScraper()

# Configurar TTL personalizado (opcional)
scraper.static_data_ttl = 24 * 60 * 60  # 24 horas
scraper.dynamic_data_ttl = 5 * 60       # 5 minutos
```

### 3. Integración con Flask

```python
from flask import Flask
from herramientas_csv.intelligent_scraper import IntelligentMetroScraper, MetroScraperAPI

app = Flask(__name__)
scraper = IntelligentMetroScraper()
scraper_api = MetroScraperAPI(scraper)

@app.route('/api/station/<line_number>/<station_id>')
def get_station_data(line_number, station_id):
    return scraper_api.get_station_data(line_number, station_id)
```

## 🎯 Uso del Sistema

### Uso Básico

```python
# Obtener datos de una estación
result = scraper.scrape_station_data('2', '255')

if result:
    static_data = result['static']
    dynamic_data = result['dynamic']
    from_cache = result['from_cache']
    
    print(f"Estación: {static_data['name']}")
    print(f"Estado ascensores: {dynamic_data['elevator_status']}")
    print(f"Desde cache: {from_cache}")
```

### Uso Avanzado

```python
# Forzar actualización
result = scraper.scrape_station_data('2', '255', force_refresh=True)

# Actualización en lote
stations = [
    {'line_number': '1', 'station_id': '1'},
    {'line_number': '1', 'station_id': '2'},
    {'line_number': '2', 'station_id': '255'}
]
scraper.batch_update_stations(stations)

# Procesamiento asíncrono
def callback(result):
    print(f"Datos recibidos: {result}")

scraper.request_station_data_async('2', '255', callback)
```

### Uso en JavaScript

```javascript
// El sistema se inicializa automáticamente
// Al hacer clic en una estación, se cargan los datos automáticamente

// Forzar actualización manual
window.metroScraper.refreshStation('2', '255');

// Obtener estado del cache
const cacheStatus = window.metroScraper.getCacheStatus();
```

## 🔌 API Endpoints

### GET `/api/station/<line_number>/<station_id>`
Obtiene datos de una estación (usa cache si está disponible)

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "static": {
      "station_id": "255",
      "line_number": "2",
      "name": "Las Rosas",
      "accesses": [...],
      "services": [...],
      "correspondences": [...]
    },
    "dynamic": {
      "elevator_status": "Funcionando",
      "last_update": "Actualizado hace 5 minutos",
      "scraped_at": "2024-01-15T10:30:00"
    }
  },
  "from_cache": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

### GET `/api/station/<line_number>/<station_id>/refresh`
Fuerza la actualización de datos de una estación

### GET `/api/cache/status`
Obtiene estadísticas del cache

**Respuesta:**
```json
{
  "success": true,
  "cache_stats": {
    "total_cached_stations": 45,
    "recently_updated": 12,
    "cache_file": "datos_estaciones/scraper_cache.db",
    "csv_file": "datos_estaciones/estaciones_completas.csv"
  }
}
```

## 🧪 Pruebas

### Ejecutar Pruebas

```bash
python test_scraper.py
```

### Pruebas Incluidas

- ✅ Scraping de estaciones individuales
- ✅ Verificación de cache
- ✅ Actualización forzada
- ✅ Generación de CSV
- ✅ Estadísticas del sistema

## 📈 Monitoreo y Estadísticas

### Métricas Disponibles

- **Estaciones en cache**: Total de estaciones almacenadas
- **Actualizaciones recientes**: Estaciones actualizadas en la última hora
- **Tiempo de respuesta**: Velocidad de las consultas
- **Tasa de éxito**: Porcentaje de scraping exitoso

### Logs del Sistema

```
🔍 Scraping estación 255 de línea 2
✅ Datos obtenidos del cache para estación 255
✅ Datos actualizados para estación 255
📊 Datos cargados (desde cache)
```

## 🔒 Consideraciones de Seguridad

### Rate Limiting
- Pausa de 1 segundo entre consultas en lote
- Timeout de 10 segundos por consulta
- User-Agent personalizado para evitar bloqueos

### Manejo de Errores
- Reintentos automáticos en caso de fallo
- Fallback a datos del cache
- Notificaciones de error en tiempo real

## 🚀 Optimizaciones

### Performance
- **Cache inteligente**: Evita consultas innecesarias
- **Procesamiento asíncrono**: No bloquea la interfaz
- **Compresión de datos**: Almacenamiento eficiente
- **Lazy loading**: Carga datos solo cuando se necesitan

### Escalabilidad
- **Base de datos SQLite**: Ligera y eficiente
- **Cola de procesamiento**: Manejo de múltiples requests
- **TTL configurable**: Control de frescura de datos

## 🔧 Configuración Avanzada

### Personalizar TTL

```python
scraper = IntelligentMetroScraper()

# Datos estáticos (nombres, accesos, etc.)
scraper.static_data_ttl = 24 * 60 * 60  # 24 horas

# Datos dinámicos (estado ascensores, etc.)
scraper.dynamic_data_ttl = 5 * 60       # 5 minutos
```

### Configurar User-Agent

```python
scraper.session.headers.update({
    'User-Agent': 'Tu-Aplicacion/1.0 (contacto@tuapp.com)'
})
```

### Personalizar URLs

```python
def custom_url_generator(line_number, station_id):
    return f"https://tu-dominio.com/linea/{line_number}/estacion/{station_id}"

scraper.get_station_url = custom_url_generator
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de conexión**
   - Verificar conectividad a internet
   - Comprobar que la web de Metro Madrid esté accesible

2. **Datos no se actualizan**
   - Verificar TTL configurado
   - Forzar actualización manual

3. **Cache corrupto**
   - Eliminar archivo `scraper_cache.db`
   - Reiniciar aplicación

4. **JavaScript no funciona**
   - Verificar que `realtime_scraper.js` esté cargado
   - Comprobar consola del navegador

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

scraper = IntelligentMetroScraper()
# Ahora verás logs detallados
```

## 📞 Soporte

Para problemas o preguntas sobre el sistema de scraping:

1. Revisar logs de la aplicación
2. Ejecutar `test_scraper.py` para diagnóstico
3. Verificar estado del cache en `/api/cache/status`

## 🔄 Actualizaciones Futuras

- [ ] Soporte para múltiples fuentes de datos
- [ ] Machine Learning para predicción de cambios
- [ ] API REST completa
- [ ] Dashboard de administración
- [ ] Exportación a múltiples formatos
- [ ] Integración con APIs oficiales

---

**¡El sistema está listo para usar! 🚇✨** 