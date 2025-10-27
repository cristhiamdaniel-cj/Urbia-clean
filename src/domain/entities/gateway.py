"""
Entity: Gateway
Gateway edge para procesamiento distribuido
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from src.domain.value_objects.location import Location


@dataclass
class Gateway:
    """Gateway Edge"""
    
    id: str
    name: str
    location: Location
    port: int
    is_active: bool = True
    connected_sensors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_sensor(self, sensor_id: str) -> None:
        """Agregar sensor al gateway"""
        if sensor_id not in self.connected_sensors:
            self.connected_sensors.append(sensor_id)
    
    def remove_sensor(self, sensor_id: str) -> None:
        """Remover sensor del gateway"""
        if sensor_id in self.connected_sensors:
            self.connected_sensors.remove(sensor_id)
    
    def sensor_count(self) -> int:
        """Número de sensores conectados"""
        return len(self.connected_sensors)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Gateway):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
