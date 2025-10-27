"""
Application Service: Telemetry Service
Procesa telemetría de sensores
"""
from typing import List, Optional
from datetime import datetime
from src.domain.entities.telemetry import Telemetry
from src.domain.entities.sensor import Sensor
from src.domain.repositories.telemetry_repository import ITelemetryRepository
from src.domain.repositories.sensor_repository import ISensorRepository
from src.shared.events.event_bus import EventBus
from src.shared.events.events import TelemetryReceivedEvent, CriticalAlertEvent


class TelemetryService:
    """Servicio para procesamiento de telemetría"""
    
    def __init__(
        self,
        telemetry_repository: ITelemetryRepository,
        sensor_repository: ISensorRepository,
        event_bus: EventBus
    ):
        self.telemetry_repository = telemetry_repository
        self.sensor_repository = sensor_repository
        self.event_bus = event_bus
    
    def process_telemetry(
        self,
        sensor_id: str,
        value: float,
        gateway_id: Optional[str] = None
    ) -> Telemetry:
        """
        Procesar nueva telemetría
        
        Args:
            sensor_id: ID del sensor
            value: Valor medido
            gateway_id: ID del gateway (opcional)
            
        Returns:
            Telemetría procesada
        """
        # Obtener sensor
        sensor = self.sensor_repository.find_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} no encontrado")
        
        # Verificar si es crítico
        is_critical = sensor.is_critical_value(value)
        
        # Crear telemetría
        from src.domain.value_objects.sensor_id import SensorId
        telemetry = Telemetry(
            sensor_id=SensorId(sensor_id),
            value=value,
            unit=sensor.unit,
            is_critical=is_critical,
            gateway_id=gateway_id
        )
        
        # Guardar
        self.telemetry_repository.save(telemetry)
        
        # Publicar evento
        self.event_bus.publish(TelemetryReceivedEvent(
            sensor_id=sensor_id,
            value=value,
            is_critical=is_critical
        ))
        
        # Si es crítico, publicar alerta
        if is_critical:
            self.event_bus.publish(CriticalAlertEvent(
                sensor_id=sensor_id,
                sensor_name=sensor.name,
                value=value,
                threshold=sensor.threshold_critical,
                message=f"Valor crítico detectado: {value}{sensor.unit}"
            ))
        
        return telemetry
    
    def get_latest_telemetry(self, sensor_id: str) -> Optional[Telemetry]:
        """Obtener última telemetría de un sensor"""
        return self.telemetry_repository.get_latest(sensor_id)
    
    def get_sensor_history(
        self,
        sensor_id: str,
        limit: int = 100
    ) -> List[Telemetry]:
        """Obtener historial de telemetría"""
        return self.telemetry_repository.find_by_sensor(sensor_id, limit)
