#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def agregar_api_v5_route():
    """Agrega la nueva API v5 para cálculo de rutas al app.py"""
    
    codigo_nuevo = '''

# ============================================================================
# API v5.0 - SISTEMA AVANZADO DE RUTAS
# ============================================================================

@app.route('/api/v5/route')
def calculate_route_v5():
    """API v5.0 para calcular rutas con algoritmos avanzados"""
    try:
        # Obtener parámetros
        origen = request.args.get('origen', '').strip().upper()
        destino = request.args.get('destino', '').strip().upper()
        algoritmo = request.args.get('algoritmo', 'dijkstra_bidirectional')
        optimizacion = request.args.get('optimizacion', 'min_time')
        
        # Validar parámetros obligatorios
        if not origen or not destino:
            return jsonify({
                'success': False,
                'error': 'Parámetros origen y destino son obligatorios',
                'ejemplo': '/api/v5/route?origen=SOL&destino=CALLAO'
            }), 400
        
        if origen == destino:
            return jsonify({
                'success': False,
                'error': 'Las estaciones de origen y destino no pueden ser iguales'
            }), 400
        
        # Cargar sistema v5.0
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado',
                'solucion': 'Ejecuta: python generar_timing_avanzado.py'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        # Buscar IDs de estaciones
        origen_id = None
        destino_id = None
        
        for station_id, station_data in metro_data['stations'].items():
            if station_data['nombre'] == origen:
                origen_id = station_id
            if station_data['nombre'] == destino:
                destino_id = station_id
        
        if not origen_id:
            return jsonify({
                'success': False,
                'error': f'Estación de origen "{origen}" no encontrada',
                'sugerencia': 'Verifica el nombre exacto de la estación'
            }), 404
        
        if not destino_id:
            return jsonify({
                'success': False,
                'error': f'Estación de destino "{destino}" no encontrada',
                'sugerencia': 'Verifica el nombre exacto de la estación'
            }), 404
        
        # Crear grafo y calcular ruta
        from collections import defaultdict
        import heapq
        
        # Crear grafo simplificado
        grafo = defaultdict(list)
        edges_dict = {}
        
        for edge in metro_data['edges']:
            from_id = edge['from_id']
            to_id = edge['to_id']
            
            grafo[from_id].append(to_id)
            edges_dict[(from_id, to_id)] = edge
        
        # Algoritmo Dijkstra simplificado
        def dijkstra_simple(start, end):
            distances = {start: 0}
            previous = {}
            unvisited = set(metro_data['stations'].keys())
            
            while unvisited:
                current = min(unvisited, key=lambda x: distances.get(x, float('inf')))
                
                if distances.get(current, float('inf')) == float('inf'):
                    break
                    
                if current == end:
                    break
                    
                unvisited.remove(current)
                
                for neighbor in grafo[current]:
                    if neighbor in unvisited:
                        edge = edges_dict.get((current, neighbor))
                        if edge:
                            # Calcular coste según optimización
                            if optimizacion == 'min_time':
                                coste = edge['time'] + edge['transfer_penalty']
                            elif optimizacion == 'min_transfers':
                                coste = edge['time'] + (edge['transfer_penalty'] * 5)
                            elif optimizacion == 'min_distance':
                                coste = edge['distance']
                            else:
                                coste = edge['time']
                            
                            new_distance = distances[current] + coste
                            
                            if new_distance < distances.get(neighbor, float('inf')):
                                distances[neighbor] = new_distance
                                previous[neighbor] = current
            
            # Reconstruir path
            if end not in previous and end != start:
                return None
            
            path = []
            current = end
            while current is not None:
                path.append(current)
                current = previous.get(current)
            path.reverse()
            
            return {
                'path': path,
                'total_time': distances.get(end, 0),
                'algorithm': algoritmo
            }
        
        # Calcular ruta
        resultado = dijkstra_simple(origen_id, destino_id)
        
        if not resultado:
            return jsonify({
                'success': False,
                'error': 'No se encontró ruta entre las estaciones',
                'origen': origen,
                'destino': destino
            }), 404
        
        # Contar transbordos
        transbordos = 0
        linea_actual = None
        
        path_detallado = []
        for i, station_id in enumerate(resultado['path']):
            station_info = metro_data['stations'][station_id]
            
            # Determinar línea actual
            if i < len(resultado['path']) - 1:
                next_station = resultado['path'][i + 1]
                edge = edges_dict.get((station_id, next_station))
                if edge:
                    if linea_actual is None:
                        linea_actual = edge['line']
                    elif linea_actual != edge['line']:
                        transbordos += 1
                        linea_actual = edge['line']
            
            path_detallado.append({
                'id': station_id,
                'nombre': station_info['nombre'],
                'lineas': station_info['lineas'],
                'es_transbordo': len(station_info['lineas']) > 1 and i > 0 and i < len(resultado['path']) - 1
            })
        
        # Respuesta exitosa
        return jsonify({
            'success': True,
            'data': {
                'origen': {
                    'id': origen_id,
                    'nombre': origen
                },
                'destino': {
                    'id': destino_id,
                    'nombre': destino
                },
                'ruta': {
                    'tiempo_total': round(resultado['total_time'], 1),
                    'transbordos': transbordos,
                    'estaciones': len(resultado['path']),
                    'algoritmo': algoritmo,
                    'optimizacion': optimizacion,
                    'path': path_detallado
                }
            },
            'meta': {
                'version': '5.0.0',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error en API v5 route: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'version': '5.0.0'
        }), 500

@app.route('/api/v5/stations')
def get_stations_v5():
    """API v5.0 para obtener todas las estaciones disponibles"""
    try:
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        estaciones = []
        for station_id, station_data in metro_data['stations'].items():
            estaciones.append({
                'id': station_id,
                'nombre': station_data['nombre'],
                'lineas': station_data['lineas'],
                'correspondencias': station_data.get('correspondencias', [])
            })
        
        # Ordenar por nombre
        estaciones.sort(key=lambda x: x['nombre'])
        
        return jsonify({
            'success': True,
            'data': estaciones,
            'total': len(estaciones),
            'meta': {
                'version': '5.0.0',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v5/info')
def get_info_v5():
    """API v5.0 información del sistema"""
    try:
        import json
        import os
        
        sistema_file = 'timing/metro_madrid_v5.json'
        if not os.path.exists(sistema_file):
            return jsonify({
                'success': False,
                'error': 'Sistema v5.0 no encontrado'
            }), 500
        
        with open(sistema_file, 'r', encoding='utf-8') as f:
            metro_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': {
                'meta': metro_data['meta'],
                'statistics': metro_data['statistics'],
                'algorithms': metro_data['algorithms'],
                'endpoints': {
                    'route': '/api/v5/route?origen=SOL&destino=CALLAO',
                    'stations': '/api/v5/stations',
                    'info': '/api/v5/info'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''
    
    print("📝 Agregando API v5.0 al archivo app.py...")
    
    # Leer archivo actual
    with open('app.py', 'r', encoding='utf-8') as f:
        contenido_actual = f.read()
    
    # Verificar si ya existe la API v5
    if 'api/v5/route' in contenido_actual:
        print("⚠️  API v5.0 ya existe en app.py")
        return False
    
    # Agregar antes de la última línea o al final
    if 'if __name__ == \'__main__\':' in contenido_actual:
        # Insertar antes del if __name__
        partes = contenido_actual.rsplit('if __name__ == \'__main__\':', 1)
        nuevo_contenido = partes[0] + codigo_nuevo + '\nif __name__ == \'__main__\':' + partes[1]
    else:
        # Agregar al final
        nuevo_contenido = contenido_actual + codigo_nuevo
    
    # Escribir archivo actualizado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)
    
    print("✅ API v5.0 agregada exitosamente!")
    print("\n🔗 Endpoints disponibles:")
    print("   • /api/v5/route?origen=SOL&destino=CALLAO")
    print("   • /api/v5/stations")
    print("   • /api/v5/info")
    
    return True

if __name__ == '__main__':
    agregar_api_v5_route() 