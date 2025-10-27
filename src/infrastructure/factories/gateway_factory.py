"""
Factory para crear gateways
"""
from src.domain.entities.gateway import Gateway
from src.domain.value_objects.location import Location


class GatewayFactory:
    """Factory para crear gateways"""
    
    @staticmethod
    def create_gateway(
        gateway_id: str,
        name: str,
        latitude: float,
        longitude: float,
        port: int = 5001
    ) -> Gateway:
        """Crear gateway con ubicación"""
        location = Location(
            latitude=latitude,
            longitude=longitude,
            city="Manizales"
        )
        
        return Gateway(
            id=gateway_id,
            name=name,
            location=location,
            port=port
        )
    
    @staticmethod
    def create_manizales_gateways() -> list:
        """Crear gateways para Manizales"""
        return [
            GatewayFactory.create_gateway(
                gateway_id="GW-NORTE",
                name="Gateway Norte",
                latitude=5.0702,
                longitude=-75.5138,
                port=5001
            ),
            GatewayFactory.create_gateway(
                gateway_id="GW-SUR",
                name="Gateway Sur",
                latitude=5.0407,
                longitude=-75.4813,
                port=5002
            )
        ]
