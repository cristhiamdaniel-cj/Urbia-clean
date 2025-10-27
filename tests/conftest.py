"""
Fixtures compartidas para todos los tests
"""
import pytest
from config.di_container import DIContainer
from src.infrastructure.persistence.sensor_loader import SensorLoader


@pytest.fixture(scope="function")
def container():
    """
    Fixture que crea un contenedor DI con sensores precargados
    """
    container = DIContainer()
    
    # Cargar sensores de Manizales
    loader = SensorLoader(
        sensor_factory=container.sensor_factory,
        sensor_service=container.sensor_service
    )
    
    try:
        loader.load_manizales_sensors()
    except Exception as e:
        pass  # Ignorar errores de sensores duplicados
    
    # Inicializar SDN
    container.sdn_controller.initialize_routes()
    
    return container
