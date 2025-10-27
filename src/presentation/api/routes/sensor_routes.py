"""
Rutas API para sensores
"""
from flask import Blueprint, jsonify, request
from src.application.dto.sensor_dto import SensorDTO, SensorListDTO
from src.shared.exceptions.domain_exceptions import SensorNotFoundException
from config.di_container import DIContainer


sensor_bp = Blueprint('sensors', __name__, url_prefix='/api/sensors')


@sensor_bp.route('/', methods=['GET'])
def get_all_sensors():
    """GET /api/sensors - Obtener todos los sensores"""
    try:
        container = DIContainer()
        sensors = container.sensor_service.get_all_sensors()
        
        # Formato detallado para el mapa
        sensors_data = []
        for sensor in sensors:
            # Obtener última telemetría
            telemetry = container.telemetry_service.get_latest_telemetry(str(sensor.id))
            
            sensor_data = {
                'id': str(sensor.id),
                'name': sensor.name,
                'type': sensor.type,
                'location': {
                    'lat': sensor.location.latitude,
                    'lng': sensor.location.longitude,
                    'address': sensor.location.address if hasattr(sensor.location, 'address') else '',
                    'city': sensor.location.city
                },
                'priority': sensor.priority.value,
                'is_active': sensor.is_active,
                'unit': sensor.unit,
                'min_value': sensor.min_value,
                'max_value': sensor.max_value,
                'current_value': telemetry.value if telemetry else None,
                'is_critical': telemetry.is_critical if telemetry else False,
                'last_update': telemetry.timestamp.isoformat() if telemetry else None
            }
            sensors_data.append(sensor_data)
        
        return jsonify(sensors_data), 200
        
    except Exception as e:
        print(f"Error en /api/sensors: {e}")
        return jsonify({'error': str(e)}), 500


@sensor_bp.route('/<sensor_id>', methods=['GET'])
def get_sensor(sensor_id: str):
    """GET /api/sensors/:id - Obtener sensor específico"""
    try:
        container = DIContainer()
        sensor = container.sensor_service.get_sensor(sensor_id)
        
        dto = SensorDTO.from_entity(sensor)
        
        return jsonify(dto.to_dict()), 200
        
    except SensorNotFoundException as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
