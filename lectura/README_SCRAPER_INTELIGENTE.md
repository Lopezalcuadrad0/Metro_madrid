# 🚇 Metro Scraper Inteligente

Sistema de scraping inteligente para el Metro de Madrid con cache automático y actualizaciones selectivas.

## 🎯 Características

- **Cache inteligente** con fecha de modificación
- **Actualización selectiva** de 9 estaciones aleatorias cada hora
- **Scraping de trenes en tiempo real** (cuando el metro esté abierto)
- **Base de datos SQLite** para almacenamiento eficiente
- **Sistema de prioridades** para estaciones importantes
- **Configuración flexible** de parámetros

## 📁 Archivos del Sistema

### Core
- `metro_scraper_inteligente.py` - Scraper principal con cache inteligente
- `auto_updater.py` - Actualizaciones automáticas cada hora
- `test_realtime_trains.py` - Pruebas de trenes en tiempo real
- `config_scraper.py` - Configuración del sistema

### Base de Datos
- `datos_estaciones/metro_cache_inteligente.db` - Base de datos SQLite

### Logs
- `metro_scraper_inteligente.log` - Log del scraper
- `auto_updater.log` - Log del auto updater
- `realtime_trains_test.log` - Log de pruebas de trenes

## 🚀 Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Crear directorio de datos:**
```bash
mkdir -p datos_estaciones
```

## 📖 Uso

### 1. Configuración Inicial
```bash
python config_scraper.py
```
- Ver configuración actual
- Actualizar parámetros
- Ver estadísticas

### 2. Ejecutar Scraper Inteligente
```bash
python metro_scraper_inteligente.py
```
- Actualiza 9 estaciones aleatorias
- Exporta datos a CSV
- Muestra estadísticas

### 3. Auto Updater (Recomendado)
```bash
python auto_updater.py
```
- Actualizaciones automáticas cada hora
- Ejecuta una actualización inicial
- Logs detallados

### 4. Probar Trenes en Tiempo Real
```bash
python test_realtime_trains.py
```
- **Usar cuando el metro esté abierto (mañana)**
- Prueba scraping de trenes
- Muestra datos en tiempo real

## ⚙️ Configuración

### Parámetros Configurables

| Parámetro | Valor por Defecto | Descripción |
|-----------|-------------------|-------------|
| `update_interval_hours` | 1 | Intervalo entre actualizaciones |
| `stations_per_update` | 9 | Estaciones por actualización |
| `metro_operating_hours_start` | 06:00 | Inicio horario metro |
| `metro_operating_hours_end` | 01:30 | Fin horario metro |

### Estructura de la Base de Datos

#### Tabla `station_cache`
- `station_id` - ID de la estación
- `line_number` - Número de línea
- `station_name` - Nombre de la estación
- `url` - URL de la página
- `tariff_zone` - Zona tarifaria
- `schedule` - Horarios
- `station_status` - Estado de la estación
- `adapted_for_disabled` - Adaptación para discapacitados
- `accesses` - Accesos (JSON)
- `services` - Servicios (JSON)
- `correspondences` - Correspondencias (JSON)
- `connections` - Conexiones (JSON)
- `elevator_status` - Estado ascensores
- `escalator_status` - Estado escaleras
- `moving_walkway_status` - Estado pasillos móviles
- `defibrillator` - Desfibrilador
- `mobile_coverage` - Cobertura móvil
- `metroteca` - Metroteca
- `once_service` - Servicio ONCE
- `last_updated` - Última actualización
- `last_checked` - Última verificación
- `priority_score` - Puntuación de prioridad
- `raw_html` - HTML raw (30KB)
- `html_hash` - Hash del HTML

#### Tabla `realtime_trains`
- `station_id` - ID de la estación
- `line_number` - Número de línea
- `direction` - Dirección del tren
- `next_train_time` - Próximo tren
- `destination` - Destino
- `status` - Estado del tren
- `last_updated` - Última actualización

## 🔄 Sistema de Cache Inteligente

### Prioridades
1. **Nuevas estaciones** (prioridad 20)
2. **Estaciones existentes** (prioridad 10)
3. **Estaciones sin cambios** (prioridad 0)

### Algoritmo de Selección
1. Verificar estaciones que no se actualizaron en la última hora
2. Ordenar por prioridad y fecha de última actualización
3. Seleccionar las primeras 9 estaciones
4. Si no hay suficientes, tomar estaciones aleatorias del CSV

### Verificación de Cambios
- Calcula hash MD5 del HTML
- Solo actualiza si el HTML ha cambiado
- Actualiza timestamp de verificación

## 🚆 Trenes en Tiempo Real

### Funcionalidad
- Extrae información de próximos trenes
- Almacena dirección, tiempo, destino y estado
- Actualiza cada vez que se scrapea la estación

### Uso (Mañana)
```bash
# Cuando el metro esté abierto
python test_realtime_trains.py
```

## 📊 Exportación de Datos

### CSV
- `datos_estaciones/estaciones_inteligentes.csv`
- Incluye todos los campos de la base de datos
- Formato UTF-8

### Estadísticas
```bash
python config_scraper.py
# Opción 3: Ver estadísticas
```

## 🛠️ Mantenimiento

### Logs
- Revisar logs regularmente
- Los logs se rotan automáticamente
- Nivel de logging: INFO

### Base de Datos
- Backup automático no implementado
- Tamaño estimado: ~50MB para todas las estaciones
- Limpieza manual si es necesario

### Rendimiento
- Pausa aleatoria entre requests (1-3 segundos)
- Timeout de 30 segundos por request
- User-Agent realista para evitar bloqueos

## 🔮 Próximas Funcionalidades

1. **Movimiento de trenes** - Implementación de tracking en tiempo real
2. **API REST** - Endpoints para acceder a datos
3. **Dashboard web** - Interfaz para monitorear el scraper
4. **Alertas** - Notificaciones de cambios importantes
5. **Backup automático** - Respaldos de la base de datos

## 🐛 Solución de Problemas

### Error de Importación
```bash
pip install -r requirements.txt
```

### Base de Datos Corrupta
```bash
# Eliminar y recrear
rm datos_estaciones/metro_cache_inteligente.db
python metro_scraper_inteligente.py
```

### Logs Llenos
```bash
# Limpiar logs antiguos
rm *.log
```

## 📞 Soporte

Para problemas o sugerencias:
1. Revisar logs
2. Verificar configuración
3. Comprobar conectividad de red
4. Verificar que el metro esté abierto (para trenes en tiempo real) 