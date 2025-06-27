// Variables globales para Metro Ligero
let metroLigeroLayers = {};
let lineColors = {};

// Hacer metroLigeroLayers global para que pueda ser accedida desde otros scripts
window.metroLigeroLayers = metroLigeroLayers;

// Inicializar capas de Metro Ligero
function initializeMetroLigeroLayers() {
    console.log('Inicializando capas de Metro Ligero...');
    window.metroLigeroLayers = {
        'ML1': L.layerGroup(),
        'ML2': L.layerGroup(),
        'ML3': L.layerGroup()
    };
    console.log('Capas de Metro Ligero inicializadas:', Object.keys(window.metroLigeroLayers));
    
    // Cargar colores de líneas
    fetch('/static/data/line_colors.json')
        .then(response => response.json())
        .then(data => {
            lineColors = data.metro_ligero || {};
            console.log('Colores de Metro Ligero cargados:', lineColors);
        })
        .catch(error => {
            console.error('Error cargando colores de Metro Ligero:', error);
            lineColors = {
                '1': '#70C5E8',
                '2': '#9B4782',
                '3': '#DE1E40'
            };
        });
}

// Función principal para dibujar Metro Ligero
function drawMetroLigero(metroLigeroData) {
    console.log('Iniciando dibujo de Metro Ligero con datos:', metroLigeroData);
    
    if (!metroLigeroData || !metroLigeroData.stations) {
        console.error('Datos de Metro Ligero inválidos');
        return;
    }
    
    // Asegurar que las capas estén inicializadas
    if (Object.keys(window.metroLigeroLayers).length === 0) {
        console.log('Capas no inicializadas, inicializando ahora...');
        initializeMetroLigeroLayers();
    }
    
    // Procesar estaciones
    metroLigeroData.stations.forEach(station => {
        const { name, lat, lon, lines, id_estacion, id_modal } = station;
        
        // Obtener color de la primera línea (para el marcador)
        const firstLine = lines[0];
        const lineNumber = firstLine.replace('ML', '');
        // Usar el color del archivo de datos si está disponible
        let lineColor = '#70C5E8'; // Color por defecto
        
        // Buscar el color en los datos de líneas del archivo
        if (metroLigeroData.lines) {
            const lineData = metroLigeroData.lines.find(l => l.line === firstLine);
            if (lineData && lineData.color) {
                lineColor = lineData.color;
            } else {
                lineColor = lineColors[lineNumber] || '#70C5E8';
            }
        } else {
            lineColor = lineColors[lineNumber] || '#70C5E8';
        }
        
        console.log(`Estación ${name} - Línea: ${firstLine}, Color: ${lineColor}`);
        
        // Crear marcador
        const stationMarker = L.circleMarker([lat, lon], {
            radius: 8,
            fillColor: lineColor,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        
        // Datos de la estación
        const stationData = {
            name: name,
            id_fijo: id_estacion,
            id_modal: id_modal,
            lines: new Set(lines),
            zone: 'A',
            lat: lat,
            lon: lon,
            tipo: 'metro_ligero'
        };
        
        stationMarker.stationData = stationData;
        stationMarker.clickCount = 0;
        stationMarker.clickTimer = null;
        
        // Lógica de click y doble click
        stationMarker.on('click', function(e) {
            this.clickCount++;
            if (this.clickCount === 1) {
                this.clickTimer = setTimeout(() => {
                    showMetroLigeroInfo(stationData);
                    this.clickCount = 0;
                }, 200);
            } else if (this.clickCount === 2) {
                clearTimeout(this.clickTimer);
                selectStationForRoute(stationData);
                this.clickCount = 0;
            }
        });
        
        // Crear tooltip con todas las líneas
        const lineNames = lines.map(line => {
            const num = line.replace('ML', '');
            return `ML${num}`;
        }).join(', ');
        stationMarker.bindTooltip(
            `${name}<br><strong>${lineNames}</strong><br><small>Click: Info | Doble click: Ruta</small>`,
            {
                permanent: false,
                direction: 'top',
                offset: [0, -10],
                className: 'metro-ligero-tooltip'
            }
        );
        
        // Añadir la estación a todas las capas de líneas que le corresponden
        lines.forEach(line => {
            if (window.metroLigeroLayers[line]) {
                window.metroLigeroLayers[line].addLayer(stationMarker);
                console.log(`Estación ${name} añadida a capa ${line}`);
            } else {
                console.warn(`Capa ${line} no encontrada para estación ${name}`);
            }
        });
    });
    
    // Añadir las rutas de las líneas
    if (metroLigeroData.lines) {
        console.log('Procesando rutas de líneas:', metroLigeroData.lines.length, 'rutas encontradas');
        console.log('Datos de líneas:', metroLigeroData.lines);
        metroLigeroData.lines.forEach(line => {
            const lineType = line.line;
            const lineNumber = lineType.replace('ML', '');
            // Usar el color directamente del archivo de datos
            const lineColor = line.color || lineColors[lineNumber] || '#70C5E8';
            
            console.log(`Procesando ruta ${lineType}: número=${lineNumber}, color=${lineColor}, color_del_archivo=${line.color}`);
            
            if (window.metroLigeroLayers[lineType] && line.coordinates) {
                const polyline = L.polyline(line.coordinates, {
                    color: lineColor,
                    weight: 4,
                    opacity: 0.8
                });
                window.metroLigeroLayers[lineType].addLayer(polyline);
                console.log(`Ruta de ${lineType} añadida a la capa con color ${lineColor}`);
            } else {
                console.warn(`No se pudo añadir ruta para ${lineType}: capa=${!!window.metroLigeroLayers[lineType]}, coordenadas=${!!line.coordinates}`);
            }
        });
    } else {
        console.warn('No se encontraron rutas en los datos de Metro Ligero');
    }
    
    console.log('Estaciones de Metro Ligero dibujadas en capas:', Object.keys(window.metroLigeroLayers));
    
    // NO añadir capas automáticamente al mapa - solo dibujarlas
    // Las capas se añadirán/removerán cuando el usuario pulse el botón
    console.log('Capas de Metro Ligero dibujadas y listas para activar con el botón');
    
    // NO activar el botón automáticamente
    // El botón se activará/desactivará cuando el usuario lo pulse
    console.log('Botón de Metro Ligero listo para control manual');
    
    console.log('Metro Ligero dibujado correctamente - esperando activación manual');
}

function showMetroLigeroInfo(stationData) {
    // Llenar información en el panel para Metro Ligero
    document.getElementById('station-name').textContent = stationData.name;
    document.getElementById('station-id').textContent = `${stationData.id_fijo} (Modal: ${stationData.id_modal})`;
    document.getElementById('station-line').textContent = Array.from(stationData.lines).join(', ');
    document.getElementById('station-zone').textContent = stationData.zone;
    document.getElementById('station-type').textContent = 'Metro Ligero';
    
    // Mostrar el panel de información
    document.getElementById('station-info-panel').style.display = 'block';
}

function toggleMetroLigeroLine(lineId) {
    const layer = metroLigeroLayers[lineId];
    if (!layer) {
        console.warn(`Capa ${lineId} no encontrada`);
        return;
    }
    
    const button = document.querySelector('.line-button.' + lineId.toLowerCase());
    
    if (map.hasLayer(layer)) {
        map.removeLayer(layer);
        if (button) button.classList.remove('active');
        console.log(`Capa ${lineId} removida del mapa`);
    } else {
        map.addLayer(layer);
        if (button) button.classList.add('active');
        console.log(`Capa ${lineId} añadida al mapa`);
    }
    
    // Actualizar el estado del botón principal
    const allVisible = Object.values(metroLigeroLayers).every(layer => map.hasLayer(layer));
    const mainButton = document.querySelector('.transport-button.metro-ligero');
    if (mainButton) {
        if (allVisible) {
            mainButton.classList.add('active');
        } else {
            mainButton.classList.remove('active');
        }
    }
}

function toggleAllMetroLigero() {
    console.log('toggleAllMetroLigero llamado');
    const allVisible = Object.values(metroLigeroLayers).every(layer => map.hasLayer(layer));
    console.log('Estado actual - Todas las líneas visibles:', allVisible);
    console.log('Capas disponibles:', Object.keys(metroLigeroLayers));
    
    if (allVisible) {
        // Ocultar todas las capas
        console.log('Ocultando todas las capas de Metro Ligero...');
        Object.values(metroLigeroLayers).forEach(layer => {
            map.removeLayer(layer);
        });
        console.log('Todas las capas de Metro Ligero ocultadas');
    } else {
        // Mostrar todas las capas
        console.log('Mostrando todas las capas de Metro Ligero...');
        Object.values(metroLigeroLayers).forEach(layer => {
            map.addLayer(layer);
        });
        console.log('Todas las capas de Metro Ligero mostradas');
    }
    
    // Actualizar el estado del botón principal
    const button = document.querySelector('.transport-button.metro-ligero');
    if (button) {
        if (allVisible) {
            button.classList.remove('active');
            console.log('Botón principal desactivado');
        } else {
            button.classList.add('active');
            console.log('Botón principal activado');
        }
    } else {
        console.error('Botón principal de Metro Ligero no encontrado');
    }
    
    // Actualizar el estado de los botones individuales
    Object.keys(metroLigeroLayers).forEach(lineType => {
        const lineButton = document.querySelector('.line-button.' + lineType.toLowerCase());
        if (lineButton) {
            if (allVisible) {
                lineButton.classList.remove('active');
                console.log(`Botón ${lineType} desactivado`);
            } else {
                lineButton.classList.add('active');
                console.log(`Botón ${lineType} activado`);
            }
        } else {
            console.warn(`Botón ${lineType} no encontrado`);
        }
    });
}

// Función para obtener el estado de visibilidad de una línea
function isMetroLigeroLineVisible(lineId) {
    const layer = metroLigeroLayers[lineId];
    return layer ? map.hasLayer(layer) : false;
}

// Función para obtener el estado de visibilidad de todas las líneas
function areAllMetroLigeroLinesVisible() {
    return Object.values(metroLigeroLayers).every(layer => map.hasLayer(layer));
}

// Hacer funciones disponibles globalmente INMEDIATAMENTE
window.toggleMetroLigeroLine = toggleMetroLigeroLine;
window.toggleAllMetroLigero = toggleAllMetroLigero;
window.initializeMetroLigeroLayers = initializeMetroLigeroLayers;
window.drawMetroLigero = drawMetroLigero;

// Inicializar capas inmediatamente
initializeMetroLigeroLayers();

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Metro Ligero JavaScript inicializado');
    
    // Configurar event listener para el botón principal de Metro Ligero
    const metroLigeroButton = document.getElementById('metro-ligero-button');
    console.log('Buscando botón de Metro Ligero:', metroLigeroButton);
    
    if (metroLigeroButton) {
        console.log('Botón encontrado, configurando event listener...');
        metroLigeroButton.addEventListener('click', function(e) {
            console.log('Click en botón principal de Metro Ligero detectado');
            e.preventDefault();
            if (typeof toggleAllMetroLigero === 'function') {
                console.log('Llamando a toggleAllMetroLigero...');
                toggleAllMetroLigero();
            } else {
                console.error('Función toggleAllMetroLigero no disponible');
            }
        });
        console.log('Event listener configurado para botón de Metro Ligero');
    } else {
        console.error('Botón de Metro Ligero no encontrado');
        // Intentar encontrar el botón por clase
        const buttonByClass = document.querySelector('.transport-button.metro-ligero');
        if (buttonByClass) {
            console.log('Botón encontrado por clase, configurando event listener...');
            buttonByClass.addEventListener('click', function(e) {
                console.log('Click en botón principal de Metro Ligero detectado (por clase)');
                e.preventDefault();
                if (typeof toggleAllMetroLigero === 'function') {
                    console.log('Llamando a toggleAllMetroLigero...');
                    toggleAllMetroLigero();
                } else {
                    console.error('Función toggleAllMetroLigero no disponible');
                }
            });
            console.log('Event listener configurado para botón de Metro Ligero (por clase)');
        } else {
            console.error('No se pudo encontrar el botón de Metro Ligero por ID ni por clase');
        }
    }
});

// Timestamp: 06/27/2025 18:23:00 