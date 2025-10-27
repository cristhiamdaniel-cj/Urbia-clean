"""
Interface del repositorio de sensores
Define el contrato sin implementación
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.sensor import Sensor


class ISensorRepository(ABC):
    """Interface para persistencia de sensores"""
    
    @abstractmethod
    def save(self, sensor: Sensor) -> None:
        """Guardar sensor"""
        pass
    
    @abstractmethod
    def find_by_id(self, sensor_id: str) -> Optional[Sensor]:
        """Buscar sensor por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Sensor]:
        """Obtener todos los sensores"""
        pass
    
    @abstractmethod
    def update(self, sensor: Sensor) -> None:
        """Actualizar sensor"""
        pass
    
    @abstractmethod
    def delete(self, sensor_id: str) -> None:
        """Eliminar sensor"""
        pass
    
    @abstractmethod
    def find_by_priority(self, priority: str) -> List[Sensor]:
        """Buscar sensores por prioridad"""
        pass
