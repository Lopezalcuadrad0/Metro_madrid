# 🚇 Live Timing Metro de Madrid

Sistema de seguimiento en tiempo real del metro de Madrid basado en datos GTFS reales.

## 📋 Características

- **Live Timing en Tiempo Real**: Simulación realista del movimiento de trenes
- **Interfaz Moderna**: Diseño responsive con efectos visuales atractivos
- **Datos Reales**: Basado en datos GTFS oficiales del Metro de Madrid
- **Filtrado por Líneas**: Visualización por líneas específicas
- **Estadísticas en Vivo**: Contadores de trenes activos, rutas y estaciones
- **Actualización Automática**: Datos se actualizan cada 30 segundos

## 🛠️ Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   git clone <url-del-repositorio>
   cd metro-madrid-live-timing
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verificar estructura de archivos**
   ```
   metro-madrid-live-timing/
   ├── app.py                 # Aplicación principal Flask
   ├── requirements.txt       # Dependencias Python
   ├── README.md             # Este archivo
   ├── templates/
   │   └── index.html        # Interfaz web
   └── M4/                   # Datos GTFS del Metro de Madrid
       ├── routes.txt
       ├── stops.txt
       ├── trips.txt
       ├── stop_times.txt
       ├── frequencies.txt
       ├── calendar.txt
       └── ...
   ```

## 🚀 Uso

### Iniciar la Aplicación

1. **Ejecutar el servidor**
   ```bash
   python app.py
   ```

2. **Abrir en el navegador**
   ```
   http://localhost:5000
   ```

### Funcionalidades

- **Vista General**: Muestra todos los trenes activos en el sistema
- **Filtrado por Línea**: Haz clic en los botones de línea para ver solo trenes de esa ruta
- **Información en Tiempo Real**: 
  - Hora actual del sistema
  - Próxima parada de cada tren
  - Hora de llegada estimada
  - Destino del tren
  - Estado del sistema

## 📊 Datos Utilizados

El sistema utiliza datos GTFS (General Transit Feed Specification) reales del Metro de Madrid:

- **Rutas**: 13 líneas del metro (Líneas 1-12 + Ramal)
- **Estaciones**: Todas las estaciones del metro
- **Horarios**: Horarios reales de operación
- **Frecuencias**: Frecuencias de paso según el día y hora
- **Calendario**: Días de operación (laborables, sábados, domingos)

## 🔧 Configuración

### Personalizar la Simulación

Puedes modificar el archivo `app.py` para ajustar:

- **Velocidad de simulación**: Cambiar el `time.sleep(60)` en la función `simulate_train_movement()`
- **Hora de inicio**: Modificar `current_time` en la inicialización
- **Frecuencia de actualización**: Cambiar el intervalo en el frontend (30 segundos por defecto)

### Personalizar la Interfaz

El archivo `templates/index.html` contiene:

- **Estilos CSS**: Personalización visual completa
- **JavaScript**: Lógica de actualización y filtrado
- **HTML**: Estructura de la interfaz

## 🌐 API Endpoints

La aplicación expone los siguientes endpoints:

- `GET /` - Página principal
- `GET /api/status` - Estado actual del sistema
- `GET /api/route/<route_id>` - Información de una ruta específica
- `GET /api/stop/<stop_id>` - Información de una parada específica

## 📱 Compatibilidad

- **Navegadores**: Chrome, Firefox, Safari, Edge (versiones modernas)
- **Dispositivos**: Desktop, tablet, móvil (responsive design)
- **Sistemas Operativos**: Windows, macOS, Linux

## 🐛 Solución de Problemas

### Error al cargar datos GTFS
- Verifica que la carpeta `M4/` contenga todos los archivos necesarios
- Asegúrate de que los archivos CSV estén en formato UTF-8

### Error de dependencias
- Ejecuta `pip install -r requirements.txt` nuevamente
- Verifica que tienes Python 3.8+ instalado

### Puerto ocupado
- Cambia el puerto en `app.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`

## 📈 Próximas Mejoras

- [ ] Mapa interactivo con posiciones de trenes
- [ ] Notificaciones de retrasos
- [ ] Historial de viajes
- [ ] Integración con datos de ocupación
- [ ] Modo oscuro/claro
- [ ] Exportación de datos

## 📄 Licencia

Este proyecto es de uso educativo y demostrativo. Los datos GTFS son propiedad del Consorcio Regional de Transportes de Madrid (CRTM).

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Contacto

Para preguntas o sugerencias, abre un issue en el repositorio.

---

**🚇 ¡Disfruta del Live Timing del Metro de Madrid!** 