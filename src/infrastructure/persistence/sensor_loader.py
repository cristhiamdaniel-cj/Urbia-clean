"""
Carga sensores desde configuración a la nueva arquitectura
"""
from typing import List
from src.domain.entities.sensor import Sensor
from src.infrastructure.factories.sensor_factory import SensorFactory
from src.application.services.sensor_service import SensorService


class SensorLoader:
    """Carga sensores desde configuración de Manizales"""
    
    def __init__(
        self,
        sensor_factory: SensorFactory,
        sensor_service: SensorService
    ):
        self.sensor_factory = sensor_factory
        self.sensor_service = sensor_service
    
    def load_manizales_sensors(self) -> List[Sensor]:
        """Cargar sensores de Manizales"""
        from sensors.locations.manizales_sensors import MANIZALES_SENSORS
        
        loaded_sensors = []
        
        for sensor_config in MANIZALES_SENSORS:
            try:
                # Crear sensor usando factory
                sensor = self.sensor_factory.create_from_config(sensor_config)
                
                # Registrar usando servicio
                registered_sensor = self.sensor_service.register_sensor(sensor)
                
                loaded_sensors.append(registered_sensor)
                
                print(f"✅ Sensor cargado: {sensor.name} ({sensor.id})")
                
            except Exception as e:
                print(f"❌ Error cargando sensor {sensor_config.get('id')}: {e}")
        
        print(f"\n📊 Total sensores cargados: {len(loaded_sensors)}")
        
        return loaded_sensors
