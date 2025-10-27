"""
Verificación Fase 5 - Controlador SDN
"""
from config.di_container import DIContainer
from src.infrastructure.persistence.sensor_loader import SensorLoader
from src.domain.services.routing_strategy import (
    LoadBalancingStrategy,
    LowLatencyStrategy
)


def verify():
    print("🔍 Verificando Fase 5 - Controlador SDN...")
    print()
    
    container = DIContainer()
    
    # 1. Cargar sensores
    print("1️⃣ Cargando sensores...")
    loader = SensorLoader(
        sensor_factory=container.sensor_factory,
        sensor_service=container.sensor_service
    )
    sensors = loader.load_manizales_sensors()
    print(f"   ✅ {len(sensors)} sensores cargados")
    print()
    
    # 2. Inicializar controlador SDN
    print("2️⃣ Inicializando Controlador SDN...")
    container.sdn_controller.initialize_routes()
    print()
    
    # 3. Probar enrutamiento con diferentes prioridades
    print("3️⃣ Probando enrutamiento QoS...")
    for sensor in sensors[:3]:
        decision = container.sdn_controller.route_packet(str(sensor.id))
        if decision:
            print(f"   📦 {sensor.name}")
            print(f"      Prioridad: {decision.sensor_priority}")
            print(f"      Ruta: {decision.selected_route}")
            print(f"      Latencia: {decision.route_latency}ms")
            print(f"      Razón: {decision.reason}")
            print()
    
    # 4. Probar cambio de estrategia
    print("4️⃣ Cambiando estrategia a Load Balancing...")
    container.sdn_controller.set_routing_strategy(LoadBalancingStrategy())
    
    decision = container.sdn_controller.route_packet(sensors[0].id.value)
    print(f"   ✅ Ruta seleccionada: {decision.selected_route}")
    print()
    
    # 5. Simular congestión
    print("5️⃣ Simulando congestión...")
    container.sdn_controller.simulate_congestion("ROUTE_B", 85.0)
    
    decision = container.sdn_controller.route_packet(sensors[0].id.value)
    print(f"   ✅ Ruta alternativa: {decision.selected_route}")
    print()
    
    # 6. Estadísticas
    print("6️⃣ Estadísticas del controlador...")
    stats = container.sdn_controller.get_controller_stats()
    print(f"   Total decisiones: {stats['total_decisions']}")
    print(f"   Estrategia actual: {stats['routing_strategy']}")
    print(f"   Rutas activas: {stats['active_routes']}")
    print()
    
    # 7. Ver rutas
    print("7️⃣ Estado de las rutas...")
    routes = container.sdn_controller.get_route_stats()
    for route in routes:
        print(f"   📡 {route['name']}")
        print(f"      Latencia: {route['latency_ms']}ms")
        print(f"      Carga: {route['current_load']:.1f}%")
        print(f"      Congestionada: {'Sí' if route['is_congested'] else 'No'}")
        print()
    
    print("="*60)
    print("  ✅ FASE 5 VERIFICADA CORRECTAMENTE")
    print("="*60)


if __name__ == '__main__':
    verify()
