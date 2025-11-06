#!/bin/bash
echo "🔧 Corrigiendo error SQLite..."

# Localizar el archivo problemático
SQL_FILE="src/infrastructure/database/sql_telemetry_repository.py"

if [ -f "$SQL_FILE" ]; then
    echo "✅ Archivo encontrado: $SQL_FILE"
    
    # Crear backup
    cp "$SQL_FILE" "$SQL_FILE.backup.$(date +%Y%m%d-%H%M%S)"
    echo "✅ Backup creado"
    
    # Hacer corrección directa usando sed
    sed -i 's/INDEX_sensor_time (sensor_id, timestamp),//g' "$SQL_FILE"
    sed -i 's/INDEX_timestamp (timestamp),//g' "$SQL_FILE"  
    sed -i 's/INDEX_data_type (data_type),//g' "$SQL_FILE"
    sed -i 's/INDEX_priority (priority),//g' "$SQL_FILE"
    sed -i 's/INDEX_location (location_lat, location_lng)//g' "$SQL_FILE"
    
    echo "✅ Índices problemáticos eliminados"
else
    echo "❌ Archivo no encontrado: $SQL_FILE"
fi

echo "🎉 Corrección SQLite completada"
