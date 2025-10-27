"""
Pruebas de Carga - Con Limpieza de Estado
"""
import time
import threading
import statistics
from datetime import datetime
from typing import List, Dict
import json
import sys
import gc
sys.path.insert(0, '/app')

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
        
    def create_fresh_container(self):
        """Crear contenedor completamente nuevo"""
        # Forzar limpieza de imports
        if 'config.di_container' in sys.modules:
            del sys.modules['config.di_container']
        
        # Re-importar
        from config.di_container import DIContainer
        return DIContainer()
        
    def create_test_sensors(self, container) -> List:
        """Crear sensores de prueba"""
        from src.domain.entities.sensor import Sensor
        from src.domain.value_objects.sensor_id import SensorId
        from src.domain.value_objects.location import Location
        from src.domain.value_objects.priority import Priority
        
        sensors = []
        sensor_types = ['RUIDO', 'TEMPERATURA', 'TRAFICO', 'CALIDAD_AIRE', 'LUZ']
        priorities = [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]
        
        base_lat, base_lng = 5.0703, -75.5138
        timestamp = int(time.time() * 1000)  # timestamp único
        
        for i in range(self.num_sensors):
            sensor_type = sensor_types[i % len(sensor_types)]
            priority = priorities[i % len(priorities)]
            
            lat_offset = (i % 10 - 5) * 0.01
            lng_offset = (i // 10 - 2.5) * 0.01
            
            # ID único con timestamp
            sensor_id = f"T{timestamp}-{sensor_type[:3]}-{i:03d}"
            
            sensor = Sensor(
                id=SensorId(sensor_id),
                name=f"Test {sensor_type} #{i}",
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
    
    def simulate_sensor(self, sensor, container, duration: int):
        """Simular telemetría"""
        start_time = time.time()
        packets_sent = 0
        local_latencies = []
        errors = 0
        
        while time.time() - start_time < duration:
            try:
                value = 50.0 + (hash(str(sensor.id)) % 50)
                
                route_start = time.time()
                decision = container.sdn_controller.route_packet(str(sensor.id))
                route_latency = (time.time() - route_start) * 1000
                
                container.telemetry_service.process_telemetry(str(sensor.id), value)
                
                packets_sent += 1
                local_latencies.append(route_latency)
                
                # Intervalo según prioridad
                from src.domain.value_objects.priority import Priority
                if sensor.priority == Priority.CRITICAL:
                    time.sleep(0.5)
                elif sensor.priority == Priority.HIGH:
                    time.sleep(1)
                else:
                    time.sleep(2)
                    
            except Exception as e:
                errors += 1
                if errors == 1:
                    print(f"⚠️  Error en {sensor.id}: {str(e)[:80]}")
        
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
        """Ejecutar prueba"""
        print(f"\n{'='*80}")
        print(f"🔥 PRUEBA DE CARGA - {self.num_sensors} SENSORES")
        print(f"{'='*80}\n")
        
        # Crear contenedor fresco
        print("🔧 Inicializando contenedor...")
        container = self.create_fresh_container()
        
        print(f"⏱️  Duración: {duration}s | 📡 Sensores: {self.num_sensors}\n")
        
        # Crear sensores
        print("📡 Creando sensores...")
        sensors = self.create_test_sensors(container)
        print(f"✅ {len(sensors)} sensores registrados\n")
        
        # Infraestructura
        print("🌉 Configurando gateways y rutas...")
        gateways = container.gateway_factory.create_manizales_gateways()
        for gw in gateways:
            container.gateway_service.register_gateway(gw)
        container.gateway_service.auto_assign_sensors()
        container.sdn_controller.initialize_routes()
        print("✅ Infraestructura lista\n")
        
        print(f"🚀 Iniciando simulación de {duration}s...\n")
        
        # Threads
        threads = []
        start_time = time.time()
        
        for sensor in sensors:
            thread = threading.Thread(
                target=self.simulate_sensor, 
                args=(sensor, container, duration),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Monitoreo
        last_count = 0
        while time.time() - start_time < duration:
            time.sleep(5)
            elapsed = time.time() - start_time
            current = self.results['packets_sent']
            tput = (current - last_count) / 5
            last_count = current
            
            print(f"⏳ {elapsed:5.0f}s | 📦 {current:7d} pkt | "
                  f"🔥 {tput:7.1f} pkt/s | ❌ {self.results['errors']:5d} err")
        
        # Esperar
        for t in threads:
            t.join(timeout=2)
        
        actual = time.time() - start_time
        print(f"\n✅ Completado en {actual:.1f}s\n")
        
        # Limpiar
        del container
        gc.collect()
        
        return self.generate_report(actual)
    
    def generate_report(self, duration: float) -> Dict:
        total = self.results['packets_sent']
        
        return {
            'config': {
                'sensors': self.num_sensors,
                'duration': round(duration, 1),
                'timestamp': datetime.now().isoformat()
            },
            'performance': {
                'total_packets': total,
                'throughput': round(total / duration, 2) if duration > 0 else 0,
                'errors': self.results['errors'],
                'success_rate': round((total - self.results['errors']) / total * 100, 1) 
                    if total > 0 else 0
            },
            'latency': {
                'min': round(min(self.results['latencies']), 2) if self.results['latencies'] else 0,
                'max': round(max(self.results['latencies']), 2) if self.results['latencies'] else 0,
                'mean': round(statistics.mean(self.results['latencies']), 2) if self.results['latencies'] else 0,
                'median': round(statistics.median(self.results['latencies']), 2) if self.results['latencies'] else 0,
                'stdev': round(statistics.stdev(self.results['latencies']), 2) 
                    if len(self.results['latencies']) > 1 else 0
            },
            'top_sensors': sorted(
                [{'id': k, **v} for k, v in self.results['sensor_metrics'].items()],
                key=lambda x: x['packets_sent'],
                reverse=True
            )[:10]
        }

def print_report(report: Dict):
    print(f"\n{'='*80}")
    print("📊 REPORTE DE RESULTADOS")
    print(f"{'='*80}\n")
    
    cfg = report['config']
    perf = report['performance']
    lat = report['latency']
    
    print(f"⚙️  CONFIGURACIÓN:")
    print(f"   Sensores: {cfg['sensors']} | Duración: {cfg['duration']}s\n")
    
    print(f"🚀 RENDIMIENTO:")
    print(f"   Paquetes totales: {perf['total_packets']:,}")
    print(f"   Throughput: {perf['throughput']:.2f} pkt/s")
    print(f"   Éxito: {perf['success_rate']}% | Errores: {perf['errors']}\n")
    
    print(f"⏱️  LATENCIA:")
    print(f"   Min: {lat['min']}ms | Max: {lat['max']}ms | "
          f"Media: {lat['mean']}ms | Std: {lat['stdev']}ms\n")
    
    print(f"📈 TOP 10 SENSORES:")
    for i, s in enumerate(report['top_sensors'], 1):
        print(f"   {i:2d}. {s['id']:25s} | {s['packets_sent']:5d} pkt | "
              f"{s['avg_latency']:.2f}ms")
    
    print(f"\n{'='*80}\n")

def run_comparative_tests():
    """Ejecutar pruebas comparativas"""
    configs = [
        {'sensors': 15, 'duration': 30, 'label': 'Carga Baja (actual)'},
        {'sensors': 30, 'duration': 30, 'label': 'Carga Media (2x)'},
        {'sensors': 50, 'duration': 60, 'label': 'Carga Alta (3.3x)'},
    ]
    
    all_reports = []
    
    for i, config in enumerate(configs, 1):
        print(f"\n{'#'*80}")
        print(f"# PRUEBA {i}/3: {config['label'].upper()}")
        print(f"# {config['sensors']} sensores durante {config['duration']} segundos")
        print(f"{'#'*80}")
        
        runner = LoadTestRunner(num_sensors=config['sensors'])
        report = runner.run_load_test(duration=config['duration'])
        report['label'] = config['label']
        all_reports.append(report)
        
        print_report(report)
        
        if i < len(configs):
            print("⏸️  Pausa de 15 segundos...\n")
            time.sleep(15)
    
    # Guardar
    with open('/app/results/load_test_results.json', 'w') as f:
        json.dump(all_reports, f, indent=2)
    
    # Comparación final
    print(f"\n{'='*80}")
    print("📊 COMPARACIÓN DE RESULTADOS")
    print(f"{'='*80}\n")
    print(f"{'Prueba':<20} | {'Throughput':>12} | {'Latencia':>10} | {'Éxito':>8}")
    print(f"{'-'*20}-+-{'-'*12}-+-{'-'*10}-+-{'-'*8}")
    
    for r in all_reports:
        print(f"{r['label']:<20} | {r['performance']['throughput']:>10.1f} p/s | "
              f"{r['latency']['mean']:>8.2f}ms | {r['performance']['success_rate']:>7.1f}%")
    
    print(f"\n{'='*80}\n")
    print(f"💾 Resultados completos: /app/results/load_test_results.json\n")

if __name__ == "__main__":
    run_comparative_tests()
