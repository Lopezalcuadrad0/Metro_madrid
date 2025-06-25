# 🚇 Metro de Madrid - Sistema Completo

Sistema completo e inteligente para obtener, procesar y mostrar información del Metro de Madrid en tiempo real, incluyendo datos estáticos de estaciones, scraping inteligente, y una interfaz web moderna.

## 🎯 **Características Principales**

### 🔄 **Sistema Inteligente**
- **Scraper Inteligente** con cache automático y prioridades
- **Auto-updater** cada 7 minutos con datos en tiempo real
- **NinjaScrap** - Autocompletado inteligente en tiempo real
- **Base de datos SQLite** optimizada con datos de 291 estaciones

### 🌐 **Aplicación Web Moderna**
- **Interfaz responsive** con diseño moderno
- **Mapa interactivo** con todas las líneas del metro
- **Búsqueda inteligente** con autocompletado en tiempo real
- **Sistema de trenes moderno** con colores oficiales y animaciones

### 📊 **Datos Completos**
- **291 estaciones** con información detallada
- **13 líneas** (1-12 + Ramal) completamente mapeadas
- **Accesos, servicios y correspondencias** actualizados
- **Datos GTFS** oficiales del CRTM

## 📁 **Estructura del Proyecto**

```
Metro_madrid/
├── 🚀 **Core Application**
│   ├── app.py                          # Aplicación Flask principal
│   ├── forms.py                        # Formularios web
│   ├── requirements.txt                # Dependencias del proyecto
│   └── iniciar_sistema.py              # Script de inicio automático
│
├── 📊 **Data & Database**
│   ├── db/
│   │   ├── estaciones_fijas_v2.db      # Base de datos principal (291 estaciones)
│   │   └── actualizar_bd_desde_csv.py  # Actualizador de BD desde CSV
│   ├── datos_estaciones/
│   │   ├── accesos_completos.csv       # 1012 accesos detallados
│   │   ├── conexiones_completas.csv    # 85 conexiones de transporte
│   │   ├── datos_completos_todas_lineas.json # Datos JSON completos
│   │   └── estaciones_procesadas.csv   # Estaciones procesadas
│   └── datos_clave_estaciones_definitivo.csv # CSV optimizado para búsquedas
│
├── 🛠️ **Herramientas Inteligentes**
│   ├── herramientas/
│   │   ├── scraper_ninja_tiempo_real.py    # NinjaScrap en tiempo real
│   │   ├── scraper_accesos_reales.py       # Scraper de accesos
│   │   ├── auto_scraper_integrado.py       # Auto-scraper inteligente
│   │   ├── actualizar_accesos.py           # Actualizador de accesos
│   │   ├── diagnostico_sistema_completo.py # Diagnóstico completo
│   │   └── verificar_sistema_completo.py   # Verificación del sistema
│   └── config/
│       ├── auto_updater_7min.py           # Auto-updater cada 7 minutos
│       └── metro_scraper_inteligente.log  # Logs del sistema
│
├── 🎨 **Frontend Moderno**
│   ├── templates/
│   │   ├── index.html                  # Página principal
│   │   ├── station.html                # Página de estación (con NinjaScrap)
│   │   ├── line.html                   # Página de línea
│   │   ├── map.html                    # Mapa interactivo
│   │   └── base.html                   # Template base
│   └── static/
│       ├── css/
│       │   ├── global.css              # Estilos globales
│       │   ├── modern-trains.css       # Sistema moderno de trenes
│       │   ├── realtime_scraper.css    # Estilos NinjaScrap
│       │   └── stations.css            # Estilos de estaciones
│       ├── js/
│       │   ├── modern-trains.js        # Lógica sistema moderno
│       │   ├── realtime_scraper.js     # Cliente NinjaScrap
│       │   └── line.js                 # Lógica de líneas
│       ├── logos/lineas/               # Logos oficiales de líneas
│       └── model_3D/                   # Imágenes 3D de estaciones
│
├── 📈 **Datos GTFS**
│   ├── M4/
│   │   ├── metro_madrid.db             # Base de datos GTFS
│   │   ├── routes.txt, stops.txt       # Datos oficiales CRTM
│   │   └── [archivos GTFS...]
│   └── LINESM4/                        # Archivos KMZ de líneas
│
└── 📚 **Documentación**
    ├── lectura/
    │   ├── README_HERRAMIENTAS.md      # Documentación de herramientas
    │   ├── README_NINJASCRAP.md        # Sistema de autocompletado
    │   ├── README_SISTEMA_MODERNO.md   # Sistema moderno de trenes
    │   └── README_SCRAPER.md           # Sistema de scraping
    └── correspondencias_metro.csv      # Correspondencias entre líneas
```

## 🚀 **Inicio Rápido**

### **1. Instalación**
```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd Metro_madrid

# Instalar dependencias
pip install -r requirements.txt
```

### **2. Ejecutar la Aplicación**
```bash
# Opción 1: Inicio automático (recomendado)
python iniciar_sistema.py

# Opción 2: Inicio manual
python app.py
```

### **3. Acceder a la Aplicación**
```
🌐 Aplicación web: http://localhost:5000
📊 Estado del sistema: http://localhost:5000/status
🔍 API de búsqueda: http://localhost:5000/api/station/search?q=callao
```

## ✨ **Funcionalidades Principales**

### 🔍 **NinjaScrap - Búsqueda Inteligente**
- **Autocompletado en tiempo real** mientras escribes
- **Scraping instantáneo** al seleccionar una estación
- **Datos frescos** de próximos trenes y estado de servicios
- **Navegación con teclado** (↑↓ Enter Esc)

```javascript
// Ejemplo de uso en JavaScript
window.metroScraper.searchStation('ca'); // → Callao, Canillejas...
```

### 🚄 **Sistema Moderno de Trenes**
- **Diseño visual impresionante** con colores oficiales
- **Animaciones suaves** y efectos glassmorphism
- **Información organizada** por líneas y direcciones
- **Tiempos con códigos de color**: 🔴 ≤2min 🟡 3-5min 🔵 >5min

### 🗺️ **Mapa Interactivo**
- **Todas las líneas** del Metro de Madrid
- **291 estaciones** completamente mapeadas
- **Información detallada** al hacer clic en estaciones
- **Responsive design** para móviles y tablets

### 📊 **Base de Datos Completa**
- **Accesos detallados**: 1012 registros con vestíbulos y direcciones
- **Servicios completos**: Ascensores, escaleras, accesibilidad, etc.
- **Conexiones**: 85 conexiones con Cercanías, autobuses, etc.
- **Correspondencias**: Enlaces entre líneas de metro

## 🛠️ **Herramientas de Gestión**

### **Scraper Inteligente**
```bash
# Actualizar datos de estaciones automáticamente
python herramientas/auto_scraper_integrado.py

# Diagnosticar estado del sistema
python herramientas/diagnostico_sistema_completo.py

# Verificar integridad de datos
python herramientas/verificar_sistema_completo.py
```

### **Gestión de Datos**
```bash
# Actualizar base de datos desde CSV
python db/actualizar_bd_desde_csv.py

# Actualizar accesos faltantes
python herramientas/actualizar_accesos.py

# Generar datos clave optimizados
python herramientas/generar_csv_datos_clave.py
```

## 🔌 **API REST Completa**

### **Búsqueda de Estaciones**
```bash
# Búsqueda con autocompletado
GET /api/station/search?q=<query>

# Ejemplo
curl "http://localhost:5000/api/station/search?q=callao"
```

### **Información de Estaciones**
```bash
# Datos completos de una estación
GET /api/station/<line>/<id>

# Ejemplo: Callao línea 3
curl "http://localhost:5000/api/station/3/307"
```

### **NinjaScrap en Tiempo Real**
```bash
# Scraping instantáneo
GET /api/station/ninjascrap/<station_name>

# Ejemplo
curl "http://localhost:5000/api/station/ninjascrap/Callao"
```

### **Sistema Moderno de Trenes**
```bash
# Datos de trenes con formato moderno
GET /api/station/raw-trains/<station_name>

# Ejemplo
curl "http://localhost:5000/api/station/raw-trains/Argüelles"
```

## 📈 **Estadísticas del Sistema**

### **Cobertura Completa**
- ✅ **291 estaciones** mapeadas (100% del Metro Madrid)
- ✅ **13 líneas** completas (Líneas 1-12 + Ramal)
- ✅ **1012 accesos** detallados con vestíbulos
- ✅ **85 conexiones** con otros transportes
- ✅ **6 servicios** por estación (ascensores, escaleras, etc.)

### **Rendimiento**
- ⚡ **Búsqueda instantánea** con datos en memoria
- 🔄 **Auto-actualización** cada 7 minutos
- 💾 **Cache inteligente** para optimizar consultas
- 📱 **Responsive** en móviles y tablets

## 🎨 **Personalización**

### **Colores de Líneas**
```css
/* Colores oficiales del Metro Madrid */
:root {
    --linea-1: #00AEEF;
    --linea-2: #EF3340;
    --linea-3: #FFCB05;
    --linea-4: #B6BD00;
    --linea-5: #00A94F;
    /* ... más líneas */
}
```

### **Configuración del Sistema**
```python
# Configurar intervalos de actualización
AUTO_UPDATE_INTERVAL = 7 * 60  # 7 minutos
CACHE_TTL = 24 * 60 * 60       # 24 horas

# Configurar scraping
SCRAPER_DELAY = 1              # 1 segundo entre consultas
MAX_RETRIES = 3                # 3 reintentos
```

## 🔧 **Configuración Avanzada**

### **Variables de Entorno**
```bash
# Configurar en .env
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///db/estaciones_fijas_v2.db
AUTO_UPDATE_ENABLED=True
```

### **Optimización de Rendimiento**
```python
# Configurar cache en memoria
MEMORY_CACHE_SIZE = 1000       # Estaciones en memoria
CSV_RELOAD_INTERVAL = 3600     # Recargar CSV cada hora
```

## 🐛 **Solución de Problemas**

### **Problemas Comunes**

1. **Error al cargar datos**
   ```bash
   # Verificar archivos CSV
   ls datos_estaciones/*.csv
   
   # Regenerar datos clave
   python herramientas/generar_csv_datos_clave.py
   ```

2. **Base de datos corrupta**
   ```bash
   # Regenerar desde CSV
   python db/actualizar_bd_desde_csv.py
   ```

3. **NinjaScrap no funciona**
   ```bash
   # Verificar scraper
   python herramientas/scraper_ninja_tiempo_real.py
   ```

### **Diagnóstico del Sistema**
```bash
# Ejecutar diagnóstico completo
python herramientas/diagnostico_sistema_completo.py

# Ver logs del sistema
tail -f config/metro_scraper_inteligente.log
```

## 📞 **Soporte y Contribución**

### **Reportar Problemas**
1. Ejecutar diagnóstico del sistema
2. Revisar logs de errores
3. Verificar conectividad de red
4. Comprobar integridad de archivos

### **Contribuir al Proyecto**
1. Fork el repositorio
2. Crear rama para nueva funcionalidad
3. Seguir estándares de código
4. Enviar Pull Request

## 🔮 **Próximas Funcionalidades**

- [ ] **Notificaciones push** para trenes próximos
- [ ] **Modo offline** con datos en cache
- [ ] **API GraphQL** para consultas avanzadas
- [ ] **Dashboard de administración** web
- [ ] **Integración con mapas** de Google Maps
- [ ] **Machine Learning** para predicción de tiempos

## 📄 **Licencia**

Este proyecto es de uso educativo y demostrativo. Los datos del Metro de Madrid son propiedad del Consorcio Regional de Transportes de Madrid (CRTM).

---

**🚇 ¡Sistema Metro Madrid completo y funcionando al 100%! ✨**

*Desarrollado con ❤️ para la comunidad de Madrid* 