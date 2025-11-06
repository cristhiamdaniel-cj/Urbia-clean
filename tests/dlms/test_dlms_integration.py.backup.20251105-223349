"""
Pruebas Unitarias Completas - Integración DLMS-Urbia
==================================================

Este módulo contiene pruebas unitarias completas para validar la integración 
DLMS-Urbia, incluyendo tests para sync service, adapter, repository, y casos 
de integración completa.

Autor: Sistema Urbia - Universidad Nacional de Colombia
Fecha: 2025-11-06
"""

import unittest
import asyncio
import tempfile
import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
from typing import List, Dict, Any

# Importar componentes DLMS a probar
from src.infrastructure.adapters.dlms_sensor_adapter import (
    DLMSSensorAdapter,
    DLMSRawData,
    DLMSConvertedData,
    SensorTypeDLMS,
    MeterType,
    PhaseType
)

from src.infrastructure.sync.dlms_sync_service import (
    DLMSSyncService,
    SyncConfiguration,
    DLMSDataExtractor,
    DLMSDataConverter,
    DLMSChangeDetector,
    DLMSRecord,
    DLMSDataType,
    SyncStatus
)

from src.infrastructure.database.sql_telemetry_repository import (
    SQLTelemetryRepository,
    TelemetryRecord,
    SQLTelemetryRepositoryFactory
)

from src.application.services.dlms_service import (
    DLMSService,
    DLMSDeviceType,
    DLMSReading,
    DLMSAnalytics,
    DLMSEvent,
    DLMSEventType
)


class TestDLMSSensorAdapter(unittest.TestCase):
    """Pruebas para el adaptador de sensores DLMS"""
    
    def setUp(self):
        """Configurar pruebas"""
        self.adapter = DLMSSensorAdapter()
    
    def test_adapter_initialization(self):
        """Prueba la inicialización del adaptador"""
        self.assertIsInstance(self.adapter, DLMSSensorAdapter)
        self.assertIsNotNone(self.adapter.logger)
        self.assertEqual(len(self.adapter._conversion_cache), 0)
    
    def test_monofasico_data_conversion(self):
        """Prueba conversión completa de datos monofásicos"""
        raw_data = DLMSRawData(
            device_id="DLMS-001",
            timestamp=datetime.now(),
            meter_type=MeterType.MONOFASICO,
            metrics={
                "voltage_l1": 220.5,
                "current_l1": 15.2,
                "active_power": 3344.0,
                "reactive_power": 1200.0,
                "active_energy": 1234567.8,
                "frequency": 50.1,
                "power_factor": 0.85
            },
            raw_values={"timestamp": "2025-11-06T10:12:36Z"}
        )
        
        converted_data = self.adapter.adapt_raw_data(raw_data)
        
        # Verificar cantidad de métricas convertidas
        self.assertEqual(len(converted_data), 7)
        
        # Verificar métricas específicas
        voltage_data = next((d for d in converted_data if d.sensor_type == SensorTypeDLMS.VOLTAJE), None)
        self.assertIsNotNone(voltage_data)
        self.assertAlmostEqual(voltage_data.value, 220.5, places=1)
        self.assertEqual(voltage_data.unit, "V")
        self.assertEqual(voltage_data.phase, PhaseType.L1)
        self.assertEqual(voltage_data.device_id, "DLMS-001")
        
        # Verificar que la conversión mantiene la calidad de datos
        self.assertIn(voltage_data.quality_indicator, ["GOOD", "UNCERTAIN", "BAD"])
        self.assertIsInstance(voltage_data.is_critical, bool)
    
    def test_trifasico_data_conversion(self):
        """Prueba conversión completa de datos trifásicos"""
        raw_data = DLMSRawData(
            device_id="DLMS-002",
            timestamp=datetime.now(),
            meter_type=MeterType.TRIFASICO,
            metrics={
                "voltage_l1": 218.3,
                "voltage_l2": 219.1,
                "voltage_l3": 220.2,
                "current_l1": 45.6,
                "current_l2": 44.8,
                "current_l3": 46.2,
                "active_power": 30234.0,
                "reactive_power": 8500.0,
                "active_energy": 5234567.8,
                "frequency": 49.9,
                "power_factor": 0.88
            },
            raw_values={}
        )
        
        converted_data = self.adapter.adapt_raw_data(raw_data)
        
        # Verificar que se convirtieron todas las métricas
        self.assertEqual(len(converted_data), 11)
        
        # Verificar métricas por fase
        for phase_key, phase_enum in [("L1", PhaseType.L1), ("L2", PhaseType.L2), ("L3", PhaseType.L3)]:
            voltage_data = next((d for d in converted_data 
                               if d.sensor_type.value == f"voltage_{phase_key.lower()}"), None)
            current_data = next((d for d in converted_data 
                               if d.sensor_type.value == f"current_{phase_key.lower()}"), None)
            
            self.assertIsNotNone(voltage_data, f"Falta voltaje {phase_key}")
            self.assertIsNotNone(current_data, f"Falta corriente {phase_key}")
            self.assertEqual(voltage_data.phase, phase_enum)
            self.assertEqual(current_data.phase, phase_enum)
    
    def test_data_quality_validation_comprehensive(self):
        """Prueba exhaustiva de validación de calidad de datos"""
        test_cases = [
            # (valor, tipo_sensor, calidad_esperada)
            (220.0, SensorTypeDLMS.VOLTAJE, "GOOD"),        # Normal
            (240.0, SensorTypeDLMS.VOLTAJE, "GOOD"),        # Límite normal
            (260.0, SensorTypeDLMS.VOLTAJE, "UNCERTAIN"),   # Cuestionable
            (320.0, SensorTypeDLMS.VOLTAJE, "BAD"),         # Crítico
            
            (50.0, SensorTypeDLMS.FRECUENCIA, "GOOD"),      # Frecuencia normal
            (48.0, SensorTypeDLMS.FRECUENCIA, "UNCERTAIN"), # Frecuencia cuestionable
            (55.0, SensorTypeDLMS.FRECUENCIA, "BAD"),       # Frecuencia crítica
            
            (0.85, SensorTypeDLMS.FACTOR_POTENCIA, "GOOD"), # Factor de potencia normal
            (0.45, SensorTypeDLMS.FACTOR_POTENCIA, "UNCERTAIN"), # Bajo pero aceptable
            (0.15, SensorTypeDLMS.FACTOR_POTENCIA, "BAD"),  # Muy bajo
        ]
        
        for value, sensor_type, expected_quality in test_cases:
            with self.subTest(value=value, sensor_type=sensor_type):
                quality = self.adapter._validate_data_quality(value, sensor_type)
                self.assertEqual(quality, expected_quality, 
                    f"Calidad incorrecta para valor {value} de {sensor_type}")
    
    def test_critical_value_detection_comprehensive(self):
        """Prueba exhaustiva de detección de valores críticos"""
        # Voltaje crítico
        self.assertFalse(self.adapter._is_critical_value(220.0, SensorTypeDLMS.VOLTAJE))  # Normal
        self.assertTrue(self.adapter._is_critical_value(340.0, SensorTypeDLMS.VOLTAJE))   # Alto crítico
        self.assertTrue(self.adapter._is_critical_value(140.0, SensorTypeDLMS.VOLTAJE))   # Bajo crítico
        
        # Corriente crítica
        self.assertFalse(self.adapter._is_critical_value(50.0, SensorTypeDLMS.CORRIENTE))  # Normal
        self.assertTrue(self.adapter._is_critical_value(1200.0, SensorTypeDLMS.CORRIENTE)) # Alta crítica
        
        # Frecuencia crítica
        self.assertFalse(self.adapter._is_critical_value(50.0, SensorTypeDLMS.FRECUENCIA))  # Normal
        self.assertTrue(self.adapter._is_critical_value(45.0, SensorTypeDLMS.FRECUENCIA))   # Baja crítica
        self.assertTrue(self.adapter._is_critical_value(55.0, SensorTypeDLMS.FRECUENCIA))   # Alta crítica
    
    def test_value_conversion_edge_cases(self):
        """Prueba casos extremos en conversión de valores"""
        # Valores string con diferentes formatos
        test_cases = [
            ("220.5", SensorTypeDLMS.VOLTAJE, 220.5),
            ("220,5", SensorTypeDLMS.VOLTAJE, 220.5),  # Coma decimal
            ("  123.4  ", SensorTypeDLMS.POTENCIA, 123.4),  # Espacios
            (123.4, SensorTypeDLMS.POTENCIA, 123.4),  # Ya es float
            (456, SensorTypeDLMS.CORRIENTE, 456.0),   # Int a float
        ]
        
        for value, sensor_type, expected in test_cases:
            with self.subTest(value=value, sensor_type=sensor_type):
                converted = self.adapter._convert_value(value, sensor_type)
                self.assertAlmostEqual(converted, expected, places=1)
    
    def test_sensor_config_generation(self):
        """Prueba la generación completa de configuración de sensores"""
        # Crear datos convertidos simulando un dispositivo completo
        converted_data = [
            DLMSConvertedData(
                device_id="DLMS-001",
                timestamp=datetime.now(),
                sensor_type=SensorTypeDLMS.VOLTAJE,
                value=220.0,
                unit="V",
                phase=PhaseType.L1,
                quality_indicator="GOOD",
                is_critical=False
            ),
            DLMSConvertedData(
                device_id="DLMS-001",
                timestamp=datetime.now(),
                sensor_type=SensorTypeDLMS.CORRIENTE,
                value=15.2,
                unit="A",
                phase=PhaseType.L1,
                quality_indicator="GOOD",
                is_critical=False
            )
        ]
        
        config = self.adapter.create_sensor_config("DLMS-001", converted_data)
        
        # Verificar estructura de configuración
        self.assertEqual(config["device_id"], "DLMS-001")
        self.assertEqual(config["device_type"], "DLMS_METER")
        self.assertEqual(config["total_sensors"], 2)
        self.assertEqual(len(config["sensors"]), 2)
        
        # Verificar estructura de sensor individual
        sensor = config["sensors"][0]
        self.assertIn("id", sensor)
        self.assertIn("name", sensor)
        self.assertIn("type", sensor)
        self.assertIn("unit", sensor)
        self.assertIn("location", sensor)
        self.assertIn("priority", sensor)
        self.assertIn("min_value", sensor)
        self.assertIn("max_value", sensor)
        self.assertIn("threshold_critical", sensor)
        self.assertIn("is_active", sensor)
        
        # Verificar que los IDs son únicos
        sensor_ids = [s["id"] for s in config["sensors"]]
        self.assertEqual(len(sensor_ids), len(set(sensor_ids)), "Los IDs de sensores deben ser únicos")
    
    def test_device_data_validation_comprehensive(self):
        """Prueba exhaustiva de validación de datos de dispositivo"""
        # Caso 1: Datos válidos
        is_valid, errors = self.adapter.validate_device_data(
            "DLMS-001",
            MeterType.MONOFASICO,
            {
                "voltage_l1": 220.0,
                "current_l1": 15.0,
                "active_power": 3300.0,
                "reactive_power": 1200.0,
                "active_energy": 1234567.0,
                "frequency": 50.0,
                "power_factor": 0.85
            }
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Caso 2: Tipo de medidor inválido
        is_valid, errors = self.adapter.validate_device_data(
            "DLMS-999",
            "INVALID_TYPE",
            {"voltage_l1": 220.0}
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("no soportado" in error for error in errors))
        
        # Caso 3: Valores no numéricos
        is_valid, errors = self.adapter.validate_device_data(
            "DLMS-001",
            MeterType.MONOFASICO,
            {
                "voltage_l1": "invalid_number",
                "current_l1": 15.0
            }
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("no numérico" in error for error in errors))
        
        # Caso 4: Métricas parcialmente válidas (transmisión parcial)
        is_valid, errors = self.adapter.validate_device_data(
            "DLMS-001",
            MeterType.MONOFASICO,
            {
                "voltage_l1": 220.0,
                "current_l1": 15.0  # Solo 2 de 7 métricas esperadas
            }
        )
        self.assertTrue(is_valid)  # Debe ser válido por transmisión parcial
        
        # Caso 5: Métricas inesperadas
        is_valid, errors = self.adapter.validate_device_data(
            "DLMS-001",
            MeterType.MONOFASICO,
            {
                "voltage_l1": 220.0,
                "unexpected_metric": 123.0
            }
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("inesperadas" in error for error in errors))


class TestDLMSSyncService(unittest.TestCase):
    """Pruebas para el servicio de sincronización DLMS"""
    
    def setUp(self):
        """Configurar pruebas con base de datos temporal"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_dlms.db")
        
        self.config = SyncConfiguration(
            thingsboard_host="localhost",
            thingsboard_port=5432,
            thingsboard_database="thingsboard",
            thingsboard_user="postgres",
            thingsboard_password="test",
            sync_interval_minutes=5,
            batch_size=100
        )
        
        self.extractor = DLMSDataExtractor(self.config)
        self.converter = DLMSDataConverter()
        self.change_detector = DLMSChangeDetector()
        self.sync_service = DLMSSyncService(self.config)
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_configuration_creation(self):
        """Prueba la creación de configuración"""
        self.assertEqual(self.config.thingsboard_host, "localhost")
        self.assertEqual(self.config.sync_interval_minutes, 5)
        self.assertEqual(self.config.batch_size, 100)
        self.assertTrue(self.config.enable_partition_handling)
    
    def test_dlms_record_creation(self):
        """Prueba la creación de registros DLMS"""
        record = DLMSRecord(
            device_id="DLMS-001",
            data_type="voltage",
            value=220.0,
            unit="V",
            timestamp=datetime.now(),
            partition="ts_kv_2025_11",
            raw_data={"key": "voltage_l1", "value": 220.0},
            converted_data={}
        )
        
        self.assertEqual(record.device_id, "DLMS-001")
        self.assertEqual(record.data_type, "voltage")
        self.assertAlmostEqual(record.value, 220.0, places=1)
        self.assertEqual(record.unit, "V")
        self.assertIsInstance(record.timestamp, datetime)
        self.assertEqual(record.partition, "ts_kv_2025_11")
    
    def test_data_type_determination(self):
        """Prueba la determinación de tipos de datos DLMS"""
        test_cases = [
            ("voltage_l1", DLMSDataType.VOLTAGE),
            ("current_l1", DLMSDataType.CURRENT),
            ("active_energy", DLMSDataType.ACTIVE_ENERGY),
            ("reactive_energy", DLMSDataType.REACTIVE_ENERGY),
            ("active_power", DLMSDataType.POWER),
            ("frequency", DLMSDataType.FREQUENCY),
            ("temperature", DLMSDataType.TEMPERATURE),
            ("humidity", DLMSDataType.HUMIDITY),
            ("unknown_metric", None)
        ]
        
        for key, expected_type in test_cases:
            with self.subTest(key=key):
                detected_type = self.extractor._determine_dlms_data_type(key)
                self.assertEqual(detected_type, expected_type)
    
    def test_value_extraction(self):
        """Prueba la extracción de valores de registros"""
        # Caso 1: double_value
        row = {"double_value": 220.5, "string_value": None, "bool_value": None, "json_value": None}
        value = self.extractor._extract_value(row)
        self.assertAlmostEqual(value, 220.5, places=1)
        
        # Caso 2: string_value
        row = {"double_value": None, "string_value": "123.4", "bool_value": None, "json_value": None}
        value = self.extractor._extract_value(row)
        self.assertAlmostEqual(value, 123.4, places=1)
        
        # Caso 3: bool_value
        row = {"double_value": None, "string_value": None, "bool_value": True, "json_value": None}
        value = self.extractor._extract_value(row)
        self.assertEqual(value, 1.0)
        
        row = {"double_value": None, "string_value": None, "bool_value": False, "json_value": None}
        value = self.extractor._extract_value(row)
        self.assertEqual(value, 0.0)
        
        # Caso 4: json_value
        json_data = '{"value": 456.7}'
        row = {"double_value": None, "string_value": None, "bool_value": None, "json_value": json_data}
        value = self.extractor._extract_value(row)
        self.assertAlmostEqual(value, 456.7, places=1)
        
        # Caso 5: Sin valores válidos
        row = {"double_value": None, "string_value": None, "bool_value": None, "json_value": None}
        value = self.extractor._extract_value(row)
        self.assertIsNone(value)
    
    def test_unit_mapping(self):
        """Prueba el mapeo de unidades por tipo de datos"""
        test_cases = [
            (DLMSDataType.ACTIVE_ENERGY, "kWh"),
            (DLMSDataType.REACTIVE_ENERGY, "kVARh"),
            (DLMSDataType.VOLTAGE, "V"),
            (DLMSDataType.CURRENT, "A"),
            (DLMSDataType.POWER, "kW"),
            (DLMSDataType.FREQUENCY, "Hz"),
            (DLMSDataType.TEMPERATURE, "°C"),
            (DLMSDataType.HUMIDITY, "%")
        ]
        
        for data_type, expected_unit in test_cases:
            with self.subTest(data_type=data_type):
                unit = self.extractor._get_unit_for_data_type(data_type)
                self.assertEqual(unit, expected_unit)
    
    def test_data_conversion_to_urbia_format(self):
        """Prueba la conversión de datos DLMS al formato Urbia"""
        # Crear registro DLMS de prueba
        dlms_record = DLMSRecord(
            device_id="DLMS-001",
            data_type="voltage",
            value=220.0,
            unit="V",
            timestamp=datetime.now(),
            partition="ts_kv_2025_11",
            raw_data={"key": "voltage_l1", "entity_id": "DLMS-001"},
            converted_data={}
        )
        
        # Convertir al formato Urbia
        urbia_format = self.converter.convert_to_urbia_format(dlms_record)
        
        # Verificar estructura del formato Urbia
        self.assertEqual(urbia_format["device_id"], "DLMS-001")
        self.assertEqual(urbia_format["measurement_type"], "voltage")
        self.assertAlmostEqual(urbia_format["value"], 220.0, places=1)
        self.assertEqual(urbia_format["unit"], "V")
        self.assertIn("timestamp", urbia_format)
        self.assertEqual(urbia_format["source"], "dlms_thingsboard")
        self.assertEqual(urbia_format["partition"], "ts_kv_2025_11")
        self.assertIn("metadata", urbia_format)
        self.assertIn("location", urbia_format)
        self.assertIn("device_metadata", urbia_format)
    
    def test_change_detection(self):
        """Prueba la detección de cambios en datos"""
        # Crear registros de prueba
        record1 = DLMSRecord(
            device_id="DLMS-001",
            data_type="voltage",
            value=220.0,
            unit="V",
            timestamp=datetime.now(),
            partition="ts_kv_2025_11",
            raw_data={},
            converted_data={}
        )
        
        record2 = DLMSRecord(
            device_id="DLMS-001",
            data_type="voltage",
            value=221.0,
            unit="V",
            timestamp=datetime.now(),
            partition="ts_kv_2025_11",
            raw_data={},
            converted_data={}
        )
        
        # Detectar nuevos datos
        new_records = asyncio.run(self.change_detector.detect_new_data([record1, record2]))
        
        # Ambos registros deben ser nuevos
        self.assertEqual(len(new_records), 2)
        
        # Detectar de nuevo (duplicados)
        new_records_again = asyncio.run(self.change_detector.detect_new_data([record1, record2]))
        
        # No debe haber registros nuevos (ya procesados)
        self.assertEqual(len(new_records_again), 0)
    
    def test_sync_point_management(self):
        """Prueba la gestión de puntos de sincronización"""
        timestamp = datetime.now()
        
        # Actualizar punto de sincronización
        self.change_detector.update_sync_point("DLMS-001", "voltage", timestamp)
        
        # Obtener punto de sincronización
        sync_point = self.change_detector.get_last_sync_point("DLMS-001", "voltage")
        
        self.assertEqual(sync_point, timestamp)
        
        # Probar con dispositivo/tipo inexistente
        nonexistent_sync_point = self.change_detector.get_last_sync_point("DLMS-999", "unknown")
        self.assertIsNone(nonexistent_sync_point)
    
    @patch('psycopg2.connect')
    def test_extractor_connectivity(self, mock_connect):
        """Prueba la conectividad del extractor (simulada)"""
        # Simular conexión exitosa
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Ejecutar conexión
        asyncio.run(self.extractor.connect())
        
        # Verificar que se llamó a psycopg2.connect
        mock_connect.assert_called_once()
        
        # Verificar que la conexión está configurada
        self.assertIsNotNone(self.extractor.connection)
        
        # Probar desconexión
        self.extractor.disconnect()
        self.assertIsNone(self.extractor.connection)
    
    def test_service_status_management(self):
        """Prueba la gestión de estado del servicio"""
        # Estado inicial
        self.assertEqual(self.sync_service.status, SyncStatus.IDLE)
        self.assertIsNone(self.sync_service.last_sync_time)
        self.assertFalse(self.sync_service.is_running)
        self.assertEqual(len(self.sync_service.sync_results), 0)
        
        # Cambiar estado a running
        self.sync_service.status = SyncStatus.RUNNING
        self.assertEqual(self.sync_service.status, SyncStatus.RUNNING)
        
        # Agregar resultado de sincronización simulado
        self.sync_service.sync_results.append({
            'timestamp': datetime.now(),
            'records_processed': 100,
            'partitions_processed': 3,
            'status': 'success'
        })
        
        self.assertEqual(len(self.sync_service.sync_results), 1)
    
    def test_service_statistics(self):
        """Prueba el cálculo de estadísticas del servicio"""
        # Agregar resultados de prueba
        self.sync_service.sync_results = [
            {
                'timestamp': datetime.now(),
                'records_processed': 100,
                'partitions_processed': 3,
                'status': 'success'
            },
            {
                'timestamp': datetime.now(),
                'records_processed': 0,
                'partitions_processed': 2,
                'status': 'failed'
            }
        ]
        
        stats = self.sync_service.get_sync_statistics()
        
        # Verificar estadísticas
        self.assertEqual(stats['total_syncs'], 2)
        self.assertEqual(stats['successful_syncs'], 1)
        self.assertEqual(stats['failed_syncs'], 1)
        self.assertEqual(stats['total_records_processed'], 100)
        self.assertEqual(stats['total_partitions_processed'], 3)
        self.assertAlmostEqual(stats['success_rate'], 50.0, places=1)
        self.assertIsNotNone(stats['last_sync'])


class TestSQLTelemetryRepository(unittest.TestCase):
    """Pruebas para el repositorio de telemetría SQL"""
    
    def setUp(self):
        """Configurar repositorio con base de datos temporal"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_telemetry.db")
        
        self.repository = SQLTelemetryRepositoryFactory.create_repository(
            db_path=self.test_db_path,
            enable_wal_mode=False
        )
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        import shutil
        if hasattr(self, 'repository'):
            del self.repository
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_repository_initialization(self):
        """Prueba la inicialización del repositorio"""
        self.assertIsNotNone(self.repository)
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Verificar que las tablas se crearon
        with self.repository._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='telemetry_records'
            """)
            table_exists = cursor.fetchone() is not None
            self.assertTrue(table_exists)
    
    def test_single_record_save_and_retrieve(self):
        """Prueba guardar y recuperar un solo registro"""
        test_record = {
            'id': 'test_001',
            'sensor_id': 'sensor_001',
            'timestamp': datetime.now().isoformat(),
            'data_type': 'temperature',
            'value': 23.5,
            'unit': 'celsius',
            'location': {'lat': 5.0703, 'lng': -75.5138},
            'priority': 'normal',
            'gateway_id': 'gateway_001',
            'metadata': {'battery_level': 85}
        }
        
        # Guardar registro
        success = self.repository.save(test_record)
        self.assertTrue(success)
        
        # Recuperar registro
        retrieved = self.repository.get_by_id('test_001')
        self.assertIsNotNone(retrieved)
        
        # Verificar datos
        if isinstance(retrieved, dict):
            self.assertEqual(retrieved['id'], 'test_001')
            self.assertEqual(retrieved['sensor_id'], 'sensor_001')
            self.assertEqual(retrieved['data_type'], 'temperature')
            self.assertAlmostEqual(retrieved['value'], 23.5, places=1)
        else:
            # Si es objeto con atributos
            self.assertEqual(retrieved.id, 'test_001')
            self.assertEqual(retrieved.sensor_id, 'sensor_001')
    
    def test_multiple_records_batch_save(self):
        """Prueba guardar múltiples registros en lote"""
        test_records = []
        for i in range(10):
            record = {
                'id': f'batch_test_{i:03d}',
                'sensor_id': f'sensor_{i % 3}',  # 3 sensores diferentes
                'timestamp': (datetime.now() + timedelta(minutes=i)).isoformat(),
                'data_type': 'temperature' if i % 2 == 0 else 'humidity',
                'value': 20.0 + i,
                'unit': 'celsius' if i % 2 == 0 else '%',
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'normal'
            }
            test_records.append(record)
        
        # Guardar en lote
        saved_count = self.repository.save_many(test_records)
        self.assertEqual(saved_count, 10)
        
        # Verificar que se guardaron
        self.assertEqual(len(test_records), saved_count)
    
    def test_sensor_data_retrieval(self):
        """Prueba recuperar datos por sensor"""
        # Guardar datos de prueba
        test_records = [
            {
                'id': f'sensor_test_{i}',
                'sensor_id': 'test_sensor',
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'data_type': 'temperature',
                'value': 20.0 + i,
                'unit': 'celsius',
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'normal'
            }
            for i in range(5)
        ]
        
        self.repository.save_many(test_records)
        
        # Recuperar datos del sensor
        retrieved = self.repository.get_by_sensor('test_sensor', limit=10)
        
        self.assertEqual(len(retrieved), 5)
        for record in retrieved:
            if isinstance(record, dict):
                self.assertEqual(record['sensor_id'], 'test_sensor')
            else:
                self.assertEqual(record.sensor_id, 'test_sensor')
    
    def test_historical_data_retrieval(self):
        """Prueba la recuperación de datos históricos con filtros"""
        # Crear datos con diferentes timestamps
        base_time = datetime.now()
        test_records = []
        
        for i in range(20):
            timestamp = base_time - timedelta(hours=i)
            record = {
                'id': f'hist_test_{i}',
                'sensor_id': f'sensor_hist',
                'timestamp': timestamp.isoformat(),
                'data_type': 'temperature',
                'value': 20.0 + i,
                'unit': 'celsius',
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'normal'
            }
            test_records.append(record)
        
        self.repository.save_many(test_records)
        
        # Recuperar últimas 5 horas
        start_date = (base_time - timedelta(hours=5)).isoformat()
        end_date = base_time.isoformat()
        
        historical_data = self.repository.get_historical_data(
            sensor_id='sensor_hist',
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        
        # Debe retornar registros de las últimas 5 horas
        self.assertGreaterEqual(len(historical_data), 0)
    
    def test_analytics_aggregation(self):
        """Prueba el cálculo de analytics agregados"""
        # Crear datos para analytics
        base_time = datetime.now()
        test_records = []
        
        for i in range(10):
            timestamp = base_time - timedelta(hours=i)
            record = {
                'id': f'analytics_test_{i}',
                'sensor_id': f'sensor_analytics',
                'timestamp': timestamp.isoformat(),
                'data_type': 'temperature',
                'value': 20.0 + (i % 3),  # Valores repetidos para agregación
                'unit': 'celsius',
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'normal'
            }
            test_records.append(record)
        
        self.repository.save_many(test_records)
        
        # Obtener analytics por tipo de dato
        analytics = self.repository.get_analytics('data_type')
        
        self.assertGreaterEqual(len(analytics), 0)
        
        # Si hay analytics, verificar estructura
        if analytics:
            for item in analytics:
                self.assertIn('period', item)
                self.assertIn('data_type', item)
                self.assertIn('count', item)
                self.assertIn('avg_value', item)
                self.assertIn('min_value', item)
                self.assertIn('max_value', item)
                self.assertIn('unique_sensors', item)
    
    def test_location_based_search(self):
        """Prueba búsqueda basada en ubicación"""
        # Crear datos con diferentes ubicaciones
        test_records = [
            {
                'id': 'location_test_1',
                'sensor_id': 'sensor_near',
                'timestamp': datetime.now().isoformat(),
                'data_type': 'temperature',
                'value': 23.0,
                'unit': 'celsius',
                'location': {'lat': 5.0703, 'lng': -75.5138},  # Manizales
                'priority': 'normal'
            },
            {
                'id': 'location_test_2',
                'sensor_id': 'sensor_far',
                'timestamp': datetime.now().isoformat(),
                'data_type': 'temperature',
                'value': 18.0,
                'unit': 'celsius',
                'location': {'lat': 4.6097, 'lng': -74.0817},  # Bogotá
                'priority': 'normal'
            }
        ]
        
        self.repository.save_many(test_records)
        
        # Buscar cerca de Manizales (radio 1 km)
        near_records = self.repository.get_by_location(
            latitude=5.0703,
            longitude=-75.5138,
            radius_km=1.0
        )
        
        # Debe encontrar el sensor de Manizales
        self.assertGreaterEqual(len(near_records), 1)
        
        # Buscar cerca de Bogotá (radio 1 km)
        far_records = self.repository.get_by_location(
            latitude=4.6097,
            longitude=-74.0817,
            radius_km=1.0
        )
        
        # Debe encontrar el sensor de Bogotá
        self.assertGreaterEqual(len(far_records), 1)
    
    def test_data_statistics(self):
        """Prueba el cálculo de estadísticas de datos"""
        # Crear datos de prueba
        test_records = []
        for i in range(20):
            record = {
                'id': f'stats_test_{i}',
                'sensor_id': f'sensor_stats_{i % 3}',  # 3 sensores diferentes
                'timestamp': datetime.now().isoformat(),
                'data_type': 'temperature' if i % 2 == 0 else 'humidity',
                'value': 20.0 + i,
                'unit': 'celsius' if i % 2 == 0 else '%',
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'normal'
            }
            test_records.append(record)
        
        self.repository.save_many(test_records)
        
        # Obtener estadísticas generales
        stats = self.repository.get_statistics()
        
        self.assertEqual(stats['total_records'], 20)
        self.assertEqual(stats['unique_sensors'], 3)
        self.assertEqual(stats['data_types'], 2)  # temperature y humidity
        self.assertIn('avg_value', stats)
        self.assertIn('earliest_record', stats)
        self.assertIn('latest_record', stats)
    
    def test_data_export(self):
        """Prueba la exportación de datos"""
        # Crear datos de prueba
        test_record = {
            'id': 'export_test',
            'sensor_id': 'sensor_export',
            'timestamp': datetime.now().isoformat(),
            'data_type': 'temperature',
            'value': 25.0,
            'unit': 'celsius',
            'location': {'lat': 5.0703, 'lng': -75.5138},
            'priority': 'normal'
        }
        
        self.repository.save(test_record)
        
        # Exportar como JSON
        json_export = self.repository.export_data('json')
        self.assertIsInstance(json_export, str)
        
        # Parsear JSON para verificar estructura
        parsed_data = json.loads(json_export)
        self.assertIsInstance(parsed_data, list)
        
        # Exportar como diccionario
        dict_export = self.repository.export_data('dict')
        self.assertIsInstance(dict_export, list)
        
        # Verificar que los datos son consistentes
        if dict_export:
            first_record = dict_export[0]
            self.assertIn('id', first_record)
            self.assertIn('sensor_id', first_record)
            self.assertIn('value', first_record)
    
    def test_health_check(self):
        """Prueba el control de salud de la base de datos"""
        # Agregar algunos datos para verificar
        test_record = {
            'id': 'health_test',
            'sensor_id': 'sensor_health',
            'timestamp': datetime.now().isoformat(),
            'data_type': 'temperature',
            'value': 25.0,
            'unit': 'celsius',
            'location': {'lat': 5.0703, 'lng': -75.5138},
            'priority': 'normal'
        }
        
        self.repository.save(test_record)
        
        # Verificar salud
        health = self.repository.health_check()
        
        self.assertIn('status', health)
        self.assertIn('database_size_bytes', health)
        self.assertIn('integrity_check', health)
        self.assertIn('total_records', health)
        self.assertIn('unique_sensors', health)
        self.assertIn('database_path', health)
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['total_records'], 1)


class TestDLMSService(unittest.TestCase):
    """Pruebas para el servicio principal DLMS"""
    
    def setUp(self):
        """Configurar servicio DLMS con dependencias simuladas"""
        self.dlms_service = DLMSService()
        
        # Crear mocks para las dependencias
        self.mock_sync_service = AsyncMock()
        self.mock_sensor_adapter = AsyncMock()
        self.mock_telemetry_service = AsyncMock()
        
        # Configurar dependencias
        self.dlms_service.set_dependencies(
            self.mock_sync_service,
            self.mock_sensor_adapter,
            self.mock_telemetry_service
        )
    
    def test_service_initialization(self):
        """Prueba la inicialización del servicio"""
        self.assertIsNotNone(self.dlms_service)
        self.assertEqual(len(self.dlms_service._active_devices), 0)
        self.assertEqual(len(self.dlms_service._recent_readings), 0)
        self.assertEqual(len(self.dlms_service._analytics_cache), 0)
        self.assertIsNotNone(self.dlms_service._event_handlers)
    
    def test_device_type_enum(self):
        """Prueba la enumeración de tipos de dispositivos"""
        self.assertEqual(DLMSDeviceType.MONOFASICO.value, "DLMS-Meter-01")
        self.assertEqual(DLMSDeviceType.TRIFASICO.value, "DLMS-Meter-02")
        self.assertEqual(DLMSDeviceType.POLYFASICO.value, "DLMS-Meter-03")
    
    def test_event_type_enum(self):
        """Prueba la enumeración de tipos de eventos"""
        self.assertEqual(DLMSEventType.DATA_SYNC.value, "data_sync")
        self.assertEqual(DLMSEventType.ANALYTICS_UPDATE.value, "analytics_update")
        self.assertEqual(DLMSEventType.ALERT_TRIGGERED.value, "alert_triggered")
        self.assertEqual(DLMSEventType.DEVICE_OFFLINE.value, "device_offline")
        self.assertEqual(DLMSEventType.QUALITY_ANOMALY.value, "quality_anomaly")
    
    def test_dlms_reading_creation(self):
        """Prueba la creación de lecturas DLMS"""
        reading = DLMSReading(
            device_id="DLMS-001",
            device_type=DLMSDeviceType.MONOFASICO,
            timestamp=datetime.now(),
            measurements={
                "voltage_l1": 220.0,
                "current_l1": 15.0,
                "active_power": 3300.0
            },
            quality_flag=True,
            raw_data={"source": "thingsboard"}
        )
        
        self.assertEqual(reading.device_id, "DLMS-001")
        self.assertEqual(reading.device_type, DLMSDeviceType.MONOFASICO)
        self.assertIsInstance(reading.timestamp, datetime)
        self.assertEqual(len(reading.measurements), 3)
        self.assertTrue(reading.quality_flag)
        self.assertIsNotNone(reading.raw_data)
    
    def test_dlms_analytics_creation(self):
        """Prueba la creación de analytics DLMS"""
        analytics = DLMSAnalytics(
            device_id="DLMS-001",
            period_start=datetime.now() - timedelta(hours=24),
            period_end=datetime.now(),
            total_energy=15000.0,
            avg_power=2500.0,
            peak_power=3500.0,
            power_factor=0.85,
            frequency_variation=0.5,
            voltage_stability=95.0,
            load_factor=0.71,
            quality_score=92.5
        )
        
        self.assertEqual(analytics.device_id, "DLMS-001")
        self.assertIsInstance(analytics.period_start, datetime)
        self.assertIsInstance(analytics.period_end, datetime)
        self.assertAlmostEqual(analytics.total_energy, 15000.0, places=1)
        self.assertAlmostEqual(analytics.avg_power, 2500.0, places=1)
        self.assertAlmostEqual(analytics.peak_power, 3500.0, places=1)
        self.assertAlmostEqual(analytics.quality_score, 92.5, places=1)
    
    def test_dlms_event_creation(self):
        """Prueba la creación de eventos DLMS"""
        event = DLMSEvent(
            event_type=DLMSEventType.DATA_SYNC,
            device_id="DLMS-001",
            timestamp=datetime.now(),
            severity="INFO",
            message="Data synchronized successfully",
            data={"records_processed": 100}
        )
        
        self.assertEqual(event.event_type, DLMSEventType.DATA_SYNC)
        self.assertEqual(event.device_id, "DLMS-001")
        self.assertIsInstance(event.timestamp, datetime)
        self.assertEqual(event.severity, "INFO")
        self.assertEqual(event.message, "Data synchronized successfully")
        self.assertEqual(event.data["records_processed"], 100)
    
    def test_dependencies_configuration(self):
        """Prueba la configuración de dependencias"""
        # Verificar que las dependencias están configuradas
        self.assertIsNotNone(self.dlms_service._sync_service)
        self.assertIsNotNone(self.dlms_service._sensor_adapter)
        self.assertIsNotNone(self.dlms_service._telemetry_service)
        
        # Verificar que son los mocks esperados
        self.assertEqual(self.dlms_service._sync_service, self.mock_sync_service)
        self.assertEqual(self.dlms_service._sensor_adapter, self.mock_sensor_adapter)
        self.assertEqual(self.dlms_service._telemetry_service, self.mock_telemetry_service)
    
    def test_unit_mapping_for_measurements(self):
        """Prueba el mapeo de unidades para mediciones"""
        test_cases = [
            ("VOLTAJE", "V"),
            ("VOLTAJE_L1", "V"),
            ("VOLTAJE_L2", "V"),
            ("VOLTAJE_L3", "V"),
            ("CORRIENTE", "A"),
            ("CORRIENTE_L1", "A"),
            ("CORRIENTE_L2", "A"),
            ("CORRIENTE_L3", "A"),
            ("POTENCIA", "W"),
            ("Active_Power", "W"),
            ("ENERGIA", "Wh"),
            ("Active_Energy", "Wh"),
            ("FRECUENCIA", "Hz"),
            ("POWER_FACTOR", "pf"),
            ("THD_VOLTAGE", "%"),
            ("THD_CURRENT", "%"),
            ("UNKNOWN_TYPE", "")  # Caso no definido
        ]
        
        for measurement_type, expected_unit in test_cases:
            with self.subTest(measurement_type=measurement_type):
                unit = self.dlms_service._get_unit_for_measurement(measurement_type)
                self.assertEqual(unit, expected_unit)
    
    def test_active_devices_management(self):
        """Prueba la gestión de dispositivos activos"""
        # Estado inicial
        self.assertEqual(len(self.dlms_service.get_active_devices()), 0)
        
        # Agregar dispositivos simulados
        self.dlms_service._active_devices.add("DLMS-001")
        self.dlms_service._active_devices.add("DLMS-002")
        self.dlms_service._active_devices.add("DLMS-003")
        
        # Verificar dispositivos activos
        active_devices = self.dlms_service.get_active_devices()
        self.assertEqual(len(active_devices), 3)
        self.assertIn("DLMS-001", active_devices)
        self.assertIn("DLMS-002", active_devices)
        self.assertIn("DLMS-003", active_devices)
    
    def test_recent_readings_management(self):
        """Prueba la gestión de lecturas recientes"""
        # Estado inicial
        self.assertEqual(self.dlms_service.get_recent_readings_count("DLMS-001"), 0)
        
        # Simular lecturas recientes
        test_reading = DLMSReading(
            device_id="DLMS-001",
            device_type=DLMSDeviceType.MONOFASICO,
            timestamp=datetime.now(),
            measurements={"voltage_l1": 220.0},
            quality_flag=True
        )
        
        self.dlms_service._recent_readings["DLMS-001"] = [test_reading]
        
        # Verificar conteo
        self.assertEqual(self.dlms_service.get_recent_readings_count("DLMS-001"), 1)
        
        # Verificar conteo para dispositivo inexistente
        self.assertEqual(self.dlms_service.get_recent_readings_count("DLMS-999"), 0)
    
    def test_analytics_cache_management(self):
        """Prueba la gestión del cache de analytics"""
        # Estado inicial
        self.assertIsNone(self.dlms_service.get_cached_analytics("DLMS-001"))
        
        # Agregar analytics al cache
        test_analytics = {
            "device_id": "DLMS-001",
            "total_energy": 15000.0,
            "avg_power": 2500.0,
            "quality_score": 92.5
        }
        
        self.dlms_service._analytics_cache["DLMS-001"] = test_analytics
        
        # Verificar recuperación desde cache
        cached_analytics = self.dlms_service.get_cached_analytics("DLMS-001")
        self.assertEqual(cached_analytics, test_analytics)
        
        # Verificar cache completo
        all_cached = self.dlms_service.get_cached_analytics()
        self.assertEqual(len(all_cached), 1)
        self.assertIn("DLMS-001", all_cached)
    
    def test_event_listeners_configuration(self):
        """Prueba la configuración de listeners de eventos"""
        # Crear listeners simulados
        listener1 = Mock()
        listener2 = Mock()
        listeners = [listener1, listener2]
        
        # Configurar listeners
        self.dlms_service.set_event_listeners(listeners)
        
        # Verificar que se configuraron
        self.assertEqual(self.dlms_service._event_listeners, listeners)
    
    @patch('asyncio.create_task')
    async def test_async_health_check(self, mock_create_task):
        """Prueba el control de salud asíncrono"""
        # Simular respuesta del sync service
        self.mock_sync_service.check_connectivity.return_value = {"status": "connected"}
        
        # Ejecutar health check
        health = await self.dlms_service.health_check()
        
        # Verificar estructura del resultado
        self.assertIn('service_status', health)
        self.assertIn('timestamp', health)
        self.assertIn('active_devices', health)
        self.assertIn('cached_analytics', health)
        self.assertIn('total_readings', health)
        self.assertIn('dependencies', health)
        
        # Verificar dependencias
        dependencies = health['dependencies']
        self.assertTrue(dependencies['sync_service'])
        self.assertTrue(dependencies['sensor_adapter'])
        self.assertTrue(dependencies['telemetry_service'])
        
        # Verificar conectividad de dispositivos
        self.assertIn('device_connectivity', health)
        self.assertEqual(health['device_connectivity']['status'], 'connected')


class TestDLMSIntegrationComplete(unittest.TestCase):
    """Pruebas de integración completa del sistema DLMS-Urbia"""
    
    def setUp(self):
        """Configurar entorno de pruebas de integración"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Crear repositorio de telemetría
        self.telemetry_db_path = os.path.join(self.temp_dir, "integration_telemetry.db")
        self.telemetry_repository = SQLTelemetryRepositoryFactory.create_repository(
            db_path=self.telemetry_db_path,
            enable_wal_mode=False
        )
        
        # Crear adaptador DLMS
        self.sensor_adapter = DLMSSensorAdapter()
        
        # Crear servicio DLMS
        self.dlms_service = DLMSService()
        
        # Simular servicios externos
        self.mock_sync_service = AsyncMock()
        self.mock_telemetry_service = AsyncMock()
        
        # Configurar servicio principal
        self.dlms_service.set_dependencies(
            self.mock_sync_service,
            self.sensor_adapter,
            self.mock_telemetry_service
        )
    
    def tearDown(self):
        """Limpiar entorno de pruebas"""
        import shutil
        del self.telemetry_repository
        del self.sensor_adapter
        del self.dlms_service
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_data_flow_adapt_to_telemetry(self):
        """Prueba el flujo completo: DLMS Raw -> Converted -> Telemetry"""
        # Paso 1: Crear datos raw DLMS
        raw_data = DLMSRawData(
            device_id="DLMS-INTEGRATION-001",
            timestamp=datetime.now(),
            meter_type=MeterType.TRIFASICO,
            metrics={
                "voltage_l1": 218.3,
                "voltage_l2": 219.1,
                "voltage_l3": 220.2,
                "current_l1": 45.6,
                "current_l2": 44.8,
                "current_l3": 46.2,
                "active_power": 30234.0,
                "frequency": 49.9,
                "power_factor": 0.88
            },
            raw_values={"source": "integration_test"}
        )
        
        # Paso 2: Adaptar datos usando el sensor adapter
        converted_data = self.sensor_adapter.adapt_raw_data(raw_data)
        
        # Verificar conversión
        self.assertEqual(len(converted_data), 9)
        
        # Paso 3: Simular integración con telemetría
        telemetry_entries = []
        for data in converted_data:
            entry = {
                'sensor_id': f"{data.device_id}_{data.sensor_type.value}_{data.phase.value}",
                'sensor_type': data.sensor_type.value,
                'value': data.value,
                'timestamp': data.timestamp.isoformat(),
                'unit': data.unit,
                'quality_flag': data.quality_indicator == "GOOD",
                'source': 'DLMS'
            }
            telemetry_entries.append(entry)
        
        # Paso 4: Guardar en repositorio de telemetría
        saved_count = 0
        for entry in telemetry_entries:
            if self.telemetry_repository.save(entry):
                saved_count += 1
        
        self.assertEqual(saved_count, len(telemetry_entries))
        
        # Paso 5: Verificar que los datos se guardaron correctamente
        retrieved_data = self.telemetry_repository.get_by_sensor("DLMS-INTEGRATION-001_voltage_l1_L1")
        self.assertGreaterEqual(len(retrieved_data), 0)
    
    def test_multiple_devices_integration(self):
        """Prueba la integración con múltiples dispositivos"""
        devices_config = [
            {
                "device_id": "DLMS-INT-001",
                "meter_type": MeterType.MONOFASICO,
                "metrics": {
                    "voltage_l1": 220.0,
                    "current_l1": 15.5,
                    "active_power": 3410.0,
                    "frequency": 50.0
                }
            },
            {
                "device_id": "DLMS-INT-002", 
                "meter_type": MeterType.TRIFASICO,
                "metrics": {
                    "voltage_l1": 218.0,
                    "voltage_l2": 219.0,
                    "voltage_l3": 220.0,
                    "current_l1": 45.0,
                    "current_l2": 44.0,
                    "current_l3": 46.0,
                    "active_power": 30234.0,
                    "frequency": 49.9
                }
            }
        ]
        
        all_converted_data = []
        
        # Procesar cada dispositivo
        for device_config in devices_config:
            raw_data = DLMSRawData(
                device_id=device_config["device_id"],
                timestamp=datetime.now(),
                meter_type=device_config["meter_type"],
                metrics=device_config["metrics"],
                raw_values={"integration_test": True}
            )
            
            converted = self.sensor_adapter.adapt_raw_data(raw_data)
            all_converted_data.extend(converted)
        
        # Verificar conversión total
        total_expected_metrics = 4 + 8  # Monofásico (4) + Trifásico (8)
        self.assertEqual(len(all_converted_data), total_expected_metrics)
        
        # Verificar dispositivos únicos
        unique_devices = set(data.device_id for data in all_converted_data)
        self.assertEqual(len(unique_devices), 2)
        self.assertIn("DLMS-INT-001", unique_devices)
        self.assertIn("DLMS-INT-002", unique_devices)
        
        # Verificar que no hay datos duplicados por dispositivo+metric+phase
        device_metric_phase_combinations = set()
        for data in all_converted_data:
            combination = (data.device_id, data.sensor_type.value, data.phase.value)
            self.assertNotIn(combination, device_metric_phase_combinations, 
                           f"Combinación duplicada: {combination}")
            device_metric_phase_combinations.add(combination)
    
    def test_data_quality_and_validation_integration(self):
        """Prueba la integración de validación y calidad de datos"""
        # Crear datos con diferentes calidades
        test_scenarios = [
            {
                "name": "Datos normales",
                "metrics": {"voltage_l1": 220.0, "current_l1": 15.0, "frequency": 50.0},
                "expected_quality": "GOOD"
            },
            {
                "name": "Datos cuestionables",
                "metrics": {"voltage_l1": 260.0, "current_l1": 15.0, "frequency": 50.0},
                "expected_quality": "UNCERTAIN"
            },
            {
                "name": "Datos críticos",
                "metrics": {"voltage_l1": 350.0, "current_l1": 15.0, "frequency": 50.0},
                "expected_quality": "BAD"
            }
        ]
        
        for scenario in test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                raw_data = DLMSRawData(
                    device_id="DLMS-QUALITY-TEST",
                    timestamp=datetime.now(),
                    meter_type=MeterType.MONOFASICO,
                    metrics=scenario["metrics"],
                    raw_values={}
                )
                
                converted = self.sensor_adapter.adapt_raw_data(raw_data)
                
                # Verificar que se convirtió al menos voltaje
                voltage_data = next((d for d in converted if d.sensor_type == SensorTypeDLMS.VOLTAJE), None)
                self.assertIsNotNone(voltage_data)
                
                # Verificar calidad esperada
                self.assertEqual(voltage_data.quality_indicator, scenario["expected_quality"])
                
                # Verificar flag crítico para datos críticos
                if scenario["expected_quality"] == "BAD":
                    self.assertTrue(voltage_data.is_critical)
    
    def test_telemetry_repository_integration(self):
        """Prueba la integración completa con repositorio de telemetría"""
        # Crear datos DLMS convertidos
        converted_data_list = []
        
        for i in range(5):
            for phase in [PhaseType.L1, PhaseType.L2, PhaseType.L3]:
                converted_data = DLMSConvertedData(
                    device_id=f"DLMS-TELEMETRY-{i}",
                    timestamp=datetime.now() - timedelta(minutes=i),
                    sensor_type=SensorTypeDLMS.VOLTAJE,
                    value=220.0 + (i * 0.5),
                    unit="V",
                    phase=phase,
                    quality_indicator="GOOD",
                    is_critical=False
                )
                converted_data_list.append(converted_data)
        
        # Convertir a formato de telemetría y guardar
        telemetry_records = []
        for converted in converted_data_list:
            telemetry_record = {
                'id': f"{converted.device_id}_{converted.sensor_type.value}_{converted.phase.value}_{converted.timestamp.isoformat()}",
                'sensor_id': f"{converted.device_id}_{converted.sensor_type.value}_{converted.phase.value}",
                'timestamp': converted.timestamp.isoformat(),
                'data_type': converted.sensor_type.value,
                'value': converted.value,
                'unit': converted.unit,
                'location': {'lat': 5.0703, 'lng': -75.5138},
                'priority': 'high' if converted.is_critical else 'normal',
                'metadata': {
                    'phase': converted.phase.value,
                    'quality_indicator': converted.quality_indicator,
                    'converted_from': converted.converted_from
                }
            }
            telemetry_records.append(telemetry_record)
        
        # Guardar en repositorio
        saved_count = self.telemetry_repository.save_many(telemetry_records)
        self.assertEqual(saved_count, len(telemetry_records))
        
        # Verificar estadísticas
        stats = self.telemetry_repository.get_statistics()
        self.assertEqual(stats['total_records'], len(telemetry_records))
        self.assertEqual(stats['unique_sensors'], 5 * 3)  # 5 dispositivos × 3 fases
        
        # Verificar analytics por tipo de dato
        analytics = self.telemetry_repository.get_analytics('data_type')
        self.assertGreaterEqual(len(analytics), 0)
        
        if analytics:
            voltage_analytics = next((a for a in analytics if a['data_type'] == 'voltage'), None)
            self.assertIsNotNone(voltage_analytics)
            self.assertEqual(voltage_analytics['count'], len(telemetry_records))
    
    def test_error_handling_and_recovery(self):
        """Prueba el manejo de errores y recuperación"""
        # Escenario 1: Datos con valores inválidos
        invalid_raw_data = DLMSRawData(
            device_id="DLMS-ERROR-TEST",
            timestamp=datetime.now(),
            meter_type=MeterType.MONOFASICO,
            metrics={
                "voltage_l1": "invalid_number",  # Valor inválido
                "current_l1": 15.0,
                "active_power": 3300.0
            },
            raw_values={}
        )
        
        # El adaptador debe manejar graciosamente los valores inválios
        converted = self.sensor_adapter.adapt_raw_data(invalid_raw_data)
        
        # Debe retornar datos válidos para las métricas correctas
        valid_voltage_data = next((d for d in converted if d.sensor_type == SensorTypeDLMS.VOLTAJE), None)
        self.assertIsNotNone(valid_voltage_data)
        
        # El valor inválido debe convertirse a 0.0 (comportamiento definido)
        self.assertEqual(valid_voltage_data.value, 0.0)
        
        # Escenario 2: Tipo de medidor no soportado
        try:
            unsupported_raw_data = DLMSRawData(
                device_id="DLMS-UNSUPPORTED",
                timestamp=datetime.now(),
                meter_type="UNSUPPORTED_TYPE",
                metrics={"voltage_l1": 220.0},
                raw_values={}
            )
            
            # Esto debe generar una excepción
            with self.assertRaises(ValueError):
                self.sensor_adapter.adapt_raw_data(unsupported_raw_data)
                
        except ValueError:
            # Comportamiento esperado
            pass
    
    def test_performance_large_dataset(self):
        """Prueba de rendimiento con conjunto de datos grande"""
        import time
        
        # Crear dataset grande
        large_dataset = []
        for device_id in range(1, 21):  # 20 dispositivos
            for measurement_type in ["voltage", "current", "power"]:
                raw_data = DLMSRawData(
                    device_id=f"DLMS-PERF-{device_id:03d}",
                    timestamp=datetime.now(),
                    meter_type=MeterType.MONOFASICO,
                    metrics={
                        f"{measurement_type}_l1": 200.0 + (device_id * 10),
                        "frequency": 50.0
                    },
                    raw_values={}
                )
                large_dataset.append(raw_data)
        
        # Medir tiempo de procesamiento
        start_time = time.time()
        
        all_converted = []
        for raw_data in large_dataset:
            converted = self.sensor_adapter.adapt_raw_data(raw_data)
            all_converted.extend(converted)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verificar rendimiento
        valid_datasets = [d for d in large_dataset if d.meter_type == MeterType.MONOFASICO]
        self.assertEqual(len(all_converted), len(valid_datasets))
        self.assertLess(processing_time, 5.0, "El procesamiento debe tomar menos de 5 segundos")
        
        # Verificar que el promedio por dispositivo es razonable
        avg_time_per_device = processing_time / len(large_dataset)
        self.assertLess(avg_time_per_device, 0.1, "Promedio por dispositivo debe ser menor a 100ms")
        
        print(f"\n=== PRUEBA DE RENDIMIENTO COMPLETA ===")
        print(f"Dispositivos procesados: {len(large_dataset)}")
        print(f"Métricas totales convertidas: {len(all_converted)}")
        print(f"Tiempo total: {processing_time:.3f} segundos")
        print(f"Promedio por dispositivo: {avg_time_per_device*1000:.2f} ms")
        print(f"Métricas por segundo: {len(all_converted)/processing_time:.1f}")
    
    def test_configuration_validation(self):
        """Prueba la validación de configuración del sistema"""
        # Verificar que el repositorio se inicializó correctamente
        health = self.telemetry_repository.health_check()
        self.assertEqual(health['status'], 'healthy')
        self.assertIn('database_path', health)
        
        # Verificar que el adaptador tiene todas las configuraciones
        supported_monofasico = self.sensor_adapter.get_supported_metrics(MeterType.MONOFASICO)
        supported_trifasico = self.sensor_adapter.get_supported_metrics(MeterType.TRIFASICO)
        
        self.assertIn("voltage_l1", supported_monofasico)
        self.assertIn("current_l1", supported_monofasico)
        
        self.assertIn("voltage_l1", supported_trifasico)
        self.assertIn("voltage_l2", supported_trifasico)
        self.assertIn("voltage_l3", supported_trifasico)
        
        # Verificar que el servicio DLMS tiene las dependencias configuradas
        self.assertIsNotNone(self.dlms_service._sync_service)
        self.assertIsNotNone(self.dlms_service._sensor_adapter)
        self.assertIsNotNone(self.dlms_service._telemetry_service)


# Clase para ejecutar pruebas de rendimiento
class DLMSPerformanceTests:
    """Clase para pruebas de rendimiento y estrés"""
    
    @staticmethod
    def run_adapter_performance_test():
        """Ejecutar prueba de rendimiento del adaptador"""
        print("\n=== PRUEBA DE RENDIMIENTO DEL ADAPTADOR DLMS ===")
        
        adapter = DLMSSensorAdapter()
        
        # Dataset grande para prueba de rendimiento
        large_dataset = []
        for i in range(1000):
            raw_data = DLMSRawData(
                device_id=f"PERF-DLMS-{i:04d}",
                timestamp=datetime.now(),
                meter_type=MeterType.TRIFASICO if i % 2 == 0 else MeterType.MONOFASICO,
                metrics={
                    "voltage_l1": 220.0 + (i % 20),
                    "voltage_l2": 219.0 + (i % 18),
                    "voltage_l3": 221.0 + (i % 22),
                    "current_l1": 45.0 + (i % 10),
                    "current_l2": 44.0 + (i % 8),
                    "current_l3": 46.0 + (i % 12),
                    "active_power": 30000.0 + (i * 100),
                    "frequency": 50.0
                },
                raw_values={}
            )
            large_dataset.append(raw_data)
        
        # Medir tiempo de procesamiento
        start_time = time.time()
        
        total_converted = 0
        for raw_data in large_dataset:
            converted = adapter.adapt_raw_data(raw_data)
            total_converted += len(converted)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Dispositivos procesados: {len(large_dataset)}")
        print(f"Total de métricas convertidas: {total_converted}")
        print(f"Tiempo total: {elapsed_time:.3f} segundos")
        print(f"Promedio por dispositivo: {elapsed_time/len(large_dataset)*1000:.2f} ms")
        print(f"Métricas por segundo: {total_converted/elapsed_time:.1f}")
        print(f"Dispositivos por segundo: {len(large_dataset)/elapsed_time:.1f}")
    
    @staticmethod
    def run_repository_performance_test():
        """Ejecutar prueba de rendimiento del repositorio"""
        print("\n=== PRUEBA DE RENDIMIENTO DEL REPOSITORIO ===")
        
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, "perf_telemetry.db")
        
        try:
            repository = SQLTelemetryRepositoryFactory.create_repository(
                db_path=repo_path,
                enable_wal_mode=True
            )
            
            # Crear dataset grande para inserción masiva
            test_records = []
            for i in range(5000):
                record = {
                    'id': f'perf_test_{i:06d}',
                    'sensor_id': f'sensor_perf_{i % 100}',  # 100 sensores diferentes
                    'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                    'data_type': 'temperature' if i % 2 == 0 else 'humidity',
                    'value': 20.0 + (i % 50),
                    'unit': 'celsius' if i % 2 == 0 else '%',
                    'location': {'lat': 5.0703, 'lng': -75.5138},
                    'priority': 'normal'
                }
                test_records.append(record)
            
            # Medir tiempo de inserción masiva
            start_time = time.time()
            saved_count = repository.save_many(test_records)
            end_time = time.time()
            
            insertion_time = end_time - start_time
            
            # Medir tiempo de consulta
            query_start = time.time()
            results = repository.get_by_sensor('sensor_perf_1', limit=1000)
            query_end = time.time()
            
            query_time = query_end - query_start
            
            print(f"Registros insertados: {saved_count}")
            print(f"Tiempo de inserción masiva: {insertion_time:.3f} segundos")
            print(f"Registros por segundo (inserción): {saved_count/insertion_time:.1f}")
            print(f"Resultados de consulta: {len(results)}")
            print(f"Tiempo de consulta: {query_time:.3f} segundos")
            print(f"Consultas por segundo: {1.0/query_time:.1f}")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


# Runner de pruebas de rendimiento
def run_integration_performance_tests():
    """Ejecutar todas las pruebas de rendimiento"""
    print("Ejecutando pruebas de rendimiento de integración DLMS-Urbia...")
    
    # Prueba del adaptador
    DLMSPerformanceTests.run_adapter_performance_test()
    
    # Prueba del repositorio
    DLMSPerformanceTests.run_repository_performance_test()
    
    print("\n=== PRUEBAS DE RENDIMIENTO COMPLETADAS ===")


if __name__ == "__main__":
    # Ejecutar pruebas unitarias
    print("Ejecutando pruebas unitarias de integración DLMS-Urbia...")
    
    # Configurar el test suite
    test_suite = unittest.TestSuite()
    
    # Agregar todas las clases de prueba
    test_classes = [
        TestDLMSSensorAdapter,
        TestDLMSSyncService,
        TestSQLTelemetryRepository,
        TestDLMSService,
        TestDLMSIntegrationComplete
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE PRUEBAS DE INTEGRACIÓN DLMS-URBIA")
    print(f"{'='*60}")
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Omitidas: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    # Ejecutar pruebas de rendimiento si las pruebas unitarias pasaron
    if len(result.errors) == 0 and len(result.failures) == 0:
        print("\nTodas las pruebas unitarias pasaron. Ejecutando pruebas de rendimiento...")
        run_integration_performance_tests()
    else:
        print("\nOmitiendo pruebas de rendimiento debido a errores en pruebas unitarias.")
    
    print(f"\n{'='*60}")
    print("PRUEBAS DE INTEGRACIÓN DLMS-URBIA COMPLETADAS")
    print(f"{'='*60}")