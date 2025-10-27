"""
Entity: Route
Representa una ruta de red
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Route:
    """Ruta de red"""
    
    id: str
    name: str
    latency_ms: float
    bandwidth_mbps: float
    hop_count: int
    is_available: bool = True
    current_load: float = 0.0  # Porcentaje
    
    def is_congested(self, threshold: float = 80.0) -> bool:
        """Verificar si ruta está congestionada"""
        return self.current_load >= threshold
    
    def can_handle_priority(self, priority: str) -> bool:
        """Verificar si ruta puede manejar prioridad"""
        if priority == "CRITICA":
            return self.latency_ms <= 25.0  # Baja latencia
        elif priority == "ALTA":
            return self.latency_ms <= 35.0
        return True  # Normal/Baja puede usar cualquiera
    
    def calculate_score(self, priority: str) -> float:
        """
        Calcular score de ruta para una prioridad
        Mayor score = mejor ruta
        """
        if not self.is_available:
            return 0.0
        
        # Factores del score
        latency_score = 100 - (self.latency_ms / 2)
        bandwidth_score = self.bandwidth_mbps
        load_score = 100 - self.current_load
        
        # Pesos según prioridad
        if priority == "CRITICA":
            return (latency_score * 0.6) + (load_score * 0.3) + (bandwidth_score * 0.1)
        elif priority == "ALTA":
            return (latency_score * 0.4) + (load_score * 0.4) + (bandwidth_score * 0.2)
        else:  # NORMAL/BAJA
            return (bandwidth_score * 0.5) + (load_score * 0.3) + (latency_score * 0.2)
    
    def add_load(self, percentage: float) -> None:
        """Incrementar carga"""
        self.current_load = min(100.0, self.current_load + percentage)
    
    def __repr__(self) -> str:
        return f"Route({self.name}, {self.latency_ms}ms, {self.current_load:.1f}%)"
