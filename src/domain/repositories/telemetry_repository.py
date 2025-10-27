"""
Interface del repositorio de telemetría
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.domain.entities.telemetry import Telemetry


class ITelemetryRepository(ABC):
    """Interface para persistencia de telemetría"""
    
    @abstractmethod
    def save(self, telemetry: Telemetry) -> None:
        """Guardar telemetría"""
        pass
    
    @abstractmethod
    def find_by_sensor(self, sensor_id: str, limit: int = 100) -> List[Telemetry]:
        """Obtener telemetría de un sensor"""
        pass
    
    @abstractmethod
    def find_by_time_range(
        self, 
        start: datetime, 
        end: datetime
    ) -> List[Telemetry]:
        """Obtener telemetría en rango de tiempo"""
        pass
    
    @abstractmethod
    def get_latest(self, sensor_id: str) -> Optional[Telemetry]:
        """Obtener última telemetría de un sensor"""
        pass
