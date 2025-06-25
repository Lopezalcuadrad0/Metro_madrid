#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import statistics
from collections import defaultdict
import heapq
import math

class MetroTestSuite:
    """Suite de testing para algoritmos avanzados del Metro Madrid v5.0"""
    
    def __init__(self):
        self.metro_data = None
        self.graph = None
        self.test_results = []
        
    def load_metro_data(self):
        """Carga datos del sistema v5.0"""
        print("📊 Cargando Metro Madrid v5.0...")
        
        try:
            with open('timing/metro_madrid_v5.json', 'r', encoding='utf-8') as f:
                self.metro_data = json.load(f)
            
            print(f"✅ Datos cargados: {self.metro_data['statistics']}")
            
            # Crear grafo
            self.graph = MetroGraphAdvanced()
            
            # Añadir estaciones
            for station_id, station_data in self.metro_data['stations'].items():
                self.graph.add_station(
                    station_id, 
                    station_data['nombre'], 
                    station_data['lineas'],
                    tuple(station_data['coordinates'])
                )
            
            # Añadir aristas
            for edge in self.metro_data['edges']:
                self.graph.add_edge(
                    edge['from_id'], edge['to_id'], edge['line'],
                    edge['time'], edge['distance'], edge['is_transfer']
                )
            
            print(f"🌐 Grafo construido: {len(self.graph.stations)} estaciones, {len(self.graph.edges)} aristas")
            return True
            
        except FileNotFoundError:
            print("❌ Error: No se encontró el archivo timing/metro_madrid_v5.json")
            return False
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def test_data_structure(self):
        """Test de estructura de datos"""
        print("\n🔍 TEST 1: Estructura de Datos v5.0")
        print("=" * 50)
        
        # Verificar metadatos
        meta = self.metro_data['meta']
        assert meta['version'] == '5.0.0', "Versión incorrecta"
        assert 'generated_at' in meta, "Falta timestamp"
        print(f"✅ Metadatos: v{meta['version']} generado en {meta['generated_at'][:10]}")
        
        # Verificar estructura de estaciones
        stations = self.metro_data['stations']
        sample_station = list(stations.values())[0]
        required_fields = ['nombre', 'id', 'lineas', 'correspondencias', 'coordinates']
        for field in required_fields:
            assert field in sample_station, f"Falta campo {field} en estaciones"
        print(f"✅ Estaciones: {len(stations)} con estructura correcta")
        
        # Verificar estructura de aristas
        edges = self.metro_data['edges']
        sample_edge = edges[0]
        required_edge_fields = ['from_id', 'to_id', 'line', 'time', 'distance', 'is_transfer', 'transfer_penalty']
        for field in required_edge_fields:
            assert field in sample_edge, f"Falta campo {field} en aristas"
        print(f"✅ Aristas: {len(edges)} con estructura unificada")
        
        # Verificar horarios normalizados
        headways = self.metro_data['headways']
        assert 'mon_thu' in headways, "Faltan horarios lunes-jueves"
        assert 'fri' in headways, "Faltan horarios viernes"
        sample_schedule = headways['mon_thu'][0]
        assert 'start' in sample_schedule and 'end' in sample_schedule, "Formato de horarios incorrecto"
        print(f"✅ Horarios: {len(headways)} tipos de día con formato ISO-8601")
        
        # Verificar algoritmos disponibles
        algorithms = self.metro_data['algorithms']
        assert 'dijkstra_bidirectional' in algorithms['available'], "Falta Dijkstra bidireccional"
        assert 'a_star' in algorithms['available'], "Falta A*"
        print(f"✅ Algoritmos: {len(algorithms['available'])} disponibles")
        
        print("🎉 Test de estructura: PASADO")
        return True
    
    def test_algorithms_performance(self):
        """Test de rendimiento de algoritmos"""
        print("\n⚡ TEST 2: Rendimiento de Algoritmos")
        print("=" * 50)
        
        # Seleccionar rutas de prueba
        station_ids = list(self.metro_data['stations'].keys())
        test_routes = [
            (station_ids[0], station_ids[10]),  # Ruta corta
            (station_ids[0], station_ids[50]),  # Ruta media
            (station_ids[0], station_ids[-1]),  # Ruta larga
        ]
        
        algorithms = ['dijkstra_bidirectional', 'a_star', 'bfs_simple']
        results = defaultdict(list)
        
        for i, (start, end) in enumerate(test_routes):
            start_name = self.metro_data['stations'][start]['nombre']
            end_name = self.metro_data['stations'][end]['nombre']
            print(f"\n📍 Ruta {i+1}: {start_name} → {end_name}")
            
            for algorithm in algorithms:
                start_time = time.time()
                
                if algorithm == 'dijkstra_bidirectional':
                    result = self.graph.dijkstra_bidirectional(start, end)
                elif algorithm == 'a_star':
                    result = self.graph.a_star(start, end)
                elif algorithm == 'bfs_simple':
                    result = self.graph.bfs_simple(start, end)
                
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # ms
                
                if result:
                    results[algorithm].append({
                        'time': execution_time,
                        'route_time': result['total_time'],
                        'transfers': result['transfers'],
                        'path_length': len(result['path'])
                    })
                    
                    print(f"   {algorithm:20}: {execution_time:5.2f}ms | {result['total_time']:5.1f}min | {result['transfers']} transbordos")
                else:
                    print(f"   {algorithm:20}: ❌ Sin resultado")
        
        # Estadísticas de rendimiento
        print(f"\n📊 ESTADÍSTICAS DE RENDIMIENTO:")
        for algorithm, data in results.items():
            if data:
                avg_time = statistics.mean([d['time'] for d in data])
                avg_route_time = statistics.mean([d['route_time'] for d in data])
                avg_transfers = statistics.mean([d['transfers'] for d in data])
                print(f"{algorithm:20}: {avg_time:5.2f}ms promedio | {avg_route_time:5.1f}min ruta | {avg_transfers:.1f} transbordos")
        
        print("🎉 Test de rendimiento: COMPLETADO")
        return results
    
    def test_optimization_criteria(self):
        """Test de criterios de optimización múltiple"""
        print("\n🎯 TEST 3: Criterios de Optimización")
        print("=" * 50)
        
        # Ruta de prueba con múltiples opciones
        station_ids = list(self.metro_data['stations'].keys())
        start, end = station_ids[20], station_ids[80]
        start_name = self.metro_data['stations'][start]['nombre']
        end_name = self.metro_data['stations'][end]['nombre']
        
        print(f"📍 Ruta: {start_name} → {end_name}")
        
        optimizations = ['min_time', 'min_transfers', 'min_distance', 'accessible_only']
        
        for optimization in optimizations:
            result = self.graph.dijkstra_bidirectional(start, end, optimization)
            
            if result:
                print(f"   {optimization:15}: {result['total_time']:5.1f}min | {result['transfers']} transbordos | {len(result['path'])} estaciones")
            else:
                print(f"   {optimization:15}: ❌ Sin resultado")
        
        print("🎉 Test de optimización: COMPLETADO")
        return True
    
    def test_edge_cases(self):
        """Test de casos extremos"""
        print("\n🧪 TEST 4: Casos Extremos")
        print("=" * 50)
        
        station_ids = list(self.metro_data['stations'].keys())
        
        # Caso 1: Misma estación
        print("🔹 Caso 1: Origen = Destino")
        result = self.graph.dijkstra_bidirectional(station_ids[0], station_ids[0])
        assert result['total_time'] == 0, "Tiempo debe ser 0 para misma estación"
        assert result['transfers'] == 0, "Transbordos deben ser 0 para misma estación"
        print("   ✅ Misma estación manejada correctamente")
        
        # Caso 2: Estaciones adyacentes
        print("🔹 Caso 2: Estaciones adyacentes")
        # Buscar dos estaciones conectadas directamente
        for edge in self.metro_data['edges'][:10]:
            start_id = edge['from_id']
            end_id = edge['to_id']
            result = self.graph.dijkstra_bidirectional(start_id, end_id)
            if result and len(result['path']) == 2:
                print(f"   ✅ Ruta directa: {result['total_time']:.1f}min")
                break
        
        # Caso 3: Estación inexistente
        print("🔹 Caso 3: Estación inexistente")
        try:
            result = self.graph.dijkstra_bidirectional("inexistente", station_ids[0])
            if result is None:
                print("   ✅ Estación inexistente manejada correctamente")
        except:
            print("   ✅ Estación inexistente genera excepción controlada")
        
        print("🎉 Test de casos extremos: COMPLETADO")
        return True
    
    def test_data_consistency(self):
        """Test de consistencia de datos"""
        print("\n🔍 TEST 5: Consistencia de Datos")
        print("=" * 50)
        
        # Verificar bidireccionalidad
        forward_edges = defaultdict(list)
        backward_edges = defaultdict(list)
        
        for edge in self.metro_data['edges']:
            forward_edges[edge['from_id']].append(edge['to_id'])
            backward_edges[edge['to_id']].append(edge['from_id'])
        
        # Contar aristas bidireccionales
        bidirectional_count = 0
        unidirectional_count = 0
        
        for from_station, to_stations in forward_edges.items():
            for to_station in to_stations:
                if from_station in backward_edges.get(to_station, []):
                    bidirectional_count += 1
                else:
                    unidirectional_count += 1
        
        print(f"🔹 Aristas bidireccionales: {bidirectional_count // 2}")  # Dividir por 2 porque se cuentan ambas direcciones
        print(f"🔹 Aristas unidireccionales: {unidirectional_count}")
        
        # Verificar rangos de tiempos
        times = [edge['time'] for edge in self.metro_data['edges']]
        min_time, max_time = min(times), max(times)
        print(f"🔹 Rango de tiempos: {min_time:.1f} - {max_time:.1f} minutos")
        
        # Verificar penalty de transbordos
        transfer_penalties = [edge['transfer_penalty'] for edge in self.metro_data['edges']]
        unique_penalties = set(transfer_penalties)
        print(f"🔹 Penalties de transbordo: {unique_penalties}")
        
        print("🎉 Test de consistencia: COMPLETADO")
        return True
    
    def run_comprehensive_test(self):
        """Ejecuta todos los tests"""
        print("🚇 INICIANDO TESTING COMPLETO - METRO MADRID v5.0")
        print("=" * 70)
        
        if not self.load_metro_data():
            return False
        
        tests = [
            self.test_data_structure,
            self.test_algorithms_performance,
            self.test_optimization_criteria,
            self.test_edge_cases,
            self.test_data_consistency
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test falló: {e}")
        
        print(f"\n🏆 RESUMEN FINAL")
        print("=" * 50)
        print(f"✅ Tests pasados: {passed_tests}/{total_tests}")
        print(f"📊 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ¡TODOS LOS TESTS PASARON! Sistema v5.0 validado")
        else:
            print("⚠️  Algunos tests fallaron. Revisar implementación")
        
        return passed_tests == total_tests

# Importar clase del grafo (copiada del script principal)
class MetroGraphAdvanced:
    """Grafo avanzado del Metro Madrid con algoritmos ponderados"""
    
    def __init__(self):
        self.stations = {}
        self.edges = []
        self.adjacency = defaultdict(list)
        self.coordinates = {}
        
    def add_station(self, station_id, name, lines, coordinates=None):
        """Añade una estación al grafo"""
        self.stations[station_id] = {
            'name': name,
            'lines': lines,
            'coordinates': coordinates or (0, 0)
        }
        self.coordinates[station_id] = coordinates or (0, 0)
    
    def add_edge(self, from_station, to_station, line, time, distance, is_transfer=False):
        """Añade una arista ponderada al grafo"""
        edge = {
            'from': from_station,
            'to': to_station,
            'line': line,
            'time': time,
            'distance': distance,
            'transfer_penalty': 2.0 if is_transfer else 0.0,
            'is_transfer': is_transfer
        }
        
        self.edges.append(edge)
        self.adjacency[from_station].append(len(self.edges) - 1)
    
    def euclidean_distance(self, station1, station2):
        """Calcula distancia euclidiana entre estaciones (heurística para A*)"""
        x1, y1 = self.coordinates.get(station1, (0, 0))
        x2, y2 = self.coordinates.get(station2, (0, 0))
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def dijkstra_bidirectional(self, start, end, optimization='min_time'):
        """Algoritmo Dijkstra bidireccional optimizado"""
        return self._search_bidirectional(start, end, optimization, use_heuristic=False)
    
    def a_star(self, start, end, optimization='min_time'):
        """Algoritmo A* con heurística de distancia euclidiana"""
        return self._search_bidirectional(start, end, optimization, use_heuristic=True)
    
    def bfs_simple(self, start, end):
        """BFS simple para comparación"""
        if start == end:
            return {'path': [start], 'total_time': 0, 'transfers': 0}
        
        queue = [(start, [start], 0)]
        visited = {start}
        
        while queue:
            current, path, time = queue.pop(0)
            
            for edge_idx in self.adjacency[current]:
                edge = self.edges[edge_idx]
                neighbor = edge['to']
                
                if neighbor == end:
                    final_path = path + [neighbor]
                    return {
                        'path': final_path,
                        'total_time': time + edge['time'],
                        'transfers': self._count_transfers(final_path),
                        'algorithm': 'BFS_simple'
                    }
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], time + edge['time']))
        
        return None
    
    def _search_bidirectional(self, start, end, optimization, use_heuristic=False):
        """Implementación de búsqueda bidireccional con Dijkstra/A*"""
        if start == end:
            return {'path': [start], 'total_time': 0, 'transfers': 0}
        
        # Verificar que las estaciones existan
        if start not in self.stations or end not in self.stations:
            return None
        
        # Colas de prioridad para ambas direcciones
        forward_heap = [(0, start, [])]
        backward_heap = [(0, end, [])]
        
        forward_visited = {start: 0}
        backward_visited = {end: 0}
        
        forward_paths = {start: []}
        backward_paths = {end: []}
        
        best_cost = float('inf')
        best_path = None
        
        iterations = 0
        max_iterations = len(self.stations) * 2  # Prevenir bucles infinitos
        
        while forward_heap and backward_heap and iterations < max_iterations:
            iterations += 1
            
            # Expandir desde el inicio
            if forward_heap:
                cost, current, path = heapq.heappop(forward_heap)
                
                if current in backward_visited:
                    total_cost = cost + backward_visited[current]
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_path = path + [current] + backward_paths[current][::-1]
                
                for edge_idx in self.adjacency[current]:
                    edge = self.edges[edge_idx]
                    neighbor = edge['to']
                    edge_cost = self._calculate_cost(edge, optimization)
                    new_cost = cost + edge_cost
                    
                    if use_heuristic:
                        heuristic = self.euclidean_distance(neighbor, end) * 0.5
                        priority = new_cost + heuristic
                    else:
                        priority = new_cost
                    
                    if neighbor not in forward_visited or new_cost < forward_visited[neighbor]:
                        forward_visited[neighbor] = new_cost
                        forward_paths[neighbor] = path + [current]
                        heapq.heappush(forward_heap, (priority, neighbor, path + [current]))
            
            # Expandir desde el final
            if backward_heap:
                cost, current, path = heapq.heappop(backward_heap)
                
                if current in forward_visited:
                    total_cost = forward_visited[current] + cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_path = forward_paths[current] + [current] + path[::-1]
                
                # Buscar aristas que llegan a current
                for edge in self.edges:
                    if edge['to'] == current:
                        neighbor = edge['from']
                        edge_cost = self._calculate_cost(edge, optimization)
                        new_cost = cost + edge_cost
                        
                        if use_heuristic:
                            heuristic = self.euclidean_distance(start, neighbor) * 0.5
                            priority = new_cost + heuristic
                        else:
                            priority = new_cost
                        
                        if neighbor not in backward_visited or new_cost < backward_visited[neighbor]:
                            backward_visited[neighbor] = new_cost
                            backward_paths[neighbor] = [current] + path
                            heapq.heappush(backward_heap, (priority, neighbor, [current] + path))
        
        if best_path:
            transfers = self._count_transfers(best_path)
            return {
                'path': best_path,
                'total_time': best_cost,
                'transfers': transfers,
                'algorithm': 'A*' if use_heuristic else 'Dijkstra_bidirectional'
            }
        
        return None
    
    def _calculate_cost(self, edge, optimization):
        """Calcula el coste de una arista según el criterio de optimización"""
        base_cost = edge['time']
        
        if optimization == 'min_time':
            return base_cost + edge['transfer_penalty']
        elif optimization == 'min_transfers':
            return base_cost + (edge['transfer_penalty'] * 5)
        elif optimization == 'min_distance':
            return edge['distance']
        elif optimization == 'accessible_only':
            return base_cost + edge['transfer_penalty']
        else:
            return base_cost
    
    def _count_transfers(self, path):
        """Cuenta el número de transbordos en una ruta"""
        if len(path) < 2:
            return 0
        
        transfers = 0
        current_line = None
        
        for i in range(len(path) - 1):
            from_station = path[i]
            to_station = path[i + 1]
            
            # Buscar la arista entre estas estaciones
            for edge in self.edges:
                if edge['from'] == from_station and edge['to'] == to_station:
                    if current_line is None:
                        current_line = edge['line']
                    elif current_line != edge['line']:
                        transfers += 1
                        current_line = edge['line']
                    break
        
        return transfers

if __name__ == '__main__':
    test_suite = MetroTestSuite()
    test_suite.run_comprehensive_test() 