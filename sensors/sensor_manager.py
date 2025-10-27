# sensors/sensor_manager.py
"""
Gestor de todos los sensores de Manizales
"""

import sys
sys.path.append('/app')

from sensors.locations.manizales_sensors import MANIZALES_SENSORS, GATEWAYS
from sensors.sensor_types.noise_sensor import NoiseSensor
from sensors.sensor_types.temperature_sensor import TemperatureSensor
from sensors.sensor_types.traffic_sensor import TrafficSensor
from sensors.sensor_types.air_quality_sensor import AirQualitySensor
from sensors.sensor_types.light_sensor import LightSensor
import time

SENSOR_CLASSES = {
    'ruido': NoiseSensor,
    'temperatura': TemperatureSensor,
    'trafico': TrafficSensor,
    'calidad_aire': AirQualitySensor,
    'iluminacion': LightSensor
}

class SensorManager:
    def __init__(self, gateway_ip='localhost', gateway_port=5001):
        self.sensors = []
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        
        # Inicializar todos los sensores
        for sensor_key, sensor_config in MANIZALES_SENSORS.items():
            sensor_type = sensor_config['type']
            sensor_class = SENSOR_CLASSES[sensor_type]
            sensor = sensor_class(sensor_config)
            self.sensors.append(sensor)
    
    def start_all(self):
        """Iniciar todos los sensores"""
        print("=" * 70)
        print("  🌐 INICIANDO SISTEMA DE SENSORES IoT - MANIZALES")
        print("=" * 70)
        print()
        
        for sensor in self.sensors:
            print(f"✓ {sensor.icono} {sensor.nombre}")
            print(f"  📍 {sensor.ubicacion}")
            print(f"  ⏱️  Intervalo: {sensor.intervalo}s | Prioridad: {sensor.prioridad}")
            print()
            sensor.start(self.gateway_ip, self.gateway_port)
        
        print("=" * 70)
        print("  ✓ Todos los sensores activos")
        print("  Presiona Ctrl+C para detener")
        print("=" * 70)
        print()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Deteniendo sensores...")
            self.stop_all()
    
    def stop_all(self):
        """Detener todos los sensores"""
        for sensor in self.sensors:
            sensor.stop()
        print("✓ Todos los sensores detenidos")


if __name__ == '__main__':
    manager = SensorManager()
    manager.start_all()
