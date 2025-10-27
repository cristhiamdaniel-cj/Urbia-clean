"""
Domain Events
Eventos que ocurren en el dominio
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DomainEvent:
    """Evento base del dominio"""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SensorRegisteredEvent(DomainEvent):
    """Sensor registrado"""
    sensor_id: str = ""
    sensor_type: str = ""


@dataclass
class TelemetryReceivedEvent(DomainEvent):
    """Telemetría recibida"""
    sensor_id: str = ""
    value: float = 0.0
    is_critical: bool = False


@dataclass
class CriticalAlertEvent(DomainEvent):
    """Alerta crítica"""
    sensor_id: str = ""
    sensor_name: str = ""
    value: float = 0.0
    threshold: float = 0.0
    message: str = ""
