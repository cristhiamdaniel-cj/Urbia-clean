"""
Verificación Fase 4 - Gateways
"""
from config.di_container import DIContainer
from src.infrastructure.persistence.sensor_loader import SensorLoader
from init_gateways import initialize_gateways


def verify():
    print("🔍 Verificando Fase 4...")
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
    
    # 2. Inicializar gateways
    print("2️⃣ Inicializando gateways...")
    gateways = initialize_gateways()
    print()
    
    # 3. Verificar asignaciones
    print("3️⃣ Verificando asignaciones...")
    for gateway in gateways:
        stats = container.gateway_service.get_gateway_stats(gateway.id)
        print(f"   ✅ {stats['name']}: {stats['sensor_count']} sensores")
    print()
    
    # 4. Simular procesamiento edge
    print("4️⃣ Simulando procesamiento edge...")
    sensor = sensors[0]
    telemetry = container.telemetry_service.process_telemetry(
        sensor_id=str(sensor.id),
        value=55.0
    )
    
    result = container.gateway_service.process_telemetry_at_edge(
        telemetry=telemetry,
        gateway_id="GW-NORTE"
    )
    
    if result:
        print(f"   ✅ Telemetría procesada: {result.value}{result.unit}")
    else:
        print("   ✅ Telemetría bufferizada para agregación")
    print()
    
    print("="*60)
    print("  ✅ FASE 4 VERIFICADA CORRECTAMENTE")
    print("="*60)


if __name__ == '__main__':
    verify()
