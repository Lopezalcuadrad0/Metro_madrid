// Variables globales para Metro
let metroLayers = {};
let metroLineColors = {};

// Hacer metroLayers global para que pueda ser accedida desde otros scripts
window.metroLayers = metroLayers;

// Inicializar capas de Metro
function initializeMetroLayers() {
    console.log('Inicializando capas de Metro...');
    window.metroLayers = {
        '1': L.layerGroup(),
        '2': L.layerGroup(),
        '3': L.layerGroup(),
        '4': L.layerGroup(),
        '5': L.layerGroup(),
        '6': L.layerGroup(),
        '7': L.layerGroup(),
        '8': L.layerGroup(),
        '9': L.layerGroup(),
        '10': L.layerGroup(),
        '11': L.layerGroup(),
        '12': L.layerGroup(),
        'R': L.layerGroup()
    };
    console.log('Capas de Metro inicializadas:', Object.keys(window.metroLayers));
    
    // Cargar colores de líneas
    fetch('/static/data/line_colors.json')
        .then(response => response.json())
        .then(data => {
            metroLineColors = data.metro || {};
            console.log('Colores de Metro cargados:', metroLineColors);
        })
        .catch(error => {
            console.error('Error cargando colores de Metro:', error);
            // Colores por defecto
            metroLineColors = {
                '1': '#00AEEF',
                '2': '#FF0000',
                '3': '#FFD700',
                '4': '#B25400',
                '5': '#39B54A',
                '6': '#9E9E9E',
                '7': '#FF9800',
                '8': '#FF69B4',
                '9': '#9C27B0',
                '10': '#0D47A1',
                '11': '#006400',
                '12': '#a49a00',
                'R': '#0055A4'
            };
        });
}

// Función principal para dibujar Metro
function drawMetro(metroData) {
    console.log('Iniciando dibujo de Metro con datos:', metroData);
    
    if (!metroData || !metroData.stations) {
        console.error('Datos de Metro inválidos');
        return;
    }
    
    // Asegurar que las capas estén inicializadas
    if (Object.keys(window.metroLayers).length === 0) {
        console.log('Capas no inicializadas, inicializando ahora...');
        initializeMetroLayers();
    }
    
    // Procesar estaciones
    metroData.stations.forEach(station => {
        const { name, lat, lon, lines, id_estacion, id_modal } = station;
        
        // Obtener color de la primera línea (para el marcador)
        const firstLine = lines[0];
        const lineColor = metroLineColors[firstLine] || '#0055A4';
        
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
            tipo: 'metro'
        };
        
        stationMarker.stationData = stationData;
        stationMarker.clickCount = 0;
        stationMarker.clickTimer = null;
        
        // Lógica de click y doble click
        stationMarker.on('click', function(e) {
            this.clickCount++;
            if (this.clickCount === 1) {
                this.clickTimer = setTimeout(() => {
                    showMetroInfo(stationData);
                    this.clickCount = 0;
                }, 200);
            } else if (this.clickCount === 2) {
                clearTimeout(this.clickTimer);
                selectStationForRoute(stationData);
                this.clickCount = 0;
            }
        });
        
        // Crear tooltip con todas las líneas
        const lineNames = lines.map(line => `L${line}`).join(', ');
        stationMarker.bindTooltip(
            `${name}<br><strong>${lineNames}</strong><br><small>Click: Info | Doble click: Ruta</small>`,
            {
                permanent: false,
                direction: 'top',
                offset: [0, -10],
                className: 'metro-tooltip'
            }
        );
        
        // Añadir la estación a todas las capas de líneas que le corresponden
        lines.forEach(line => {
            if (window.metroLayers[line]) {
                window.metroLayers[line].addLayer(stationMarker);
                console.log(`Estación ${name} añadida a capa L${line}`);
            } else {
                console.warn(`Capa L${line} no encontrada para estación ${name}`);
            }
        });
    });
    
    // Añadir las rutas de las líneas
    if (metroData.lines) {
        console.log('Procesando rutas de líneas:', metroData.lines.length, 'rutas encontradas');
        metroData.lines.forEach(line => {
            const lineType = line.line;
            const lineColor = line.color || metroLineColors[lineType] || '#0055A4';
            
            console.log(`Procesando ruta L${lineType}: color=${lineColor}`);
            
            if (window.metroLayers[lineType] && line.coordinates) {
                const polyline = L.polyline(line.coordinates, {
                    color: lineColor,
                    weight: 4,
                    opacity: 0.8
                });
                window.metroLayers[lineType].addLayer(polyline);
                console.log(`Ruta de L${lineType} añadida a la capa con color ${lineColor}`);
            } else {
                console.warn(`No se pudo añadir ruta para L${lineType}: capa=${!!window.metroLayers[lineType]}, coordenadas=${!!line.coordinates}`);
            }
        });
    } else {
        console.warn('No se encontraron rutas en los datos de Metro');
    }
    
    console.log('Estaciones de Metro dibujadas en capas:', Object.keys(window.metroLayers));
    
    // NO añadir capas automáticamente al mapa - solo dibujarlas
    // Las capas se añadirán/removerán cuando el usuario pulse el botón
    console.log('Capas de Metro dibujadas y listas para activar con el botón');
    
    // NO activar el botón automáticamente
    // El botón se activará/desactivará cuando el usuario lo pulse
    console.log('Botón de Metro listo para control manual');
    
    console.log('Metro dibujado correctamente - esperando activación manual');
}

function showMetroInfo(stationData) {
    // Llenar información en el panel para Metro
    document.getElementById('station-name').textContent = stationData.name;
    document.getElementById('station-id').textContent = `${stationData.id_fijo} (Modal: ${stationData.id_modal})`;
    document.getElementById('station-line').textContent = Array.from(stationData.lines).map(l => `L${l}`).join(', ');
    document.getElementById('station-zone').textContent = stationData.zone;
    document.getElementById('station-type').textContent = 'Metro';
    
    // Mostrar el panel de información
    document.getElementById('station-info-panel').style.display = 'block';
}

function toggleAllMetro() {
    console.log('toggleAllMetro llamado');
    const allVisible = Object.values(metroLayers).every(layer => map.hasLayer(layer));
    console.log('Estado actual - Todas las líneas visibles:', allVisible);
    console.log('Capas disponibles:', Object.keys(metroLayers));
    
    if (allVisible) {
        // Ocultar todas las capas
        console.log('Ocultando todas las capas de Metro...');
        Object.values(metroLayers).forEach(layer => {
            map.removeLayer(layer);
        });
        console.log('Todas las capas de Metro ocultadas');
    } else {
        // Mostrar todas las capas
        console.log('Mostrando todas las capas de Metro...');
        Object.values(metroLayers).forEach(layer => {
            map.addLayer(layer);
        });
        console.log('Todas las capas de Metro mostradas');
    }
    
    // Actualizar el estado del botón principal
    const button = document.querySelector('.transport-button.metro');
    if (button) {
        if (allVisible) {
            button.classList.remove('active');
            console.log('Botón principal desactivado');
        } else {
            button.classList.add('active');
            console.log('Botón principal activado');
        }
    } else {
        console.error('Botón principal de Metro no encontrado');
    }
    
    // Actualizar botones individuales
    Object.keys(metroLayers).forEach(lineNumber => {
        const lineButton = document.querySelector(`.line-button.metro-line[data-line="${lineNumber}"]`);
        if (lineButton) {
            if (allVisible) {
                lineButton.classList.remove('active');
            } else {
                lineButton.classList.add('active');
            }
        }
    });
}

// Función para obtener el estado de visibilidad de todas las líneas
function areAllMetroLinesVisible() {
    return Object.values(metroLayers).every(layer => map.hasLayer(layer));
}

// Función para alternar una línea específica de Metro
function toggleMetroLine(lineNumber) {
    console.log(`toggleMetroLine llamado para línea ${lineNumber}`);
    
    if (!metroLayers[lineNumber]) {
        console.error(`Capa L${lineNumber} no encontrada`);
        return;
    }
    
    const isVisible = map.hasLayer(metroLayers[lineNumber]);
    const button = document.querySelector(`.line-button.metro-line[data-line="${lineNumber}"]`);
    
    if (isVisible) {
        // Ocultar la línea
        map.removeLayer(metroLayers[lineNumber]);
        if (button) {
            button.classList.remove('active');
        }
        console.log(`Línea ${lineNumber} oculta`);
    } else {
        // Mostrar la línea
        map.addLayer(metroLayers[lineNumber]);
        if (button) {
            button.classList.add('active');
        }
        console.log(`Línea ${lineNumber} mostrada`);
    }
    
    // Actualizar el estado del botón principal
    updateMainMetroButtonState();
}

// Función para actualizar el estado del botón principal
function updateMainMetroButtonState() {
    const mainButton = document.querySelector('.transport-button.metro');
    const allVisible = areAllMetroLinesVisible();
    
    if (mainButton) {
        if (allVisible) {
            mainButton.classList.add('active');
        } else {
            mainButton.classList.remove('active');
        }
    }
}

// Configurar event listeners para botones individuales
function setupMetroLineButtons() {
    console.log('Configurando botones individuales de Metro...');
    
    const lineButtons = document.querySelectorAll('.line-button.metro-line');
    lineButtons.forEach(button => {
        const lineNumber = button.getAttribute('data-line');
        console.log(`Configurando botón para línea ${lineNumber}`);
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(`Click en botón de línea ${lineNumber}`);
            toggleMetroLine(lineNumber);
        });
        
        // Activar botón si la línea está visible
        if (metroLayers[lineNumber] && map.hasLayer(metroLayers[lineNumber])) {
            button.classList.add('active');
        }
    });
    
    console.log(`${lineButtons.length} botones de líneas de Metro configurados`);
}

// Hacer funciones disponibles globalmente INMEDIATAMENTE
window.toggleAllMetro = toggleAllMetro;
window.initializeMetroLayers = initializeMetroLayers;
window.drawMetro = drawMetro;
window.toggleMetroLine = toggleMetroLine;
window.setupMetroLineButtons = setupMetroLineButtons;

// Inicializar capas inmediatamente
initializeMetroLayers();

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Metro JavaScript inicializado');
    
    // Configurar event listener para el botón principal de Metro
    const metroButton = document.querySelector('.transport-button.metro');
    console.log('Buscando botón de Metro:', metroButton);
    
    if (metroButton) {
        console.log('Botón encontrado, configurando event listener...');
        metroButton.addEventListener('click', function(e) {
            console.log('Click en botón principal de Metro detectado');
            e.preventDefault();
            if (typeof toggleAllMetro === 'function') {
                console.log('Llamando a toggleAllMetro...');
                toggleAllMetro();
            } else {
                console.error('Función toggleAllMetro no disponible');
            }
        });
        console.log('Event listener configurado para botón de Metro');
    } else {
        console.error('Botón de Metro no encontrado');
    }
    
    // Configurar botones individuales de líneas
    setupMetroLineButtons();
});

// Timestamp: 06/27/2025 18:35:00 