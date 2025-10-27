"""
In-Memory implementation of ITelemetryRepository
"""
from typing import List, Optional
from datetime import datetime
from collections import defaultdict
from src.domain.entities.telemetry import Telemetry
from src.domain.repositories.telemetry_repository import ITelemetryRepository


class InMemoryTelemetryRepository(ITelemetryRepository):
    """Repositorio en memoria para telemetría"""
    
    def __init__(self, max_per_sensor: int = 1000):
        # Organizar por sensor_id para búsquedas rápidas
        self._telemetry: dict = defaultdict(list)
        self._max_per_sensor = max_per_sensor
    
    def save(self, telemetry: Telemetry) -> None:
        """Guardar telemetría"""
        sensor_id = str(telemetry.sensor_id)
        self._telemetry[sensor_id].append(telemetry)
        
        # Limitar tamaño (FIFO)
        if len(self._telemetry[sensor_id]) > self._max_per_sensor:
            self._telemetry[sensor_id].pop(0)
    
    def find_by_sensor(self, sensor_id: str, limit: int = 100) -> List[Telemetry]:
        """Obtener telemetría de un sensor"""
        data = self._telemetry.get(sensor_id, [])
        return data[-limit:]  # Últimos N registros
    
    def find_by_time_range(
        self, 
        start: datetime, 
        end: datetime
    ) -> List[Telemetry]:
        """Obtener telemetría en rango de tiempo"""
        result = []
        for telemetry_list in self._telemetry.values():
            for t in telemetry_list:
                if start <= t.timestamp <= end:
                    result.append(t)
        return sorted(result, key=lambda x: x.timestamp)
    
    def get_latest(self, sensor_id: str) -> Optional[Telemetry]:
        """Obtener última telemetría de un sensor"""
        data = self._telemetry.get(sensor_id, [])
        return data[-1] if data else None
    
    def count_by_sensor(self, sensor_id: str) -> int:
        """Contar telemetría de un sensor"""
        return len(self._telemetry.get(sensor_id, []))
    
    def clear(self) -> None:
        """Limpiar repositorio"""
        self._telemetry.clear()
