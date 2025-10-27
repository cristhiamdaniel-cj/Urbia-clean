from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config.di_container import DIContainer
from src.presentation.api.routes.sensor_routes import sensor_bp
from src.presentation.api.routes.telemetry_routes import telemetry_bp
from src.domain.entities.sensor import Sensor
from src.domain.value_objects.sensor_id import SensorId
from src.domain.value_objects.location import Location
from src.domain.value_objects.priority import Priority
import json

def create_app():
    app = Flask(
        __name__,
        template_folder='/app/dashboard/templates',
        static_folder='/app/dashboard/static'
    )
    
    app.config['JSON_SORT_KEYS'] = False
    CORS(app)
    
    container = DIContainer()
    
    # Analizador SDN
    try:
        from src.infrastructure.analysis.sdn_analyzer import SDNAnalyzer
        container.sdn_analyzer = SDNAnalyzer()
        print("✅ Analizador SDN inicializado")
    except Exception as e:
        print(f"⚠️ Analizador: {e}")
    
    # CARGAR 15 SENSORES CON TODOS LOS CAMPOS
    sensors_loaded = 0
    try:
        print("📋 Cargando sensores avanzados...")
        with open('/app/config/sensors_advanced.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        for sensor_cfg in config['sensors']:
            try:
                sensor = Sensor(
                    id=SensorId(sensor_cfg['id']),
                    name=sensor_cfg['name'],
                    type=sensor_cfg['type'],
                    location=Location(
                        sensor_cfg['location']['lat'],
                        sensor_cfg['location']['lng'],
                        sensor_cfg['location']['city']
                    ),
                    priority=Priority[sensor_cfg['priority']],
                    unit=sensor_cfg['unit'],
                    min_value=sensor_cfg['min_value'],
                    max_value=sensor_cfg['max_value']
                )
                container.sensor_service.register_sensor(sensor)
                sensors_loaded += 1
                print(f"  ✅ {sensor_cfg['id']}")
            except Exception as e:
                print(f"  ❌ {sensor_cfg.get('id', 'Unknown')}: {e}")
        
        print(f"✅ {sensors_loaded} sensores avanzados cargados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    if sensors_loaded == 0:
        print("⚠️ Usando sensores básicos")
        from src.infrastructure.persistence.sensor_loader import SensorLoader
        loader = SensorLoader(
            sensor_factory=container.sensor_factory,
            sensor_service=container.sensor_service
        )
        sensors = loader.load_manizales_sensors()
        print(f"✅ {len(sensors)} sensores básicos")
    
    # Gateways
    try:
        gateways = container.gateway_factory.create_manizales_gateways()
        for gateway in gateways:
            container.gateway_service.register_gateway(gateway)
        container.gateway_service.auto_assign_sensors()
        print(f"✅ {len(gateways)} gateways")
    except Exception as e:
        print(f"⚠️ Gateways: {e}")
    
    # SDN
    try:
        container.sdn_controller.initialize_routes()
        print("✅ SDN inicializado")
    except Exception as e:
        print(f"⚠️ SDN: {e}")
    
    # Generador
    try:
        from src.infrastructure.telemetry.advanced_telemetry import start_advanced_telemetry
        start_advanced_telemetry(container)
        print("✅ Generador iniciado")
    except Exception as e:
        print(f"⚠️ Usando generador básico")
        from threading import Thread
        import time, random
        def basic_gen():
            while True:
                try:
                    for sensor in container.sensor_service.get_active_sensors():
                        value = random.uniform(50, 80)
                        container.telemetry_service.process_telemetry(str(sensor.id), value)
                        decision = container.sdn_controller.route_packet(str(sensor.id))
                        if hasattr(container, 'sdn_analyzer'):
                            container.sdn_analyzer.record_packet(
                                str(sensor.id), 'GW-Norte',
                                getattr(decision, 'latency', 20.0),
                                getattr(decision, 'strategy', 'round_robin')
                            )
                    time.sleep(2)
                except: pass
        Thread(target=basic_gen, daemon=True).start()
    
    app.register_blueprint(sensor_bp)
    app.register_blueprint(telemetry_bp)
    
    @app.route('/')
    def index():
        return render_template('index_iot_dynamic.html')
    
    @app.route('/network-topology')
    def network_topology():
        return render_template('network_topology.html')
    
    @app.route('/network-topology-explained')
    def network_topology_explained():
        return render_template('network_topology_explained.html')
    
    @app.route('/analysis')
    def analysis():
        return render_template('analysis_dashboard.html')
    
    @app.route('/admin')
    def admin_panel():
        return render_template('admin_panel.html')
    
    @app.route('/api-docs')
    def api_docs():
        return """<!DOCTYPE html><html><body><h1>API Docs</h1></body></html>"""
    
    @app.route('/api/sdn-analysis')
    def sdn_analysis():
        try:
            if hasattr(container, 'sdn_analyzer'):
                return jsonify(container.sdn_analyzer.get_analysis()), 200
            return jsonify({'error': 'No disponible'}), 503
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/metrics')
    def get_metrics():
        try:
            sensors = container.sensor_service.get_all_sensors()
            active = container.sensor_service.get_active_sensors()
            critical = sum(1 for s in active if container.telemetry_service.get_latest_telemetry(str(s.id)) and container.telemetry_service.get_latest_telemetry(str(s.id)).is_critical)
            return jsonify({'total_sensors': len(sensors), 'active_sensors': len(active), 'critical_alerts': critical}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/events')
    def get_events():
        try:
            decisions = container.sdn_controller.get_recent_decisions(limit=50)
            events = [{'timestamp': d.get('timestamp', 'N/A'), 'type': f"Enrutamiento {d.get('priority', 'Normal')}", 'sensor': d.get('sensor_id', 'Unknown'), 'action': f"Paquete → {d.get('selected_route', 'Unknown')}", 'latency': f"{d.get('latency', 0)}ms"} for d in decisions]
            return jsonify(events), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
