"""
Iniciar generación de telemetría automática
"""
import time
import random
from threading import Thread
from config.di_container import DIContainer


def generate_telemetry_loop():
    """Loop infinito generando telemetría"""
    container = DIContainer()
    
    print("🔄 Iniciando generación de telemetría...")
    
    while True:
        try:
            # Obtener sensores activos
            sensors = container.sensor_service.get_active_sensors()
            
            for sensor in sensors:
                # Generar valor según tipo
                sensor_type = sensor.type.upper()
                
                if sensor_type == 'RUIDO':
                    value = random.uniform(40, 80)
                elif sensor_type == 'TEMPERATURA':
                    value = random.uniform(15, 28)
                elif sensor_type == 'TRAFICO':
                    value = random.uniform(20, 150)
                elif sensor_type == 'CALIDAD_AIRE':
                    value = random.uniform(30, 120)
                elif sensor_type == 'LUZ':
                    value = random.uniform(100, 5000)
                else:
                    value = random.uniform(0, 100)
                
                # Procesar telemetría
                telemetry = container.telemetry_service.process_telemetry(
                    sensor_id=str(sensor.id),
                    value=value
                )
                
                # Enrutar paquete con SDN
                decision = container.sdn_controller.route_packet(str(sensor.id))
                
                if decision:
                    print(f"📦 {sensor.name}: {value:.1f}{sensor.unit} → {decision.selected_route}")
            
            # Esperar 5 segundos
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)


if __name__ == '__main__':
    generate_telemetry_loop()
