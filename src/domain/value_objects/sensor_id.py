"""
Value Object: SensorId
Inmutable, validado, con igualdad por valor
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SensorId:
    """Identificador único de sensor"""
    
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 3:
            raise ValueError("SensorId debe tener al menos 3 caracteres")
        
        if not self.value.replace('-', '').replace('_', '').isalnum():
            raise ValueError("SensorId solo puede contener letras, números, - y _")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"SensorId('{self.value}')"
