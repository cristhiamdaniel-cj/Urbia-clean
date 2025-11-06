"""
SQL Telemetry Repository - Versión Completa
Implementación completa con todos los métodos requeridos por los tests DLMS
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class TelemetryRecord:
    """Registro de telemetría para SQLite con estructura completa"""
    id: str
    sensor_id: str
    timestamp: str
    data_type: str
    value: float
    unit: str
    location_lat: float
    location_lng: float
    priority: str
    gateway_id: Optional[str] = None
    metadata_json: Optional[str] = None
    processed: bool = False
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()


class SQLTelemetryRepository:
    """
    Repositorio SQL completo para telemetría con todos los métodos requeridos
    """
    
    def __init__(self, db_path: str = "telemetry.db", enable_wal_mode: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Crear conexión persistente
        self.conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=30.0
        )
        
        if enable_wal_mode:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=10000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
        
        # Inicializar esquema
        self._init_database()
    
    def _init_database(self):
        """Inicializa el esquema de base de datos"""
        try:
            # Tabla principal de registros
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id TEXT PRIMARY KEY,
                    sensor_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    data_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    location_lat REAL NOT NULL,
                    location_lng REAL NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'normal',
                    gateway_id TEXT,
                    metadata_json TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para rendimiento
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp 
                ON telemetry_records (sensor_id, timestamp)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_data_type 
                ON telemetry_records (data_type)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority 
                ON telemetry_records (priority)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_location 
                ON telemetry_records (location_lat, location_lng)
            """)
            
            self.conn.commit()
            self.logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def save(self, telemetry: Union[Dict, Any]) -> bool:
        """
        Guarda un registro de telemetría
        
        Args:
            telemetry: Objeto de telemetría (dict o objeto con atributos)
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            record = self._convert_to_record(telemetry)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO telemetry_records 
                    (id, sensor_id, timestamp, data_type, value, unit, 
                     location_lat, location_lng, priority, gateway_id, 
                     metadata_json, processed, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id, record.sensor_id, record.timestamp,
                    record.data_type, record.value, record.unit,
                    record.location_lat, record.location_lng, record.priority,
                    record.gateway_id, record.metadata_json, record.processed,
                    record.created_at
                ))
                
            self.logger.debug(f"Registro guardado: {record.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store telemetry record: {e}")
            return False
    
    def save_many(self, telemetry_list: List[Union[Dict, Any]]) -> int:
        """
        Guarda múltiples registros de telemetría de forma eficiente
        """
        saved_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for telemetry in telemetry_list:
                    try:
                        record = self._convert_to_record(telemetry)
                        cursor.execute("""
                            INSERT OR REPLACE INTO telemetry_records 
                            (id, sensor_id, timestamp, data_type, value, unit, 
                             location_lat, location_lng, priority, gateway_id, 
                             metadata_json, processed, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.id, record.sensor_id, record.timestamp,
                            record.data_type, record.value, record.unit,
                            record.location_lat, record.location_lng, record.priority,
                            record.gateway_id, record.metadata_json, record.processed,
                            record.created_at
                        ))
                        saved_count += 1
                    except Exception as e:
                        self.logger.error(f"Error guardando registro individual: {e}")
                        continue
                        
            self.logger.info(f"Guardados {saved_count}/{len(telemetry_list)} registros")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Failed to save many records: {e}")
            return 0
    
    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Obtiene un registro por su ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM telemetry_records WHERE id = ?
                """, (record_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo registro por ID: {e}")
            return None
    
    def get_by_sensor(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene registros por sensor
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM telemetry_records 
                    WHERE sensor_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (sensor_id, limit))
                
                return [self._row_to_dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo datos por sensor: {e}")
            return []
    
    def get_historical_data(self, sensor_id: Optional[str] = None, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          limit: int = 1000) -> List[Dict]:
        """
        Obtiene datos históricos con filtros
        """
        try:
            query = "SELECT * FROM telemetry_records WHERE 1=1"
            params = []
            
            if sensor_id:
                query += " AND sensor_id = ?"
                params.append(sensor_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos: {e}")
            return []
    
    def get_analytics(self, group_by: str = 'data_type') -> List[Dict]:
        """
        Calcula analytics agregados
        """
        try:
            # Validar group_by
            valid_groups = ['data_type', 'sensor_id', 'priority', 'hour', 'day', 'month']
            if group_by not in valid_groups:
                self.logger.warning(f"group_by '{group_by}' no válido, usando 'data_type'")
                group_by = 'data_type'
            
            if group_by == 'hour':
                group_expr = "strftime('%Y-%m-%d %H:00:00', timestamp)"
            elif group_by == 'day':
                group_expr = "strftime('%Y-%m-%d', timestamp)"
            elif group_by == 'month':
                group_expr = "strftime('%Y-%m', timestamp)"
            else:
                group_expr = group_by
            
            query = f"""
                SELECT 
                    {group_expr} as period,
                    data_type,
                    COUNT(*) as count,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(DISTINCT sensor_id) as unique_sensors
                FROM telemetry_records
                GROUP BY {group_expr}, data_type
                ORDER BY period DESC
            """
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error calculando analytics: {e}")
            return []
    
    def get_by_location(self, latitude: float, longitude: float, 
                       radius_km: float = 1.0) -> List[Dict]:
        """
        Búsqueda basada en ubicación
        """
        try:
            # Fórmula aproximada para distancia en SQLite
            # Usar la fórmula de Haversine simplificada
            query = """
                SELECT *
                FROM (
                    SELECT *,
                        (6371 * acos(
                            cos(radians(?)) * cos(radians(location_lat)) * 
                            cos(radians(location_lng) - radians(?)) + 
                            sin(radians(?)) * sin(radians(location_lat))
                        )) as distance
                    FROM telemetry_records
                ) as location_data
                WHERE distance <= ?
                ORDER BY distance
            """
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (latitude, longitude, latitude, radius_km))
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Error en búsqueda por ubicación: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calcula estadísticas generales
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Estadísticas básicas
                cursor.execute("SELECT COUNT(*) FROM telemetry_records")
                total_records = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT sensor_id) FROM telemetry_records")
                unique_sensors = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT data_type) FROM telemetry_records")
                data_types = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(value) FROM telemetry_records")
                avg_value = cursor.fetchone()[0] or 0.0
                
                cursor.execute("SELECT MIN(timestamp) FROM telemetry_records")
                earliest = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(timestamp) FROM telemetry_records")
                latest = cursor.fetchone()[0]
                
                return {
                    'total_records': total_records,
                    'unique_sensors': unique_sensors,
                    'data_types': data_types,
                    'avg_value': round(avg_value, 2) if avg_value else 0.0,
                    'earliest_record': earliest,
                    'latest_record': latest
                }
                
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas: {e}")
            return {
                'total_records': 0,
                'unique_sensors': 0,
                'data_types': 0,
                'avg_value': 0.0,
                'earliest_record': None,
                'latest_record': None
            }
    
    def export_data(self, format: str = 'dict') -> Union[str, List[Dict]]:
        """
        Exporta datos en diferentes formatos
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM telemetry_records ORDER BY timestamp DESC")
                rows = [self._row_to_dict(row) for row in cursor.fetchall()]
                
                if format.lower() == 'json':
                    return json.dumps(rows, indent=2, default=str)
                else:
                    return rows
                    
        except Exception as e:
            self.logger.error(f"Error exportando datos: {e}")
            return [] if format.lower() != 'json' else '[]'
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de salud de la base de datos
        """
        try:
            stats = self.get_statistics()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar integridad
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                # Obtener tamaño de la base de datos
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    'status': 'healthy' if integrity_result == 'ok' else 'error',
                    'database_size_bytes': db_size,
                    'integrity_check': integrity_result,
                    'total_records': stats.get('total_records', 0),
                    'unique_sensors': stats.get('unique_sensors', 0),
                    'database_path': str(self.db_path),
                    'wal_mode_enabled': True
                }
                
        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'database_path': str(self.db_path)
            }
    
    def _convert_to_record(self, telemetry: Union[Dict, Any]) -> TelemetryRecord:
        """
        Convierte diferentes tipos de entrada a TelemetryRecord
        """
        # Manejo flexible de diferentes tipos de entrada
        if hasattr(telemetry, '__dict__'):
            # Objeto con atributos
            data = asdict(telemetry) if hasattr(telemetry, '__dataclass_fields__') else telemetry.__dict__
        else:
            # Diccionario
            data = telemetry
        
        # Extraer ubicación
        location = data.get('location', {})
        if isinstance(location, dict):
            lat = location.get('lat', 0.0)
            lng = location.get('lng', 0.0)
        else:
            lat = getattr(data, 'lat', 0.0)
            lng = getattr(data, 'lng', 0.0)
        
        return TelemetryRecord(
            id=data.get('id', str(data.get('sensor_id', '')) + '_' + str(data.get('timestamp', ''))),
            sensor_id=str(data.get('sensor_id', '')),
            timestamp=data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            data_type=data.get('data_type', 'unknown'),
            value=float(data.get('value', 0.0)),
            unit=data.get('unit', ''),
            location_lat=float(lat),
            location_lng=float(lng),
            priority=str(data.get('priority', 'normal')),
            gateway_id=data.get('gateway_id'),
            metadata_json=json.dumps(data.get('metadata', {})) if data.get('metadata') else None,
            processed=data.get('processed', False)
        )
    
    def _row_to_dict(self, row) -> Dict:
        """
        Convierte una fila SQL a diccionario
        """
        # Verificar si row es un resultado de query con descripción
        if hasattr(row, 'description') and hasattr(row, 'fetchone'):
            # row es un cursor, obtener la primera fila
            row = row.fetchone()
        
        # Si es una tupla/fila de resultado
        if len(row) == 13:  # 13 columnas en nuestra tabla principal
            return {
                'id': row[0],
                'sensor_id': row[1],
                'timestamp': row[2],
                'data_type': row[3],
                'value': row[4],
                'unit': row[5],
                'location': {'lat': row[6], 'lng': row[7]},
                'priority': row[8],
                'gateway_id': row[9],
                'metadata': json.loads(row[10]) if row[10] else None,
                'processed': bool(row[11]),
                'created_at': row[12]
            }
        elif len(row) == 7:  # 7 columnas en analytics (period, data_type, count, avg_value, min_value, max_value, unique_sensors)
            return {
                'period': row[0],
                'data_type': row[1],
                'count': row[2],
                'avg_value': row[3],
                'min_value': row[4],
                'max_value': row[5],
                'unique_sensors': row[6]
            }
        elif len(row) >= 14:  # Resultado de query de ubicación con distancia
            return {
                'id': row[0],
                'sensor_id': row[1],
                'timestamp': row[2],
                'data_type': row[3],
                'value': row[4],
                'unit': row[5],
                'location': {'lat': row[6], 'lng': row[7]},
                'priority': row[8],
                'gateway_id': row[9],
                'metadata': json.loads(row[10]) if row[10] else None,
                'processed': bool(row[11]),
                'created_at': row[12],
                'distance': row[13] if len(row) > 13 else 0.0
            }
        else:
            # Mapeo por índice si no sabemos la estructura
            return {f'col_{i}': val for i, val in enumerate(row)}
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager para conexiones
        """
        try:
            yield self.conn
        except Exception as e:
            self.logger.error(f"Error en conexión: {e}")
            raise
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.logger.info("Conexión a base de datos cerrada")
    
    def __del__(self):
        """Cleanup cuando el objeto se destruye"""
        self.close()


class SQLTelemetryRepositoryFactory:
    """Factory para crear instancias del repositorio SQL"""
    
    @staticmethod
    def create_repository(db_path: str = "telemetry.db", 
                         enable_wal_mode: bool = True) -> SQLTelemetryRepository:
        """
        Crea una instancia del repositorio SQL
        
        Args:
            db_path: Ruta al archivo de base de datos
            enable_wal_mode: Habilitar WAL mode
            
        Returns:
            SQLTelemetryRepository: Instancia configurada
        """
        return SQLTelemetryRepository(db_path, enable_wal_mode)


# Configuración de ejemplo
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear repositorio
    repo = SQLTelemetryRepositoryFactory.create_repository()
    
    # Ejemplo de uso
    print("=== SQL Telemetry Repository Demo ===")
    print(f"Health Check: {repo.health_check()}")
    
    # Ejemplo de datos de telemetría
    sample_telemetry = {
        'id': 'sensor_001_temp_2025_11_06_10_12_36',
        'sensor_id': 'sensor_001',
        'timestamp': '2025-11-06T10:12:36Z',
        'data_type': 'temperature',
        'value': 23.5,
        'unit': 'celsius',
        'location': {'lat': 5.0703, 'lng': -75.5138},  # Manizales
        'priority': 'normal',
        'gateway_id': 'gateway_norte_001',
        'metadata': {'battery_level': 85, 'signal_strength': -45}
    }
    
    # Guardar datos
    if repo.save(sample_telemetry):
        print("✓ Datos de telemetría guardados correctamente")
    
    # Obtener datos históricos
    historical_data = repo.get_historical_data(limit=5)
    print(f"✓ Recuperados {len(historical_data)} registros históricos")
    
    # Obtener analytics
    analytics = repo.get_analytics('data_type')
    print(f"✓ Analytics por tipo de dato: {len(analytics)} categorías")
    
    # Búsqueda por ubicación
    location_data = repo.get_by_location(5.0703, -75.5138, 5.0)
    print(f"✓ Datos en radio de 5km: {len(location_data)} registros")
    
    print("\n=== Repositorio SQL configurado y funcionando ===")
    
    repo.close()