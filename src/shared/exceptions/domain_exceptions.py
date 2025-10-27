"""
Excepciones del dominio
Representan errores de reglas de negocio
"""


class DomainException(Exception):
    """Excepción base del dominio"""
    pass


class SensorNotFoundException(DomainException):
    """Sensor no encontrado"""
    def __init__(self, sensor_id: str):
        super().__init__(f"Sensor '{sensor_id}' no encontrado")
        self.sensor_id = sensor_id


class InvalidSensorDataException(DomainException):
    """Datos de sensor inválidos"""
    pass


class TelemetryValidationException(DomainException):
    """Error de validación de telemetría"""
    pass


class GatewayNotAvailableException(DomainException):
    """Gateway no disponible"""
    def __init__(self, gateway_id: str):
        super().__init__(f"Gateway '{gateway_id}' no disponible")
        self.gateway_id = gateway_id
