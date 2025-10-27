"""
DTOs para Telemetría
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from src.domain.entities.telemetry import Telemetry


@dataclass
class TelemetryDTO:
    """DTO para telemetría"""
    
    sensor_id: str
    value: float
    unit: str
    timestamp: str
    is_critical: bool
    gateway_id: Optional[str]
    age_seconds: float
    
    @staticmethod
    def from_entity(telemetry: Telemetry) -> 'TelemetryDTO':
        """Crear desde entidad"""
        return TelemetryDTO(
            sensor_id=str(telemetry.sensor_id),
            value=telemetry.value,
            unit=telemetry.unit,
            timestamp=telemetry.timestamp.isoformat(),
            is_critical=telemetry.is_critical,
            gateway_id=telemetry.gateway_id,
            age_seconds=telemetry.age_seconds()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TelemetryHistoryDTO:
    """DTO para historial de telemetría"""
    
    sensor_id: str
    sensor_name: str
    data: List[Dict[str, Any]]
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
