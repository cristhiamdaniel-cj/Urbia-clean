"""
Value Object: Location
Representa una ubicación geográfica
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Location:
    """Ubicación geográfica"""
    
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    
    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitud debe estar entre -90 y 90")
        
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitud debe estar entre -180 y 180")
    
    def distance_to(self, other: 'Location') -> float:
        """Calcular distancia a otra ubicación (Haversine)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def __str__(self) -> str:
        return f"{self.latitude}, {self.longitude}"
