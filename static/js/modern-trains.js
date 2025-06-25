/**
 * MODERN TRAINS - Sistema moderno de trenes para Metro de Madrid
 * ==============================================================
 * 
 * Maneja la visualización de próximos trenes y datos en tiempo real
 */

// Variables globales
let currentTrainsData = null;
let trainsUpdateInterval = null;

// Función para inicializar el sistema de trenes
function initializeModernTrains() {
    console.log('🚄 Inicializando sistema moderno de trenes');
    
    // Limpiar intervalos existentes
    if (trainsUpdateInterval) {
        clearInterval(trainsUpdateInterval);
    }
}

// Función para actualizar los trenes modernos por ID de estación
async function updateModernTrainsById(stationId, containerId = 'modernTrainsContainer') {
    try {
        console.log(`🚄 Actualizando trenes para estación ID: ${stationId}`);
        
        // Si tenemos el id_modal, convertirlo a nombre de estación
        let stationName = null;
        
        // Intentar obtener el nombre desde el input de búsqueda primero
        const searchInput = document.getElementById('stationSearchInput');
        stationName = searchInput ? searchInput.value.trim() : '';
        
        // Si no hay nombre en el input, intentar usar el stationId si parece ser un nombre
        if (!stationName) {
            // Si stationId parece ser un nombre (contiene letras), usarlo directamente
            if (isNaN(stationId) && typeof stationId === 'string' && stationId.length > 2) {
                stationName = stationId;
                console.log(`✅ Usando stationId como nombre: ${stationName}`);
            } else if (!isNaN(stationId)) {
                // Solo si es un número, intentar convertir id_modal a nombre
                try {
                    const nameResponse = await fetch(`/api/station/id-modal/${stationId}/name`);
                    if (nameResponse.ok) {
                        const nameData = await nameResponse.json();
                        stationName = nameData.station_name;
                        console.log(`✅ Nombre de estación obtenido desde id_modal: ${stationName}`);
                    }
                } catch (error) {
                    console.warn('No se pudo obtener el nombre de la estación desde id_modal:', error);
                }
            }
        }
        
        // Si aún no tenemos nombre, mostrar error
        if (!stationName) {
            throw new Error(`No se pudo obtener el nombre de la estación para ID: ${stationId}`);
        }
        
        // Ahora usar el endpoint correcto con el nombre de la estación
        const response = await fetch(`/api/station/raw-trains/${encodeURIComponent(stationName)}`);
        
        if (!response.ok) {
            throw new Error(`Estación no encontrada: ${stationName}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('✅ Datos de trenes obtenidos:', data);
        
        // Mostrar los datos en el contenedor
        displayRawTrainsData(data, containerId);
        
        // Devolver éxito
        return data;
        
    } catch (error) {
        console.error('❌ Error cargando trenes:', error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <p>❌ Error cargando trenes: ${error.message}</p>
                    <button onclick="updateModernTrainsById('${stationId}', '${containerId}')" class="retry-button">
                        🔄 Reintentar
                    </button>
                </div>
            `;
        }
        
        // Re-lanzar el error para que pueda ser capturado por el .catch()
        throw error;
    }
}

// Función para mostrar los datos de trenes crudos
function displayRawTrainsData(data, containerId = 'modernTrainsContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    console.log('📊 Datos recibidos en displayRawTrainsData:', data);
    
    // Verificar si tenemos datos de trenes
    if (!data.trains_data || !data.trains_data.lineas || data.trains_data.lineas.length === 0) {
        container.innerHTML = `
            <div class="no-trains-message">
                <h4>🚄 Próximos Trenes</h4>
                <p>No hay información disponible en este momento</p>
                <small>Última actualización: ${new Date().toLocaleTimeString()}</small>
            </div>
        `;
        return;
    }
    
    let html = '<div class="modern-trains-container">';
    html += '<div class="trains-header">';
    html += '<h4>🚄 Próximos Trenes</h4>';
    html += '<div class="trains-status">';
    html += `<span class="status-indicator online">● En tiempo real</span>`;
    html += `<small>Actualizado: ${new Date().toLocaleTimeString()}</small>`;
    html += '</div>';
    html += '</div>';
    
    html += '<div class="trains-content">';
    
    // Mostrar cada línea - usar data.trains_data.lineas
    data.trains_data.lineas.forEach(linea => {
        html += '<div class="line-container">';
        html += `<div class="line-header" style="border-left: 4px solid ${linea.color}">`;
        html += `<img src="${linea.logo}" alt="Línea ${linea.numero}" class="line-logo">`;
        html += `<span class="line-name">${linea.nombre}</span>`;
        html += '</div>';
        
        html += '<div class="directions-container">';
        linea.direcciones.forEach(direccion => {
            html += '<div class="direction">';
            html += `<div class="destination">${direccion.destino}</div>`;
            
            if (direccion.sin_prevision) {
                html += '<div class="no-prediction">Sin previsión</div>';
            } else {
                html += '<div class="times">';
                direccion.tiempos.forEach((tiempo, index) => {
                    const isNext = index === 0;
                    html += `<span class="time ${isNext ? 'next' : ''}">${tiempo} min</span>`;
                });
                html += '</div>';
            }
            html += '</div>';
        });
        html += '</div>';
        html += '</div>';
    });
    
    html += '</div>'; // trains-content
    html += '</div>'; // modern-trains-container
    
    container.innerHTML = html;
}

// Función para mostrar trenes detallados
function showDetailedTrains() {
    if (currentTrainsData && currentTrainsData.proximos_trenes_html) {
        // Crear modal con información detallada
        const modal = document.createElement('div');
        modal.className = 'trains-modal';
        modal.innerHTML = `
            <div class="trains-modal-content">
                <div class="trains-modal-header">
                    <h3>🚄 Horarios Detallados</h3>
                    <button onclick="closeTrainsModal()" class="close-btn">&times;</button>
                </div>
                <div class="trains-modal-body">
                    ${currentTrainsData.proximos_trenes_html}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Añadir estilos para el modal
        const style = document.createElement('style');
        style.textContent = `
            .trains-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            .trains-modal-content {
                background: white;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 80%;
                overflow-y: auto;
            }
            .trains-modal-header {
                padding: 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .trains-modal-body {
                padding: 20px;
            }
            .close-btn {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
            }
            .close-btn:hover {
                color: #333;
            }
        `;
        document.head.appendChild(style);
    }
}

// Función para cerrar modal de trenes
function closeTrainsModal() {
    const modal = document.querySelector('.trains-modal');
    if (modal) {
        modal.remove();
    }
}

// Función para actualizar trenes automáticamente
function startAutoUpdate(stationId, containerId = 'modernTrainsContainer', interval = 30000) {
    console.log(`🔄 Iniciando actualización automática cada ${interval/1000}s`);
    
    // Actualización inicial
    updateModernTrainsById(stationId, containerId);
    
    // Configurar intervalo
    trainsUpdateInterval = setInterval(() => {
        updateModernTrainsById(stationId, containerId);
    }, interval);
}

// Función para detener actualización automática
function stopAutoUpdate() {
    if (trainsUpdateInterval) {
        clearInterval(trainsUpdateInterval);
        trainsUpdateInterval = null;
        console.log('⏹️ Actualización automática detenida');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeModernTrains();
});

// Exportar funciones para uso global
window.updateModernTrainsById = updateModernTrainsById;
window.displayRawTrainsData = displayRawTrainsData;
window.showDetailedTrains = showDetailedTrains;
window.closeTrainsModal = closeTrainsModal;
window.startAutoUpdate = startAutoUpdate;
window.stopAutoUpdate = stopAutoUpdate; 