"""
Strategy Pattern: Algoritmos de enrutamiento
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.route import Route
from src.domain.entities.sensor import Sensor


class RoutingStrategy(ABC):
    """Interface para estrategias de enrutamiento"""
    
    @abstractmethod
    def select_route(
        self,
        available_routes: List[Route],
        sensor: Sensor
    ) -> Optional[Route]:
        """Seleccionar mejor ruta"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Nombre de la estrategia"""
        pass


class QoSRoutingStrategy(RoutingStrategy):
    """
    Enrutamiento basado en Quality of Service
    Considera prioridad del sensor
    """
    
    def select_route(
        self,
        available_routes: List[Route],
        sensor: Sensor
    ) -> Optional[Route]:
        """Seleccionar ruta según QoS"""
        if not available_routes:
            return None
        
        # Filtrar rutas disponibles
        active_routes = [r for r in available_routes if r.is_available]
        if not active_routes:
            return None
        
        priority = sensor.priority.value
        
        # Filtrar por capacidad de prioridad
        capable_routes = [
            r for r in active_routes 
            if r.can_handle_priority(priority)
        ]
        
        if not capable_routes:
            # Si ninguna puede manejar, usar la mejor disponible
            capable_routes = active_routes
        
        # Calcular scores
        scored_routes = [
            (route, route.calculate_score(priority))
            for route in capable_routes
        ]
        
        # Ordenar por score (mayor a menor)
        scored_routes.sort(key=lambda x: x[1], reverse=True)
        
        return scored_routes[0][0]
    
    def get_strategy_name(self) -> str:
        return "QoS-Based Routing"


class LoadBalancingStrategy(RoutingStrategy):
    """
    Enrutamiento con balanceo de carga
    Distribuye tráfico equitativamente
    """
    
    def select_route(
        self,
        available_routes: List[Route],
        sensor: Sensor
    ) -> Optional[Route]:
        """Seleccionar ruta con menor carga"""
        active_routes = [r for r in available_routes if r.is_available]
        if not active_routes:
            return None
        
        # Ordenar por carga (menor a mayor)
        sorted_routes = sorted(active_routes, key=lambda r: r.current_load)
        
        return sorted_routes[0]
    
    def get_strategy_name(self) -> str:
        return "Load Balancing"


class LowLatencyStrategy(RoutingStrategy):
    """
    Enrutamiento de baja latencia
    Siempre usa ruta más rápida disponible
    """
    
    def select_route(
        self,
        available_routes: List[Route],
        sensor: Sensor
    ) -> Optional[Route]:
        """Seleccionar ruta con menor latencia"""
        active_routes = [r for r in available_routes if r.is_available]
        if not active_routes:
            return None
        
        # Ordenar por latencia (menor a mayor)
        sorted_routes = sorted(active_routes, key=lambda r: r.latency_ms)
        
        return sorted_routes[0]
    
    def get_strategy_name(self) -> str:
        return "Low Latency"


class HighThroughputStrategy(RoutingStrategy):
    """
    Enrutamiento de alto throughput
    Prioriza ancho de banda
    """
    
    def select_route(
        self,
        available_routes: List[Route],
        sensor: Sensor
    ) -> Optional[Route]:
        """Seleccionar ruta con mayor ancho de banda"""
        active_routes = [r for r in available_routes if r.is_available]
        if not active_routes:
            return None
        
        # Ordenar por bandwidth (mayor a menor)
        sorted_routes = sorted(
            active_routes,
            key=lambda r: r.bandwidth_mbps,
            reverse=True
        )
        
        return sorted_routes[0]
    
    def get_strategy_name(self) -> str:
        return "High Throughput"
