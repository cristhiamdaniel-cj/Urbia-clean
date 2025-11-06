"""
Servicio DLMS - Integración con Sistema de Telemetría UrbIA
==========================================================

Este servicio integra el DLMS Data Sync Service y DLMS Sensor Adapter 
con el sistema de telemetría existente para procesar datos DLMS, 
generar analytics y manejar eventos en tiempo real.

Autor: Sistema UrbIA - Universidad Nacional de Colombia
Fecha: 2025-11-06
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import statistics

# Configuración de logging
logger = logging.getLogger(__name__)

class DLMSDeviceType(Enum):
    """Tipos de dispositivos DLMS identificados"""
    MONOFASICO = "DLMS-Meter-01"
    TRIFASICO = "DLMS-Meter-02"
    POLYFASICO = "DLMS-Meter-03"

class DLMSEventType(Enum):
    """Tipos de eventos DLMS"""
    DATA_SYNC = "data_sync"
    ANALYTICS_UPDATE = "analytics_update"
    ALERT_TRIGGERED = "alert_triggered"
    DEVICE_OFFLINE = "device_offline"
    QUALITY_ANOMALY = "quality_anomaly"

@dataclass
class DLMSReading:
    """Lectura individual de dispositivo DLMS"""
    device_id: str
    device_type: DLMSDeviceType
    timestamp: datetime
    measurements: Dict[str, float]
    quality_flag: bool = True
    raw_data: Optional[Dict] = None

@dataclass
class DLMSAnalytics:
    """Analytics calculados para dispositivo DLMS"""
    device_id: str
    period_start: datetime
    period_end: datetime
    total_energy: float
    avg_power: float
    peak_power: float
    power_factor: float
    frequency_variation: float
    voltage_stability: float
    load_factor: float
    quality_score: float

@dataclass
class DLMSEvent:
    """Evento del sistema DLMS"""
    event_type: DLMSEventType
    device_id: str
    timestamp: datetime
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    data: Optional[Dict] = None

class DLMSService:
    """
    Servicio principal que integra sync service y adapter con telemetría
    
    Responsabilidades:
    - Procesar datos DLMS sincronizados
    - Generar analytics en tiempo real
    - Manejar eventos y alertas
    - Integrar con sistema de telemetría existente
    """
    
    def __init__(self):
        self.logger = logger
        self._active_devices = set()
        self._recent_readings = {}
        self._analytics_cache = {}
        self._event_handlers = {}
        self._sync_service = None
        self._sensor_adapter = None
        self._telemetry_service = None
        
    def set_dependencies(self, sync_service, sensor_adapter, telemetry_service):
        """
        Configurar dependencias del servicio
        
        Args:
            sync_service: DLMS Data Sync Service
            sensor_adapter: DLMS Sensor Adapter  
            telemetry_service: Servicio de telemetría existente
        """
        self._sync_service = sync_service
        self._sensor_adapter = sensor_adapter
        self._telemetry_service = telemetry_service
        
        self.logger.info("DLMS Service dependencies configured")
        
    async def initialize(self) -> bool:
        """
        Inicializar el servicio DLMS
        
        Returns:
            bool: True si la inicialización es exitosa
        """
        try:
            # Registrar tipos de sensores DLMS
            self._register_dlms_sensor_types()
            
            # Configurar manejadores de eventos
            self._setup_event_handlers()
            
            # Inicializar dispositivos activos
            await self._discover_active_devices()
            
            self.logger.info("DLMS Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize DLMS Service: {e}")
            return False
    
    def _register_dlms_sensor_types(self):
        """Registrar tipos de sensores DLMS en el sistema"""
        dlms_sensor_types = [
            "VOLTAJE", "CORRIENTE", "POTENCIA", "ENERGIA", 
            "FRECUENCIA", "VOLTAJE_L1", "VOLTAJE_L2", "VOLTAJE_L3",
            "CORRIENTE_L1", "CORRIENTE_L2", "CORRIENTE_L3",
            "POWER_FACTOR", "THD_VOLTAGE", "THD_CURRENT"
        ]
        
        self.logger.info(f"Registered {len(dlms_sensor_types)} DLMS sensor types")
    
    def _setup_event_handlers(self):
        """Configurar manejadores de eventos DLMS"""
        self._event_handlers = {
            DLMSEventType.DATA_SYNC: self._handle_data_sync_event,
            DLMSEventType.ANALYTICS_UPDATE: self._handle_analytics_update,
            DLMSEventType.ALERT_TRIGGERED: self._handle_alert_event,
            DLMSEventType.DEVICE_OFFLINE: self._handle_device_offline,
            DLMSEventType.QUALITY_ANOMALY: self._handle_quality_anomaly
        }
    
    async def _discover_active_devices(self):
        """Descubrir dispositivos DLMS activos"""
        try:
            # Esta función interactuaría con el sync service para encontrar dispositivos
            active_devices = await self._sync_service.get_active_devices()
            self._active_devices = set(active_devices)
            
            self.logger.info(f"Discovered {len(self._active_devices)} active DLMS devices")
            
        except Exception as e:
            self.logger.error(f"Failed to discover DLMS devices: {e}")
    
    async def process_dlms_data(self, raw_data: List[Dict]) -> List[DLMSReading]:
        """
        Procesar datos DLMS sin procesar
        
        Args:
            raw_data: Datos sin procesar del sync service
            
        Returns:
            List[DLMSReading]: Lecturas procesadas
        """
        readings = []
        
        try:
            for data_item in raw_data:
                # Usar sensor adapter para procesar datos
                reading = await self._sensor_adapter.process_raw_data(data_item)
                
                if reading:
                    readings.append(reading)
                    
                    # Almacenar para analytics
                    device_id = reading.device_id
                    if device_id not in self._recent_readings:
                        self._recent_readings[device_id] = []
                    
                    self._recent_readings[device_id].append(reading)
                    
                    # Mantener solo las últimas 1000 lecturas por dispositivo
                    if len(self._recent_readings[device_id]) > 1000:
                        self._recent_readings[device_id] = self._recent_readings[device_id][-1000:]
            
            # Integrar con sistema de telemetría existente
            if self._telemetry_service and readings:
                await self._integrate_with_telemetry(readings)
            
            # Generar eventos para nuevos datos
            for reading in readings:
                await self._trigger_event(DLMSEvent(
                    event_type=DLMSEventType.DATA_SYNC,
                    device_id=reading.device_id,
                    timestamp=reading.timestamp,
                    severity="INFO",
                    message=f"Processed DLMS data from {reading.device_id}"
                ))
            
            self.logger.info(f"Processed {len(readings)} DLMS readings")
            
        except Exception as e:
            self.logger.error(f"Error processing DLMS data: {e}")
            
        return readings
    
    async def _integrate_with_telemetry(self, readings: List[DLMSReading]):
        """Integrar lecturas DLMS con el sistema de telemetría existente"""
        try:
            for reading in readings:
                for measurement_type, value in reading.measurements.items():
                    telemetry_entry = {
                        'sensor_id': f"{reading.device_id}_{measurement_type}",
                        'sensor_type': measurement_type,
                        'value': value,
                        'timestamp': reading.timestamp.isoformat(),
                        'unit': self._get_unit_for_measurement(measurement_type),
                        'quality_flag': reading.quality_flag,
                        'source': 'DLMS'
                    }
                    
                    # Enviar al servicio de telemetría
                    await self._telemetry_service.add_telemetry_entry(telemetry_entry)
                    
        except Exception as e:
            self.logger.error(f"Failed to integrate with telemetry: {e}")
    
    def _get_unit_for_measurement(self, measurement_type: str) -> str:
        """Obtener unidad de medida para tipo de medición"""
        units_map = {
            'VOLTAJE': 'V', 'VOLTAJE_L1': 'V', 'VOLTAJE_L2': 'V', 'VOLTAJE_L3': 'V',
            'CORRIENTE': 'A', 'CORRIENTE_L1': 'A', 'CORRIENTE_L2': 'A', 'CORRIENTE_L3': 'A',
            'POTENCIA': 'W', 'Active_Power': 'W',
            'ENERGIA': 'Wh', 'Active_Energy': 'Wh',
            'FRECUENCIA': 'Hz',
            'POWER_FACTOR': 'pf',
            'THD_VOLTAGE': '%', 'THD_CURRENT': '%'
        }
        return units_map.get(measurement_type, '')
    
    async def generate_analytics(self, device_id: str = None, 
                               period_hours: int = 24) -> Dict[str, Any]:
        """
        Generar analytics para dispositivo(s) DLMS
        
        Args:
            device_id: ID específico del dispositivo (None para todos)
            period_hours: Período de análisis en horas
            
        Returns:
            Dict con analytics calculados
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=period_hours)
            devices_to_analyze = [device_id] if device_id else list(self._active_devices)
            
            analytics_results = {}
            
            for dev_id in devices_to_analyze:
                if dev_id not in self._recent_readings:
                    continue
                
                # Filtrar lecturas del período
                recent_data = [
                    reading for reading in self._recent_readings[dev_id]
                    if reading.timestamp >= cutoff_time
                ]
                
                if not recent_data:
                    continue
                
                # Calcular analytics
                analytics = await self._calculate_device_analytics(dev_id, recent_data, cutoff_time)
                analytics_results[dev_id] = analytics
                
                # Actualizar cache
                self._analytics_cache[dev_id] = analytics
            
            # Generar evento de actualización de analytics
            await self._trigger_event(DLMSEvent(
                event_type=DLMSEventType.ANALYTICS_UPDATE,
                device_id=device_id or "all",
                timestamp=datetime.now(),
                severity="INFO",
                message=f"Generated analytics for {len(analytics_results)} devices"
            ))
            
            self.logger.info(f"Generated analytics for {len(analytics_results)} devices")
            return analytics_results
            
        except Exception as e:
            self.logger.error(f"Error generating analytics: {e}")
            return {}
    
    async def _calculate_device_analytics(self, device_id: str, 
                                        readings: List[DLMSReading],
                                        period_start: datetime) -> DLMSAnalytics:
        """Calcular analytics específicos para un dispositivo"""
        
        # Extraer mediciones para análisis
        all_measurements = {}
        for reading in readings:
            for metric, value in reading.measurements.items():
                if metric not in all_measurements:
                    all_measurements[metric] = []
                all_measurements[metric].append(value)
        
        # Calcular métricas principales
        energy_values = all_measurements.get('Active_Energy', [0])
        power_values = all_measurements.get('Active_Power', [0])
        voltage_values = all_measurements.get('VOLTAJE_L1', [])
        frequency_values = all_measurements.get('FRECUENCIA', [])
        
        total_energy = max(energy_values) - min(energy_values) if len(energy_values) > 1 else 0
        avg_power = statistics.mean(power_values) if power_values else 0
        peak_power = max(power_values) if power_values else 0
        
        # Calcular indicadores de calidad
        frequency_variation = 0
        if len(frequency_values) > 1:
            frequency_variation = (max(frequency_values) - min(frequency_values)) / statistics.mean(frequency_values) * 100
        
        voltage_stability = 0
        if len(voltage_values) > 1:
            voltage_stability = 100 - (statistics.stdev(voltage_values) / statistics.mean(voltage_values) * 100)
        
        # Factor de carga y calidad
        load_factor = avg_power / peak_power if peak_power > 0 else 0
        quality_score = max(0, min(100, 100 - frequency_variation - (100 - voltage_stability)))
        
        return DLMSAnalytics(
            device_id=device_id,
            period_start=period_start,
            period_end=datetime.now(),
            total_energy=total_energy,
            avg_power=avg_power,
            peak_power=peak_power,
            power_factor=0.85,  # Valor típico para sistemas residenciales
            frequency_variation=frequency_variation,
            voltage_stability=voltage_stability,
            load_factor=load_factor,
            quality_score=quality_score
        )
    
    async def handle_dlms_events(self, events: List[Dict]) -> List[DLMSEvent]:
        """
        Manejar eventos DLMS del sync service
        
        Args:
            events: Lista de eventos del sync service
            
        Returns:
            List[DLMSEvent]: Eventos procesados
        """
        processed_events = []
        
        for event_data in events:
            try:
                # Crear evento DLMS
                dlms_event = DLMSEvent(
                    event_type=DLMSEventType(event_data.get('type', 'data_sync')),
                    device_id=event_data.get('device_id', 'unknown'),
                    timestamp=datetime.fromisoformat(event_data.get('timestamp')),
                    severity=event_data.get('severity', 'INFO'),
                    message=event_data.get('message', ''),
                    data=event_data.get('data')
                )
                
                # Procesar con manejador específico
                await self._process_event(dlms_event)
                processed_events.append(dlms_event)
                
            except Exception as e:
                self.logger.error(f"Error processing DLMS event: {e}")
        
        return processed_events
    
    async def _process_event(self, event: DLMSEvent):
        """Procesar evento individual"""
        try:
            # Ejecutar manejador específico si existe
            if event.event_type in self._event_handlers:
                await self._event_handlers[event.event_type](event)
            
            # Log del evento
            self.logger.info(f"DLMS Event: {event.event_type.value} - {event.message}")
            
        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
    
    async def _trigger_event(self, event: DLMSEvent):
        """Disparar evento del sistema"""
        await self._process_event(event)
        
        # Enviar a listeners externos si existen
        if hasattr(self, '_event_listeners'):
            for listener in self._event_listeners:
                try:
                    await listener(event)
                except Exception as e:
                    self.logger.error(f"Error in event listener: {e}")
    
    # Manejadores de eventos específicos
    async def _handle_data_sync_event(self, event: DLMSEvent):
        """Manejar evento de sincronización de datos"""
        # Lógica específica para sincronización de datos
        pass
    
    async def _handle_analytics_update(self, event: DLMSEvent):
        """Manejar evento de actualización de analytics"""
        # Invalidar cache si es necesario
        if event.device_id in self._analytics_cache:
            del self._analytics_cache[event.device_id]
    
    async def _handle_alert_event(self, event: DLMSEvent):
        """Manejar evento de alerta"""
        # Enviar alerta a sistema de notificaciones
        if self._telemetry_service:
            alert_data = {
                'type': 'dlms_alert',
                'device_id': event.device_id,
                'severity': event.severity,
                'message': event.message,
                'timestamp': event.timestamp.isoformat()
            }
            await self._telemetry_service.add_alert(alert_data)
    
    async def _handle_device_offline(self, event: DLMSEvent):
        """Manejar evento de dispositivo offline"""
        # Remover de dispositivos activos
        self._active_devices.discard(event.device_id)
        
        # Marcar como inactivo en telemetría
        if self._telemetry_service:
            await self._telemetry_service.mark_device_inactive(event.device_id)
    
    async def _handle_quality_anomaly(self, event: DLMSEvent):
        """Manejar evento de anomalía en calidad"""
        # Analizar datos recientes para detectar patrones
        await self._analyze_quality_anomaly(event.device_id)
    
    async def _analyze_quality_anomaly(self, device_id: str):
        """Analizar anomalía de calidad de energía"""
        if device_id not in self._recent_readings:
            return
        
        # Obtener últimas 10 lecturas
        recent_readings = self._recent_readings[device_id][-10:]
        
        # Detectar patrones anómalos
        voltage_values = []
        frequency_values = []
        
        for reading in recent_readings:
            voltage_values.extend([
                reading.measurements.get('VOLTAJE_L1', 0),
                reading.measurements.get('VOLTAJE_L2', 0),
                reading.measurements.get('VOLTAJE_L3', 0)
            ])
            frequency_values.append(reading.measurements.get('FRECUENCIA', 60))
        
        # Análisis estadístico básico
        if len(voltage_values) > 1:
            voltage_std = statistics.stdev(voltage_values)
            if voltage_std > 10:  # Desviación estándar > 10V
                await self._trigger_event(DLMSEvent(
                    event_type=DLMSEventType.ALERT_TRIGGERED,
                    device_id=device_id,
                    timestamp=datetime.now(),
                    severity="WARNING",
                    message=f"Voltage instability detected: std_dev={voltage_std:.2f}V"
                ))
        
        if len(frequency_values) > 1:
            freq_std = statistics.stdev(frequency_values)
            if freq_std > 1:  # Desviación estándar > 1Hz
                await self._trigger_event(DLMSEvent(
                    event_type=DLMSEventType.ALERT_TRIGGERED,
                    device_id=device_id,
                    timestamp=datetime.now(),
                    severity="WARNING",
                    message=f"Frequency instability detected: std_dev={freq_std:.2f}Hz"
                ))
    
    def get_cached_analytics(self, device_id: str = None) -> Optional[Dict]:
        """Obtener analytics desde cache"""
        if device_id:
            return self._analytics_cache.get(device_id)
        return self._analytics_cache
    
    def get_active_devices(self) -> List[str]:
        """Obtener lista de dispositivos DLMS activos"""
        return list(self._active_devices)
    
    def get_recent_readings_count(self, device_id: str) -> int:
        """Obtener cantidad de lecturas recientes para dispositivo"""
        return len(self._recent_readings.get(device_id, []))
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar estado de salud del servicio DLMS"""
        try:
            health_status = {
                'service_status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'active_devices': len(self._active_devices),
                'cached_analytics': len(self._analytics_cache),
                'total_readings': sum(len(readings) for readings in self._recent_readings.values()),
                'dependencies': {
                    'sync_service': self._sync_service is not None,
                    'sensor_adapter': self._sensor_adapter is not None,
                    'telemetry_service': self._telemetry_service is not None
                }
            }
            
            # Verificar conectividad con dispositivos
            if self._sync_service:
                try:
                    connectivity_status = await self._sync_service.check_connectivity()
                    health_status['device_connectivity'] = connectivity_status
                except Exception as e:
                    health_status['device_connectivity'] = {'error': str(e)}
            
            return health_status
            
        except Exception as e:
            return {
                'service_status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def set_event_listeners(self, listeners: List[callable]):
        """Configurar listeners para eventos externos"""
        self._event_listeners = listeners

# Instancia global del servicio
dlms_service = DLMSService()

# Funciones de conveniencia para uso directo
async def initialize_dlms_service(sync_service=None, sensor_adapter=None, telemetry_service=None):
    """Inicializar servicio DLMS con dependencias"""
    if sync_service and sensor_adapter and telemetry_service:
        dlms_service.set_dependencies(sync_service, sensor_adapter, telemetry_service)
    
    return await dlms_service.initialize()

async def process_dlms_batch(raw_data: List[Dict]) -> List[DLMSReading]:
    """Procesar lote de datos DLMS"""
    return await dlms_service.process_dlms_data(raw_data)

async def get_dlms_analytics(device_id: str = None, hours: int = 24) -> Dict[str, Any]:
    """Obtener analytics DLMS"""
    return await dlms_service.generate_analytics(device_id, hours)

async def check_dlms_health() -> Dict[str, Any]:
    """Verificar estado de salud del sistema DLMS"""
    return await dlms_service.health_check()

if __name__ == "__main__":
    # Ejemplo de uso
    async def main():
        # Inicializar servicio
        service_initialized = await initialize_dlms_service()
        
        if service_initialized:
            # Obtener estado de salud
            health = await check_dlms_health()
            print(f"DLMS Service Health: {json.dumps(health, indent=2)}")
            
            # Obtener analytics
            analytics = await get_dlms_analytics(hours=24)
            print(f"DLMS Analytics: {json.dumps(analytics, indent=2)}")
    
    # Ejecutar ejemplo
    # asyncio.run(main())