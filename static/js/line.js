document.addEventListener('DOMContentLoaded', () => {
    // Las variables `stationsData` y `lineInfo` deben estar disponibles globalmente
    // o pasarse de otra manera antes de que este script se ejecute.
    if (typeof stationsData === 'undefined' || typeof lineInfo === 'undefined') {
        console.error("Los datos de la línea o las estaciones no están definidos.");
        return;
    }

    console.log("Datos de estaciones:", stationsData);
    console.log("Información de línea:", lineInfo);

    const API_URL = {
        stationSchedule: "/api/schedules/station/",
        status: "/api/status"
    };

    // Colores de las líneas del metro
    function getLineColor(lineName) {
        const colors = {
            '1': '#00AEEF', '2': '#FF0000', '3': '#FFDF00', '4': '#824100',
            '5': '#339900', '6': '#999999', '7': '#FF6600', '8': '#FF69B4',
            '9': '#990066', '10': '#000099', '11': '#006600', '12': '#999933',
            'R': '#FF0000', 'C': '#0070C0', 'ML1': '#36A9E1', 'ML2': '#97C93D', 'ML3': '#FAB20B'
        };
        return colors[lineName] || '#666666';
    }

    function renderStations() {
        const stationList = document.querySelector('.station-list');
        if (!stationList) return;
        
        stationList.innerHTML = ''; // Reset content

        if (!stationsData || stationsData.length === 0) return;

        stationsData.forEach((station, index) => {
            const stationEntry = document.createElement('li');
            
            const isInterchange = station.connecting_lines && station.connecting_lines.length > 1;
            const isTerminus = index === 0 || index === stationsData.length - 1;
            
            stationEntry.className = 'station-entry';
            if (isInterchange) stationEntry.classList.add('interchange');
            if (isTerminus) stationEntry.classList.add('terminus');

            stationEntry.dataset.stopId = station.id;

            // Generar HTML para las correspondencias
            let correspondenciasHtml = '';
            if (station.connecting_lines && station.connecting_lines.length > 1) {
                console.log(`Estación ${station.name} tiene ${station.connecting_lines.length} líneas de conexión:`, station.connecting_lines);
                
                correspondenciasHtml = '<div class="station-correspondencias">';
                let addedConnections = 0;
                
                // Normalizar el nombre de la línea actual para comparación
                const currentLineName = lineInfo.name ? lineInfo.name.toString().replace(/[^0-9A-Za-z]/g, '') : '';
                const currentLineId = lineInfo.id ? lineInfo.id.toString().replace(/[^0-9A-Za-z]/g, '') : '';
                
                station.connecting_lines.forEach(conn => {
                    // Normalizar el nombre de la conexión para comparación
                    const connName = conn.name ? conn.name.toString().replace(/[^0-9A-Za-z]/g, '') : '';
                    
                    // Comparar tanto con el nombre como con el ID de la línea actual
                    if (connName !== currentLineName && connName !== currentLineId && conn.name !== lineInfo.name) {
                        const lineName = conn.name.trim();

                        // Lista de todas las correspondencias que tienen un icono SVG.
                        const svgIconLines = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'R', 'C', 'ML1', 'ML2', 'ML3'];
                        
                        // Mapeo para nombres de archivo que no siguen el patrón 'linea-X'.
                        const specialFileNames = {
                            '6': 'linea-6-circular',
                            '12': 'linea-12-metrosur',
                            'R': 'ramal',
                            'C': 'cercanias-renfe',
                            'ML1': 'ml1',
                            'ML2': 'ml2',
                            'ML3': 'ml3'
                        };

                        // Si la correspondencia tiene un icono SVG, creamos la etiqueta con badge.
                        if (svgIconLines.includes(lineName)) {
                            const color = getLineColor(lineName);
                            correspondenciasHtml += `<span class="line-badge" style="background-color: ${color}">${lineName}</span>`;
                        } else {
                            // Para el resto (BI, BL, BN, AEA, ET), se muestra un texto corto como fallback.
                            correspondenciasHtml += `<span class="line-badge interchange-fallback">${lineName}</span>`;
                        }

                        addedConnections++;
                    }
                });
                
                // Solo mostrar el contenedor si realmente hay correspondencias
                if (addedConnections > 0) {
                    correspondenciasHtml += '</div>';
                } else {
                    correspondenciasHtml = '';
                }
            }

            stationEntry.innerHTML = `
                <div class="station-item">
                    <div class="station-marker"></div>
                    <div class="station-info">
                        <span class="station-name">${station.name}</span>
                        ${correspondenciasHtml}
                        <div class="station-actions">
                            <button class="btn-more-info" onclick="goToStation('${station.name}', '${station.id}')">ℹ️ Info</button>
                            <button class="btn-favorite-station" onclick="addFavoriteStation('${station.id}', '${lineInfo.id}', '${station.name}')">⭐ Fav</button>
                        </div>
                    </div>
                </div>
                <div class="schedule-container"></div>
            `;
            stationList.appendChild(stationEntry);
            
            stationEntry.querySelector('.station-item').addEventListener('click', () => toggleSchedule(station.id));
        });
    }

    async function toggleSchedule(stopId) {
        const stationEntry = document.querySelector(`.station-entry[data-stop-id="${stopId}"]`);
        if (!stationEntry) return;

        const container = stationEntry.querySelector('.schedule-container');
        const isVisible = container.style.display === 'block';
        
        // Ocultar todos los contenedores de horarios
        document.querySelectorAll('.schedule-container').forEach(c => c.style.display = 'none');
        
        if (isVisible) return; // Si ya estaba visible, lo dejamos cerrado

        container.style.display = 'block';
        container.innerHTML = '<p>Buscando horarios...</p>';

        try {
            const response = await fetch(`${API_URL.stationSchedule}${stopId}`);
            const data = await response.json();

            if (!response.ok || data.error) throw new Error(data.error || 'No se encontraron horarios.');
            
            let html = '<h5>Próximas salidas:</h5><ul>';
            if (data.schedules && Object.keys(data.schedules).length > 0) {
                for (const dir in data.schedules) {
                    html += `<li><strong>Sentido ${dir}:</strong><ol>`;
                    const departures = data.schedules[dir];
                    if (departures.length > 0) {
                        departures.slice(0, 5).forEach(t => { html += `<li>${t}</li>`; });
                    } else {
                         html += `<li>No hay salidas próximas.</li>`;
                    }
                    html += `</ol></li>`;
                }
            } else {
                html += '<li>No hay información de horarios disponible.</li>';
            }
            container.innerHTML = html + '</ul>';

        } catch (error) {
            container.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    function updateTrainPositions() {
        fetch(API_URL.status)
            .then(res => res.json())
            .then(data => {
                document.querySelectorAll('.train-icon-wrapper').forEach(el => el.remove());
                const trains = data.trains || [];
                
                trains.forEach(train => {
                    if (train.route_id === lineInfo.id && train.next_stop_id) {
                        const nextStationEl = document.querySelector(`.station-entry[data-stop-id="${train.next_stop_id}"]`);
                        if (nextStationEl) {
                            const trainWrapper = document.createElement('li');
                            trainWrapper.className = 'train-icon-wrapper';
                            const trainIcon = document.createElement('div');
                            trainIcon.className = 'train-icon';
                            trainIcon.innerHTML = '🚇';
                            trainIcon.title = `Tren ${train.train_id}`;
                            
                            const progress = train.progress || 0;
                            trainIcon.style.left = `calc(${progress}% - 12px)`;
                            
                            trainWrapper.appendChild(trainIcon);
                            nextStationEl.parentNode.insertBefore(trainWrapper, nextStationEl);
                        }
                    }
                });
            })
            .catch(err => console.error("Error actualizando trenes:", err));
    }
    
    // Funciones para los botones de acción
    window.goToStation = function(stationName, stationId) {
        window.location.href = `/station/${lineInfo.id}/${stationId}`;
    };

    window.addFavoriteStation = function(stationId, lineId, stationName) {
        // Esta función se implementará cuando esté el sistema de favoritos
        console.log(`Añadiendo a favoritos: ${stationName} (ID: ${stationId}, Línea: ${lineId})`);
        alert('Funcionalidad de favoritos próximamente disponible');
    };

    // Iniciar todo
    renderStations();
    setInterval(updateTrainPositions, 15000);
    updateTrainPositions();
}); 