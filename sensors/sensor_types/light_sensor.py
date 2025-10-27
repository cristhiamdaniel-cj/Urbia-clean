from .base_sensor import BaseSensor
import random
import time

class LightSensor(BaseSensor):
    """Sensor de Iluminación"""
    
    def read_value(self):
        """Simular nivel de luz en lux"""
        hour = time.localtime().tm_hour
        
        # Luz natural según hora
        if 6 <= hour <= 18:
            natural_light = 800
        else:
            natural_light = 0
        
        # Luz artificial
        if hour >= 18 or hour <= 6:
            artificial = 200
        else:
            artificial = 50
        
        light = natural_light + artificial + random.uniform(-50, 50)
        return max(0, round(light))
