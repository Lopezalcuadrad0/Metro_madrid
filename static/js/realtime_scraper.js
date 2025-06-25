/**
 * Sistema de Scraping en Tiempo Real para Estaciones del Metro de Madrid
 * - Carga datos automáticamente al hacer clic en estaciones
 * - Muestra indicadores de carga
 * - Gestiona cache y actualizaciones
 */

class RealtimeMetroScraper {
    constructor() {
        this.loadingStations = new Set();
        this.cacheStatus = {};
        this.init();
    }

    init() {
        console.log('🚇 Inicializando sistema de scraping en tiempo real...');
        this.setupEventListeners();
        this.updateCacheStatus();
    }

    setupEventListeners() {
        // Escuchar clics en estaciones del mapa
        document.addEventListener('click', (e) => {
            const stationMarker = e.target.closest('.station-marker, .leaflet-marker-icon');
            if (stationMarker) {
                const stationId = stationMarker.dataset.stationId;
                const lineNumber = stationMarker.dataset.lineNumber;
                
                if (stationId && lineNumber) {
                    this.loadStationData(lineNumber, stationId);
                }
            }
        });

        // Escuchar clics en enlaces de estaciones
        document.addEventListener('click', (e) => {
            const stationLink = e.target.closest('a[href*="/station/"]');
            if (stationLink) {
                const href = stationLink.getAttribute('href');
                const match = href.match(/\/station\/(\d+)\/(\d+)/);
                if (match) {
                    const lineNumber = match[1];
                    const stationId = match[2];
                    this.loadStationData(lineNumber, stationId);
                }
            }
        });
    }

    async loadStationData(lineNumber, stationId) {
        if (this.loadingStations.has(stationId)) {
            console.log(`⏳ Estación ${stationId} ya se está cargando...`);
            return;
        }

        this.loadingStations.add(stationId);
        this.showLoadingIndicator(stationId);

        try {
            console.log(`🔍 Cargando datos de estación ${stationId} (Línea ${lineNumber})...`);
            
            // Usar el nuevo endpoint completo que incluye todos los servicios
            const response = await fetch(`/api/station/${lineNumber}/${stationId}/complete`);
            const result = await response.json();

            if (result.success) {
                this.handleStationData(stationId, result.data, result.from_cache);
            } else {
                this.handleError(stationId, result.error);
            }

        } catch (error) {
            console.error(`❌ Error cargando estación ${stationId}:`, error);
            this.handleError(stationId, 'Error de conexión');
        } finally {
            this.loadingStations.delete(stationId);
            this.hideLoadingIndicator(stationId);
        }
    }

    async forceRefreshStation(lineNumber, stationId) {
        try {
            console.log(`🔄 Forzando actualización de estación ${stationId}...`);
            
            // Obtener el nombre de la estación
            const searchResponse = await fetch(`/api/station/search?q=${stationId}`);
            const searchResult = await searchResponse.json();
            
            if (!searchResult || searchResult.length === 0) {
                throw new Error('Estación no encontrada');
            }
            
            const stationName = searchResult[0].value;
            
            // Usar el endpoint correcto de refresh
            const response = await fetch(`/api/station/refresh-trains/${encodeURIComponent(stationName)}`);
            const result = await response.json();

            if (result.success) {
                this.handleStationData(stationId, result, false);
                this.showNotification('✅ Datos actualizados correctamente', 'success');
            } else {
                this.handleError(stationId, result.error);
            }

        } catch (error) {
            console.error(`❌ Error actualizando estación ${stationId}:`, error);
            this.handleError(stationId, 'Error de conexión');
        }
    }

    handleStationData(stationId, data, fromCache) {
        console.log(`✅ Datos recibidos para estación ${stationId}`, data);
        
        // El endpoint /complete devuelve {data: {static: {...}, dynamic: {...}}}
        let staticData = data;
        let dynamicData = {};
        
        // Si viene del endpoint /complete, extraer static y dynamic
        if (data.data && data.data.static) {
            staticData = data.data.static;
            dynamicData = data.data.dynamic || {};
        }

        // Buscar elementos de la interfaz que mostrar los datos
        const stationElements = document.querySelectorAll(`[data-station-id="${stationId}"]`);
        
        stationElements.forEach(element => {
            // Actualizar información básica
            const nameElement = element.querySelector('.station-name');
            if (nameElement && staticData.name) {
                nameElement.textContent = staticData.name;
            }

            // Actualizar estado de ascensores
            const elevatorElement = element.querySelector('.elevator-status');
            if (elevatorElement) {
                const elevatorStatus = dynamicData.elevator_status || 'No disponible';
                elevatorElement.textContent = elevatorStatus;
                elevatorElement.className = 'elevator-status ' + this.getElevatorStatusClass(elevatorStatus);
            }

            // Actualizar estado de escaleras
            const escalatorElement = element.querySelector('.escalator-status');
            if (escalatorElement) {
                const escalatorStatus = dynamicData.escalator_status || 'No disponible';
                escalatorElement.textContent = escalatorStatus;
                escalatorElement.className = 'escalator-status ' + this.getElevatorStatusClass(escalatorStatus);
            }

            // Actualizar próximos trenes
            const trainsElement = element.querySelector('.next-trains');
            if (trainsElement && dynamicData.proximos_trenes_html) {
                trainsElement.innerHTML = dynamicData.proximos_trenes_html;
            }

            // Actualizar zona tarifaria
            const tariffElement = element.querySelector('.tariff-zone');
            if (tariffElement && staticData.zona_tarifaria) {
                tariffElement.textContent = `Zona ${staticData.zona_tarifaria}`;
            }

            // Actualizar servicios
            const servicesElement = element.querySelector('.station-services');
            if (servicesElement && staticData.services) {
                servicesElement.innerHTML = this.formatServicesFromObject(staticData.services);
            }

            // Actualizar servicios detallados
            const detailedServicesElement = element.querySelector('.detailed-services');
            if (detailedServicesElement && staticData.servicios_detallados) {
                detailedServicesElement.innerHTML = this.formatServices(staticData.servicios_detallados);
            }

            // Actualizar correspondencias
            const correspondencesElement = element.querySelector('.correspondences');
            if (correspondencesElement && staticData.correspondencias) {
                correspondencesElement.innerHTML = this.formatCorrespondences(staticData.correspondencias);
            }

            // Actualizar última actualización
            const lastUpdateElement = element.querySelector('.last-update');
            if (lastUpdateElement && dynamicData.last_update) {
                lastUpdateElement.textContent = `Actualizado: ${dynamicData.last_update}`;
            }
        });

        // Si estamos en la página de detalle de estación, actualizar toda la página
        if (window.location.pathname.includes(`/station/${stationId}`)) {
            this.updateStationDetailPage(staticData, dynamicData);
        }
        
        // Mostrar notificación
        const cacheText = fromCache ? ' (desde cache)' : ' (actualizado)';
        this.showNotification(`📊 Datos cargados${cacheText}`, 'info');
        
        // Actualizar estadísticas de cache
        this.updateCacheStatus();
    }

    formatServicesFromObject(services) {
        if (!services) {
            return '<span class="no-data">Sin servicios especiales</span>';
        }

        const serviceIcons = {
            'accessible': '♿',
            'defibrillator': '💓',
            'elevators': '🛗',
            'escalators': '🛗',
            'mobileCoverage': '📱',
            'shops': '🛍️',
            'bibliometro': '📚',
            'ttp_office': '🏢',
            'park_ride': '🅿️',
            'once': '👁️',
            'historical': '🏛️'
        };

        const serviceNames = {
            'accessible': 'Accesible',
            'defibrillator': 'Desfibrilador',
            'elevators': 'Ascensores',
            'escalators': 'Escaleras mecánicas',
            'mobileCoverage': 'Cobertura móvil',
            'shops': 'Tiendas',
            'bibliometro': 'Bibliometro',
            'ttp_office': 'Oficina TTP',
            'park_ride': 'Parking',
            'once': 'ONCE',
            'historical': 'Histórico'
        };

        const activeServices = Object.entries(services)
            .filter(([key, value]) => value === true)
            .map(([key, value]) => {
                const icon = serviceIcons[key] || '🔧';
                const name = serviceNames[key] || key;
                return `<span class="service-badge" title="${name}">${icon} ${name}</span>`;
            });

        if (activeServices.length === 0) {
            return '<span class="no-data">Sin servicios especiales</span>';
        }

        return activeServices.join(' ');
    }

    updateStationDetailPage(data) {
        // Actualizar título de la página
        const pageTitle = document.querySelector('h1');
        if (pageTitle && data.station_name) {
            pageTitle.textContent = data.station_name;
        }

        // Actualizar próximos trenes
        const trainsContainer = document.getElementById('next-trains-container');
        if (trainsContainer && data.proximos_trenes_html) {
            trainsContainer.innerHTML = data.proximos_trenes_html;
        }

        // Actualizar estado de ascensores
        const elevatorContainer = document.getElementById('elevator-status-container');
        if (elevatorContainer && data.estado_ascensores) {
            elevatorContainer.innerHTML = `<p><strong>Estado de ascensores:</strong> ${data.estado_ascensores}</p>`;
        }

        // Actualizar estado de escaleras
        const escalatorContainer = document.getElementById('escalator-status-container');
        if (escalatorContainer && data.estado_escaleras) {
            escalatorContainer.innerHTML = `<p><strong>Estado de escaleras:</strong> ${data.estado_escaleras}</p>`;
        }

        // Actualizar última actualización
        const lastUpdateContainer = document.getElementById('last-update-container');
        if (lastUpdateContainer && data.last_update) {
            lastUpdateContainer.innerHTML = `<p><strong>Última actualización:</strong> ${data.last_update}</p>`;
        }
    }

    formatCorrespondences(correspondences) {
        if (!correspondences || correspondences.length === 0) {
            return '<span class="no-data">Sin correspondencias</span>';
        }

        return correspondences.map(line => 
            `<span class="line-badge">${line}</span>`
        ).join(' ');
    }

    formatServices(services) {
        if (!services || services.length === 0) {
            return '<span class="no-data">Sin servicios especiales</span>';
        }

        return services.map(service => 
            `<span class="service-badge">${service}</span>`
        ).join(' ');
    }

    formatAccesses(accesses) {
        if (!accesses || accesses.length === 0) {
            return '<p class="no-data">Información de accesos no disponible</p>';
        }

        return accesses.map(access => `
            <div class="access-item">
                <h4>${access.nombre || 'Acceso sin nombre'}</h4>
                <p><strong>Vestíbulo:</strong> ${access.vestibulo}</p>
                <p><strong>Dirección:</strong> ${access.direccion}</p>
            </div>
        `).join('');
    }

    formatConnections(connections) {
        if (!connections || connections.length === 0) {
            return '<p class="no-data">Sin conexiones adicionales</p>';
        }

        return connections.map(connection => 
            `<span class="connection-badge">${connection}</span>`
        ).join(' ');
    }

    getElevatorStatusClass(status) {
        if (!status) return 'unknown';
        
        const lowerStatus = status.toLowerCase();
        if (lowerStatus.includes('funcionando') || lowerStatus.includes('operativo')) {
            return 'working';
        } else if (lowerStatus.includes('averiado') || lowerStatus.includes('fuera de servicio')) {
            return 'broken';
        } else if (lowerStatus.includes('mantenimiento')) {
            return 'maintenance';
        }
        return 'unknown';
    }

    showLoadingIndicator(stationId) {
        const stationElements = document.querySelectorAll(`[data-station-id="${stationId}"]`);
        
        stationElements.forEach(element => {
            // Añadir clase de carga
            element.classList.add('loading');
            
            // Añadir spinner si no existe
            if (!element.querySelector('.loading-spinner')) {
                const spinner = document.createElement('div');
                spinner.className = 'loading-spinner';
                spinner.innerHTML = '⏳';
                element.appendChild(spinner);
            }
        });
    }

    hideLoadingIndicator(stationId) {
        const stationElements = document.querySelectorAll(`[data-station-id="${stationId}"]`);
        
        stationElements.forEach(element => {
            element.classList.remove('loading');
            
            const spinner = element.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        });
    }

    handleError(stationId, error) {
        console.error(`❌ Error en estación ${stationId}:`, error);
        
        const stationElements = document.querySelectorAll(`[data-station-id="${stationId}"]`);
        
        stationElements.forEach(element => {
            element.classList.add('error');
            
            // Mostrar mensaje de error
            const errorElement = element.querySelector('.error-message') || document.createElement('div');
            errorElement.className = 'error-message';
            errorElement.textContent = `Error: ${error}`;
            
            if (!element.querySelector('.error-message')) {
                element.appendChild(errorElement);
            }
        });

        this.showNotification(`❌ Error cargando datos: ${error}`, 'error');
    }

    async updateCacheStatus() {
        try {
            const response = await fetch('/api/cache/status');
            const result = await response.json();

            if (result.success) {
                this.cacheStatus = result.cache_stats;
                this.updateCacheUI();
            }
        } catch (error) {
            console.error('Error obteniendo estado del cache:', error);
        }
    }

    updateCacheUI() {
        const cacheInfoElement = document.getElementById('cache-info');
        if (cacheInfoElement && this.cacheStatus) {
            cacheInfoElement.innerHTML = `
                <div class="cache-stats">
                    <span class="cache-stat">
                        <strong>${this.cacheStatus.total_cached_stations || 0}</strong> estaciones en cache
                    </span>
                    <span class="cache-stat">
                        <strong>${this.cacheStatus.recently_updated || 0}</strong> actualizadas recientemente
                    </span>
                </div>
            `;
        }
    }

    showNotification(message, type = 'info') {
        // Crear notificación
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Añadir al DOM
        const container = document.getElementById('notifications-container') || document.body;
        container.appendChild(notification);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Métodos públicos para uso externo
    refreshStation(lineNumber, stationId) {
        return this.forceRefreshStation(lineNumber, stationId);
    }

    getCacheStatus() {
        return this.cacheStatus;
    }
}

// Inicializar el scraper cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    window.metroScraper = new RealtimeMetroScraper();
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeMetroScraper;
} 