// CERCANÍAS JAVASCRIPT - MANEJO DE CAPAS Y COLORES CON RUTAS REALES
// =================================================================

// Variables globales para Cercanías
var cercaniasLayers = {};
var cercaniasMarkers = {};
var cercaniasLines = {};
var cercaniasActive = false;
var cercaniasStationsLayer = null;
var cercaniasRoutesLayer = null;

// Configuración de colores de líneas de Cercanías
var CERCANIAS_COLORS = {
    'C-1': '#70C5E8',
    'C-2': '#00B04F', 
    'C-3': '#9B4782',
    'C-4a': '#004E98',
    'C-4b': '#004E98',
    'C-5': '#F2C500',
    'C-7a': '#DE1E40',
    'C-7b': '#DE1E40',
    'C-8': '#808080',
    'C-8a': '#B2B2B2',
    'C-8b': '#E20714',
    'C-9': '#F09600',
    'C-10': '#B0D136'
};

// Correspondencias típicas de cada línea de Cercanías
var CERCANIAS_CORRESPONDENCIAS = {
    'C-1': 'Metro: L1, L6, L9, L10 | Bus: EMT',
    'C-2': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-3': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-4a': 'Metro: L1, L6, L9, L10 | Bus: EMT',
    'C-4b': 'Metro: L1, L6, L9, L10 | Bus: EMT',
    'C-5': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-7a': 'Metro: L1, L6, L9, L10 | Bus: EMT',
    'C-7b': 'Metro: L1, L6, L9, L10 | Bus: EMT',
    'C-8': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-8a': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-8b': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos',
    'C-9': 'Bus: Interurbanos',
    'C-10': 'Metro: L1, L6, L9, L10 | Bus: EMT, Interurbanos'
};

// Función para obtener correspondencias de una línea
function getCercaniasCorrespondencias(linea) {
    return CERCANIAS_CORRESPONDENCIAS[linea] || 'Sin correspondencias específicas';
}

// Función para dibujar Cercanías
function drawCercanias(data) {
    console.log('🎯 Dibujando Cercanías...');
    console.log('📊 Datos recibidos:', data);
    
    // Crear capa de estaciones
    cercaniasStationsLayer = L.layerGroup();
    
    // Crear capa de rutas
    cercaniasRoutesLayer = L.layerGroup();
    
    // Procesar estaciones (usar 'estaciones' en lugar de 'stations')
    if (data.estaciones && data.estaciones.length > 0) {
        console.log(`📍 Procesando ${data.estaciones.length} estaciones de Cercanías`);
        
        data.estaciones.forEach(function(station) {
            if (station.latitud && station.longitud) {
                // Determinar el color de la línea para esta estación
                var lineColor = '#E20714'; // Color por defecto
                if (station.linea) {
                    lineColor = CERCANIAS_COLORS[station.linea] || '#E20714';
                }
                
                // Crear marcador personalizado para estaciones de Cercanías
                var marker = L.circleMarker([station.latitud, station.longitud], {
                    radius: 7,
                    fillColor: lineColor,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.85
                });
                
                // Crear tooltip con información de la estación
                var correspondencias = getCercaniasCorrespondencias(station.linea);
                var tooltipContent = `
                    <div class="cercanias-tooltip">
                        <strong>${station.nombre}</strong><br>
                        ${station.linea ? 'Línea: ' + station.linea : ''}<br>
                        ${station.codigo ? 'Código: ' + station.codigo : ''}<br>
                        ${station.municipio ? 'Municipio: ' + station.municipio : ''}<br>
                        <strong>Correspondencias:</strong><br>
                        ${correspondencias}
        </div>
    `;
    
                marker.bindTooltip(tooltipContent, {
            permanent: false, 
            direction: 'top',
            className: 'cercanias-tooltip'
        });
    
                // Agregar a la capa de estaciones
                cercaniasStationsLayer.addLayer(marker);
        }
    });
}

    // Procesar rutas reales (usar 'tramos' en lugar de 'rutas')
    if (data.tramos && data.tramos.length > 0) {
        console.log(`🛤️ Procesando ${data.tramos.length} tramos de Cercanías en orden inverso`);
        
        // Procesar tramos en orden inverso para mejor visualización
        for (var i = data.tramos.length - 1; i >= 0; i--) {
            var tramo = data.tramos[i];
            
            if (tramo.coordenadas && tramo.coordenadas.length > 0) {
                // Determinar el color basado en la línea del tramo
                var lineColor = '#E20714'; // Color por defecto
                if (tramo.linea) {
                    lineColor = CERCANIAS_COLORS[tramo.linea] || '#E20714';
                }
                
                // Crear línea con color específico del tramo
                var polyline = L.polyline(tramo.coordenadas, {
                    color: lineColor,
                    weight: 3,
                    opacity: 0.8
                });
                
                // Crear tooltip para el tramo
                var correspondencias = getCercaniasCorrespondencias(tramo.linea);
                var tramoTooltip = `
                    <div class="cercanias-route-tooltip">
                        <strong>${tramo.nombre || 'Tramo Cercanías'}</strong><br>
                        ${tramo.linea ? 'Línea: ' + tramo.linea : ''}<br>
                        ${tramo.sentido ? 'Sentido: ' + tramo.sentido : ''}<br>
                        ${tramo.codigo ? 'Código: ' + tramo.codigo : ''}<br>
                        <strong>Correspondencias:</strong><br>
                        ${correspondencias}
                    </div>
                `;
                
                polyline.bindTooltip(tramoTooltip, {
                    permanent: false,
                    direction: 'center',
                    className: 'cercanias-route-tooltip'
                });
                
                // Agregar a la capa de rutas
                cercaniasRoutesLayer.addLayer(polyline);
            }
        }
    }
    
    console.log('✅ Cercanías dibujadas correctamente');
    console.log(`📊 Resumen: ${cercaniasStationsLayer.getLayers().length} estaciones, ${cercaniasRoutesLayer.getLayers().length} tramos`);
}

// Función para alternar Cercanías (activar/desactivar)
function toggleCercanias() {
    if (!map) {
        console.error('❌ Mapa no disponible');
        return;
    }
    
    cercaniasActive = !cercaniasActive;
    console.log(`🎯 ${cercaniasActive ? 'Activando' : 'Desactivando'} Cercanías`);
    
    if (cercaniasActive) {
        // Activar capas
        if (cercaniasStationsLayer) {
            map.addLayer(cercaniasStationsLayer);
            console.log('📍 Capa de estaciones activada');
        }
        
        if (cercaniasRoutesLayer) {
            map.addLayer(cercaniasRoutesLayer);
            console.log('🛤️ Capa de tramos activada');
        }
    } else {
        // Desactivar capas
        if (cercaniasStationsLayer) {
            map.removeLayer(cercaniasStationsLayer);
            console.log('📍 Capa de estaciones desactivada');
        }
        
        if (cercaniasRoutesLayer) {
            map.removeLayer(cercaniasRoutesLayer);
            console.log('🛤️ Capa de tramos desactivada');
        }
    }
}

// Función para mostrar solo estaciones
function toggleCercaniasStations() {
    if (!map || !cercaniasActive) {
        console.log('❌ Cercanías no está activo');
        return;
    }
    
    if (cercaniasStationsLayer) {
        if (map.hasLayer(cercaniasStationsLayer)) {
            map.removeLayer(cercaniasStationsLayer);
            console.log('📍 Estaciones ocultadas');
        } else {
            map.addLayer(cercaniasStationsLayer);
            console.log('📍 Estaciones mostradas');
        }
    }
}

// Función para mostrar solo tramos
function toggleCercaniasRoutes() {
    if (!map || !cercaniasActive) {
        console.log('❌ Cercanías no está activo');
        return;
    }
    
    if (cercaniasRoutesLayer) {
        if (map.hasLayer(cercaniasRoutesLayer)) {
            map.removeLayer(cercaniasRoutesLayer);
            console.log('🛤️ Tramos ocultados');
        } else {
            map.addLayer(cercaniasRoutesLayer);
            console.log('🛤️ Tramos mostrados');
        }
    }
}

// Función para mostrar todas las líneas (no se usa en la versión simplificada)
function showAllCercaniasLines() {
    console.log('🎯 Función showAllCercaniasLines no disponible en versión simplificada');
}

// Función para alternar líneas individuales (no se usa en la versión simplificada)
function toggleCercaniasLine(lineId) {
    console.log('🎯 Función toggleCercaniasLine no disponible en versión simplificada');
}

// Event listeners para botones de control
document.addEventListener('DOMContentLoaded', function() {
    // Botón principal de Cercanías
    var cercaniasButton = document.querySelector('#cercanias-button');
    if (cercaniasButton) {
        cercaniasButton.addEventListener('click', function() {
            this.classList.toggle('active');
            toggleCercanias();
        });
    }
    
    console.log('🎯 Event listeners de Cercanías configurados');
});

// Hacer funciones globales
window.drawCercanias = drawCercanias;
window.toggleCercanias = toggleCercanias;
window.toggleCercaniasStations = toggleCercaniasStations;
window.toggleCercaniasRoutes = toggleCercaniasRoutes;
window.showAllCercaniasLines = showAllCercaniasLines;

console.log('🚂 Script de Cercanías cargado (versión simplificada)'); 