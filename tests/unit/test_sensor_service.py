"""
Tests unitarios para SensorService
"""
import pytest
from src.domain.entities.sensor import Sensor, Location, Priority


class TestSensorService:
    """Tests para SensorService"""
    
    def test_register_sensor(self, container):
        """Test: registrar un sensor"""
        service = container.sensor_service
        
        sensor = Sensor(
            id="TEST-UNIQUE-001",
            name="Test Sensor",
            type="TEMPERATURA",
            location=Location(5.0689, -75.5174, "Manizales"),
            priority=Priority.NORMAL,
            unit="°C",
            min_value=0.0,
            max_value=50.0
        )
        
        service.register_sensor(sensor)
        retrieved = service.get_sensor("TEST-UNIQUE-001")
        
        assert retrieved is not None
        assert retrieved.name == "Test Sensor"
    
    def test_get_all_sensors(self, container):
        """Test: obtener todos los sensores"""
        service = container.sensor_service
        all_sensors = service.get_all_sensors()
        assert len(all_sensors) >= 5
    
    def test_get_active_sensors(self, container):
        """Test: obtener sensores activos"""
        service = container.sensor_service
        active_sensors = service.get_active_sensors()
        assert len(active_sensors) >= 5
