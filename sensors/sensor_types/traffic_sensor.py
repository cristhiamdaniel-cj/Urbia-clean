from .base_sensor import BaseSensor
import random
import time

class TrafficSensor(BaseSensor):
    """Sensor de Tráfico Vehicular"""
    
    def read_value(self):
        """Simular conteo de vehículos"""
        hour = time.localtime().tm_hour
        
        # Horas pico
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_traffic = 60
            variance = 30
        elif 22 <= hour or hour <= 6:
            base_traffic = 5
            variance = 5
        else:
            base_traffic = 30
            variance = 15
        
        traffic = base_traffic + random.uniform(-variance, variance)
        return max(0, round(traffic))
