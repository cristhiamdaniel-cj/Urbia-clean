"""
Value Object: Priority
Nivel de prioridad del sensor
"""
from enum import Enum


class Priority(Enum):
    """Niveles de prioridad"""
    
    CRITICAL = "CRITICA"
    HIGH = "ALTA"
    NORMAL = "NORMAL"
    LOW = "BAJA"
    
    @property
    def interval_seconds(self) -> int:
        """Intervalo de envío según prioridad"""
        intervals = {
            Priority.CRITICAL: 5,
            Priority.HIGH: 10,
            Priority.NORMAL: 30,
            Priority.LOW: 120
        }
        return intervals[self]
    
    @property
    def color(self) -> str:
        """Color para UI"""
        colors = {
            Priority.CRITICAL: "#dc3545",
            Priority.HIGH: "#fd7e14",
            Priority.NORMAL: "#28a745",
            Priority.LOW: "#6c757d"
        }
        return colors[self]
    
    def __str__(self) -> str:
        return self.value
