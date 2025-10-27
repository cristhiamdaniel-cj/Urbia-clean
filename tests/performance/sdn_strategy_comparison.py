"""
Análisis Comparativo de las 4 Estrategias SDN
Para validar cuál es más eficiente según el escenario
"""
import time
import threading
import statistics
import json
from datetime import datetime
import sys
sys.path.insert(0, '/app')

from config.di_container import DIContainer
from src.domain.entities.sensor import Sensor
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority

class SDNStrategyBenchmark:
    """Prueba comparativa de estrategias SDN"""
    
    STRATEGIES = ['round_robin', 'shortest_path', 'priority_based', 'load_balancing']
    
    def __init__(self, num_sensors: int = 30, duration: int = 30):
        self.num_sensors = num_sensors
        self.duration = duration
        self.results = {}
        
    def create_test_sensors(self, container, priority_dist=None) -> list:
        """Crear sensores con distribución de prioridad configurable"""
        sensors = []
        
        if priority_dist is None:
            # Distribución estándar
            priority_dist = {
                Priority.CRITICAL: 0.2,
                Priority.HIGH: 0.3,
                Priority.NORMAL: 0.4,
                Priority.LOW: 0.1
            }
        
        priorities = []
        for priority, ratio in priority_dist.items():
            count = int(self.num_sensors * ratio)
            priorities.extend([priority] * count)
        
        # Completar hasta num_sensors
        while len(priorities) < self.num_sensors:
            priorities.append(Priority.NORMAL)
        
        sensor_types = ['RUIDO', 'TEMPERATURA', 'TRAFICO', 'CALIDAD_AIRE', 'LUZ']
        base_lat, base_lng = 5.0703, -75.5138
        
        for i in range(self.num_sensors):
            sensor_type = sensor_types[i % len(sensor_types)]
            priority = priorities[i]
            
            lat_offset = (i % 10 - 5) * 0.01
            lng_offset = (i // 10 - 2.5) * 0.01
            
            sensor = Sensor(
                id=SensorId(f"SDN-{sensor_type[:3]}-{i:03d}-{int(time.time())}"),
                name=f"SDN Test {sensor_type} #{i}",
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
    
    def test_strategy(self, strategy_name: str, sensors: list) -> dict:
        """Probar una estrategia específica"""
        print(f"\n{'='*80}")
        print(f"🧪 PROBANDO ESTRATEGIA: {strategy_name.upper().replace('_', ' ')}")
        print(f"{'='*80}\n")
        
        # Crear nuevo contenedor
        container = DIContainer()
        
        # Registrar sensores
        for sensor in sensors:
            container.sensor_service.register_sensor(sensor)
        
        # Configurar infraestructura
        gateways = container.gateway_factory.create_manizales_gateways()
        for gw in gateways:
            container.gateway_service.register_gateway(gw)
        container.gateway_service.auto_assign_sensors()
        container.sdn_controller.initialize_routes()
        
        # Forzar estrategia específica
        container.sdn_controller.current_strategy_index = self.STRATEGIES.index(strategy_name)
        
        metrics = {
            'latencies': [],
            'packets_sent': 0,
            'critical_packets': 0,
            'route_distribution': {},
            'errors': 0
        }
        lock = threading.Lock()
        
        def simulate_sensor(sensor):
            nonlocal metrics
            start_time = time.time()
            
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
                        
                        # Contar distribución de rutas
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
        
        for sensor in sensors:
            thread = threading.Thread(target=simulate_sensor, args=(sensor,), daemon=True)
            thread.start()
            threads.append(thread)
        
        # Monitoreo
        print(f"⏱️  Ejecutando durante {self.duration}s...\n")
        while time.time() - start_time < self.duration:
            time.sleep(5)
            elapsed = time.time() - start_time
            print(f"   {elapsed:.0f}s | {metrics['packets_sent']} paquetes enviados")
        
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
            'critical_ratio': round(metrics['critical_packets'] / metrics['packets_sent'] * 100, 1)
                if metrics['packets_sent'] > 0 else 0,
            'latency': {
                'min': round(min(metrics['latencies']), 2) if metrics['latencies'] else 0,
                'max': round(max(metrics['latencies']), 2) if metrics['latencies'] else 0,
                'mean': round(statistics.mean(metrics['latencies']), 2) if metrics['latencies'] else 0,
                'median': round(statistics.median(metrics['latencies']), 2) if metrics['latencies'] else 0,
                'p95': round(sorted(metrics['latencies'])[int(len(metrics['latencies']) * 0.95)], 2)
                    if len(metrics['latencies']) > 20 else 0,
                'stdev': round(statistics.stdev(metrics['latencies']), 2)
                    if len(metrics['latencies']) > 1 else 0
            },
            'route_distribution': metrics['route_distribution'],
            'errors': metrics['errors'],
            'success_rate': round((metrics['packets_sent'] - metrics['errors']) / 
                                 metrics['packets_sent'] * 100, 1)
                if metrics['packets_sent'] > 0 else 0
        }
        
        print(f"\n✅ Completado: {result['total_packets']} paquetes, "
              f"{result['throughput']} pkt/s, "
              f"latencia media {result['latency']['mean']}ms\n")
        
        return result
    
    def run_comparison(self):
        """Ejecutar comparación completa"""
        print(f"\n{'#'*80}")
        print(f"# ANÁLISIS COMPARATIVO DE ESTRATEGIAS SDN")
        print(f"# {self.num_sensors} sensores durante {self.duration}s por estrategia")
        print(f"{'#'*80}\n")
        
        # Crear sensores base (se copiarán para cada estrategia)
        print("📡 Creando configuración base de sensores...")
        container_temp = DIContainer()
        base_sensors = self.create_test_sensors(container_temp)
        print(f"✅ {len(base_sensors)} sensores configurados\n")
        
        all_results = []
        
        for i, strategy in enumerate(self.STRATEGIES, 1):
            print(f"\n{'='*80}")
            print(f"PRUEBA {i}/4: {strategy.upper().replace('_', ' ')}")
            print(f"{'='*80}")
            
            result = self.test_strategy(strategy, base_sensors)
            all_results.append(result)
            
            if i < len(self.STRATEGIES):
                print(f"\n⏸️  Pausa de 10 segundos antes de la siguiente estrategia...")
                time.sleep(10)
        
        # Guardar resultados
        with open('/app/results/sdn_strategy_comparison.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Imprimir comparación final
        self.print_comparison(all_results)
        
        return all_results
    
    def print_comparison(self, results):
        """Imprimir tabla comparativa"""
        print(f"\n\n{'='*80}")
        print("📊 COMPARACIÓN FINAL DE ESTRATEGIAS")
        print(f"{'='*80}\n")
        
        print(f"{'Estrategia':<25} | {'Throughput':>12} | {'Latencia':>10} | {'P95':>8} | {'Éxito':>8}")
        print(f"{'-'*25}-+-{'-'*12}-+-{'-'*10}-+-{'-'*8}-+-{'-'*8}")
        
        for r in results:
            strategy_name = r['strategy'].replace('_', ' ').title()
            print(f"{strategy_name:<25} | {r['throughput']:>10.2f} p/s | "
                  f"{r['latency']['mean']:>8.2f}ms | {r['latency']['p95']:>6.2f}ms | "
                  f"{r['success_rate']:>7.1f}%")
        
        print(f"\n{'='*80}\n")
        
        # Ganadores
        best_throughput = max(results, key=lambda x: x['throughput'])
        best_latency = min(results, key=lambda x: x['latency']['mean'])
        
        print("🏆 MEJORES ESTRATEGIAS:")
        print(f"   • Máximo Throughput: {best_throughput['strategy'].replace('_', ' ').title()} "
              f"({best_throughput['throughput']:.1f} pkt/s)")
        print(f"   • Mínima Latencia: {best_latency['strategy'].replace('_', ' ').title()} "
              f"({best_latency['latency']['mean']:.2f}ms)")
        
        print(f"\n💾 Resultados detallados: /app/results/sdn_strategy_comparison.json\n")

if __name__ == "__main__":
    benchmark = SDNStrategyBenchmark(num_sensors=30, duration=30)
    benchmark.run_comparison()
