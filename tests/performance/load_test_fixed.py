"""
Sistema de Pruebas de Carga para UrbIA IoT - VERSIÓN CORREGIDA
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
        self.results = {
            'latencies': [],
            'packets_sent': 0,
            'errors': 0,
            'sensor_metrics': {}
        }
        self.lock = threading.Lock()
        
    def create_test_sensors(self, container) -> List[Sensor]:
        """Crear sensores de prueba"""
        sensors = []
        sensor_types = ['RUIDO', 'TEMPERATURA', 'TRAFICO', 'CALIDAD_AIRE', 'LUZ']
        priorities = [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]
        
        base_lat, base_lng = 5.0703, -75.5138
        
        for i in range(self.num_sensors):
            sensor_type = sensor_types[i % len(sensor_types)]
            priority = priorities[i % len(priorities)]
            
            lat_offset = (i % 10 - 5) * 0.01
            lng_offset = (i // 10 - 2.5) * 0.01
            
            sensor = Sensor(
                id=SensorId(f"LOAD-{sensor_type[:3]}-{i:03d}"),
                name=f"Load Test {sensor_type} #{i}",
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
    
    def simulate_sensor(self, sensor: Sensor, container, duration: int):
        """Simular telemetría de un sensor"""
        start_time = time.time()
        packets_sent = 0
        local_latencies = []
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                value = 50.0 + (hash(sensor.id.value) % 50)
                
                # Medir latencia
                route_start = time.time()
                decision = container.sdn_controller.route_packet(str(sensor.id))
                route_latency = (time.time() - route_start) * 1000
                
                # Procesar telemetría
                container.telemetry_service.process_telemetry(str(sensor.id), value)
                
                packets_sent += 1
                local_latencies.append(route_latency)
                
                # Intervalo según prioridad
                if sensor.priority == Priority.CRITICAL:
                    time.sleep(0.5)
                elif sensor.priority == Priority.HIGH:
                    time.sleep(1)
                else:
                    time.sleep(2)
                    
            except Exception as e:
                errors += 1
                if errors <= 3:  # Solo imprimir primeros 3 errores
                    print(f"⚠️  Error en {sensor.id}: {str(e)[:50]}")
        
        # Guardar métricas
        with self.lock:
            self.results['latencies'].extend(local_latencies)
            self.results['packets_sent'] += packets_sent
            self.results['errors'] += errors
            self.results['sensor_metrics'][str(sensor.id)] = {
                'packets_sent': packets_sent,
                'errors': errors,
                'avg_latency': statistics.mean(local_latencies) if local_latencies else 0
            }
    
    def run_load_test(self, duration: int = 60):
        """Ejecutar prueba de carga"""
        print(f"\n{'='*80}")
        print(f"🔥 PRUEBA DE CARGA - {self.num_sensors} SENSORES")
        print(f"{'='*80}\n")
        
        # IMPORTANTE: Crear nuevo contenedor para cada prueba
        container = DIContainer()
        
        print(f"⏱️  Duración: {duration}s | 📡 Sensores: {self.num_sensors}\n")
        
        # Crear sensores
        print("🔧 Creando sensores...")
        sensors = self.create_test_sensors(container)
        print(f"✅ {len(sensors)} sensores creados\n")
        
        # Inicializar infraestructura
        gateways = container.gateway_factory.create_manizales_gateways()
        for gw in gateways:
            container.gateway_service.register_gateway(gw)
        container.gateway_service.auto_assign_sensors()
        container.sdn_controller.initialize_routes()
        
        print(f"🚀 Iniciando simulación...\n")
        
        # Lanzar threads
        threads = []
        start_time = time.time()
        
        for sensor in sensors:
            thread = threading.Thread(
                target=self.simulate_sensor, 
                args=(sensor, container, duration)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Monitoreo
        last_count = 0
        while time.time() - start_time < duration:
            time.sleep(5)
            elapsed = time.time() - start_time
            current_count = self.results['packets_sent']
            throughput = (current_count - last_count) / 5
            last_count = current_count
            
            print(f"⏳ {elapsed:5.0f}s | 📦 {current_count:7d} paquetes | "
                  f"🔥 {throughput:7.1f} pkt/s | ❌ {self.results['errors']:5d} errores")
        
        # Esperar threads
        for thread in threads:
            thread.join(timeout=2)
        
        actual_duration = time.time() - start_time
        print(f"\n✅ Completado en {actual_duration:.1f}s\n")
        
        return self.generate_report(actual_duration)
    
    def generate_report(self, duration: float) -> Dict:
        """Generar reporte"""
        total_packets = self.results['packets_sent']
        
        report = {
            'config': {
                'sensors': self.num_sensors,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            },
            'performance': {
                'total_packets': total_packets,
                'throughput': total_packets / duration if duration > 0 else 0,
                'errors': self.results['errors'],
                'success_rate': ((total_packets - self.results['errors']) / total_packets * 100) 
                    if total_packets > 0 else 0
            },
            'latency': {
                'min': min(self.results['latencies']) if self.results['latencies'] else 0,
                'max': max(self.results['latencies']) if self.results['latencies'] else 0,
                'mean': statistics.mean(self.results['latencies']) if self.results['latencies'] else 0,
                'median': statistics.median(self.results['latencies']) if self.results['latencies'] else 0,
                'stdev': statistics.stdev(self.results['latencies']) 
                    if len(self.results['latencies']) > 1 else 0
            },
            'top_sensors': sorted(
                [{'id': k, **v} for k, v in self.results['sensor_metrics'].items()],
                key=lambda x: x['packets_sent'],
                reverse=True
            )[:10]
        }
        
        return report

def print_report(report: Dict):
    """Imprimir reporte"""
    print(f"\n{'='*80}")
    print("📊 REPORTE DE RESULTADOS")
    print(f"{'='*80}\n")
    
    print("⚙️  CONFIGURACIÓN:")
    print(f"   Sensores: {report['config']['sensors']}")
    print(f"   Duración: {report['config']['duration']:.1f}s\n")
    
    print("🚀 RENDIMIENTO:")
    print(f"   Total paquetes: {report['performance']['total_packets']:,}")
    print(f"   Throughput: {report['performance']['throughput']:.2f} pkt/s")
    print(f"   Tasa de éxito: {report['performance']['success_rate']:.1f}%")
    print(f"   Errores: {report['performance']['errors']:,}\n")
    
    print("⏱️  LATENCIA (ms):")
    print(f"   Min: {report['latency']['min']:.2f} | "
          f"Max: {report['latency']['max']:.2f} | "
          f"Media: {report['latency']['mean']:.2f} | "
          f"Std: {report['latency']['stdev']:.2f}\n")
    
    print("📈 TOP 10 SENSORES:")
    for i, s in enumerate(report['top_sensors'], 1):
        print(f"   {i:2d}. {s['id']:20s} | {s['packets_sent']:5d} pkt | "
              f"{s['avg_latency']:.2f}ms | {s['errors']} err")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    configs = [
        {'sensors': 15, 'duration': 30},
        {'sensors': 30, 'duration': 30},
        {'sensors': 50, 'duration': 60},
    ]
    
    all_reports = []
    
    for i, config in enumerate(configs, 1):
        print(f"\n{'#'*80}")
        print(f"# PRUEBA {i}/3: {config['sensors']} SENSORES")
        print(f"{'#'*80}\n")
        
        runner = LoadTestRunner(num_sensors=config['sensors'])
        report = runner.run_load_test(duration=config['duration'])
        all_reports.append(report)
        
        print_report(report)
        
        if i < len(configs):
            print("⏸️  Pausa de 10 segundos...\n")
            time.sleep(10)
    
    # Guardar resultados
    with open('/app/results/load_test_results.json', 'w') as f:
        json.dump(all_reports, f, indent=2)
    
    print(f"\n💾 Resultados guardados: /app/results/load_test_results.json\n")
