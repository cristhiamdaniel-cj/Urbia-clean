"""
In-Memory implementation of ISensorRepository
Útil para testing y desarrollo
"""
from typing import List, Optional, Dict
from src.domain.entities.sensor import Sensor
from src.domain.repositories.sensor_repository import ISensorRepository
from src.shared.exceptions.domain_exceptions import SensorNotFoundException


class InMemorySensorRepository(ISensorRepository):
    """Repositorio en memoria para sensores"""
    
    def __init__(self):
        self._sensors: Dict[str, Sensor] = {}
    
    def save(self, sensor: Sensor) -> None:
        """Guardar sensor"""
        self._sensors[str(sensor.id)] = sensor
    
    def find_by_id(self, sensor_id: str) -> Optional[Sensor]:
        """Buscar sensor por ID"""
        return self._sensors.get(sensor_id)
    
    def find_all(self) -> List[Sensor]:
        """Obtener todos los sensores"""
        return list(self._sensors.values())
    
    def update(self, sensor: Sensor) -> None:
        """Actualizar sensor"""
        sensor_id = str(sensor.id)
        if sensor_id not in self._sensors:
            raise SensorNotFoundException(sensor_id)
        self._sensors[sensor_id] = sensor
    
    def delete(self, sensor_id: str) -> None:
        """Eliminar sensor"""
        if sensor_id in self._sensors:
            del self._sensors[sensor_id]
    
    def find_by_priority(self, priority: str) -> List[Sensor]:
        """Buscar sensores por prioridad"""
        return [
            sensor for sensor in self._sensors.values()
            if sensor.priority.value == priority
        ]
    
    def count(self) -> int:
        """Contar sensores"""
        return len(self._sensors)
    
    def clear(self) -> None:
        """Limpiar repositorio (útil para testing)"""
        self._sensors.clear()
