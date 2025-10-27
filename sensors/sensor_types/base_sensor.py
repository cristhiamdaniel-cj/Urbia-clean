# sensors/types/base_sensor.py
"""
Clase base para todos los sensores IoT
"""

import random
import json
import time
import socket
import threading
from datetime import datetime
from abc import ABC, abstractmethod

class BaseSensor(ABC):
    def __init__(self, config):
        self.id = config['id']
        self.type = config['type']
        self.nombre = config['nombre']
        self.ubicacion = config['ubicacion']
        self.coordenadas = config['coordenadas']
        self.puerto = config['puerto']
        self.prioridad = config['prioridad']
        self.intervalo = config['intervalo']
        self.unidad = config['unidad']
        self.rango_normal = config['rango_normal']
        self.rango_alerta = config['rango_alerta']
        self.icono = config['icono']
        
        self.running = False
        self.thread = None
    
    @abstractmethod
    def read_value(self):
        """Leer valor del sensor (simulado)"""
        pass
    
    def generate_telemetry(self):
        """Generar paquete de telemetría"""
        value = self.read_value()
        
        # Determinar si es alerta
        is_alert = (value < self.rango_alerta[0] or 
                   value > self.rango_alerta[1])
        
        telemetry = {
            'sensor_id': self.id,
            'type': self.type,
            'nombre': self.nombre,
            'timestamp': datetime.now().isoformat(),
            'ubicacion': self.ubicacion,
            'coordenadas': self.coordenadas,
            'value': value,
            'unidad': self.unidad,
            'prioridad': 'CRITICA' if is_alert else self.prioridad,
            'is_alert': is_alert,
            'puerto': self.puerto
        }
        
        return telemetry
    
    def send_telemetry(self, gateway_ip, gateway_port):
        """Enviar telemetría al gateway"""
        try:
            telemetry = self.generate_telemetry()
            
            # Crear socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((gateway_ip, gateway_port))
            
            # Enviar JSON
            message = json.dumps(telemetry).encode()
            sock.sendall(message)
            sock.close()
            
            print(f"{self.icono} [{self.id}] Telemetría enviada: "
                  f"{telemetry['value']} {self.unidad} "
                  f"{'🚨 ALERTA' if telemetry['is_alert'] else ''}")
            
            return telemetry
            
        except Exception as e:
            print(f"❌ Error enviando telemetría desde {self.id}: {e}")
            return None
    
    def run(self, gateway_ip='localhost', gateway_port=5001):
        """Ejecutar sensor continuamente"""
        self.running = True
        print(f"🚀 Iniciando sensor {self.id} - Intervalo: {self.intervalo}s")
        
        while self.running:
            self.send_telemetry(gateway_ip, gateway_port)
            time.sleep(self.intervalo)
    
    def start(self, gateway_ip='localhost', gateway_port=5001):
        """Iniciar sensor en thread separado"""
        self.thread = threading.Thread(
            target=self.run,
            args=(gateway_ip, gateway_port),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        """Detener sensor"""
        self.running = False
        if self.thread:
            self.thread.join()
