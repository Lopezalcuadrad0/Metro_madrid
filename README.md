# Metro de Madrid - Sistema de Información

Sistema completo para obtener y mostrar información del Metro de Madrid, incluyendo datos estáticos de estaciones y datos en tiempo real.

## 📁 Estructura del Proyecto

```
metro madrid bien/
├── app.py                          # Aplicación principal Flask
├── requirements.txt                 # Dependencias del proyecto
├── README.md                       # Este archivo
├── README_SISTEMA_OPTIMIZADO.md    # Documentación técnica detallada
├── datos_clave_estaciones.csv      # CSV con datos clave para búsquedas rápidas
├── metro_madrid.png                # Imagen del metro
├── PLANO ESQUEMÁTICO DE LA WEB 10.06.2025_0.pdf
│
├── herramientas/                   # Herramientas de gestión y scraping
│   ├── scraper_datos_detallados.py    # Scraper para datos detallados de estaciones
│   ├── scraper_ninja_tiempo_real.py   # Scraper Ninja para datos en tiempo real
│   ├── menu_scraper_estatico.py       # Menú para ejecutar scraper estático
│   ├── generar_csv_datos_clave.py     # Genera CSV con datos clave
│   ├── diagnostico_datos.py           # Diagnóstico de la base de datos
│   ├── completar_datos_faltantes.py   # Completa datos faltantes
│   ├── forzar_actualizacion_completa.py # Fuerza actualización completa
│   └── crear_tablas_fijas.py          # Crea las tablas de la base de datos
│
├── config/                        # Configuración y logs
│   ├── auto_updater_7min.py          # Auto-updater para datos en tiempo real
│   ├── auto_updater_7min.log         # Log del auto-updater
│   └── metro_scraper_inteligente.log # Log del scraper inteligente
│
├── db/                            # Bases de datos
│   ├── estaciones_fijas_v2.db        # Base de datos principal con estaciones
│   └── estaciones_fijas.db           # Base de datos anterior
│
├── datos_estaciones/              # Datos de estaciones
│   ├── estaciones/                    # CSVs por línea
│   ├── estaciones_procesadas.csv      # Estaciones procesadas
│   ├── metro_fijo.db                  # Base de datos local
│   └── scraper_config.json            # Configuración del scraper
│
├── M4/                            # Datos GTFS
│   ├── metro_madrid.db               # Base de datos GTFS
│   ├── mmadrid4.py                   # Script GTFS
│   ├── create_gtfs_db.py             # Creador de BD GTFS
│   └── [archivos GTFS...]
│
├── LINESM4/                       # Archivos KMZ de líneas
│   └── [archivos .kmz...]
│
├── static/                        # Archivos estáticos de la web
│   ├── css/                           # Estilos CSS
│   ├── js/                            # JavaScript
│   ├── logos/                         # Logos y iconos
│   ├── data/                          # Datos JSON
│   └── utils/                         # Utilidades
│
├── templates/                     # Plantillas HTML
│   ├── index.html                     # Página principal
│   ├── line.html                      # Página de línea
│   ├── station.html                   # Página de estación
│   └── [otras plantillas...]
│
└── lectura/                       # Documentación
    ├── README.md                      # Documentación general
    ├── README_ESTRUCTURA_NUEVA.md     # Estructura nueva
    ├── README_HERRAMIENTAS.md         # Herramientas
    ├── README_NINJASCRAP.md           # Scraper Ninja
    ├── README_SCRAPER_INTELIGENTE.md  # Scraper inteligente
    └── README_SCRAPER.md              # Scraper general
```

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 🛠️ Herramientas Principales

### Gestión de Datos
- **`herramientas/generar_csv_datos_clave.py`**: Genera CSV con datos clave para búsquedas rápidas
- **`herramientas/scraper_datos_detallados.py`**: Obtiene datos detallados de estaciones
- **`herramientas/menu_scraper_estatico.py`**: Menú para ejecutar scraper estático bajo demanda

### Diagnóstico y Mantenimiento
- **`herramientas/diagnostico_datos.py`**: Diagnostica el estado de la base de datos
- **`herramientas/completar_datos_faltantes.py`**: Completa datos faltantes
- **`herramientas/forzar_actualizacion_completa.py`**: Fuerza actualización completa

### Configuración
- **`config/auto_updater_7min.py`**: Auto-updater para datos en tiempo real
- **`herramientas/crear_tablas_fijas.py`**: Crea las tablas de la base de datos

## 📊 Características

- **Base de datos fija**: Datos estáticos de estaciones (dirección, accesos, servicios)
- **Scraper Ninja**: Datos en tiempo real (próximos trenes, estado de ascensores)
- **Búsquedas optimizadas**: CSV en memoria para búsquedas rápidas
- **Interfaz web**: Aplicación Flask con interfaz moderna
- **Auto-updater**: Actualización automática de datos en tiempo real

## 🔧 Uso de Herramientas

### Generar CSV de datos clave
```bash
python herramientas/generar_csv_datos_clave.py
```

### Ejecutar scraper estático
```bash
python herramientas/menu_scraper_estatico.py
```

### Diagnosticar base de datos
```bash
python herramientas/diagnostico_datos.py
```

### Forzar actualización completa
```bash
python herramientas/forzar_actualizacion_completa.py
```

## 📝 Notas

- La aplicación usa una base de datos fija para datos estáticos
- El scraper Ninja se ejecuta automáticamente cada 7 minutos para datos en tiempo real
- Los datos clave se cargan en memoria al inicio para búsquedas rápidas
- El scraper estático se ejecuta solo bajo demanda para evitar lentitud

Para más detalles técnicos, consulta `README_SISTEMA_OPTIMIZADO.md`. 