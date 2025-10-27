"""
Script de verificación Fase 3
"""
from config.di_container import DIContainer
from src.infrastructure.persistence.sensor_loader import SensorLoader


def verify():
    print("🔍 Verificando Fase 3...")
    print()
    
    # 1. Verificar DI Container
    print("1️⃣ Verificando DI Container...")
    container = DIContainer()
    print(f"   ✅ Event Bus: {container.event_bus}")
    print(f"   ✅ Sensor Service: {container.sensor_service}")
    print(f"   ✅ Telemetry Service: {container.telemetry_service}")
    print()
    
    # 2. Cargar sensores
    print("2️⃣ Cargando sensores...")
    loader = SensorLoader(
        sensor_factory=container.sensor_factory,
        sensor_service=container.sensor_service
    )
    sensors = loader.load_manizales_sensors()
    print(f"   ✅ {len(sensors)} sensores cargados")
    print()
    
    # 3. Verificar servicios
    print("3️⃣ Verificando servicios...")
    all_sensors = container.sensor_service.get_all_sensors()
    active_sensors = container.sensor_service.get_active_sensors()
    print(f"   ✅ Total sensores: {len(all_sensors)}")
    print(f"   ✅ Sensores activos: {len(active_sensors)}")
    print()
    
    # 4. Simular telemetría
    print("4️⃣ Simulando telemetría...")
    sensor = sensors[0]
    telemetry = container.telemetry_service.process_telemetry(
        sensor_id=str(sensor.id),
        value=50.0
    )
    print(f"   ✅ Telemetría procesada: {telemetry.value}{telemetry.unit}")
    print()
    
    print("="*60)
    print("  ✅ FASE 3 VERIFICADA CORRECTAMENTE")
    print("="*60)


if __name__ == '__main__':
    verify()
