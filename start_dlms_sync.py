#!/usr/bin/env python3
"""
Script de Inicio para Sincronización DLMS - Sistema Urbia
========================================================

Script principal para inicializar y ejecutar el servicio de sincronización DLMS
con soporte para múltiples modos de operación y manejo robusto de errores.

Modos disponibles:
- auto: Sincronización automática continua
- manual: Sincronización manual única
- historical: Sincronización de datos históricos

Autor: Sistema Urbia
Fecha: 2025-11-06
"""

import argparse
import asyncio
import logging
import os
import sys
import signal
import traceback
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Agregar el directorio src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.sync.dlms_sync_service import (
    DLMSSyncService,
    SyncConfiguration,
    create_dlms_sync_service,
    SyncStatus
)
from src.infrastructure.sync.dlms_sync_utils import DLMSConfigManager


class DLMSStartupError(Exception):
    """Excepción personalizada para errores de inicio del servicio DLMS"""
    pass


class DLMSStartScript:
    """Script principal para iniciar el servicio de sincronización DLMS"""
    
    def __init__(self):
        self.config_path = Path("config/settings_dlms.yaml")
        self.logs_dir = Path("logs")
        self.service: Optional[DLMSSyncService] = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar sistema de logging"""
        self.logs_dir.mkdir(exist_ok=True)
        
        log_file = self.logs_dir / f"dlms_sync_startup_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Sistema de logging inicializado")
    
    def load_config(self, config_file: Optional[Path] = None) -> Dict[str, Any]:
        """Cargar configuración desde archivo YAML"""
        config_path = config_file or self.config_path
        
        if not config_path.exists():
            raise DLMSStartupError(f"Archivo de configuración no encontrado: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Configuración cargada desde: {config_path}")
            return config
            
        except yaml.YAMLError as e:
            raise DLMSStartupError(f"Error cargando configuración YAML: {e}")
        except Exception as e:
            raise DLMSStartupError(f"Error leyendo archivo de configuración: {e}")
    
    def get_sync_config_from_yaml(self, config: Dict[str, Any]) -> SyncConfiguration:
        """Convertir configuración YAML a SyncConfiguration"""
        try:
            # Extraer configuración de ThingsBoard
            tb_config = config.get('thingsboard', {})
            sync_config = config.get('sync', {})
            
            # Crear configuración del servicio
            service_config = SyncConfiguration(
                thingsboard_host="192.168.46.124",  # Default desde código existente
                thingsboard_port=5432,
                thingsboard_database="thingsboard",
                thingsboard_user="postgres",
                thingsboard_password=os.getenv('THINGSBOARD_DB_PASSWORD', ''),
                
                # Configuraciones desde YAML
                sync_interval_minutes=sync_config.get('intervals', {}).get('telemetry_normal', 300) // 60,
                batch_size=tb_config.get('payload', {}).get('batch_size', 100),
                max_workers=5,
                retention_days=config.get('database', {}).get('retention', {}).get('days', 365),
                enable_partition_handling=True
            )
            
            self.logger.info("Configuración del servicio creada desde YAML")
            return service_config
            
        except Exception as e:
            self.logger.error(f"Error creando configuración desde YAML: {e}")
            # Fallback a configuración por defecto
            return SyncConfiguration()
    
    def validate_environment(self):
        """Validar variables de entorno requeridas"""
        required_vars = ['THINGSBOARD_DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.logger.error(f"Variables de entorno faltantes: {missing_vars}")
            self.logger.info("Ejemplo de configuración:")
            self.logger.info("export THINGSBOARD_DB_PASSWORD='tu_password'")
            raise DLMSStartupError(f"Variables de entorno requeridas: {missing_vars}")
        
        self.logger.info("Variables de entorno validadas correctamente")
    
    async def run_auto_mode(self, config: Dict[str, Any]):
        """Ejecutar modo automático - sincronización continua"""
        self.logger.info("Iniciando modo AUTOMÁTICO de sincronización DLMS")
        
        try:
            service_config = self.get_sync_config_from_yaml(config)
            self.service = DLMSSyncService(service_config)
            
            # Configurar manejo de señales para parada limpia
            def signal_handler(signum, frame):
                self.logger.info(f"Señal recibida: {signum}")
                asyncio.create_task(self.shutdown())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Iniciar servicio
            await self.service.start()
            self.logger.info("Servicio automático iniciado correctamente")
            self.logger.info("Modo: Sincronización automática continua")
            self.logger.info(f"Intervalo: {service_config.sync_interval_minutes} minutos")
            
            # Mantener servicio activo
            try:
                while True:
                    await asyncio.sleep(60)  # Verificar cada minuto
                    
                    # Log de estado cada 10 minutos
                    status = self.service.get_status()
                    if status.get('status') == SyncStatus.RUNNING.value:
                        self.logger.debug(f"Estado del servicio: {status['status']}")
                        
            except KeyboardInterrupt:
                self.logger.info("Interrupción de teclado detectada")
            except Exception as e:
                self.logger.error(f"Error en modo automático: {e}")
                raise
                
        except Exception as e:
            self.logger.error(f"Error ejecutando modo automático: {e}")
            raise DLMSStartupError(f"Fallo en modo automático: {e}")
    
    async def run_manual_mode(self, config: Dict[str, Any]):
        """Ejecutar modo manual - sincronización única"""
        self.logger.info("Iniciando modo MANUAL de sincronización DLMS")
        
        try:
            service_config = self.get_sync_config_from_yaml(config)
            self.service = DLMSSyncService(service_config)
            
            # Crear instancia temporal para sincronización manual
            temp_service = create_dlms_sync_service({
                'thingsboard_host': service_config.thingsboard_host,
                'thingsboard_port': service_config.thingsboard_port,
                'thingsboard_database': service_config.thingsboard_database,
                'thingsboard_user': service_config.thingsboard_user,
                'thingsboard_password': service_config.thingsboard_password,
                'batch_size': service_config.batch_size,
                'sync_interval_minutes': service_config.sync_interval_minutes
            })
            
            # Conectar y ejecutar sincronización
            await temp_service.start()
            
            self.logger.info("Ejecutando sincronización manual...")
            result = await temp_service.manual_sync()
            
            # Mostrar resultados
            self.logger.info("=== RESULTADOS SINCRONIZACIÓN MANUAL ===")
            self.logger.info(f"Éxito: {result.get('success')}")
            self.logger.info(f"Duración: {result.get('duration_seconds', 0):.2f} segundos")
            self.logger.info(f"Registros procesados: {result.get('records_processed', 0)}")
            self.logger.info(f"Particiones procesadas: {result.get('partitions_processed', [])}")
            self.logger.info(f"Timestamp: {result.get('timestamp')}")
            
            if not result.get('success'):
                self.logger.error(f"Error en sincronización: {result.get('error')}")
            
            await temp_service.stop()
            
        except Exception as e:
            self.logger.error(f"Error ejecutando modo manual: {e}")
            self.logger.error(traceback.format_exc())
            raise DLMSStartupError(f"Fallo en modo manual: {e}")
    
    async def run_historical_mode(self, config: Dict[str, Any], 
                                 start_date: str, end_date: Optional[str] = None):
        """Ejecutar modo histórico - sincronización de datos históricos"""
        self.logger.info("Iniciando modo HISTÓRICO de sincronización DLMS")
        
        try:
            # Validar fechas
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise DLMSStartupError(f"Formato de fecha inválido: {start_date}")
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    raise DLMSStartupError(f"Formato de fecha inválido: {end_date}")
            else:
                end_dt = datetime.now()
            
            self.logger.info(f"Rango de fechas: {start_dt} hasta {end_dt}")
            
            service_config = self.get_sync_config_from_yaml(config)
            self.service = DLMSSyncService(service_config)
            
            # Crear instancia temporal para sincronización histórica
            temp_service = create_dlms_sync_service({
                'thingsboard_host': service_config.thingsboard_host,
                'thingsboard_port': service_config.thingsboard_port,
                'thingsboard_database': service_config.thingsboard_database,
                'thingsboard_user': service_config.thingsboard_user,
                'thingsboard_password': service_config.thingsboard_password,
                'batch_size': service_config.batch_size // 2,  # Lotes más pequeños para histórico
                'sync_interval_minutes': service_config.sync_interval_minutes
            })
            
            await temp_service.start()
            
            # Ejecutar sincronización histórica por particiones
            self.logger.info("Ejecutando sincronización histórica...")
            
            # Obtener particiones en el rango de fechas
            partitions = temp_service.extractor.get_partition_list()
            historical_partitions = []
            
            for partition in partitions:
                # Filtrar particiones por fecha (formato ts_kv_YYYY_MM)
                try:
                    parts = partition.split('_')
                    if len(parts) >= 4:
                        year = int(parts[2])
                        month = int(parts[3])
                        partition_date = datetime(year, month, 1)
                        
                        if start_dt <= partition_date <= end_dt:
                            historical_partitions.append(partition)
                except (ValueError, IndexError):
                    continue
            
            self.logger.info(f"Particiones históricas encontradas: {historical_partitions}")
            
            # Procesar cada partición histórica
            total_records = 0
            processed_partitions = []
            
            for partition in historical_partitions:
                self.logger.info(f"Procesando partición histórica: {partition}")
                
                # Sincronizar con filtro de fecha
                result = await temp_service.extractor.extract_dlms_data(
                    partition, 
                    last_sync=start_dt
                )
                
                total_records += len(result)
                processed_partitions.append(partition)
                
                self.logger.info(f"Registros en {partition}: {len(result)}")
                
                # Pequeña pausa entre particiones
                await asyncio.sleep(2)
            
            # Convertir datos
            converted_data = []
            for partition in processed_partitions:
                records = await temp_service.extractor.extract_dlms_data(
                    partition, 
                    last_sync=start_dt
                )
                
                for record in records:
                    converted = temp_service.converter.convert_to_urbia_format(record)
                    converted_data.append(converted)
            
            # Almacenar resultados
            await temp_service._store_converted_data(converted_data)
            
            await temp_service.stop()
            
            # Mostrar resultados
            self.logger.info("=== RESULTADOS SINCRONIZACIÓN HISTÓRICA ===")
            self.logger.info(f"Registros totales procesados: {total_records}")
            self.logger.info(f"Particiones procesadas: {processed_partitions}")
            self.logger.info(f"Rango de fechas: {start_dt} - {end_dt}")
            self.logger.info(f"Datos convertidos: {len(converted_data)}")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando modo histórico: {e}")
            self.logger.error(traceback.format_exc())
            raise DLMSStartupError(f"Fallo en modo histórico: {e}")
    
    async def run_status_mode(self):
        """Mostrar estado del servicio"""
        if not self.service:
            self.logger.info("No hay servicio activo para mostrar estado")
            return
        
        try:
            status = self.service.get_status()
            stats = self.service.get_sync_statistics()
            
            self.logger.info("=== ESTADO DEL SERVICIO DLMS ===")
            self.logger.info(f"Estado: {status.get('status')}")
            self.logger.info(f"Última sincronización: {status.get('last_sync_time')}")
            self.logger.info(f"En ejecución: {status.get('is_running')}")
            
            self.logger.info("--- Configuración ---")
            config_info = status.get('configuration', {})
            for key, value in config_info.items():
                self.logger.info(f"{key}: {value}")
            
            self.logger.info("--- Estadísticas ---")
            for key, value in stats.items():
                self.logger.info(f"{key}: {value}")
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estado: {e}")
    
    async def shutdown(self):
        """Cerrar servicio de manera segura"""
        self.logger.info("Iniciando cierre seguro del servicio...")
        
        if self.service:
            try:
                await self.service.stop()
                self.logger.info("Servicio detenido correctamente")
            except Exception as e:
                self.logger.error(f"Error cerrando servicio: {e}")
        
        self.logger.info("Cierre completado")


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Script de inicio para sincronización DLMS - Sistema Urbia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  Modo automático (sincronización continua):
    python start_dlms_sync.py auto

  Modo manual (sincronización única):
    python start_dlms_sync.py manual

  Modo histórico (rango de fechas):
    python start_dlms_sync.py historical --start-date 2024-11-01T00:00:00 --end-date 2024-11-30T23:59:59

  Mostrar estado del servicio:
    python start_dlms_sync.py status

Variables de entorno requeridas:
  THINGSBOARD_DB_PASSWORD    Contraseña para PostgreSQL de ThingsBoard

Configuración:
  config/settings_dlms.yaml   Archivo de configuración principal
        """
    )
    
    # Argumentos globales
    parser.add_argument('--config', type=Path, help='Archivo de configuración alternativo')
    parser.add_argument('--verbose', '-v', action='store_true', help='Activar logging detallado')
    parser.add_argument('--dry-run', action='store_true', help='Ejecutar en modo prueba sin cambios')
    
    # Subcomandos
    subparsers = parser.add_subparsers(dest='command', help='Modos de operación')
    
    # Modo automático
    auto_parser = subparsers.add_parser('auto', help='Ejecutar sincronización automática continua')
    
    # Modo manual
    manual_parser = subparsers.add_parser('manual', help='Ejecutar sincronización manual única')
    
    # Modo histórico
    historical_parser = subparsers.add_parser('historical', help='Ejecutar sincronización de datos históricos')
    historical_parser.add_argument('--start-date', required=True, 
                                 help='Fecha de inicio (formato ISO: 2024-11-01T00:00:00)')
    historical_parser.add_argument('--end-date', 
                                 help='Fecha de fin (formato ISO: 2024-11-30T23:59:59)')
    
    # Modo estado
    status_parser = subparsers.add_parser('status', help='Mostrar estado del servicio')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configurar logging detallado si se solicita
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear instancia del script de inicio
    startup_script = DLMSStartScript()
    
    try:
        # Validar entorno
        startup_script.validate_environment()
        
        # Cargar configuración
        config = startup_script.load_config(args.config)
        
        # Ejecutar según el modo solicitado
        if args.command == 'auto':
            if args.dry_run:
                startup_script.logger.info("Modo prueba activado - no se ejecutarán cambios")
                return 0
            
            asyncio.run(startup_script.run_auto_mode(config))
            
        elif args.command == 'manual':
            if args.dry_run:
                startup_script.logger.info("Modo prueba activado - no se ejecutarán cambios")
                return 0
            
            asyncio.run(startup_script.run_manual_mode(config))
            
        elif args.command == 'historical':
            if args.dry_run:
                startup_script.logger.info("Modo prueba activado - no se ejecutarán cambios")
                return 0
            
            asyncio.run(startup_script.run_historical_mode(
                config, args.start_date, args.end_date
            ))
            
        elif args.command == 'status':
            asyncio.run(startup_script.run_status_mode())
        
        return 0
        
    except DLMSStartupError as e:
        startup_script.logger.error(f"Error de inicio DLMS: {e}")
        return 1
    except KeyboardInterrupt:
        startup_script.logger.info("Script interrumpido por el usuario")
        return 0
    except Exception as e:
        startup_script.logger.error(f"Error inesperado: {e}")
        startup_script.logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)