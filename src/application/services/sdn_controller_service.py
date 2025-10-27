"""
Application Service: SDN Controller
Controlador SDN principal del sistema
"""
from typing import List, Optional
import uuid
from datetime import datetime
from src.domain.entities.route import Route
from src.domain.entities.sensor import Sensor
from src.domain.entities.routing_decision import RoutingDecision
from src.domain.services.routing_strategy import RoutingStrategy, QoSRoutingStrategy
from src.domain.repositories.sensor_repository import ISensorRepository
from src.shared.events.event_bus import EventBus


class SDNControllerService:
    """Servicio del controlador SDN"""
    
    def __init__(
        self,
        sensor_repository: ISensorRepository,
        event_bus: EventBus,
        routing_strategy: Optional[RoutingStrategy] = None
    ):
        self.sensor_repository = sensor_repository
        self.event_bus = event_bus
        
        # Estrategia por defecto: QoS
        self.routing_strategy = routing_strategy or QoSRoutingStrategy()
        
        # Rutas del sistema
        self._routes: List[Route] = []
        
        # Historial de decisiones
        self._decisions_history: List[RoutingDecision] = []
    
    def initialize_routes(self) -> None:
        """Inicializar rutas del sistema"""
        self._routes = [
            Route(
                id="ROUTE_A",
                name="Ruta A (Larga)",
                latency_ms=29.2,
                bandwidth_mbps=100.0,
                hop_count=3,
                current_load=0.0
            ),
            Route(
                id="ROUTE_B",
                name="Ruta B (Corta)",
                latency_ms=20.0,
                bandwidth_mbps=50.0,
                hop_count=2,
                current_load=0.0
            )
        ]
        
        print(f"✅ {len(self._routes)} rutas inicializadas")
    
    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Cambiar estrategia de enrutamiento"""
        self.routing_strategy = strategy
        print(f"🔄 Estrategia cambiada a: {strategy.get_strategy_name()}")
    
    def route_packet(self, sensor_id: str) -> Optional[RoutingDecision]:
        """
        Enrutar paquete de un sensor
        
        Returns:
            RoutingDecision con la ruta seleccionada
        """
        # Obtener sensor
        sensor = self.sensor_repository.find_by_id(sensor_id)
        if not sensor:
            return None
        
        # Seleccionar ruta usando estrategia
        selected_route = self.routing_strategy.select_route(
            self._routes,
            sensor
        )
        
        if not selected_route:
            return None
        
        # Crear decisión
        decision = RoutingDecision(
            packet_id=str(uuid.uuid4())[:8],
            sensor_id=sensor_id,
            sensor_priority=sensor.priority.value,
            selected_route=selected_route.name,
            route_latency=selected_route.latency_ms,
            route_load=selected_route.current_load,
            reason=self._get_decision_reason(selected_route, sensor)
        )
        
        # Incrementar carga
        selected_route.add_load(0.5)  # 0.5% por paquete
        
        # Guardar en historial
        self._decisions_history.append(decision)
        
        # Limitar historial a últimos 1000
        if len(self._decisions_history) > 1000:
            self._decisions_history = self._decisions_history[-1000:]
        
        return decision
    
    def _get_decision_reason(self, route: Route, sensor: Sensor) -> str:
        """Generar razón de la decisión"""
        priority = sensor.priority.value
        
        if priority == "CRITICA":
            return f"Prioridad crítica → Ruta de baja latencia ({route.latency_ms}ms)"
        elif route.is_congested():
            return f"Ruta principal congestionada → Alternativa ({route.name})"
        elif priority == "NORMAL":
            return f"Tráfico normal → Balanceo de carga"
        else:
            return f"Tráfico bulk → Alta capacidad ({route.bandwidth_mbps}Mbps)"
    
    def get_route_stats(self) -> List[dict]:
        """Obtener estadísticas de rutas"""
        return [
            {
                'id': route.id,
                'name': route.name,
                'latency_ms': route.latency_ms,
                'bandwidth_mbps': route.bandwidth_mbps,
                'current_load': route.current_load,
                'is_available': route.is_available,
                'is_congested': route.is_congested()
            }
            for route in self._routes
        ]
    
    def get_recent_decisions(self, limit: int = 100) -> List[dict]:
        """Obtener decisiones recientes"""
        recent = self._decisions_history[-limit:]
        return [d.to_dict() for d in recent]
    
    def simulate_congestion(self, route_id: str, load: float = 85.0) -> None:
        """Simular congestión en una ruta"""
        for route in self._routes:
            if route.id == route_id:
                route.current_load = load
                print(f"⚠️ Congestión simulada en {route.name}: {load}%")
                break
    
    def reset_loads(self) -> None:
        """Resetear cargas de todas las rutas"""
        for route in self._routes:
            route.current_load = 0.0
        print("🔄 Cargas de rutas reseteadas")
    
    def get_controller_stats(self) -> dict:
        """Estadísticas generales del controlador"""
        total_decisions = len(self._decisions_history)
        
        # Contar por ruta
        route_counts = {}
        for decision in self._decisions_history:
            route = decision.selected_route
            route_counts[route] = route_counts.get(route, 0) + 1
        
        return {
            'total_decisions': total_decisions,
            'routing_strategy': self.routing_strategy.get_strategy_name(),
            'route_distribution': route_counts,
            'active_routes': len([r for r in self._routes if r.is_available])
        }
