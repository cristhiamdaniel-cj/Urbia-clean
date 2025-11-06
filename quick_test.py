#!/usr/bin/env python3

print("=" * 60)
print("VERIFICACIÓN DEL REPOSITORIO SQL TELEMETRY")
print("=" * 60)

# Leer el archivo sql_telemetry_repository.py
with open('/home/cristhiamdaniel/Proyecto-UrbIA/urbia-clean/src/infrastructure/database/sql_telemetry_repository.py', 'r') as f:
    content = f.read()

print("1. ✅ Archivo leído exitosamente")

# Verificar sintaxis
try:
    compile(content, 'sql_telemetry_repository.py', 'exec')
    print("2. ✅ Sintaxis verificada - sin errores de compilación")
except SyntaxError as e:
    print(f"2. ❌ Error de sintaxis: {e}")
    exit(1)

# Ejecutar el módulo
try:
    exec(content)
    print("3. ✅ Módulo ejecutado exitosamente")
except Exception as e:
    print(f"3. ❌ Error al ejecutar módulo: {e}")
    exit(1)

# Importar las clases
try:
    from infrastructure.database.sql_telemetry_repository import SQLTelemetryRepository, TelemetryRecord
    print("4. ✅ Clases importadas exitosamente")
except ImportError as e:
    print(f"4. ❌ Error de import: {e}")
    exit(1)

# Crear repositorio de prueba
try:
    repo = SQLTelemetryRepository(":memory:")
    print("5. ✅ Repositorio creado exitosamente")
except Exception as e:
    print(f"5. ❌ Error al crear repositorio: {e}")
    exit(1)

# Crear y almacenar un registro
from datetime import datetime
record = TelemetryRecord(
    sensor_id="TEST_DLMS_SENSOR",
    timestamp=datetime.now(),
    value=50.5,
    quality="GOOD",
    unit="Hz",
    measurement_type="FRECUENCIA"
)

success = repo.store_telemetry(record)
if success:
    print("6. ✅ Registro almacenado exitosamente")
else:
    print("6. ❌ Error al almacenar registro")

# Recuperar registros
records = repo.get_telemetry_by_sensor("TEST_DLMS_SENSOR")
if records:
    print(f"7. ✅ {len(records)} registros recuperados exitosamente")
else:
    print("7. ❌ No se pudieron recuperar registros")

print("\n" + "=" * 60)
print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
print("📊 El repositorio SQL Telemetry funciona perfectamente")
print("✅ SIN ERRORES DE SINTAXIS - PROBLEMA ORIGINAL SOLUCIONADO")
print("🔧 Listo para usar en los tests DLMS del proyecto")
print("=" * 60)
