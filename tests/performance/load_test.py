"""
Sistema de Pruebas de Carga para UrbIA IoT
Simula 50+ sensores y mide rendimiento del controlador SDN
"""
import time
import threading
import statistics
from datetime import datetime
from typing import List, Dict
import json
import sys
sys.path.insert(0, '/app')

from config.di_container import DIContainer
from src.domain.entities.sensor import Sensor
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority

class LoadTestRunner:
    def __init__(self, num_sensors: int = 50):
        self.num_sensors = num_sensors
        self.container = DIContainer()
        self.results = {
            'latencies': [],
            'throughput': [],
            'errors': 0,
            'strategy_distribution': {'round_robin': 0, 'shortest_path': 0, 'priority': 0, 'load_balance': 0},
            'sensor_metrics': {}
        }
        self.lock = threading.Lock()
        
    def create_test_sensors(self) -> List[Sensor]:
        """Crear sensores de prueba"""
        sensors = []
        sensor_types = ['RUIDO', 'TEMPERATURA', 'TRAFICO', 'CALIDAD_AIRE', 'LUZ']
        priorities = [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]
        
        # Coordenadas alrededor de Manizales
        base_lat, base_lng = 5.0703, -75.5138
        
        for i in range(self.num_sensors):
            sensor_type = sensor_types[i % len(sensor_types)]
            priority = priorities[i % len(priorities)]
            
            # Distribuir geográficamente
            lat_offset = (i % 10 - 5) * 0.01
            lng_offset = (i // 10 - 2.5) * 0.01
            
            sensor = Sensor(
                id=SensorId(f"TEST-{sensor_type[:3]}-{i:03d}"),
                name=f"Test Sensor {sensor_type} #{i}",
                type=sensor_type,
                location=Location(
                    base_lat + lat_offset,
                    base_lng + lng_offset,
                    "Manizales"
                ),
                priority=priority,
                unit="test_unit",
                min_value=0,
                max_value=100
            )
            sensors.append(sensor)
            self.container.sensor_service.register_sensor(sensor)
            
        return sensors
    
    def simulate_sensor(self, sensor: Sensor, duration: int):
        """Simular telemetría de un sensor"""
        start_time = time.time()
        packets_sent = 0
        local_latencies = []
        
        while time.time() - start_time < duration:
            try:
                # Generar valor
                value = 50.0 + (hash(sensor.id.value) % 50)
                
                # Medir tiempo de enrutamiento
                route_start = time.time()
                decision = self.container.sdn_controller.route_packet(str(sensor.id))
                route_latency = (time.time() - route_start) * 1000  # ms
                
                # Procesar telemetría
                self.container.telemetry_service.process_telemetry(str(sensor.id), value)
                
                packets_sent += 1
                local_latencies.append(route_latency)
                
                # Registrar estrategia usada
                with self.lock:
                    strategy_key = decision.strategy.lower().replace(' ', '_')
                    if strategy_key in self.results['strategy_distribution']:
                        self.results['strategy_distribution'][strategy_key] += 1
                
                # Intervalo variable según prioridad
                if sensor.priority == Priority.CRITICAL:
                    time.sleep(0.5)
                elif sensor.priority == Priority.HIGH:
                    time.sleep(1)
                else:
                    time.sleep(2)
                    
            except Exception as e:
                with self.lock:
                    self.results['errors'] += 1
                print(f"Error en sensor {sensor.id}: {e}")
        
        # Guardar métricas del sensor
        with self.lock:
            self.results['latencies'].extend(local_latencies)
            self.results['sensor_metrics'][str(sensor.id)] = {
                'packets_sent': packets_sent,
                'avg_latency': statistics.mean(local_latencies) if local_latencies else 0
            }
    
    def run_load_test(self, duration: int = 60):
        """Ejecutar prueba de carga"""
        print(f"\n{'='*80}")
        print(f"🔥 PRUEBA DE CARGA - {self.num_sensors} SENSORES")
        print(f"{'='*80}\n")
        
        print(f"⏱️  Duración: {duration} segundos")
        print(f"📡 Sensores: {self.num_sensors}")
        print(f"🎯 Objetivo: Medir capacidad máxima del sistema\n")
        
        # Crear sensores
        print("🔧 Creando sensores de prueba...")
        sensors = self.create_test_sensors()
        print(f"✅ {len(sensors)} sensores creados\n")
        
        # Inicializar gateways
        gateways = self.container.gateway_factory.create_manizales_gateways()
        for gw in gateways:
            self.container.gateway_service.register_gateway(gw)
        self.container.gateway_service.auto_assign_sensors()
        
        # Inicializar SDN
        self.container.sdn_controller.initialize_routes()
        
        print(f"🚀 Iniciando simulación ({datetime.now().strftime('%H:%M:%S')})...\n")
        
        # Lanzar threads para cada sensor
        threads = []
        start_time = time.time()
        
        for sensor in sensors:
            thread = threading.Thread(target=self.simulate_sensor, args=(sensor, duration))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Monitoreo en tiempo real
        last_packet_count = 0
        while time.time() - start_time < duration:
            time.sleep(5)
            elapsed = time.time() - start_time
            total_packets = sum(m['packets_sent'] for m in self.results['sensor_metrics'].values())
            throughput = (total_packets - last_packet_count) / 5
            last_packet_count = total_packets
            
            print(f"⏳ {elapsed:.0f}s | 📦 {total_packets} paquetes | 🔥 {throughput:.1f} pkt/s | ❌ {self.results['errors']} errores")
        
        # Esperar a que terminen todos los threads
        for thread in threads:
            thread.join()
        
        actual_duration = time.time() - start_time
        
        print(f"\n✅ Prueba completada en {actual_duration:.1f} segundos\n")
        
        # Generar reporte
        return self.generate_report(actual_duration)
    
    def generate_report(self, duration: float) -> Dict:
        """Generar reporte de resultados"""
        total_packets = sum(m['packets_sent'] for m in self.results['sensor_metrics'].values())
        
        report = {
            'test_config': {
                'num_sensors': self.num_sensors,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            },
            'performance': {
                'total_packets': total_packets,
                'avg_throughput': total_packets / duration,
                'errors': self.results['errors'],
                'error_rate': (self.results['errors'] / total_packets * 100) if total_packets > 0 else 0
            },
            'latency': {
                'min': min(self.results['latencies']) if self.results['latencies'] else 0,
                'max': max(self.results['latencies']) if self.results['latencies'] else 0,
                'mean': statistics.mean(self.results['latencies']) if self.results['latencies'] else 0,
                'median': statistics.median(self.results['latencies']) if self.results['latencies'] else 0,
                'stdev': statistics.stdev(self.results['latencies']) if len(self.results['latencies']) > 1 else 0
            },
            'strategies': self.results['strategy_distribution'],
            'top_sensors': sorted(
                [{'id': k, **v} for k, v in self.results['sensor_metrics'].items()],
                key=lambda x: x['packets_sent'],
                reverse=True
            )[:10]
        }
        
        return report

def print_report(report: Dict):
    """Imprimir reporte formateado"""
    print(f"\n{'='*80}")
    print("📊 REPORTE DE PRUEBA DE CARGA")
    print(f"{'='*80}\n")
    
    print("⚙️  CONFIGURACIÓN:")
    print(f"   • Sensores: {report['test_config']['num_sensors']}")
    print(f"   • Duración: {report['test_config']['duration']:.1f}s")
    print(f"   • Fecha: {report['test_config']['timestamp']}\n")
    
    print("🚀 RENDIMIENTO:")
    print(f"   • Total de paquetes: {report['performance']['total_packets']:,}")
    print(f"   • Throughput promedio: {report['performance']['avg_throughput']:.2f} pkt/s")
    print(f"   • Errores: {report['performance']['errors']} ({report['performance']['error_rate']:.2f}%)\n")
    
    print("⏱️  LATENCIA (ms):")
    print(f"   • Mínima: {report['latency']['min']:.2f}")
    print(f"   • Máxima: {report['latency']['max']:.2f}")
    print(f"   • Media: {report['latency']['mean']:.2f}")
    print(f"   • Mediana: {report['latency']['median']:.2f}")
    print(f"   • Desv. Estándar: {report['latency']['stdev']:.2f}\n")
    
    print("🎯 ESTRATEGIAS SDN:")
    total_decisions = sum(report['strategies'].values())
    for strategy, count in report['strategies'].items():
        pct = (count / total_decisions * 100) if total_decisions > 0 else 0
        print(f"   • {strategy.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
    
    print(f"\n📈 TOP 10 SENSORES MÁS ACTIVOS:")
    for i, sensor in enumerate(report['top_sensors'], 1):
        print(f"   {i:2d}. {sensor['id']:20s} | {sensor['packets_sent']:4d} paquetes | {sensor['avg_latency']:.2f}ms")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    # Prueba con diferentes cargas
    test_configs = [
        {'sensors': 15, 'duration': 30, 'label': 'Carga Baja (Sistema Actual)'},
        {'sensors': 30, 'duration': 30, 'label': 'Carga Media'},
        {'sensors': 50, 'duration': 60, 'label': 'Carga Alta'},
    ]
    
    all_reports = []
    
    for config in test_configs:
        print(f"\n\n{'#'*80}")
        print(f"# {config['label']}")
        print(f"{'#'*80}\n")
        
        runner = LoadTestRunner(num_sensors=config['sensors'])
        report = runner.run_load_test(duration=config['duration'])
        report['label'] = config['label']
        all_reports.append(report)
        
        print_report(report)
        
        # Esperar entre pruebas
        if config != test_configs[-1]:
            print("⏸️  Esperando 10 segundos antes de la siguiente prueba...")
            time.sleep(10)
    
    # Guardar todos los reportes
    with open('/app/results/load_test_results.json', 'w') as f:
        json.dump(all_reports, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: /app/results/load_test_results.json")
