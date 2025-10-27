"""
Eventos relacionados con gateways
"""
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.events.events import DomainEvent


@dataclass
class GatewayStartedEvent(DomainEvent):
    """Gateway iniciado"""
    gateway_id: str = ""
    gateway_name: str = ""


@dataclass
class GatewayStoppedEvent(DomainEvent):
    """Gateway detenido"""
    gateway_id: str = ""
    reason: str = ""


@dataclass
class SensorConnectedToGatewayEvent(DomainEvent):
    """Sensor conectado a gateway"""
    sensor_id: str = ""
    gateway_id: str = ""


@dataclass
class TelemetryAggregatedEvent(DomainEvent):
    """Telemetría agregada en gateway"""
    gateway_id: str = ""
    sensor_id: str = ""
    original_count: int = 0
    aggregated_value: float = 0.0


@dataclass
class GatewayOverloadEvent(DomainEvent):
    """Gateway sobrecargado"""
    gateway_id: str = ""
    current_load: float = 0.0
    sensor_count: int = 0
