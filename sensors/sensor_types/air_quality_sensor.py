from .base_sensor import BaseSensor
import random

class AirQualitySensor(BaseSensor):
    """Sensor de Calidad del Aire (AQI)"""
    
    def read_value(self):
        """Simular AQI (0-500)"""
        # Manizales generalmente tiene buen aire
        base_aqi = 35
        
        # Variación aleatoria
        aqi = base_aqi + random.uniform(-10, 30)
        
        # Eventos de contaminación (raro)
        if random.random() < 0.02:
            aqi += random.uniform(50, 100)
        
        return max(0, round(aqi))
