"""
Entity: Telemetry
Datos de telemetría de un sensor
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.domain.value_objects.sensor_id import SensorId


@dataclass
class Telemetry:
    """Datos de telemetría"""
    
    sensor_id: SensorId
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_critical: bool = False
    gateway_id: Optional[str] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        """Validaciones"""
        if self.value is None:
            raise ValueError("Telemetría debe tener valor")
    
    def age_seconds(self) -> float:
        """Edad de la telemetría en segundos"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def is_fresh(self, max_age_seconds: int = 60) -> bool:
        """Verificar si telemetría es reciente"""
        return self.age_seconds() <= max_age_seconds
    
    def __repr__(self) -> str:
        return f"Telemetry({self.sensor_id}, {self.value}{self.unit})"
