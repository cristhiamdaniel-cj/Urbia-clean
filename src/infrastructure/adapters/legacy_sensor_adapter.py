"""
Adapter para integrar sensores legacy con nueva arquitectura
Bridge Pattern
"""
import time
import requests
from threading import Thread
from src.domain.value_objects.sensor_id import SensorId
from config.di_container import DIContainer


class LegacySensorAdapter:
    """Adaptador para sensores del código legacy"""
    
    def __init__(self, legacy_sensor_instance):
        """
        Args:
            legacy_sensor_instance: Instancia del sensor legacy (BaseSensor)
        """
        self.legacy_sensor = legacy_sensor_instance
        self.container = DIContainer()
        self.running = False
    
    def start(self):
        """Iniciar sensor adaptado"""
        self.running = True
        thread = Thread(target=self._telemetry_loop)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """Detener sensor"""
        self.running = False
    
    def _telemetry_loop(self):
        """Loop de envío de telemetría"""
        while self.running:
            try:
                # Generar valor con el sensor legacy
                value = self.legacy_sensor.generar_valor()
                
                # Procesar con la nueva arquitectura
                self.container.telemetry_service.process_telemetry(
                    sensor_id=self.legacy_sensor.sensor_id,
                    value=value,
                    gateway_id=None  # Se asignará por gateway
                )
                
                # Esperar según intervalo
                time.sleep(self.legacy_sensor.intervalo)
                
            except Exception as e:
                print(f"❌ Error en sensor {self.legacy_sensor.sensor_id}: {e}")
                time.sleep(5)
