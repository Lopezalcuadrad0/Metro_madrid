# 🚀 NinjaScrap - Sistema de Autocompletado Inteligente

## 📋 **Descripción**

NinjaScrap es un sistema de autocompletado inteligente que ejecuta scraping en tiempo real para obtener datos frescos de las estaciones del Metro de Madrid sin necesidad de almacenarlos en base de datos.

## ✨ **Características**

- **🔍 Autocompletado en tiempo real** - Mientras escribes "ca" te muestra "Canillejas", "Callao", etc.
- **⚡ NinjaScrap instantáneo** - Al seleccionar una estación, ejecuta el scraper en tiempo real
- **📊 Datos frescos** - Próximos trenes, estado de ascensores y escaleras en tiempo real
- **🎨 Interfaz moderna** - Diseño atractivo con animaciones y colores del Metro

## 🛠️ **Cómo funciona**

### 1. **Autocompletado**
- Escribe en el campo de búsqueda (mínimo 2 caracteres)
- El sistema busca estaciones que coincidan
- Muestra sugerencias con iconos de líneas y colores
- Navegación con teclado (↑↓ Enter Esc)

### 2. **NinjaScrap**
- Al seleccionar una estación, ejecuta el scraper
- Obtiene datos en tiempo real de la web oficial
- Muestra próximos trenes con HTML original
- Estado de ascensores y escaleras mecánicas

## 🔧 **Integración con tu Scraper**

### **Paso 1: Reemplazar la función de simulación**

En `app.py`, reemplaza la función `simulate_ninjascrap_data()` con tu scraper real:

```python
def execute_real_ninjascrap(station_data):
    """Ejecuta tu scraper real aquí"""
    try:
        # Tu código de scraping aquí
        # Por ejemplo:
        # scraper = MiScraper()
        # datos = scraper.scrape_station(station_data['url'])
        
        return {
            'proximos_trenes_html': datos['html_proximos_trenes'],
            'estado_ascensores': datos['estado_ascensores'],
            'estado_escaleras': datos['estado_escaleras']
        }
    except Exception as e:
        print(f"Error en scraper: {e}")
        return None
```

### **Paso 2: Modificar la API**

En la función `ninjascrap_station()`, reemplaza:

```python
# Cambiar esto:
ninjascrap_data = simulate_ninjascrap_data(station_data)

# Por esto:
ninjascrap_data = execute_real_ninjascrap(station_data)
if not ninjascrap_data:
    return jsonify({'error': 'Error ejecutando scraper'}), 500
```

### **Paso 3: Estructura de datos esperada**

Tu scraper debe devolver un diccionario con:

```python
{
    'proximos_trenes_html': '<div>HTML de próximos trenes</div>',
    'estado_ascensores': 'Operativo/Averiado/En mantenimiento',
    'estado_escaleras': 'Operativo/Averiado/En mantenimiento'
}
```

## 🎯 **APIs disponibles**

### **Autocompletado**
```
GET /api/station/search?q=ca
```
Devuelve estaciones que contengan "ca"

### **NinjaScrap**
```
GET /api/station/ninjascrap/Sol
```
Ejecuta scraper para la estación "Sol"

## 🎨 **Personalización**

### **Colores de líneas**
Modifica la función `getLineColor()` en el JavaScript:

```javascript
function getLineColor(lineNumber) {
    const colors = {
        '1': '#1f4e79',
        '2': '#ff0000',
        // ... añadir más líneas
    };
    return colors[lineNumber] || '#666';
}
```

### **Estilos CSS**
Los estilos están en `templates/station.html`. Puedes modificar:

- `.ninjascrap-content` - Contenedor principal
- `.proximos-trenes-html` - HTML de próximos trenes
- `.autocomplete-item` - Elementos del autocompletado

## 🚀 **Uso**

1. **Abre la página**: `http://localhost:5000/station`
2. **Escribe en el campo**: "ca" → verás "Canillejas", "Callao"
3. **Selecciona una estación**: Se ejecuta NinjaScrap automáticamente
4. **Ver datos en tiempo real**: Próximos trenes, estado de servicios

## 🔄 **Actualización automática**

Para actualizar datos automáticamente, añade en el JavaScript:

```javascript
// Actualizar cada 30 segundos
setInterval(() => {
    if (currentStation) {
        executeNinjaScrap(currentStation);
    }
}, 30000);
```

## 📝 **Notas**

- El sistema es **fallback-friendly**: Si NinjaScrap falla, usa datos básicos
- **No almacena datos**: Todo se obtiene en tiempo real
- **Responsive**: Funciona en móviles y tablets
- **Accesible**: Navegación completa con teclado

## 🐛 **Solución de problemas**

### **Autocompletado no funciona**
- Verifica que la API `/api/station/search` funcione
- Revisa la consola del navegador para errores

### **NinjaScrap no carga**
- Verifica que tu scraper esté funcionando
- Revisa los logs del servidor Flask
- Comprueba que la URL de la estación sea válida

### **Estilos no se ven bien**
- Verifica que los CSS estén cargados
- Revisa que las clases coincidan con el HTML

---

**¡NinjaScrap está listo para usar! Solo necesitas integrar tu scraper real y disfrutar de datos frescos en tiempo real.** 🎉 