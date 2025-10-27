"""
Interface del repositorio de gateways
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.gateway import Gateway


class IGatewayRepository(ABC):
    """Interface para persistencia de gateways"""
    
    @abstractmethod
    def save(self, gateway: Gateway) -> None:
        """Guardar gateway"""
        pass
    
    @abstractmethod
    def find_by_id(self, gateway_id: str) -> Optional[Gateway]:
        """Buscar gateway por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Gateway]:
        """Obtener todos los gateways"""
        pass
    
    @abstractmethod
    def find_active(self) -> List[Gateway]:
        """Obtener gateways activos"""
        pass
