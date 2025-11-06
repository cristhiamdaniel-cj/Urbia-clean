"""
Rutas API para DLMS - Dashboard UrbIA
=====================================

Endpoints para el dashboard de monitoreo DLMS (Distributed Ledger Management System).
Proporciona acceso a dispositivos, telemetría, analytics y estado de salud.

Autor: Sistema UrbIA - Universidad Nacional de Colombia
Fecha: 2025-11-06
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import logging

# Importar servicio DLMS
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from application.services.dlms_service import dlms_service, DLMSDeviceType, DLMSReading

# Configurar blueprint
dlms_bp = Blueprint('dlms', __name__, url_prefix='/api/dlms')

# Logger para las rutas
logger = logging.getLogger(__name__)


def run_async(async_func):
    """Helper para ejecutar funciones asíncronas en contexto Flask síncrono"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(async_func)


@dlms_bp.route('/devices', methods=['GET'])
def get_devices():
    """
    Obtener lista de dispositivos DLMS activos
    
    Returns:
        JSON con lista de dispositivos y su estado
    """
    try:
        # Obtener dispositivos activos del servicio
        active_devices = run_async(_get_active_devices())
        
        # Obtener información adicional de cada dispositivo
        devices_info = []
        
        for device_id in active_devices:
            device_info = {
                'device_id': device_id,
                'status': 'online',
                'last_reading': run_async(_get_last_reading(device_id)),
                'readings_count': dlms_service.get_recent_readings_count(device_id),
                'device_type': _get_device_type(device_id),
                'timestamp': datetime.now().isoformat()
            }
            
            # Agregar analytics cacheados si existen
            cached_analytics = dlms_service.get_cached_analytics(device_id)
            if cached_analytics:
                device_info['cached_analytics'] = {
                    'total_energy': cached_analytics.total_energy,
                    'avg_power': cached_analytics.avg_power,
                    'quality_score': cached_analytics.quality_score
                }
            
            devices_info.append(device_info)
        
        response = {
            'success': True,
            'data': {
                'devices': devices_info,
                'total_count': len(devices_info),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"Retrieved {len(devices_info)} DLMS devices")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting DLMS devices: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve devices',
            'message': str(e)
        }), 500


@dlms_bp.route('/telemetry/<device_id>', methods=['GET'])
def get_telemetry(device_id):
    """
    Obtener telemetría de un dispositivo específico
    
    Args:
        device_id: ID del dispositivo DLMS
        
    Query Parameters:
        - hours: Período de tiempo en horas (default: 24)
        - measurements: Tipos de mediciones específicas (opcional)
        
    Returns:
        JSON con datos de telemetría del dispositivo
    """
    try:
        # Validar parámetros
        hours = request.args.get('hours', type=int, default=24)
        if hours <= 0 or hours > 168:  # Máximo 1 semana
            return jsonify({
                'success': False,
                'error': 'Invalid hours parameter (must be 1-168)'
            }), 400
        
        # Verificar que el dispositivo existe
        active_devices = run_async(_get_active_devices())
        if device_id not in active_devices:
            return jsonify({
                'success': False,
                'error': f'Device {device_id} not found or offline'
            }), 404
        
        # Obtener datos de telemetría
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Obtener lecturas recientes del servicio
        readings = _get_device_readings(device_id, cutoff_time)
        
        if not readings:
            return jsonify({
                'success': True,
                'data': {
                    'device_id': device_id,
                    'message': 'No readings found for the specified period',
                    'readings': [],
                    'timestamp': datetime.now().isoformat()
                }
            }), 200
        
        # Filtrar mediciones específicas si se solicitan
        requested_measurements = request.args.get('measurements')
        if requested_measurements:
            measurement_list = [m.strip() for m in requested_measurements.split(',')]
        else:
            measurement_list = None
        
        # Procesar lecturas para telemetría
        telemetry_data = _process_readings_for_telemetry(readings, measurement_list)
        
        # Calcular estadísticas adicionales
        statistics = _calculate_telemetry_statistics(telemetry_data)
        
        response = {
            'success': True,
            'data': {
                'device_id': device_id,
                'period_hours': hours,
                'readings_count': len(telemetry_data),
                'statistics': statistics,
                'readings': telemetry_data,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"Retrieved telemetry for device {device_id}: {len(telemetry_data)} readings")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting telemetry for device {device_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve telemetry data',
            'message': str(e)
        }), 500


@dlms_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Obtener analytics de dispositivos DLMS
    
    Query Parameters:
        - device_id: ID específico del dispositivo (opcional)
        - hours: Período de análisis en horas (default: 24)
        - cached: Usar datos cacheados (default: true)
        
    Returns:
        JSON con analytics calculados
    """
    try:
        # Validar parámetros
        device_id = request.args.get('device_id', type=str)
        hours = request.args.get('hours', type=int, default=24)
        use_cached = request.args.get('cached', type=bool, default=True)
        
        if hours <= 0 or hours > 720:  # Máximo 30 días
            return jsonify({
                'success': False,
                'error': 'Invalid hours parameter (must be 1-720)'
            }), 400
        
        analytics_data = {}
        
        # Intentar obtener analytics cacheados si se solicita
        if use_cached and not device_id:
            analytics_data = dlms_service.get_cached_analytics()
        
        # Generar analytics frescos si no hay cache o se solicita explícitamente
        if not use_cached or not analytics_data or (device_id and device_id not in analytics_data):
            try:
                fresh_analytics = run_async(
                    dlms_service.generate_analytics(device_id, hours)
                )
                
                # Convertir dataclasses a diccionarios para JSON
                analytics_data = {}
                for dev_id, analytics in fresh_analytics.items():
                    if hasattr(analytics, '__dict__'):  # Es un DLMSAnalytics
                        analytics_data[dev_id] = {
                            'device_id': analytics.device_id,
                            'period_start': analytics.period_start.isoformat(),
                            'period_end': analytics.period_end.isoformat(),
                            'total_energy': analytics.total_energy,
                            'avg_power': analytics.avg_power,
                            'peak_power': analytics.peak_power,
                            'power_factor': analytics.power_factor,
                            'frequency_variation': analytics.frequency_variation,
                            'voltage_stability': analytics.voltage_stability,
                            'load_factor': analytics.load_factor,
                            'quality_score': analytics.quality_score
                        }
                    else:
                        analytics_data[dev_id] = analytics
                        
            except Exception as e:
                logger.warning(f"Failed to generate fresh analytics: {e}")
                # Fallback a cache si está disponible
                analytics_data = dlms_service.get_cached_analytics()
                if not analytics_data:
                    raise
        
        # Preparar respuesta
        if device_id:
            # Analytics para dispositivo específico
            if device_id not in analytics_data:
                return jsonify({
                    'success': False,
                    'error': f'No analytics found for device {device_id}'
                }), 404
            
            response_data = {
                'device_id': device_id,
                'analytics': analytics_data[device_id],
                'period_hours': hours,
                'cached': use_cached
            }
        else:
            # Analytics para todos los dispositivos
            response_data = {
                'devices': analytics_data,
                'total_devices': len(analytics_data),
                'period_hours': hours,
                'cached': use_cached
            }
        
        response = {
            'success': True,
            'data': response_data,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Retrieved analytics: {len(analytics_data)} devices, hours={hours}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting DLMS analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve analytics',
            'message': str(e)
        }), 500


@dlms_bp.route('/health', methods=['GET'])
def health_check():
    """
    Verificar estado de salud del sistema DLMS
    
    Returns:
        JSON con estado de salud detallado
    """
    try:
        # Obtener estado de salud del servicio
        health_status = run_async(dlms_service.health_check())
        
        # Agregar información adicional específica para la API
        api_health = {
            'service': 'DLMS API',
            'status': 'healthy' if health_status.get('service_status') == 'healthy' else 'unhealthy',
            'version': '1.0.0',
            'endpoints': {
                'devices': '/api/dlms/devices',
                'telemetry': '/api/dlms/telemetry/<device_id>',
                'analytics': '/api/dlms/analytics',
                'health': '/api/dlms/health'
            },
            'service_details': health_status,
            'timestamp': datetime.now().isoformat()
        }
        
        # Determinar código de estado HTTP
        status_code = 200 if health_status.get('service_status') == 'healthy' else 503
        
        logger.info(f"Health check completed: {health_status.get('service_status')}")
        return jsonify({
            'success': True,
            'data': api_health
        }), status_code
        
    except Exception as e:
        logger.error(f"Error in DLMS health check: {e}")
        return jsonify({
            'success': False,
            'error': 'Health check failed',
            'message': str(e),
            'service': 'DLMS API',
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }), 500


@dlms_bp.route('/devices/<device_id>/events', methods=['POST'])
def trigger_device_event(device_id):
    """
    Disparar evento manual para un dispositivo (para testing/desarrollo)
    
    Args:
        device_id: ID del dispositivo
        
    Body:
        JSON con información del evento
        {
            "event_type": "alert_triggered",
            "severity": "WARNING",
            "message": "Manual event test",
            "data": {}
        }
        
    Returns:
        JSON confirmando el evento disparado
    """
    try:
        # Verificar que el dispositivo existe
        active_devices = run_async(_get_active_devices())
        if device_id not in active_devices:
            return jsonify({
                'success': False,
                'error': f'Device {device_id} not found'
            }), 404
        
        # Validar datos del evento
        event_data = request.get_json()
        if not event_data:
            return jsonify({
                'success': False,
                'error': 'No event data provided'
            }), 400
        
        required_fields = ['event_type', 'severity', 'message']
        for field in required_fields:
            if field not in event_data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Importar tipos de eventos
        from application.services.dlms_service import DLMSEvent, DLMSEventType
        
        # Crear y procesar evento
        event = DLMSEvent(
            event_type=DLMSEventType(event_data['event_type']),
            device_id=device_id,
            timestamp=datetime.now(),
            severity=event_data['severity'],
            message=event_data['message'],
            data=event_data.get('data')
        )
        
        # Procesar evento
        run_async(dlms_service._trigger_event(event))
        
        response = {
            'success': True,
            'data': {
                'device_id': device_id,
                'event_type': event_data['event_type'],
                'timestamp': event.timestamp.isoformat(),
                'message': 'Event triggered successfully'
            }
        }
        
        logger.info(f"Manual event triggered for device {device_id}: {event_data['event_type']}")
        return jsonify(response), 201
        
    except Exception as e:
        logger.error(f"Error triggering event for device {device_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to trigger event',
            'message': str(e)
        }), 500


# Funciones auxiliares

async def _get_active_devices():
    """Obtener lista de dispositivos activos de forma asíncrona"""
    try:
        # Si el servicio ya tiene los datos, usarlos
        if hasattr(dlms_service, '_active_devices') and dlms_service._active_devices:
            return list(dlms_service._active_devices)
        
        # Si no, intentar obtener del sync service
        if dlms_service._sync_service:
            return await dlms_service._sync_service.get_active_devices()
        
        # Fallback a lista simulada
        return ["DLMS-Meter-01", "DLMS-Meter-02", "DLMS-Meter-03"]
        
    except Exception as e:
        logger.warning(f"Could not get active devices: {e}")
        return []


async def _get_last_reading(device_id):
    """Obtener última lectura de un dispositivo"""
    try:
        if device_id in dlms_service._recent_readings and dlms_service._recent_readings[device_id]:
            last_reading = dlms_service._recent_readings[device_id][-1]
            return {
                'timestamp': last_reading.timestamp.isoformat(),
                'measurements': last_reading.measurements,
                'quality_flag': last_reading.quality_flag
            }
        return None
    except Exception as e:
        logger.warning(f"Could not get last reading for {device_id}: {e}")
        return None


def _get_device_type(device_id):
    """Determinar tipo de dispositivo basado en ID"""
    if device_id.endswith('01'):
        return DLMSDeviceType.MONOFASICO.value
    elif device_id.endswith('02'):
        return DLMSDeviceType.TRIFASICO.value
    else:
        return DLMSDeviceType.POLYFASICO.value


def _get_device_readings(device_id, cutoff_time):
    """Obtener lecturas de un dispositivo después de un tiempo específico"""
    try:
        if device_id not in dlms_service._recent_readings:
            return []
        
        readings = dlms_service._recent_readings[device_id]
        return [reading for reading in readings if reading.timestamp >= cutoff_time]
        
    except Exception as e:
        logger.warning(f"Could not get readings for {device_id}: {e}")
        return []


def _process_readings_for_telemetry(readings, measurement_filter=None):
    """Procesar lecturas para formato de telemetría"""
    telemetry_data = []
    
    for reading in readings:
        telemetry_entry = {
            'timestamp': reading.timestamp.isoformat(),
            'device_id': reading.device_id,
            'measurements': {}
        }
        
        # Filtrar mediciones si se especifica
        if measurement_filter:
            for measurement in measurement_filter:
                if measurement in reading.measurements:
                    telemetry_entry['measurements'][measurement] = reading.measurements[measurement]
        else:
            telemetry_entry['measurements'] = reading.measurements.copy()
        
        telemetry_entry['quality_flag'] = reading.quality_flag
        telemetry_data.append(telemetry_entry)
    
    return telemetry_data


def _calculate_telemetry_statistics(telemetry_data):
    """Calcular estadísticas básicas de telemetría"""
    if not telemetry_data:
        return {}
    
    try:
        from statistics import mean, stdev, median
        
        # Recopilar valores por tipo de medición
        measurement_values = {}
        timestamps = []
        
        for entry in telemetry_data:
            timestamps.append(entry['timestamp'])
            for measurement, value in entry['measurements'].items():
                if measurement not in measurement_values:
                    measurement_values[measurement] = []
                measurement_values[measurement].append(value)
        
        # Calcular estadísticas por medición
        statistics = {}
        for measurement, values in measurement_values.items():
            if values:
                statistics[measurement] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': mean(values),
                    'median': median(values),
                    'std_dev': stdev(values) if len(values) > 1 else 0,
                    'count': len(values)
                }
        
        # Estadísticas generales
        statistics['summary'] = {
            'total_readings': len(telemetry_data),
            'measurements_tracked': len(measurement_values),
            'time_span_minutes': len(set(timestamps))  # Simplificado
        }
        
        return statistics
        
    except Exception as e:
        logger.warning(f"Could not calculate telemetry statistics: {e}")
        return {'error': 'Could not calculate statistics'}


# Manejadores de error global para el blueprint
@dlms_bp.errorhandler(404)
def not_found(error):
    """Manejador para endpoints no encontrados"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested DLMS endpoint does not exist'
    }), 404


@dlms_bp.errorhandler(405)
def method_not_allowed(error):
    """Manejador para métodos HTTP no permitidos"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405


@dlms_bp.errorhandler(500)
def internal_error(error):
    """Manejador para errores internos del servidor"""
    logger.error(f"Internal DLMS API error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred in the DLMS API'
    }), 500


if __name__ == "__main__":
    # Ejemplo de uso standalone
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(dlms_bp)
    
    print("DLMS Routes API initialized")
    print("Available endpoints:")
    print("  GET  /api/dlms/devices")
    print("  GET  /api/dlms/telemetry/<device_id>")
    print("  GET  /api/dlms/analytics")
    print("  GET  /api/dlms/health")
    print("  POST /api/dlms/devices/<device_id>/events")