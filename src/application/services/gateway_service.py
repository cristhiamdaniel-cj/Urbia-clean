"""
Application Service: Gateway Service
Orquesta operaciones de gateways
"""
from typing import List, Optional
from collections import defaultdict
from src.domain.entities.gateway import Gateway
from src.domain.entities.sensor import Sensor
from src.domain.entities.telemetry import Telemetry
from src.domain.repositories.gateway_repository import IGatewayRepository
from src.domain.repositories.sensor_repository import ISensorRepository
from src.domain.services.gateway_service import GatewayDomainService
from src.shared.events.event_bus import EventBus
from src.shared.events.gateway_events import (
    GatewayStartedEvent,
    SensorConnectedToGatewayEvent,
    TelemetryAggregatedEvent,
    GatewayOverloadEvent
)


class GatewayApplicationService:
    """Servicio de aplicación para gateways"""
    
    def __init__(
        self,
        gateway_repository: IGatewayRepository,
        sensor_repository: ISensorRepository,
        event_bus: EventBus
    ):
        self.gateway_repository = gateway_repository
        self.sensor_repository = sensor_repository
        self.event_bus = event_bus
        self.domain_service = GatewayDomainService()
        
        # Buffer para agregación
        self._telemetry_buffer: dict = defaultdict(list)
    
    def register_gateway(self, gateway: Gateway) -> Gateway:
        """Registrar nuevo gateway"""
        self.gateway_repository.save(gateway)
        
        # Publicar evento
        self.event_bus.publish(GatewayStartedEvent(
            gateway_id=gateway.id,
            gateway_name=gateway.name
        ))
        
        return gateway
    
    def assign_sensor_to_gateway(
        self,
        sensor_id: str,
        gateway_id: str
    ) -> None:
        """Asignar sensor a gateway"""
        gateway = self.gateway_repository.find_by_id(gateway_id)
        sensor = self.sensor_repository.find_by_id(sensor_id)
        
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} no encontrado")
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} no encontrado")
        
        # Verificar que gateway puede manejar el sensor
        if not self.domain_service.can_handle_sensor(gateway, sensor):
            raise ValueError(f"Gateway {gateway_id} no puede manejar sensor {sensor_id}")
        
        # Asignar
        gateway.add_sensor(sensor_id)
        self.gateway_repository.save(gateway)
        
        # Publicar evento
        self.event_bus.publish(SensorConnectedToGatewayEvent(
            sensor_id=sensor_id,
            gateway_id=gateway_id
        ))
        
        # Verificar sobrecarga
        load = self.domain_service.calculate_load(gateway)
        if load > 80:
            self.event_bus.publish(GatewayOverloadEvent(
                gateway_id=gateway_id,
                current_load=load,
                sensor_count=gateway.sensor_count()
            ))
    
    def process_telemetry_at_edge(
        self,
        telemetry: Telemetry,
        gateway_id: str
    ) -> Optional[Telemetry]:
        """
        Procesar telemetría en el borde (edge processing)
        
        Returns:
            Telemetry agregada o None si se bufferizó
        """
        sensor_id = str(telemetry.sensor_id)
        key = f"{gateway_id}:{sensor_id}"
        
        # Agregar a buffer
        self._telemetry_buffer[key].append(telemetry)
        
        # Verificar si agregar
        if self.domain_service.should_aggregate(self._telemetry_buffer[key]):
            # Agregar datos
            aggregated = self.domain_service.aggregate_telemetry(
                self._telemetry_buffer[key]
            )
            
            # Publicar evento
            self.event_bus.publish(TelemetryAggregatedEvent(
                gateway_id=gateway_id,
                sensor_id=sensor_id,
                original_count=len(self._telemetry_buffer[key]),
                aggregated_value=aggregated.value
            ))
            
            # Limpiar buffer
            self._telemetry_buffer[key].clear()
            
            return aggregated
        
        # Si es crítico, enviar inmediatamente
        if telemetry.is_critical:
            return telemetry
        
        return None
    
    def auto_assign_sensors(self) -> None:
        """Asignar sensores automáticamente a gateways más cercanos"""
        gateways = self.gateway_repository.find_active()
        sensors = self.sensor_repository.find_all()
        
        for sensor in sensors:
            # Buscar gateway más cercano
            closest_gateway = None
            min_distance = float('inf')
            
            for gateway in gateways:
                if self.domain_service.can_handle_sensor(gateway, sensor):
                    distance = gateway.location.distance_to(sensor.location)
                    if distance < min_distance:
                        min_distance = distance
                        closest_gateway = gateway
            
            if closest_gateway:
                try:
                    self.assign_sensor_to_gateway(
                        str(sensor.id),
                        closest_gateway.id
                    )
                except Exception as e:
                    print(f"Error asignando {sensor.id}: {e}")
    
    def get_gateway_stats(self, gateway_id: str) -> dict:
        """Obtener estadísticas del gateway"""
        gateway = self.gateway_repository.find_by_id(gateway_id)
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} no encontrado")
        
        load = self.domain_service.calculate_load(gateway)
        
        return {
            'gateway_id': gateway.id,
            'name': gateway.name,
            'is_active': gateway.is_active,
            'sensor_count': gateway.sensor_count(),
            'load_percentage': load,
            'connected_sensors': gateway.connected_sensors
        }
