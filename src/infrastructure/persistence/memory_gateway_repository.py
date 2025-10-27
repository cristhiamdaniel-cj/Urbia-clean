"""
Implementación en memoria de IGatewayRepository
"""
from typing import List, Optional, Dict
from src.domain.entities.gateway import Gateway
from src.domain.repositories.gateway_repository import IGatewayRepository


class InMemoryGatewayRepository(IGatewayRepository):
    """Repositorio en memoria para gateways"""
    
    def __init__(self):
        self._gateways: Dict[str, Gateway] = {}
    
    def save(self, gateway: Gateway) -> None:
        """Guardar gateway"""
        self._gateways[gateway.id] = gateway
    
    def find_by_id(self, gateway_id: str) -> Optional[Gateway]:
        """Buscar por ID"""
        return self._gateways.get(gateway_id)
    
    def find_all(self) -> List[Gateway]:
        """Obtener todos"""
        return list(self._gateways.values())
    
    def find_active(self) -> List[Gateway]:
        """Obtener activos"""
        return [g for g in self._gateways.values() if g.is_active]
    
    def clear(self) -> None:
        """Limpiar repositorio"""
        self._gateways.clear()
