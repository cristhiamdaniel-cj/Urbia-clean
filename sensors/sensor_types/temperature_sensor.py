from .base_sensor import BaseSensor
import random
import math
import time

class TemperatureSensor(BaseSensor):
    """Sensor de Temperatura"""
    
    def __init__(self, config):
        super().__init__(config)
        self.base_temp = 20  # °C base para Manizales
    
    def read_value(self):
        """Simular temperatura realista de Manizales"""
        hour = time.localtime().tm_hour
        
        # Variación diurna sinusoidal
        diurnal = 5 * math.sin((hour - 6) * math.pi / 12)
        
        # Temperatura = base + variación diurna + ruido
        temp = self.base_temp + diurnal + random.uniform(-2, 2)
        
        return round(temp, 1)
