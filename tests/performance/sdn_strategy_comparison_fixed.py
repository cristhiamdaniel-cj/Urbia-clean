"""
Análisis Comparativo de Estrategias SDN - VERSIÓN CORREGIDA
"""
import time
import threading
import statistics
import json
from datetime import datetime
import sys
import gc
sys.path.insert(0, '/app')

class SDNStrategyBenchmark:
    """Prueba comparativa de estrategias SDN"""
    
    STRATEGIES = ['round_robin', 'shortest_path', 'priority_based', 'load_balancing']
    
    def __init__(self, num_sensors: int = 30, duration: int = 30):
        self.num_sensors = num_sensors
        self.duration = duration
        
    def create_sensors_for_strategy(self, container, strategy_id: str) -> list:
        """Crear sensores únicos para cada estrategia"""
        from src.domain.entities.sensor import Sensor
        from src.domain.value_objects.sensor_id import SensorId
        from src.domain.value_objects.location import Location
        from src.domain.value_objects.priority import Priority
        
        sensors = []
        priorities_list = [
            Priority.CRITICAL, Priority.CRITICAL, Priority.CRITICAL,  # 3 críticos
            Priority.HIGH, Priority.HIGH, Priority.HIGH,  # 3 high
            Priority.HIGH, Priority.HIGH, Priority.HIGH,
            Priority.NORMAL, Priority.NORMAL, Priority.NORMAL,  # resto normal/low
            Priority.NORMAL, Priority.NORMAL, Priority.NORMAL,
            Priority.NORMAL, Priority.NORMAL, Priority.NORMAL,
            Priority.NORMAL, Priority.NORMAL, Priority.NORMAL,
            Priority.NORMAL, Priority.NORMAL, Priority.NORMAL,
            Priority.LOW, Priority.LOW, Priority.LOW,
            Priority.LOW, Priority.LOW, Priority.LOW
        ]
        
        sensor_types = ['RUIDO', 'TEMPERATURA', 'TRAFICO', 'CALIDAD_AIRE', 'LUZ']
        base_lat, base_lng = 5.0703, -75.5138
        timestamp = int(time.time() * 1000000)  # Microsegundos para unicidad
        
        for i in range(self.num_sensors):
            sensor_type = sensor_types[i % len(sensor_types)]
            priority = priorities_list[i % len(priorities_list)]
            
            lat_offset = (i % 10 - 5) * 0.01
            lng_offset = (i // 10 - 2.5) * 0.01
            
            # ID único con estrategia y timestamp
            sensor_id = f"{strategy_id}-{sensor_type[:3]}-{i:03d}-{timestamp}"
            
            sensor = Sensor(
                id=SensorId(sensor_id),
                name=f"{strategy_id} {sensor_type} #{i}",
                type=sensor_type,
                location=Location(
                    base_lat + lat_offset,
                    base_lng + lng_offset,
                    "Manizales"
                ),
                priority=priority,
                unit="test",
                min_value=0,
                max_value=100
            )
            sensors.append(sensor)
            container.sensor_service.register_sensor(sensor)
            
        return sensors
    
    def test_strategy(self, strategy_name: str, strategy_index: int) -> dict:
        """Probar una estrategia específica"""
        print(f"\n{'='*80}")
        print(f"🧪 ESTRATEGIA {strategy_index + 1}/4: {strategy_name.upper().replace('_', ' ')}")
        print(f"{'='*80}\n")
        
        # Importar aquí para evitar cache
        from config.di_container import DIContainer
        
        # Crear contenedor completamente nuevo
        container = DIContainer()
        
        # Crear sensores únicos
        print(f"📡 Creando {self.num_sensors} sensores para {strategy_name}...")
        sensors = self.create_sensors_for_strategy(container, strategy_name.upper()[:3])
        print(f"✅ Sensores registrados\n")
        
        # Configurar infraestructura
        gateways = container.gateway_factory.create_manizales_gateways()
        for gw in gateways:
            container.gateway_service.register_gateway(gw)
        container.gateway_service.auto_assign_sensors()
        container.sdn_controller.initialize_routes()
        
        # FORZAR estrategia específica
        container.sdn_controller.current_strategy_index = strategy_index
        print(f"🎯 Estrategia forzada: {strategy_name}\n")
        
        metrics = {
            'latencies': [],
            'packets_sent': 0,
            'critical_packets': 0,
            'high_packets': 0,
            'normal_packets': 0,
            'route_distribution': {},
            'errors': 0
        }
        lock = threading.Lock()
        
        def simulate_sensor(sensor):
            nonlocal metrics
            start_time = time.time()
            
            from src.domain.value_objects.priority import Priority
            
            while time.time() - start_time < self.duration:
                try:
                    value = 50.0 + (hash(str(sensor.id)) % 50)
                    
                    route_start = time.time()
                    decision = container.sdn_controller.route_packet(str(sensor.id))
                    route_latency = (time.time() - route_start) * 1000
                    
                    container.telemetry_service.process_telemetry(str(sensor.id), value)
                    
                    with lock:
                        metrics['latencies'].append(route_latency)
                        metrics['packets_sent'] += 1
                        
                        if sensor.priority == Priority.CRITICAL:
                            metrics['critical_packets'] += 1
                        elif sensor.priority == Priority.HIGH:
                            metrics['high_packets'] += 1
                        else:
                            metrics['normal_packets'] += 1
                        
                        route = decision.selected_route
                        metrics['route_distribution'][route] = \
                            metrics['route_distribution'].get(route, 0) + 1
                    
                    # Intervalo según prioridad
                    if sensor.priority == Priority.CRITICAL:
                        time.sleep(0.5)
                    elif sensor.priority == Priority.HIGH:
                        time.sleep(1)
                    else:
                        time.sleep(2)
                        
                except Exception as e:
                    with lock:
                        metrics['errors'] += 1
        
        # Lanzar threads
        threads = []
        start_time = time.time()
        
        print(f"🚀 Iniciando simulación de {self.duration}s...\n")
        
        for sensor in sensors:
            thread = threading.Thread(target=simulate_sensor, args=(sensor,), daemon=True)
            thread.start()
            threads.append(thread)
        
        # Monitoreo cada 10s
        last_count = 0
        while time.time() - start_time < self.duration:
            time.sleep(10)
            elapsed = time.time() - start_time
            current = metrics['packets_sent']
            tput = (current - last_count) / 10
            last_count = current
            print(f"   ⏳ {elapsed:.0f}s | {current} pkt | {tput:.1f} pkt/s")
        
        # Esperar
        for t in threads:
            t.join(timeout=2)
        
        actual_duration = time.time() - start_time
        
        # Calcular métricas finales
        result = {
            'strategy': strategy_name,
            'duration': round(actual_duration, 1),
            'total_packets': metrics['packets_sent'],
            'throughput': round(metrics['packets_sent'] / actual_duration, 2),
            'critical_packets': metrics['critical_packets'],
            'high_packets': metrics['high_packets'],
            'normal_packets': metrics['normal_packets'],
            'latency': {
                'min': round(min(metrics['latencies']), 3) if metrics['latencies'] else 0,
                'max': round(max(metrics['latencies']), 3) if metrics['latencies'] else 0,
                'mean': round(statistics.mean(metrics['latencies']), 3) if metrics['latencies'] else 0,
                'median': round(statistics.median(metrics['latencies']), 3) if metrics['latencies'] else 0,
                'p95': round(sorted(metrics['latencies'])[int(len(metrics['latencies']) * 0.95)], 3)
                    if len(metrics['latencies']) > 20 else 0,
                'stdev': round(statistics.stdev(metrics['latencies']), 3)
                    if len(metrics['latencies']) > 1 else 0
            },
            'route_distribution': metrics['route_distribution'],
            'errors': metrics['errors'],
            'success_rate': round((metrics['packets_sent'] - metrics['errors']) / 
                                 metrics['packets_sent'] * 100, 1)
                if metrics['packets_sent'] > 0 else 0
        }
        
        print(f"\n✅ {strategy_name}: {result['total_packets']} pkt, "
              f"{result['throughput']} pkt/s, "
              f"{result['latency']['mean']}ms latencia\n")
        
        # Limpiar
        del container
        gc.collect()
        time.sleep(2)
        
        return result
    
    def run_comparison(self):
        """Ejecutar comparación completa"""
        print(f"\n{'#'*80}")
        print(f"# ANÁLISIS COMPARATIVO DE 4 ESTRATEGIAS SDN")
        print(f"# {self.num_sensors} sensores × {self.duration}s cada estrategia")
        print(f"{'#'*80}\n")
        
        all_results = []
        
        for i, strategy in enumerate(self.STRATEGIES):
            result = self.test_strategy(strategy, i)
            all_results.append(result)
            
            if i < len(self.STRATEGIES) - 1:
                print(f"⏸️  Pausa de 10s antes de la siguiente estrategia...\n")
                time.sleep(10)
        
        # Guardar
        with open('/app/results/sdn_strategy_comparison.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Imprimir comparación
        self.print_comparison(all_results)
        
        return all_results
    
    def print_comparison(self, results):
        """Tabla comparativa final"""
        print(f"\n\n{'='*80}")
        print("📊 COMPARACIÓN FINAL DE ESTRATEGIAS SDN")
        print(f"{'='*80}\n")
        
        print(f"{'Estrategia':<20} | {'Throughput':>12} | {'Lat.Media':>11} | {'P95':>9} | {'Éxito':>8}")
        print(f"{'-'*20}-+-{'-'*12}-+-{'-'*11}-+-{'-'*9}-+-{'-'*8}")
        
        for r in results:
            name = r['strategy'].replace('_', ' ').title()
            print(f"{name:<20} | {r['throughput']:>10.2f} p/s | "
                  f"{r['latency']['mean']:>9.3f}ms | {r['latency']['p95']:>7.3f}ms | "
                  f"{r['success_rate']:>7.1f}%")
        
        print(f"\n{'='*80}")
        
        # Ganadores
        best_tput = max(results, key=lambda x: x['throughput'])
        best_lat = min(results, key=lambda x: x['latency']['mean'])
        best_p95 = min(results, key=lambda x: x['latency']['p95'])
        
        print("\n🏆 MEJORES ESTRATEGIAS POR MÉTRICA:")
        print(f"   • Throughput: {best_tput['strategy'].replace('_', ' ').title()} "
              f"({best_tput['throughput']:.2f} pkt/s)")
        print(f"   • Latencia Media: {best_lat['strategy'].replace('_', ' ').title()} "
              f"({best_lat['latency']['mean']:.3f}ms)")
        print(f"   • Latencia P95: {best_p95['strategy'].replace('_', ' ').title()} "
              f"({best_p95['latency']['p95']:.3f}ms)")
        
        print(f"\n💾 Detalles: /app/results/sdn_strategy_comparison.json\n")

if __name__ == "__main__":
    benchmark = SDNStrategyBenchmark(num_sensors=30, duration=30)
    benchmark.run_comparison()
