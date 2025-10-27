"""
Dependency Injection Container
"""
from src.infrastructure.persistence.memory_sensor_repository import InMemorySensorRepository
from src.infrastructure.persistence.memory_telemetry_repository import InMemoryTelemetryRepository
from src.infrastructure.persistence.memory_gateway_repository import InMemoryGatewayRepository
from src.infrastructure.factories.sensor_factory import SensorFactory
from src.infrastructure.factories.gateway_factory import GatewayFactory
from src.application.services.sensor_service import SensorService
from src.application.services.telemetry_service import TelemetryService
from src.application.services.gateway_service import GatewayApplicationService
from src.application.services.sdn_controller_service import SDNControllerService
from src.shared.events.event_bus import EventBus


class DIContainer:
    """Contenedor de inyección de dependencias - Singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Event Bus (Singleton)
        self._event_bus = EventBus()
        
        # Repositories
        self._sensor_repository = InMemorySensorRepository()
        self._telemetry_repository = InMemoryTelemetryRepository()
        self._gateway_repository = InMemoryGatewayRepository()
        
        # Factories
        self._sensor_factory = SensorFactory()
        self._gateway_factory = GatewayFactory()
        
        # Services
        self._sensor_service = SensorService(
            sensor_repository=self._sensor_repository,
            event_bus=self._event_bus
        )
        
        self._telemetry_service = TelemetryService(
            telemetry_repository=self._telemetry_repository,
            sensor_repository=self._sensor_repository,
            event_bus=self._event_bus
        )
        
        self._gateway_service = GatewayApplicationService(
            gateway_repository=self._gateway_repository,
            sensor_repository=self._sensor_repository,
            event_bus=self._event_bus
        )
        
        self._sdn_controller = SDNControllerService(
            sensor_repository=self._sensor_repository,
            event_bus=self._event_bus
        )
        
        self._initialized = True
    
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus
    
    @property
    def sensor_repository(self):
        return self._sensor_repository
    
    @property
    def telemetry_repository(self):
        return self._telemetry_repository
    
    @property
    def gateway_repository(self):
        return self._gateway_repository
    
    @property
    def sensor_factory(self) -> SensorFactory:
        return self._sensor_factory
    
    @property
    def gateway_factory(self) -> GatewayFactory:
        return self._gateway_factory
    
    @property
    def sensor_service(self) -> SensorService:
        return self._sensor_service
    
    @property
    def telemetry_service(self) -> TelemetryService:
        return self._telemetry_service
    
    @property
    def gateway_service(self) -> GatewayApplicationService:
        return self._gateway_service
    
    @property
    def sdn_controller(self) -> SDNControllerService:
        return self._sdn_controller
