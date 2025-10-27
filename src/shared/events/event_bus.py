"""
Event Bus - Observer Pattern
Desacopla productores y consumidores de eventos
"""
from typing import Callable, Dict, List
from src.shared.events.events import DomainEvent


class EventBus:
    """Bus de eventos singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: Dict[str, List[Callable]] = {}
        return cls._instance
    
    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """Suscribirse a un tipo de evento"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent) -> None:
        """Publicar evento"""
        event_type = type(event).__name__
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error en handler de {event_type}: {e}")
    
    def clear(self) -> None:
        """Limpiar suscripciones (útil para testing)"""
        self._handlers.clear()
