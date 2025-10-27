"""
Data Transfer Objects para Sensores
Desacopla la presentación del dominio
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from src.domain.entities.sensor import Sensor


@dataclass
class SensorDTO:
    """DTO para transferir datos de sensor"""
    
    id: str
    name: str
    type: str
    location: Dict[str, Any]
    priority: str
    unit: str
    min_value: float
    max_value: float
    threshold_critical: Optional[float]
    is_active: bool
    created_at: str
    updated_at: str
    
    @staticmethod
    def from_entity(sensor: Sensor) -> 'SensorDTO':
        """Crear DTO desde entidad de dominio"""
        return SensorDTO(
            id=str(sensor.id),
            name=sensor.name,
            type=sensor.type,
            location={
                'lat': sensor.location.latitude,
                'lng': sensor.location.longitude,
                'address': sensor.location.address,
                'city': sensor.location.city
            },
            priority=sensor.priority.value,
            unit=sensor.unit,
            min_value=sensor.min_value,
            max_value=sensor.max_value,
            threshold_critical=sensor.threshold_critical,
            is_active=sensor.is_active,
            created_at=sensor.created_at.isoformat(),
            updated_at=sensor.updated_at.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)


@dataclass
class SensorListDTO:
    """DTO para lista de sensores"""
    
    sensors: list
    total: int
    active: int
    
    @staticmethod
    def from_entities(sensors: list) -> 'SensorListDTO':
        """Crear desde lista de entidades"""
        sensor_dtos = [SensorDTO.from_entity(s) for s in sensors]
        active_count = sum(1 for s in sensors if s.is_active)
        
        return SensorListDTO(
            sensors=[s.to_dict() for s in sensor_dtos],
            total=len(sensors),
            active=active_count
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
