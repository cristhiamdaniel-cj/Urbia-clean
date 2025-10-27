"""
Tests unitarios para SensorFactory
"""
import pytest
from src.infrastructure.factories.sensor_factory import SensorFactory
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority


def test_create_noise_sensor():
    """Test crear sensor de ruido"""
    location = Location(5.0689, -75.5174, "Parque Caldas")
    
    sensor = SensorFactory.create_noise_sensor(
        sensor_id="NOISE-001",
        name="Monitor Ruido Centro",
        location=location
    )
    
    assert str(sensor.id) == "NOISE-001"
    assert sensor.name == "Monitor Ruido Centro"
    assert sensor.type == "RUIDO"
    assert sensor.unit == "dB"
    assert sensor.priority == Priority.CRITICAL


def test_create_from_config():
    """Test crear sensor desde configuración"""
    config = {
        'id': 'TEST-001',
        'nombre': 'Sensor Test',
        'tipo': 'TEMPERATURA',
        'ubicacion': {
            'lat': 5.0689,
            'lng': -75.5174,
            'direccion': 'Test Address'
        },
        'prioridad': 'NORMAL'
    }
    
    sensor = SensorFactory.create_from_config(config)
    
    assert str(sensor.id) == 'TEST-001'
    assert sensor.type == 'TEMPERATURA'
    assert sensor.unit == '°C'


def test_create_from_invalid_config():
    """Test config inválida"""
    config = {'id': 'TEST'}  # Falta campos requeridos
    
    with pytest.raises(ValueError):
        SensorFactory.create_from_config(config)
