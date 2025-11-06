"""
Servicio de Sincronización Automática DLMS para Urbia
==================================================

Servicio que conecta a PostgreSQL de ThingsBoard, extrae datos DLMS
y los convierte al formato Urbia con sincronización incremental.

Autor: Sistema Urbia
Fecha: 2025-11-06
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Estados de sincronización"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DLMSDataType(Enum):
    """Tipos de datos DLMS"""
    ACTIVE_ENERGY = "active_energy"
    REACTIVE_ENERGY = "reactive_energy"
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    FREQUENCY = "frequency"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"


@dataclass
class SyncConfiguration:
    """Configuración del servicio de sincronización"""
    thingsboard_host: str = "192.168.46.124"
    thingsboard_port: int = 5432
    thingsboard_database: str = "thingsboard"
    thingsboard_user: str = "postgres"
    thingsboard_password: str = ""  # Debe configurarse desde variables de entorno
    sync_interval_minutes: int = 15
    batch_size: int = 1000
    max_workers: int = 5
    retention_days: int = 365
    enable_partition_handling: bool = True


@dataclass
class DLMSRecord:
    """Registro de datos DLMS"""
    device_id: str
    data_type: str
    value: float
    unit: str
    timestamp: datetime
    partition: str
    raw_data: Dict[str, Any]
    converted_data: Dict[str, Any]


class DLMSDataExtractor:
    """Extractor de datos DLMS desde ThingsBoard"""
    
    def __init__(self, config: SyncConfiguration):
        self.config = config
        self.connection = None
        
    async def connect(self):
        """Establecer conexión con PostgreSQL de ThingsBoard"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.thingsboard_host,
                port=self.config.thingsboard_port,
                database=self.config.thingsboard_database,
                user=self.config.thingsboard_user,
                password=self.config.thingsboard_password,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = False
            logger.info("Conexión establecida con PostgreSQL de ThingsBoard")
        except Exception as e:
            logger.error(f"Error conectando a ThingsBoard: {e}")
            raise
    
    def disconnect(self):
        """Cerrar conexión con PostgreSQL"""
        if self.connection:
            self.connection.close()
            logger.info("Conexión cerrada con PostgreSQL de ThingsBoard")
    
    def get_partition_list(self) -> List[str]:
        """Obtener lista de particiones históricas"""
        try:
            query = """
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE tablename LIKE 'ts_kv_%' 
                AND schemaname = 'public'
                ORDER BY tablename
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                partitions = [row['tablename'] for row in cursor.fetchall()]
            
            # Filtrar particiones en el rango especificado (2024_11 a 2025_11)
            valid_partitions = []
            for partition in partitions:
                try:
                    # Extraer año y mes del nombre de partición
                    parts = partition.split('_')
                    if len(parts) >= 3:
                        year = int(parts[2])
                        month = int(parts[3])
                        
                        # Verificar rango: 2024_11 hasta 2025_11
                        if (year == 2024 and month >= 11) or (year == 2025 and month <= 11):
                            valid_partitions.append(partition)
                except (ValueError, IndexError):
                    continue
            
            logger.info(f"Particiones válidas encontradas: {valid_partitions}")
            return valid_partitions
            
        except Exception as e:
            logger.error(f"Error obteniendo particiones: {e}")
            return ['ts_kv']  # Fallback a tabla principal
    
    async def extract_dlms_data(self, 
                              partition: str, 
                              last_sync: Optional[datetime] = None) -> List[DLMSRecord]:
        """Extraer datos DLMS de una partición específica"""
        try:
            # Query para extraer datos DLMS
            query = """
                SELECT 
                    entity_id,
                    ts,
                    key,
                    string_value,
                    double_value,
                    bool_value,
                    json_value
                FROM {partition}
                WHERE (
                    key LIKE '%energy%' 
                    OR key LIKE '%power%'
                    OR key LIKE '%voltage%'
                    OR key LIKE '%current%'
                    OR key LIKE '%frequency%'
                    OR key LIKE '%temperature%'
                    OR key LIKE '%humidity%'
                    OR key LIKE '%dlms%'
                )
            """.format(partition=partition)
            
            # Agregar filtro de sincronización incremental
            if last_sync:
                query += f" AND ts > '{last_sync.isoformat()}'"
            
            query += " ORDER BY ts DESC LIMIT {batch_size}".format(
                batch_size=self.config.batch_size
            )
            
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            dlms_records = []
            for row in rows:
                # Determinar tipo de datos DLMS
                data_type = self._determine_dlms_data_type(row['key'])
                if data_type:
                    # Obtener valor según el tipo
                    value = self._extract_value(row)
                    if value is not None:
                        record = DLMSRecord(
                            device_id=str(row['entity_id']),
                            data_type=data_type.value,
                            value=float(value),
                            unit=self._get_unit_for_data_type(data_type),
                            timestamp=row['ts'],
                            partition=partition,
                            raw_data=dict(row),
                            converted_data={}
                        )
                        dlms_records.append(record)
            
            logger.info(f"Extraídos {len(dlms_records)} registros DLMS de partición {partition}")
            return dlms_records
            
        except Exception as e:
            logger.error(f"Error extrayendo datos DLMS de {partition}: {e}")
            return []
    
    def _determine_dlms_data_type(self, key: str) -> Optional[DLMSDataType]:
        """Determinar tipo de datos DLMS basado en la clave"""
        key_lower = key.lower()
        
        if 'energy' in key_lower:
            return DLMSDataType.ACTIVE_ENERGY if 'active' in key_lower else DLMSDataType.REACTIVE_ENERGY
        elif 'power' in key_lower:
            return DLMSDataType.POWER
        elif 'voltage' in key_lower:
            return DLMSDataType.VOLTAGE
        elif 'current' in key_lower:
            return DLMSDataType.CURRENT
        elif 'frequency' in key_lower:
            return DLMSDataType.FREQUENCY
        elif 'temperature' in key_lower:
            return DLMSDataType.TEMPERATURE
        elif 'humidity' in key_lower:
            return DLMSDataType.HUMIDITY
        
        return None
    
    def _extract_value(self, row: Dict[str, Any]) -> Optional[float]:
        """Extraer valor numérico del registro"""
        if row['double_value'] is not None:
            return float(row['double_value'])
        elif row['string_value'] is not None:
            try:
                return float(row['string_value'])
            except ValueError:
                pass
        elif row['bool_value'] is not None:
            return 1.0 if row['bool_value'] else 0.0
        elif row['json_value'] is not None:
            try:
                json_data = json.loads(row['json_value'])
                return float(json_data.get('value', 0))
            except (json.JSONDecodeError, ValueError):
                pass
        
        return None
    
    def _get_unit_for_data_type(self, data_type: DLMSDataType) -> str:
        """Obtener unidad para el tipo de datos"""
        units = {
            DLMSDataType.ACTIVE_ENERGY: "kWh",
            DLMSDataType.REACTIVE_ENERGY: "kVARh",
            DLMSDataType.VOLTAGE: "V",
            DLMSDataType.CURRENT: "A",
            DLMSDataType.POWER: "kW",
            DLMSDataType.FREQUENCY: "Hz",
            DLMSDataType.TEMPERATURE: "°C",
            DLMSDataType.HUMIDITY: "%"
        }
        return units.get(data_type, "")


class DLMSDataConverter:
    """Conversor de datos DLMS al formato Urbia"""
    
    @staticmethod
    def convert_to_urbia_format(dlms_record: DLMSRecord) -> Dict[str, Any]:
        """Convertir registro DLMS al formato estándar Urbia"""
        return {
            "device_id": dlms_record.device_id,
            "measurement_type": dlms_record.data_type,
            "value": dlms_record.value,
            "unit": dlms_record.unit,
            "timestamp": dlms_record.timestamp.isoformat(),
            "source": "dlms_thingsboard",
            "partition": dlms_record.partition,
            "metadata": {
                "raw_key": dlms_record.raw_data.get('key', ''),
                "extraction_time": datetime.now().isoformat(),
                "data_quality": "validated"
            },
            "location": DLMSDataConverter._extract_location(dlms_record),
            "device_metadata": DLMSDataConverter._extract_device_metadata(dlms_record)
        }
    
    @staticmethod
    def _extract_location(record: DLMSRecord) -> Dict[str, str]:
        """Extraer información de ubicación del dispositivo"""
        # Lógica para extraer ubicación basada en device_id o metadata
        # Por ahora retornamos valores por defecto
        return {
            "region": "default",
            "site": "default",
            "zone": "default"
        }
    
    @staticmethod
    def _extract_device_metadata(record: DLMSRecord) -> Dict[str, Any]:
        """Extraer metadata del dispositivo"""
        return {
            "manufacturer": "Generic",
            "model": "DLMS Meter",
            "protocol": "DLMS/COSEM",
            "firmware_version": "1.0.0"
        }


class DLMSChangeDetector:
    """Detector de cambios en datos DLMS"""
    
    def __init__(self):
        self.last_sync_points = {}  # device_id -> timestamp
        self.processed_records = set()
    
    async def detect_new_data(self, 
                            extracted_records: List[DLMSRecord]) -> List[DLMSRecord]:
        """Detectar nuevos datos que no han sido procesados"""
        new_records = []
        
        for record in extracted_records:
            record_key = f"{record.device_id}_{record.data_type}_{record.timestamp}"
            
            # Verificar si el registro ya fue procesado
            if record_key not in self.processed_records:
                new_records.append(record)
                self.processed_records.add(record_key)
            
            # Actualizar punto de sincronización
            device_key = f"{record.device_id}_{record.data_type}"
            if (device_key not in self.last_sync_points or 
                record.timestamp > self.last_sync_points[device_key]):
                self.last_sync_points[device_key] = record.timestamp
        
        return new_records
    
    def get_last_sync_point(self, device_id: str, data_type: str) -> Optional[datetime]:
        """Obtener último punto de sincronización para dispositivo y tipo"""
        device_key = f"{device_id}_{data_type}"
        return self.last_sync_points.get(device_key)
    
    def update_sync_point(self, device_id: str, data_type: str, timestamp: datetime):
        """Actualizar punto de sincronización"""
        device_key = f"{device_id}_{data_type}"
        self.last_sync_points[device_key] = timestamp


class DLMSSyncService:
    """Servicio principal de sincronización DLMS"""
    
    def __init__(self, config: Optional[SyncConfiguration] = None):
        self.config = config or SyncConfiguration()
        self.extractor = DLMSDataExtractor(self.config)
        self.converter = DLMSDataConverter()
        self.change_detector = DLMSChangeDetector()
        self.status = SyncStatus.IDLE
        self.last_sync_time = None
        self.sync_thread = None
        self.is_running = False
        self.sync_results = []
        
    async def start(self):
        """Iniciar servicio de sincronización automática"""
        logger.info("Iniciando servicio de sincronización DLMS")
        
        try:
            self.status = SyncStatus.RUNNING
            await self.extractor.connect()
            
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop)
            self.sync_thread.daemon = True
            self.sync_thread.start()
            
            logger.info("Servicio de sincronización DLMS iniciado correctamente")
            
        except Exception as e:
            self.status = SyncStatus.FAILED
            logger.error(f"Error iniciando servicio: {e}")
            raise
    
    async def stop(self):
        """Detener servicio de sincronización"""
        logger.info("Deteniendo servicio de sincronización DLMS")
        
        self.is_running = False
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=10)
        
        self.extractor.disconnect()
        self.status = SyncStatus.IDLE
        
        logger.info("Servicio de sincronización detenido")
    
    def _sync_loop(self):
        """Loop principal de sincronización"""
        while self.is_running:
            try:
                logger.info("Iniciando ciclo de sincronización")
                asyncio.run(self._perform_sync())
                
                # Esperar intervalo de sincronización
                time.sleep(self.config.sync_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error en ciclo de sincronización: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    async def _perform_sync(self):
        """Realizar sincronización completa"""
        sync_start_time = datetime.now()
        
        try:
            # Obtener particiones disponibles
            partitions = self.extractor.get_partition_list()
            if not partitions:
                logger.warning("No se encontraron particiones válidas")
                return
            
            all_new_records = []
            
            # Procesar cada partición
            for partition in partitions:
                logger.info(f"Procesando partición: {partition}")
                
                # Extraer datos de la partición
                extracted_records = await self.extractor.extract_dlms_data(partition)
                
                # Detectar nuevos datos
                new_records = await self.change_detector.detect_new_data(extracted_records)
                all_new_records.extend(new_records)
                
                logger.info(f"Encontrados {len(new_records)} nuevos registros en {partition}")
            
            # Convertir datos al formato Urbia
            converted_data = []
            for record in all_new_records:
                try:
                    converted = self.converter.convert_to_urbia_format(record)
                    converted_data.append(converted)
                    
                    # Actualizar punto de sincronización
                    self.change_detector.update_sync_point(
                        record.device_id, 
                        record.data_type, 
                        record.timestamp
                    )
                    
                except Exception as e:
                    logger.error(f"Error convirtiendo registro: {e}")
            
            # Guardar datos convertidos (implementar según necesidad)
            await self._store_converted_data(converted_data)
            
            # Actualizar estado
            self.last_sync_time = sync_start_time
            self.status = SyncStatus.COMPLETED
            self.sync_results.append({
                'timestamp': sync_start_time,
                'records_processed': len(converted_data),
                'partitions_processed': len(partitions),
                'status': 'success'
            })
            
            logger.info(f"Sincronización completada: {len(converted_data)} registros procesados")
            
        except Exception as e:
            self.status = SyncStatus.FAILED
            logger.error(f"Error en sincronización: {e}")
            
            self.sync_results.append({
                'timestamp': sync_start_time,
                'records_processed': 0,
                'partitions_processed': 0,
                'status': 'failed',
                'error': str(e)
            })
    
    async def _store_converted_data(self, converted_data: List[Dict[str, Any]]):
        """Almacenar datos convertidos en el formato Urbia"""
        # Implementar almacenamiento según necesidades del sistema
        # Por ejemplo, guardar en base de datos Urbia, API REST, archivos, etc.
        
        if converted_data:
            try:
                # Ejemplo: Guardar como JSON para procesamiento posterior
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/tmp/urbia_dlms_data_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(converted_data, f, indent=2, default=str)
                
                logger.info(f"Datos convertidos guardados en: {filename}")
                
                # Aquí se puede implementar lógica para:
                # - Insertar en base de datos Urbia
                # - Enviar a API REST
                # - Publicar en message queue
                # - etc.
                
            except Exception as e:
                logger.error(f"Error almacenando datos convertidos: {e}")
                raise
    
    async def manual_sync(self, partition: Optional[str] = None) -> Dict[str, Any]:
        """Ejecutar sincronización manual"""
        logger.info("Iniciando sincronización manual")
        
        sync_start = datetime.now()
        
        try:
            self.status = SyncStatus.RUNNING
            
            # Si no se especifica partición, usar todas las disponibles
            if not partition:
                partitions = self.extractor.get_partition_list()
            else:
                partitions = [partition]
            
            all_records = []
            
            for part in partitions:
                records = await self.extractor.extract_dlms_data(part)
                all_records.extend(records)
            
            # Convertir al formato Urbia
            converted_records = []
            for record in all_records:
                converted = self.converter.convert_to_urbia_format(record)
                converted_records.append(converted)
            
            # Almacenar datos
            await self._store_converted_data(converted_records)
            
            sync_duration = (datetime.now() - sync_start).total_seconds()
            
            result = {
                'success': True,
                'duration_seconds': sync_duration,
                'partitions_processed': partitions,
                'records_processed': len(converted_records),
                'timestamp': sync_start.isoformat()
            }
            
            self.status = SyncStatus.COMPLETED
            logger.info(f"Sincronización manual completada: {result}")
            
            return result
            
        except Exception as e:
            self.status = SyncStatus.FAILED
            error_result = {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - sync_start).total_seconds(),
                'timestamp': sync_start.isoformat()
            }
            
            logger.error(f"Error en sincronización manual: {e}")
            return error_result
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del servicio"""
        return {
            'status': self.status.value,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'is_running': self.is_running,
            'recent_results': self.sync_results[-5:] if self.sync_results else [],
            'configuration': {
                'host': self.config.thingsboard_host,
                'database': self.config.thingsboard_database,
                'sync_interval_minutes': self.config.sync_interval_minutes,
                'batch_size': self.config.batch_size
            }
        }
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de sincronización"""
        if not self.sync_results:
            return {'message': 'No hay estadísticas disponibles'}
        
        successful_syncs = [r for r in self.sync_results if r.get('status') == 'success']
        failed_syncs = [r for r in self.sync_results if r.get('status') == 'failed']
        
        total_records = sum(r.get('records_processed', 0) for r in successful_syncs)
        total_partitions = sum(r.get('partitions_processed', 0) for r in successful_syncs)
        
        return {
            'total_syncs': len(self.sync_results),
            'successful_syncs': len(successful_syncs),
            'failed_syncs': len(failed_syncs),
            'total_records_processed': total_records,
            'total_partitions_processed': total_partitions,
            'success_rate': len(successful_syncs) / len(self.sync_results) * 100,
            'last_sync': self.sync_results[-1] if self.sync_results else None
        }


# Función de utilidad para crear instancia del servicio
def create_dlms_sync_service(config_dict: Optional[Dict[str, Any]] = None) -> DLMSSyncService:
    """Crear instancia del servicio de sincronización DLMS"""
    if config_dict:
        config = SyncConfiguration(**config_dict)
    else:
        config = SyncConfiguration()
        # Configurar password desde variable de entorno
        import os
        config.thingsboard_password = os.getenv('THINGSBOARD_DB_PASSWORD', '')
    
    return DLMSSyncService(config)


# Ejemplo de uso
async def main():
    """Función principal de ejemplo"""
    # Crear servicio
    service = create_dlms_sync_service()
    
    try:
        # Iniciar servicio automático
        await service.start()
        
        # Ejecutar sincronización manual
        result = await service.manual_sync()
        print(f"Resultado de sincronización manual: {result}")
        
        # Mostrar estado
        status = service.get_status()
        print(f"Estado del servicio: {json.dumps(status, indent=2)}")
        
        # Mostrar estadísticas
        stats = service.get_sync_statistics()
        print(f"Estadísticas: {json.dumps(stats, indent=2)}")
        
        # Mantener servicio activo
        print("Servicio iniciado. Presiona Ctrl+C para detener...")
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\nDeteniendo servicio...")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())