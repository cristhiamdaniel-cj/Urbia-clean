"""
Rutas API para Datos REALES de ThingsBoard UNAL
===============================================

Endpoints específicos para telemetría real del servidor ThingsBoard
de la Universidad Nacional de Colombia.

Autor: Sistema UrbIA - UNAL
Fecha: 2025-11-06
"""

from flask import Blueprint, jsonify, render_template_string
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Crear Blueprint con prefijo único
thingsboard_bp = Blueprint('thingsboard_real', __name__, url_prefix='/thingsboard-unal')

# Directorio de datos (ajustar según tu estructura)
DATA_DIR = Path("/app/data/telemetry")


@thingsboard_bp.route('/dashboard')
def dashboard_real():
    """Dashboard con mapa de UNAL Bogotá y datos reales"""
    return render_template_string(DASHBOARD_HTML_TEMPLATE)


@thingsboard_bp.route('/api/all')
def api_get_all_data():
    """Retorna TODOS los datos DLMS reales de ThingsBoard"""
    try:
        data_file = DATA_DIR / "dlms_real_data.json"
        
        if not data_file.exists():
            return jsonify({
                'success': False,
                'error': 'No hay datos disponibles',
                'message': 'Ejecuta: python sync_ssh_thingsboard.py --intervalo 10'
            }), 404
        
        with open(data_file, 'r') as f:
            datos = json.load(f)
        
        return jsonify({
            'success': True,
            'total_records': len(datos),
            'source': 'ThingsBoard UNAL - Datos Reales',
            'timestamp': datetime.now().isoformat(),
            'data': datos
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@thingsboard_bp.route('/api/summary')
def api_get_summary():
    """Resumen agrupado por dispositivo"""
    try:
        data_file = DATA_DIR / "dlms_real_data.json"
        
        if not data_file.exists():
            return jsonify({'success': False, 'error': 'No hay datos'}), 404
        
        with open(data_file, 'r') as f:
            datos = json.load(f)
        
        # Agrupar por dispositivo
        por_dispositivo = {}
        for dato in datos:
            # Extraer nombre del dispositivo de metadata o sensor_id
            device = dato.get('metadata', {}).get('device_name') or dato.get('sensor_id', '').split('_')[0]
            
            if device not in por_dispositivo:
                por_dispositivo[device] = {
                    'device_name': device,
                    'total_metrics': 0,
                    'timestamp': dato.get('timestamp', ''),
                    'location': dato.get('location', {}),
                    'metrics': []
                }
            
            por_dispositivo[device]['total_metrics'] += 1
            por_dispositivo[device]['metrics'].append({
                'code': dato.get('metadata', {}).get('dlms_code', ''),
                'name': dato.get('sensor_type', ''),
                'description': dato.get('metadata', {}).get('description', dato.get('sensor_type', '')),
                'value': dato.get('value', 0),
                'unit': dato.get('unit', '')
            })
        
        return jsonify({
            'success': True,
            'total_devices': len(por_dispositivo),
            'total_metrics': len(datos),
            'timestamp': datetime.now().isoformat(),
            'devices': por_dispositivo
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@thingsboard_bp.route('/api/devices')
def api_get_devices():
    """Lista de dispositivos DLMS reales"""
    return jsonify({
        'success': True,
        'source': 'ThingsBoard UNAL',
        'devices': [
            {
                'id': 'DLMS-Meter-01',
                'name': 'DLMS-Meter-01',
                'type': 'DLMS Energy Meter',
                'label': 'Medidor DLMS monofásico',
                'location': {'name': 'UNAL Bogotá', 'lat': 4.6381, 'lng': -74.0843},
                'status': 'active',
                'thingsboard_id': '49111400-b99f-11f0-b2a7-017993aa882e'
            },
            {
                'id': 'DLMS-Meter-02',
                'name': 'DLMS-Meter-02',
                'type': 'DLMS Energy Meter',
                'label': 'Medidor DLMS Bifásico',
                'location': {'name': 'UNAL Bogotá', 'lat': 4.6381, 'lng': -74.0843},
                'status': 'active',
                'thingsboard_id': '794f25e0-b9fd-11f0-bc69-cb99eafde0bd'
            }
        ]
    })


# Template HTML para el dashboard
DASHBOARD_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UNAL ThingsBoard - Monitoreo en Tiempo Real</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Header espectacular */
        .header {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
            backdrop-filter: blur(10px);
            color: white;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 0 5px 20px rgba(0,0,0,0.3);
            animation: fadeInDown 0.8s ease-out;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.95;
            margin-top: 10px;
            animation: fadeInUp 1s ease-out;
        }
        
        .status-badges {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
            animation: fadeIn 1.2s ease-out;
        }
        
        .badge {
            background: rgba(255,255,255,0.25);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .badge:hover {
            background: rgba(255,255,255,0.35);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .badge.success { border-color: #4CAF50; }
        .badge.pulse {
            animation: badgePulse 2s infinite;
        }
        
        @keyframes badgePulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
            50% { box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }
        }
        
        /* Container principal */
        .container {
            max-width: 1600px;
            margin: -50px auto 40px;
            padding: 0 20px;
            position: relative;
            z-index: 10;
        }
        
        /* Grid de estadísticas */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 5px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .stat-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
            margin-bottom: 15px;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .stat-value {
            font-size: 42px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 10px 0;
            animation: countUp 1s ease-out;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        /* Mapa mejorado */
        .map-container {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 15px 50px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        #map {
            height: 600px;
            position: relative;
        }
        
        /* Dispositivos */
        .devices-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }
        
        .device-card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 50px rgba(0,0,0,0.15);
            transition: all 0.3s;
            animation: slideInUp 0.6s ease-out;
        }
        
        .device-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        }
        
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 3px solid #f0f0f0;
        }
        
        .device-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .device-icon {
            width: 50px;
            height: 50px;
            border-radius: 12px;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        
        .device-name {
            font-size: 22px;
            font-weight: 700;
            color: #333;
        }
        
        .device-status {
            background: #4CAF50;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            animation: pulse 2s infinite;
        }
        
        .device-timestamp {
            color: #999;
            font-size: 13px;
            margin-bottom: 20px;
        }
        
        .metrics-grid {
            display: grid;
            gap: 12px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            transition: all 0.3s;
            border-left: 4px solid #667eea;
        }
        
        .metric:hover {
            background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
            transform: translateX(5px);
            border-left-width: 6px;
        }
        
        .metric-name {
            color: #555;
            font-size: 15px;
            font-weight: 500;
        }
        
        .metric-value {
            font-weight: 700;
            font-size: 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Animaciones */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes countUp {
            from { transform: scale(0.5); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .stats-grid { grid-template-columns: 1fr; }
            .devices-section { grid-template-columns: 1fr; }
        }
        
        /* Loader */
        .loader {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1><i class="bi bi-lightning-charge-fill"></i> Universidad Nacional - ThingsBoard</h1>
            <p>Campus Bogotá - Monitoreo DLMS en Tiempo Real</p>
            <div class="status-badges">
                <span class="badge success pulse">
                    <i class="bi bi-check-circle-fill"></i> Sistema Activo
                </span>
                <span class="badge">
                    <i class="bi bi-broadcast"></i> ThingsBoard UNAL
                </span>
                <span class="badge">
                    <i class="bi bi-clock-fill"></i> Última sync: <span id="sync-time">-</span>
                </span>
                <span class="badge">
                    <i class="bi bi-arrow-repeat"></i> Auto-actualización: 5s
                </span>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="bi bi-cpu-fill"></i>
                </div>
                <div class="stat-value" id="total-devices">0</div>
                <div class="stat-label">Medidores Activos</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="bi bi-bar-chart-fill"></i>
                </div>
                <div class="stat-value" id="total-metrics">0</div>
                <div class="stat-label">Métricas Totales</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="bi bi-lightning-fill"></i>
                </div>
                <div class="stat-value" id="energy-total">0</div>
                <div class="stat-label">Energía Total (kWh)</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="bi bi-activity"></i>
                </div>
                <div class="stat-value status-indicator" id="status">🟢</div>
                <div class="stat-label">Estado del Sistema</div>
            </div>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
        </div>
        
        <div id="devices-section" class="devices-section">
            <div class="loader">
                <div class="spinner"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Inicializar mapa
        const map = L.map('map').setView([4.6381, -74.0843], 16);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);
        
        const markers = {};
        
        // Icono personalizado animado
        const createCustomIcon = (color) => {
            return L.divIcon({
                className: 'custom-marker',
                html: `
                    <div style="
                        background: ${color};
                        color: white;
                        padding: 15px;
                        border-radius: 50%;
                        width: 50px;
                        height: 50px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 24px;
                        box-shadow: 0 10px 30px rgba(76, 175, 80, 0.6);
                        animation: bounce 2s infinite;
                        position: relative;
                    ">
                        <i class="bi bi-lightning-charge-fill"></i>
                        <div style="
                            position: absolute;
                            top: -5px;
                            right: -5px;
                            width: 15px;
                            height: 15px;
                            background: #4CAF50;
                            border-radius: 50%;
                            border: 3px solid white;
                            animation: pulse 2s infinite;
                        "></div>
                    </div>
                    <style>
                        @keyframes bounce {
                            0%, 100% { transform: translateY(0); }
                            50% { transform: translateY(-10px); }
                        }
                        @keyframes pulse {
                            0%, 100% { transform: scale(1); opacity: 1; }
                            50% { transform: scale(1.3); opacity: 0.7; }
                        }
                    </style>
                `,
                iconSize: [50, 50]
            });
        };
        
        function loadData() {
            fetch('/thingsboard-unal/api/summary')
                .then(r => r.json())
                .then(data => {
                    if (!data.success) {
                        console.error('Error:', data);
                        return;
                    }
                    
                    // Actualizar estadísticas con animación
                    animateValue('total-devices', data.total_devices || 0);
                    animateValue('total-metrics', data.total_metrics || 0);
                    document.getElementById('sync-time').textContent = new Date().toLocaleTimeString();
                    document.getElementById('status').textContent = '🟢';
                    
                    // Calcular energía total
                    let energyTotal = 0;
                    for (const [name, dev] of Object.entries(data.devices || {})) {
                        const energyMetric = dev.metrics.find(m => m.code === '110');
                        if (energyMetric) energyTotal += energyMetric.value;
                    }
                    animateValue('energy-total', energyTotal.toFixed(2));
                    
                    // Renderizar dispositivos
                    renderDevices(data.devices);
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('status').textContent = '🔴';
                });
        }
        
        function animateValue(id, value) {
            const element = document.getElementById(id);
            const start = parseFloat(element.textContent) || 0;
            const end = parseFloat(value);
            const duration = 1000;
            const startTime = Date.now();
            
            const update = () => {
                const now = Date.now();
                const progress = Math.min((now - startTime) / duration, 1);
                const current = start + (end - start) * progress;
                element.textContent = Math.floor(current);
                
                if (progress < 1) {
                    requestAnimationFrame(update);
                }
            };
            
            update();
        }
        
        function renderDevices(devices) {
            const container = document.getElementById('devices-section');
            let html = '';
            
            for (const [name, dev] of Object.entries(devices || {})) {
                // Agregar marcador al mapa
                const lat = dev.location.lat + (Math.random() - 0.5) * 0.0008;
                const lng = dev.location.lng + (Math.random() - 0.5) * 0.0008;
                
                if (!markers[name]) {
                    markers[name] = L.marker([lat, lng], {
                        icon: createCustomIcon('#4CAF50')
                    }).addTo(map);
                    
                    markers[name].bindPopup(`
                        <div style="text-align: center; padding: 10px;">
                            <h4 style="margin: 0 0 10px 0; color: #667eea;">
                                <i class="bi bi-lightning-charge-fill"></i> ${name}
                            </h4>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <strong>Métricas:</strong> ${dev.total_metrics}
                            </p>
                            <p style="margin: 5px 0; font-size: 13px; color: #666;">
                                ${dev.location.description}
                            </p>
                        </div>
                    `);
                }
                
                // Card del dispositivo
                html += `
                    <div class="device-card">
                        <div class="device-header">
                            <div class="device-title">
                                <div class="device-icon">
                                    <i class="bi bi-lightning-charge-fill"></i>
                                </div>
                                <div>
                                    <div class="device-name">${name}</div>
                                </div>
                            </div>
                            <div class="device-status">
                                <span class="pulse-dot"></span>
                                Activo
                            </div>
                        </div>
                        <div class="device-timestamp">
                            <i class="bi bi-clock"></i> ${new Date(dev.timestamp).toLocaleString()}
                        </div>
                        <div class="metrics-grid">
                `;
                
                dev.metrics.forEach(m => {
                    html += `
                        <div class="metric">
                            <span class="metric-name">
                                <i class="bi bi-graph-up"></i> ${m.description}
                            </span>
                            <span class="metric-value">${m.value} ${m.unit}</span>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        // Cargar datos al inicio
        loadData();
        
        // Auto-actualizar cada 5 segundos
        setInterval(loadData, 5000);
    </script>
</body>
</html>
'''


# Función para registrar las rutas
def register_thingsboard_routes(app):
    """
    Registra las rutas de ThingsBoard en la aplicación Flask
    
    Uso:
        from presentation.api.routes.thingsboard_real_routes import register_thingsboard_routes
        register_thingsboard_routes(app)
    """
    app.register_blueprint(thingsboard_bp)
    logger.info("✅ Rutas ThingsBoard UNAL registradas: /thingsboard-unal/*")


if __name__ == "__main__":
    print("ThingsBoard UNAL Routes")
    print("Endpoints:")
    print("  Dashboard: /thingsboard-unal/dashboard")
    print("  API All:   /thingsboard-unal/api/all")
    print("  API Sum:   /thingsboard-unal/api/summary")
    print("  Devices:   /thingsboard-unal/api/devices")