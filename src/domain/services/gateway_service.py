"""
Domain Service: Gateway Service
Lógica de negocio para gateways
"""
from typing import List, Optional
from src.domain.entities.gateway import Gateway
from src.domain.entities.sensor import Sensor
from src.domain.entities.telemetry import Telemetry


class GatewayDomainService:
    """Servicio de dominio para lógica de gateways"""
    
    @staticmethod
    def can_handle_sensor(gateway: Gateway, sensor: Sensor) -> bool:
        """
        Verificar si gateway puede manejar un sensor
        Basado en proximidad geográfica
        """
        # Calcular distancia
        distance_km = gateway.location.distance_to(sensor.location)
        
        # Gateway puede manejar sensores hasta 5km
        return distance_km <= 5.0
    
    @staticmethod
    def calculate_load(gateway: Gateway) -> float:
        """
        Calcular carga del gateway
        Basado en número de sensores conectados
        """
        max_sensors = 10  # Capacidad máxima
        current_load = len(gateway.connected_sensors)
        
        return (current_load / max_sensors) * 100
    
    @staticmethod
    def should_aggregate(telemetry_batch: List[Telemetry]) -> bool:
        """
        Decidir si agregar datos antes de enviar
        """
        # Agregar si hay más de 5 lecturas del mismo sensor
        return len(telemetry_batch) >= 5
    
    @staticmethod
    def aggregate_telemetry(telemetry_batch: List[Telemetry]) -> Telemetry:
        """
        Agregar múltiples lecturas de telemetría
        Retorna valor promedio
        """
        if not telemetry_batch:
            raise ValueError("Batch vacío")
        
        avg_value = sum(t.value for t in telemetry_batch) / len(telemetry_batch)
        
        # Tomar el más reciente como base
        latest = telemetry_batch[-1]
        
        from src.domain.entities.telemetry import Telemetry
        return Telemetry(
            sensor_id=latest.sensor_id,
            value=avg_value,
            unit=latest.unit,
            is_critical=latest.is_critical,
            gateway_id=latest.gateway_id,
            metadata={'aggregated': True, 'count': len(telemetry_batch)}
        )
