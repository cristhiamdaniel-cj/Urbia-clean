"""
Inicializar gateways del sistema
"""
from config.di_container import DIContainer


def initialize_gateways():
    """Inicializar gateways de Manizales"""
    print("="*60)
    print("  🚪 Inicializando Gateways")
    print("="*60)
    print()
    
    container = DIContainer()
    
    # Crear gateways
    gateways = container.gateway_factory.create_manizales_gateways()
    
    # Registrar
    for gateway in gateways:
        container.gateway_service.register_gateway(gateway)
        print(f"✅ Gateway registrado: {gateway.name} ({gateway.id})")
    
    print()
    print(f"📊 Total gateways: {len(gateways)}")
    print()
    
    # Auto-asignar sensores
    print("🔗 Asignando sensores a gateways...")
    container.gateway_service.auto_assign_sensors()
    
    print()
    print("="*60)
    print("  ✅ Gateways inicializados")
    print("="*60)
    
    # Mostrar estadísticas
    print()
    for gateway in gateways:
        stats = container.gateway_service.get_gateway_stats(gateway.id)
        print(f"📊 {stats['name']}:")
        print(f"   - Sensores: {stats['sensor_count']}")
        print(f"   - Carga: {stats['load_percentage']:.1f}%")
        print()
    
    return gateways


if __name__ == '__main__':
    initialize_gateways()
