"""
Entity: RoutingDecision
Representa una decisión de enrutamiento
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RoutingDecision:
    """Decisión de enrutamiento del controlador"""
    
    packet_id: str
    sensor_id: str
    sensor_priority: str
    selected_route: str
    route_latency: float
    route_load: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    alternative_route: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            'packet_id': self.packet_id,
            'sensor_id': self.sensor_id,
            'priority': self.sensor_priority,
            'selected_route': self.selected_route,
            'latency': self.route_latency,
            'load': self.route_load,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'alternative': self.alternative_route
        }
