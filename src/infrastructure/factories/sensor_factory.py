"""
Factory Pattern: Creación de sensores
Encapsula la lógica de creación compleja
"""
from typing import Dict, Any
from src.domain.entities.sensor import Sensor
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority


class SensorFactory:
    """Factory para crear sensores de diferentes tipos"""
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Sensor:
        """
        Crear sensor desde configuración
        
        Args:
            config: Diccionario con configuración del sensor
            
        Returns:
            Sensor creado y validado
            
        Raises:
            ValueError: Si la configuración es inválida
        """
        # Validar configuración requerida
        required_fields = ['id', 'nombre', 'tipo', 'ubicacion', 'prioridad']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Crear value objects
        sensor_id = SensorId(config['id'])
        
        location = Location(
            latitude=config['ubicacion']['lat'],
            longitude=config['ubicacion']['lng'],
            address=config['ubicacion'].get('direccion'),
            city=config['ubicacion'].get('ciudad', 'Manizales')
        )
        
        # Mapear prioridad
        priority_map = {
            'CRITICA': Priority.CRITICAL,
            'ALTA': Priority.HIGH,
            'NORMAL': Priority.NORMAL,
            'BAJA': Priority.LOW
        }
        priority = priority_map.get(
            config['prioridad'].upper(), 
            Priority.NORMAL
        )
        
        # Extraer rangos según tipo
        sensor_type = config['tipo'].upper()
        ranges = SensorFactory._get_ranges_for_type(sensor_type)
        
        # Crear sensor
        sensor = Sensor(
            id=sensor_id,
            name=config['nombre'],
            type=sensor_type,
            location=location,
            priority=priority,
            unit=ranges['unit'],
            min_value=ranges['min'],
            max_value=ranges['max'],
            threshold_critical=ranges.get('threshold')
        )
        
        return sensor
    
    @staticmethod
    def _get_ranges_for_type(sensor_type: str) -> Dict[str, Any]:
        """Obtener rangos y umbrales según tipo de sensor"""
        ranges = {
            'RUIDO': {
                'unit': 'dB',
                'min': 30.0,
                'max': 120.0,
                'threshold': 70.0
            },
            'TEMPERATURA': {
                'unit': '°C',
                'min': 0.0,
                'max': 50.0,
                'threshold': 30.0
            },
            'TRAFICO': {
                'unit': 'veh/min',
                'min': 0.0,
                'max': 200.0,
                'threshold': 100.0
            },
            'CALIDAD_AIRE': {
                'unit': 'AQI',
                'min': 0.0,
                'max': 500.0,
                'threshold': 100.0
            },
            'LUZ': {
                'unit': 'lux',
                'min': 0.0,
                'max': 10000.0,
                'threshold': 1000.0
            }
        }
        
        return ranges.get(sensor_type, {
            'unit': 'unknown',
            'min': 0.0,
            'max': 100.0,
            'threshold': None
        })
    
    @staticmethod
    def create_noise_sensor(
        sensor_id: str,
        name: str,
        location: Location,
        priority: Priority = Priority.CRITICAL
    ) -> Sensor:
        """Helper: Crear sensor de ruido"""
        return Sensor(
            id=SensorId(sensor_id),
            name=name,
            type='RUIDO',
            location=location,
            priority=priority,
            unit='dB',
            min_value=30.0,
            max_value=120.0,
            threshold_critical=70.0
        )
    
    @staticmethod
    def create_temperature_sensor(
        sensor_id: str,
        name: str,
        location: Location,
        priority: Priority = Priority.NORMAL
    ) -> Sensor:
        """Helper: Crear sensor de temperatura"""
        return Sensor(
            id=SensorId(sensor_id),
            name=name,
            type='TEMPERATURA',
            location=location,
            priority=priority,
            unit='°C',
            min_value=0.0,
            max_value=50.0,
            threshold_critical=30.0
        )
