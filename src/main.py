#!/usr/bin/env python3
"""
Aplicación Principal Urbia - Sistema IoT Urbano UNAL
Integración con ThingsBoard en tiempo real
"""

from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# Ruta de datos
DATA_DIR = Path(__file__).parent.parent / "data" / "telemetry"


@app.route('/')
def index():
    """Página principal con dashboard"""
    return '''
    <!DOCTYPE html>
    <html><head><title>Urbia IoT - UNAL</title><meta charset="utf-8">
    <style>
        body{font-family:Arial;margin:0;padding:20px;background:#f5f5f5}
        .container{max-width:1200px;margin:0 auto;background:white;padding:30px;border-radius:10px}
        h1{color:#2196F3;text-align:center}
        .badge{background:#2196F3;color:white;padding:5px 15px;border-radius:20px;margin:5px}
        .stats{display:flex;justify-content:space-around;margin:30px 0}
        .stat{text-align:center}
        .stat-value{font-size:36px;font-weight:bold;color:#2196F3}
        .device{border:2px solid #2196F3;padding:20px;margin:15px 0;border-radius:8px}
        .metric{display:flex;justify-content:space-between;padding:10px;background:#f9f9f9;margin:5px 0}
        .value{font-weight:bold;color:#4CAF50}
    </style>
    </head><body>
    <div class="container">
        <h1>🏙️ Urbia - Sistema IoT Urbano</h1>
        <p style="text-align:center">Universidad Nacional de Colombia - ThingsBoard Integration</p>
        <div style="text-align:center">
            <span class="badge">✅ Sistema Activo</span>
            <span class="badge">📡 Datos Reales</span>
            <span class="badge">🔌 ThingsBoard UNAL</span>
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-value" id="devices">-</div><div>Dispositivos</div></div>
            <div class="stat"><div class="stat-value" id="metrics">-</div><div>Métricas</div></div>
            <div class="stat"><div class="stat-value" id="update">-</div><div>Última Act.</div></div>
        </div>
        <h2>📊 Datos en Tiempo Real</h2>
        <div id="data"></div>
        <h3>APIs Disponibles:</h3>
        <ul>
            <li><a href="/api/telemetry/dlms-real">/api/telemetry/dlms-real</a> - Todos los datos</li>
            <li><a href="/api/telemetry/dlms-real/summary">/api/telemetry/dlms-real/summary</a> - Resumen</li>
            <li><a href="/api/telemetry/dlms-real/devices">/api/telemetry/dlms-real/devices</a> - Dispositivos</li>
        </ul>
    </div>
    <script>
        function loadData(){
            fetch('/api/telemetry/dlms-real/summary')
                .then(r=>r.json())
                .then(data=>{
                    document.getElementById('devices').textContent=data.total_devices||0;
                    document.getElementById('metrics').textContent=data.total_metrics||0;
                    document.getElementById('update').textContent=new Date().toLocaleTimeString();
                    let html='';
                    for(const[name,dev]of Object.entries(data.devices||{})){
                        html+=`<div class="device"><h3>${name}</h3>`;
                        html+=`<p>Métricas: ${dev.total_metrics} | Timestamp: ${dev.timestamp}</p>`;
                        dev.metrics.forEach(m=>{
                            html+=`<div class="metric"><span>${m.description}</span><span class="value">${m.value} ${m.unit}</span></div>`;
                        });
                        html+='</div>';
                    }
                    document.getElementById('data').innerHTML=html;
                });
        }
        loadData();
        setInterval(loadData,5000);
    </script>
    </body></html>
    '''


@app.route('/api/telemetry/dlms-real', methods=['GET'])
def get_dlms_real_data():
    """Retorna todos los datos DLMS reales"""
    try:
        data_file = DATA_DIR / "dlms_real_data.json"
        
        if not data_file.exists():
            return jsonify({
                'error': 'No hay datos disponibles',
                'message': 'Ejecuta sync_ssh_thingsboard.py'
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
        return jsonify({'error': str(e)}), 500


@app.route('/api/telemetry/dlms-real/summary', methods=['GET'])
def get_dlms_summary():
    """Resumen agrupado por dispositivo"""
    try:
        data_file = DATA_DIR / "dlms_real_data.json"
        
        if not data_file.exists():
            return jsonify({'error': 'No hay datos'}), 404
        
        with open(data_file, 'r') as f:
            datos = json.load(f)
        
        # Agrupar por dispositivo
        por_dispositivo = {}
        for dato in datos:
            device = dato['metadata']['device_name']
            if device not in por_dispositivo:
                por_dispositivo[device] = {
                    'device_name': device,
                    'total_metrics': 0,
                    'timestamp': dato['timestamp'],
                    'location': dato['location'],
                    'metrics': []
                }
            
            por_dispositivo[device]['total_metrics'] += 1
            por_dispositivo[device]['metrics'].append({
                'code': dato['metadata']['dlms_code'],
                'name': dato['sensor_type'],
                'description': dato['metadata']['description'],
                'value': dato['value'],
                'unit': dato['unit']
            })
        
        return jsonify({
            'success': True,
            'source': 'ThingsBoard UNAL',
            'total_devices': len(por_dispositivo),
            'total_metrics': len(datos),
            'timestamp': datetime.now().isoformat(),
            'devices': por_dispositivo
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/telemetry/dlms-real/devices', methods=['GET'])
def get_dlms_devices():
    """Lista dispositivos DLMS"""
    return jsonify({
        'success': True,
        'devices': [
            {
                'id': 'DLMS-Meter-01',
                'name': 'DLMS-Meter-01',
                'type': 'DLMS Energy Meter',
                'label': 'Medidor DLMS monofásico',
                'location': {
                    'name': 'Universidad Nacional de Colombia',
                    'lat': 4.6381,
                    'lng': -74.0843
                },
                'status': 'active',
                'device_id_thingsboard': '49111400-b99f-11f0-b2a7-017993aa882e'
            },
            {
                'id': 'DLMS-Meter-02',
                'name': 'DLMS-Meter-02',
                'type': 'DLMS Energy Meter',
                'label': 'Medidor DLMS Bifásico',
                'location': {
                    'name': 'Universidad Nacional de Colombia',
                    'lat': 4.6381,
                    'lng': -74.0843
                },
                'status': 'active',
                'device_id_thingsboard': '794f25e0-b9fd-11f0-bc69-cb99eafde0bd'
            }
        ]
    })


@app.route('/api/telemetry/dlms-real/device/<device_name>', methods=['GET'])
def get_device_data(device_name):
    """Datos de un dispositivo específico"""
    try:
        data_file = DATA_DIR / "dlms_real_data.json"
        
        if not data_file.exists():
            return jsonify({'error': 'No hay datos'}), 404
        
        with open(data_file, 'r') as f:
            datos = json.load(f)
        
        datos_dispositivo = [d for d in datos if d['metadata']['device_name'] == device_name]
        
        if not datos_dispositivo:
            return jsonify({'error': f'Dispositivo {device_name} no encontrado'}), 404
        
        return jsonify({
            'success': True,
            'device': device_name,
            'total_metrics': len(datos_dispositivo),
            'data': datos_dispositivo
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check del sistema"""
    data_file = DATA_DIR / "dlms_real_data.json"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_available': data_file.exists(),
        'data_dir': str(DATA_DIR)
    })


if __name__ == '__main__':
    logger.info("="*70)
    logger.info("🚀 Iniciando Urbia - Sistema IoT Urbano UNAL")
    logger.info("="*70)
    logger.info("📡 Servidor: http://localhost:5001")
    logger.info("📊 Dashboard: http://localhost:5001")
    logger.info("🔌 API DLMS: http://localhost:5001/api/telemetry/dlms-real")
    logger.info("="*70)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
