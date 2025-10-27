"""
Rutas API para telemetría
"""
from flask import Blueprint, jsonify, request
from src.application.dto.telemetry_dto import TelemetryDTO
from config.di_container import DIContainer


telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/telemetry')


@telemetry_bp.route('/current', methods=['GET'])
def get_current_telemetry():
    """GET /api/telemetry/current - Obtener telemetría actual de todos los sensores"""
    try:
        container = DIContainer()
        sensors = container.sensor_service.get_active_sensors()
        
        current_data = []
        for sensor in sensors:
            telemetry = container.telemetry_service.get_latest_telemetry(str(sensor.id))
            
            if telemetry:
                # Formato que espera el frontend
                data = {
                    'sensor_id': str(sensor.id),
                    'sensor_name': sensor.name,
                    'sensor_type': sensor.type,
                    'value': telemetry.value,
                    'unit': telemetry.unit,
                    'timestamp': telemetry.timestamp.isoformat(),
                    'is_critical': telemetry.is_critical,
                    'age_seconds': telemetry.age_seconds(),
                    # Datos adicionales del sensor
                    'location': {
                        'lat': sensor.location.latitude,
                        'lng': sensor.location.longitude
                    },
                    'priority': sensor.priority.value,
                    'status': 'active' if sensor.is_active else 'inactive'
                }
                current_data.append(data)
        
        return jsonify(current_data), 200
        
    except Exception as e:
        print(f"Error en /api/telemetry/current: {e}")
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/<sensor_id>/latest', methods=['GET'])
def get_latest_telemetry(sensor_id: str):
    """GET /api/telemetry/:id/latest - Obtener última telemetría de un sensor"""
    try:
        container = DIContainer()
        
        # Obtener sensor
        sensor = container.sensor_service.get_sensor(sensor_id)
        if not sensor:
            return jsonify({'error': 'Sensor no encontrado'}), 404
        
        # Obtener telemetría
        telemetry = container.telemetry_service.get_latest_telemetry(sensor_id)
        if not telemetry:
            return jsonify({'message': 'No hay telemetría disponible'}), 404
        
        data = {
            'sensor_id': str(sensor.id),
            'sensor_name': sensor.name,
            'sensor_type': sensor.type,
            'value': telemetry.value,
            'unit': telemetry.unit,
            'timestamp': telemetry.timestamp.isoformat(),
            'is_critical': telemetry.is_critical,
            'age_seconds': telemetry.age_seconds()
        }
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/', methods=['POST'])
def submit_telemetry():
    """POST /api/telemetry - Recibir telemetría"""
    try:
        data = request.get_json()
        
        sensor_id = data.get('sensor_id')
        value = data.get('value')
        
        if not sensor_id or value is None:
            return jsonify({'error': 'sensor_id y value requeridos'}), 400
        
        container = DIContainer()
        telemetry = container.telemetry_service.process_telemetry(
            sensor_id=sensor_id,
            value=float(value)
        )
        
        dto = TelemetryDTO.from_entity(telemetry)
        
        return jsonify({
            'message': 'Telemetría procesada',
            'data': dto.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
