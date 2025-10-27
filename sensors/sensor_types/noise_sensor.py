# sensors/types/noise_sensor.py
from .base_sensor import BaseSensor
import random
import math
import time

class NoiseSensor(BaseSensor):
    """Sensor de Ruido Ambiental"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_noise = 55  # dB base
        self.hour_factor = 0
    
    def read_value(self):
        """Simular lectura de ruido realista"""
        # Obtener hora actual
        hour = time.localtime().tm_hour
        
        # Modelar ruido según hora del día
        if 6 <= hour <= 8:  # Mañana - tráfico moderado
            self.hour_factor = 10
        elif 12 <= hour <= 14:  # Mediodía - alto tráfico
            self.hour_factor = 15
        elif 18 <= hour <= 20:  # Tarde - pico de tráfico
            self.hour_factor = 20
        elif 22 <= hour or hour <= 6:  # Noche - bajo ruido
            self.hour_factor = -10
        else:
            self.hour_factor = 5
        
        # Ruido base + factor horario + variación aleatoria
        noise = self.base_noise + self.hour_factor + random.uniform(-5, 5)
        
        # Eventos aleatorios (ambulancia, construcción, etc.)
        if random.random() < 0.05:  # 5% probabilidad
            noise += random.uniform(15, 25)  # Evento ruidoso
        
        return round(noise, 1)
