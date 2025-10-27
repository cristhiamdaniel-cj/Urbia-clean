"""
Application Service: Sensor Service
Orquesta operaciones de sensores
"""
from typing import List, Optional
from src.domain.entities.sensor import Sensor
from src.domain.repositories.sensor_repository import ISensorRepository
from src.shared.events.event_bus import EventBus
from src.shared.events.events import SensorRegisteredEvent
from src.shared.exceptions.domain_exceptions import SensorNotFoundException


class SensorService:
    """Servicio de aplicación para sensores"""
    
    def __init__(
        self,
        sensor_repository: ISensorRepository,
        event_bus: EventBus
    ):
        self.sensor_repository = sensor_repository
        self.event_bus = event_bus
    
    def register_sensor(self, sensor: Sensor) -> Sensor:
        """
        Registrar nuevo sensor
        
        Args:
            sensor: Sensor a registrar
            
        Returns:
            Sensor registrado
        """
        # Validar que no exista
        existing = self.sensor_repository.find_by_id(str(sensor.id))
        if existing:
            raise ValueError(f"Sensor {sensor.id} ya existe")
        
        # Guardar
        self.sensor_repository.save(sensor)
        
        # Publicar evento
        event = SensorRegisteredEvent(
            sensor_id=str(sensor.id),
            sensor_type=sensor.type
        )
        self.event_bus.publish(event)
        
        return sensor
    
    def get_sensor(self, sensor_id: str) -> Sensor:
        """
        Obtener sensor por ID
        
        Raises:
            SensorNotFoundException: Si no existe
        """
        sensor = self.sensor_repository.find_by_id(sensor_id)
        if not sensor:
            raise SensorNotFoundException(sensor_id)
        return sensor
    
    def get_all_sensors(self) -> List[Sensor]:
        """Obtener todos los sensores"""
        return self.sensor_repository.find_all()
    
    def get_active_sensors(self) -> List[Sensor]:
        """Obtener sensores activos"""
        all_sensors = self.sensor_repository.find_all()
        return [s for s in all_sensors if s.is_active]
    
    def activate_sensor(self, sensor_id: str) -> Sensor:
        """Activar sensor"""
        sensor = self.get_sensor(sensor_id)
        sensor.activate()
        self.sensor_repository.update(sensor)
        return sensor
    
    def deactivate_sensor(self, sensor_id: str) -> Sensor:
        """Desactivar sensor"""
        sensor = self.get_sensor(sensor_id)
        sensor.deactivate()
        self.sensor_repository.update(sensor)
        return sensor
