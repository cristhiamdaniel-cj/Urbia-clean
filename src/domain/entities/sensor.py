"""
Entity: Sensor
Entidad principal del dominio con identidad única
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority


@dataclass
class Sensor:
    """Sensor IoT con identidad única"""
    
    id: SensorId
    name: str
    type: str
    location: Location
    priority: Priority
    unit: str
    min_value: float
    max_value: float
    threshold_critical: Optional[float] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validaciones de negocio"""
        if not self.name:
            raise ValueError("Sensor debe tener nombre")
        
        if self.min_value >= self.max_value:
            raise ValueError("min_value debe ser menor que max_value")
    
    def activate(self) -> None:
        """Activar sensor"""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Desactivar sensor"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def is_critical_value(self, value: float) -> bool:
        """Verificar si valor es crítico"""
        if self.threshold_critical is None:
            return False
        return value >= self.threshold_critical
    
    def __eq__(self, other) -> bool:
        """Igualdad por identidad"""
        if not isinstance(other, Sensor):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __repr__(self) -> str:
        return f"Sensor({self.id}, {self.name}, {self.type})"
