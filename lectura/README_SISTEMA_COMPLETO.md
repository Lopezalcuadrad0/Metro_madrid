# 🚇 Sistema Completo del Metro de Madrid

Sistema completo de scraping inteligente, auto actualización y aplicación web para el Metro de Madrid.

## 🎯 Características Principales

### 🔄 Scraper Inteligente
- **Cache inteligente** con fecha de modificación
- **Sistema de prioridades** que prioriza estaciones vacías
- **Actualización selectiva** de 9 estaciones aleatorias
- **Notificaciones** cuando no se puede llenar una estación vacía
- **Base de datos SQLite** para almacenamiento eficiente

### ⏰ Auto Updater 7 Minutos
- **Actualización automática** cada 7 minutos cuando la app está corriendo
- **Ejecución en segundo plano** con threads
- **Control via API** (iniciar/detener/estado)
- **Integración automática** con la app Flask

### 🌐 Aplicación Web Flask
- **Mapa interactivo** con todas las líneas
- **Información en tiempo real** de estaciones
- **Búsqueda de estaciones** con autocompletado
- **Horarios detallados** por línea y estación
- **API REST** completa para integración

## 📁 Estructura del Proyecto

```
metro madrid bien/
├── 🚀 Core Files
│   ├── app.py                          # Aplicación Flask principal
│   ├── metro_scraper_inteligente.py    # Scraper inteligente
│   ├── auto_updater_7min.py           # Auto updater 7 minutos
│   └── test_system.py                  # Tests del sistema
│
├── 📊 Data & Cache
│   ├── datos_estaciones/
│   │   ├── metro_cache_inteligente.db  # Base de datos SQLite
│   │   ├── estaciones_inteligentes.csv # Datos exportados
│   │   └── estaciones_procesadas.csv   # Datos fuente
│   └── M4/                             # Datos GTFS
│
├── 🎨 Frontend
│   ├── templates/                      # Templates HTML
│   ├── static/
│   │   ├── css/                        # Estilos
│   │   ├── js/                         # JavaScript
│   │   ├── logos/                      # Logos de líneas
│   │   └── data/                       # Datos JSON
│
└── 📚 Documentation
    ├── README_SISTEMA_COMPLETO.md      # Este archivo
    ├── README_SCRAPER_INTELIGENTE.md   # Documentación del scraper
    └── requirements.txt                # Dependencias
```

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Verificar Datos
```bash
# Verificar que existe el archivo de estaciones
ls datos_estaciones/estaciones_procesadas.csv
```

### 3. Configurar Scraper (Opcional)
```bash
python config_scraper.py
```

## 📖 Uso del Sistema

### 🎯 Modo Completo (Recomendado)
```bash
python app.py
```
- Inicia la aplicación web
- Auto updater se ejecuta automáticamente cada 7 minutos
- Acceso web en http://localhost:5000

### 🔄 Solo Scraper Inteligente
```bash
python metro_scraper_inteligente.py
```
- Actualiza 9 estaciones con prioridades
- Exporta datos a CSV
- Muestra estadísticas

### ⏰ Solo Auto Updater
```bash
python auto_updater_7min.py
```
- Ejecuta actualizaciones cada 7 minutos
- Modo independiente

### 🧪 Tests del Sistema
```bash
python test_system.py
```
- Prueba todos los componentes
- Verifica funcionamiento

## 🔧 API Endpoints

### Auto Updater
- `GET /api/auto-updater/start` - Iniciar auto updater
- `GET /api/auto-updater/stop` - Detener auto updater  
- `GET /api/auto-updater/status` - Estado del auto updater

### Estaciones
- `GET /api/station/search?q=<query>` - Búsqueda de estaciones
- `GET /api/station/<line>/<id>` - Datos de estación
- `GET /api/station/<line>/<id>/refresh` - Forzar actualización

### Cache
- `GET /api/cache/status` - Estado del cache
- `GET /api/status` - Estado general del sistema

## 🎯 Sistema de Prioridades

### Niveles de Prioridad
1. **Prioridad 100** - Estaciones vacías (máxima prioridad)
2. **Prioridad 50** - Estaciones nunca actualizadas
3. **Prioridad 25** - Estaciones desactualizadas (>1 hora)
4. **Prioridad 0** - Estaciones actualizadas

### Algoritmo de Selección
1. Buscar estaciones vacías primero
2. Luego estaciones nunca actualizadas
3. Después estaciones desactualizadas
4. Finalmente estaciones aleatorias del CSV

## 📊 Notificaciones y Logs

### Tipos de Notificación
- ✅ **Exitoso** - Estación actualizada correctamente
- 🆕 **Nueva** - Estación vacía llenada exitosamente
- ⚠️ **Advertencia** - No se pudo llenar estación vacía
- ❌ **Error** - Error en actualización

### Archivos de Log
- `metro_scraper_inteligente.log` - Log del scraper
- `auto_updater_7min.log` - Log del auto updater
- `test_system.log` - Log de pruebas

## 🔄 Flujo de Trabajo

### 1. Inicio del Sistema
```
app.py → Inicia Flask → Auto Updater → Primera actualización
```

### 2. Ciclo de Actualización (7 min)
```
Auto Updater → Selecciona 9 estaciones → Scraper → Cache → CSV
```

### 3. Priorización
```
Estaciones vacías → Nunca actualizadas → Desactualizadas → Aleatorias
```

### 4. Notificaciones
```
Éxito → Log info
Error → Log warning/error
Vacía no llenada → Notificación especial
```

## 🛠️ Mantenimiento

### Verificar Estado
```bash
# Ver logs
tail -f metro_scraper_inteligente.log

# Ver estadísticas
python config_scraper.py
# Opción 3: Ver estadísticas
```

### Limpiar Cache
```bash
# Eliminar base de datos (se recreará)
rm datos_estaciones/metro_cache_inteligente.db
```

### Backup
```bash
# Hacer backup de datos
cp datos_estaciones/estaciones_inteligentes.csv backup_$(date +%Y%m%d).csv
```

## 🔮 Próximas Funcionalidades

1. **Movimiento de trenes** - Tracking en tiempo real
2. **Alertas push** - Notificaciones de cambios importantes
3. **Dashboard web** - Interfaz de administración
4. **Backup automático** - Respaldos programados
5. **Métricas avanzadas** - Estadísticas detalladas

## 🐛 Solución de Problemas

### Error de Importación
```bash
pip install -r requirements.txt
```

### Auto Updater No Inicia
```bash
# Verificar logs
tail -f auto_updater_7min.log

# Reiniciar manualmente
curl http://localhost:5000/api/auto-updater/start
```

### Estaciones No Se Actualizan
```bash
# Verificar configuración
python config_scraper.py

# Forzar actualización manual
python metro_scraper_inteligente.py
```

### Base de Datos Corrupta
```bash
# Eliminar y recrear
rm datos_estaciones/metro_cache_inteligente.db
python metro_scraper_inteligente.py
```

## 📞 Soporte

### Verificar Estado del Sistema
1. Revisar logs en tiempo real
2. Verificar estadísticas con `config_scraper.py`
3. Comprobar endpoints de la API
4. Ejecutar tests con `test_system.py`

### Logs Importantes
- **Scraper**: `metro_scraper_inteligente.log`
- **Auto Updater**: `auto_updater_7min.log`
- **App Flask**: Consola donde se ejecuta `app.py`

### Comandos Útiles
```bash
# Estado del auto updater
curl http://localhost:5000/api/auto-updater/status

# Forzar actualización
python metro_scraper_inteligente.py

# Ver estadísticas
python config_scraper.py
```

---

**¡El sistema está listo para funcionar 24/7 con actualizaciones automáticas cada 7 minutos!** 🚇✨ 