"""Cargador de sensores desde configuración JSON avanzada"""
import json
from typing import List
from src.domain.entities.sensor import Sensor
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority

class AdvancedSensorLoader:
    def __init__(self, config_path: str, sensor_service):
        self.config_path = config_path
        self.sensor_service = sensor_service
        
    def load_sensors(self) -> List[Sensor]:
        """Cargar sensores desde JSON"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            sensors = []
            for sensor_cfg in config.get('sensors', []):
                sensor = Sensor(
                    id=SensorId(sensor_cfg['id']),
                    name=sensor_cfg['name'],
                    type=sensor_cfg['type'],
                    location=Location(
                        sensor_cfg['location']['lat'],
                        sensor_cfg['location']['lng'],
                        sensor_cfg['location'].get('city', 'Manizales')
                    ),
                    priority=Priority[sensor_cfg['priority']],
                    unit=sensor_cfg['unit']
                )
                self.sensor_service.register_sensor(sensor)
                sensors.append(sensor)
            
            print(f"✅ {len(sensors)} sensores avanzados cargados")
            return sensors
            
        except Exception as e:
            print(f"❌ Error cargando sensores avanzados: {e}")
            return []
