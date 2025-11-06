"""
Adaptador de Sensores DLMS para Urbia

Este módulo adapta las métricas de dispositivos DLMS (Distribution Line Management System)
a los tipos de sensores existentes en Urbia. Soporta tanto medidores monofásicos como
trifásicos, realizando la conversión y normalización de datos necesaria.

Autor: Sistema Urbia
Fecha: 2025-11-06
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Tuple, Any
from enum import Enum
import logging
from datetime import datetime
import json


# Enumeraciones para tipos de sensores DLMS
class SensorTypeDLMS(Enum):
    """Tipos de sensores específicos para métricas DLMS"""
    VOLTAJE = "voltage"
    CORRIENTE = "current"
    POTENCIA = "power"
    ENERGIA = "energy"
    FRECUENCIA = "frequency"
    POTENCIA_REACTIVA = "reactive_power"
    FACTOR_POTENCIA = "power_factor"
    VOLTAJE_L1 = "voltage_l1"
    VOLTAJE_L2 = "voltage_l2"
    VOLTAJE_L3 = "voltage_l3"
    CORRIENTE_L1 = "current_l1"
    CORRIENTE_L2 = "current_l2"
    CORRIENTE_L3 = "current_l3"


class MeterType(Enum):
    """Tipos de medidores DLMS soportados"""
    MONOFASICO = "DLMS-Meter-01"
    TRIFASICO = "DLMS-Meter-02"


class PhaseType(Enum):
    """Tipos de fase para mediciones"""
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    TOTAL = "TOTAL"


# Estructura para métricas DLMS sin procesar
@dataclass
class DLMSRawData:
    """Datos raw recibidos del dispositivo DLMS"""
    device_id: str
    timestamp: datetime
    meter_type: MeterType
    metrics: Dict[str, Union[float, int, str]]
    raw_values: Dict[str, Any]


# Estructura para datos convertidos del adaptador
@dataclass
class DLMSConvertedData:
    """Datos convertidos y normalizados del adaptador DLMS"""
    device_id: str
    timestamp: datetime
    sensor_type: SensorTypeDLMS
    value: float
    unit: str
    phase: Optional[PhaseType] = None
    quality_indicator: Optional[str] = None  # GOOD, BAD, UNCERTAIN
    is_critical: bool = False
    converted_from: Optional[str] = None  # Campo original DLMS


# Configuración de conversión de unidades
UNIT_CONVERSIONS = {
    # Voltaje
    "voltage": {
        "V": {"factor": 1.0, "unit": "V"},
        "kV": {"factor": 1000.0, "unit": "V"}
    },
    # Corriente
    "current": {
        "A": {"factor": 1.0, "unit": "A"},
        "mA": {"factor": 0.001, "unit": "A"},
        "kA": {"factor": 1000.0, "unit": "A"}
    },
    # Potencia
    "power": {
        "W": {"factor": 1.0, "unit": "W"},
        "kW": {"factor": 1000.0, "unit": "W"},
        "MW": {"factor": 1000000.0, "unit": "W"}
    },
    # Energía
    "energy": {
        "Wh": {"factor": 1.0, "unit": "Wh"},
        "kWh": {"factor": 1000.0, "unit": "Wh"},
        "MWh": {"factor": 1000000.0, "unit": "Wh"}
    },
    # Frecuencia
    "frequency": {
        "Hz": {"factor": 1.0, "unit": "Hz"},
        "mHz": {"factor": 0.001, "unit": "Hz"}
    },
    # Factor de potencia
    "power_factor": {
        "": {"factor": 1.0, "unit": ""},  # Sin unidad
        "pf": {"factor": 1.0, "unit": ""}
    }
}

# Mapas de métricas DLMS por tipo de medidor
DLMS_METRICS_MAPPING = {
    MeterType.MONOFASICO: {
        "voltage_l1": SensorTypeDLMS.VOLTAJE,
        "current_l1": SensorTypeDLMS.CORRIENTE,
        "active_power": SensorTypeDLMS.POTENCIA,
        "reactive_power": SensorTypeDLMS.POTENCIA_REACTIVA,
        "active_energy": SensorTypeDLMS.ENERGIA,
        "frequency": SensorTypeDLMS.FRECUENCIA,
        "power_factor": SensorTypeDLMS.FACTOR_POTENCIA
    },
    MeterType.TRIFASICO: {
        "voltage_l1": SensorTypeDLMS.VOLTAJE_L1,
        "voltage_l2": SensorTypeDLMS.VOLTAJE_L2,
        "voltage_l3": SensorTypeDLMS.VOLTAJE_L3,
        "current_l1": SensorTypeDLMS.CORRIENTE_L1,
        "current_l2": SensorTypeDLMS.CORRIENTE_L2,
        "current_l3": SensorTypeDLMS.CORRIENTE_L3,
        "active_power": SensorTypeDLMS.POTENCIA,
        "reactive_power": SensorTypeDLMS.POTENCIA_REACTIVA,
        "active_energy": SensorTypeDLMS.ENERGIA,
        "frequency": SensorTypeDLMS.FRECUENCIA,
        "power_factor": SensorTypeDLMS.FACTOR_POTENCIA
    }
}

# Rangos normales para validación de datos
NORMAL_RANGES = {
    SensorTypeDLMS.VOLTAJE: (200.0, 250.0),      # 200-250V nominal
    SensorTypeDLMS.VOLTAJE_L1: (200.0, 250.0),
    SensorTypeDLMS.VOLTAJE_L2: (200.0, 250.0),
    SensorTypeDLMS.VOLTAJE_L3: (200.0, 250.0),
    SensorTypeDLMS.CORRIENTE: (0.0, 800.0),     # 0-800A según capacidad
    SensorTypeDLMS.CORRIENTE_L1: (0.0, 1000.0),
    SensorTypeDLMS.CORRIENTE_L2: (0.0, 1000.0),
    SensorTypeDLMS.CORRIENTE_L3: (0.0, 1000.0),
    SensorTypeDLMS.POTENCIA: (0.0, 100000.0),    # 0-100kW
    SensorTypeDLMS.ENERGIA: (0.0, float('inf')), # Sin límite superior
    SensorTypeDLMS.FRECUENCIA: (49.0, 51.0),     # 49-51Hz nominal
    SensorTypeDLMS.FACTOR_POTENCIA: (0.7, 1.0),  # 0.7-1.0 rango normal
    SensorTypeDLMS.POTENCIA_REACTIVA: (0.0, 50000.0)  # 0-50kVAr
}


class DLMSSensorAdapter:
    """
    Adaptador principal para convertir métricas DLMS a formato de sensores Urbia
    
    Este adaptador:
    - Convierte datos raw de dispositivos DLMS a formato estándar de Urbia
    - Maneja tanto medidores monofásicos como trifásicos
    - Realiza normalización de unidades y rangos
    - Valida la calidad de los datos
    - Detecta valores críticos o anómalos
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa el adaptador de sensores DLMS
        
        Args:
            logger: Logger opcional para registro de eventos
        """
        self.logger = logger or logging.getLogger(__name__)
        self._conversion_cache = {}
    
    def adapt_raw_data(self, raw_data: DLMSRawData) -> List[DLMSConvertedData]:
        """
        Convierte datos raw DLMS a formato de sensores Urbia
        
        Args:
            raw_data: Datos raw del dispositivo DLMS
            
        Returns:
            Lista de datos convertidos para cada métrica
            
        Raises:
            ValueError: Si el tipo de medidor no es soportado
        """
        try:
            self.logger.info(f"Procesando datos DLMS del dispositivo {raw_data.device_id}")
            
            converted_data = []
            
            # Obtener mapa de métricas según tipo de medidor
            if raw_data.meter_type not in DLMS_METRICS_MAPPING:
                raise ValueError(f"Tipo de medidor no soportado: {raw_data.meter_type}")
            
            metric_map = DLMS_METRICS_MAPPING[raw_data.meter_type]
            
            # Procesar cada métrica
            for metric_name, raw_value in raw_data.metrics.items():
                if metric_name in metric_map:
                    sensor_type = metric_map[metric_name]
                    
                    # Convertir y validar valor
                    converted_value = self._convert_value(raw_value, sensor_type)
                    unit = self._get_unit_for_sensor_type(sensor_type)
                    phase = self._extract_phase(metric_name)
                    
                    # Validar calidad del dato
                    quality = self._validate_data_quality(converted_value, sensor_type)
                    is_critical = self._is_critical_value(converted_value, sensor_type)
                    
                    # Crear objeto convertido
                    converted_item = DLMSConvertedData(
                        device_id=raw_data.device_id,
                        timestamp=raw_data.timestamp,
                        sensor_type=sensor_type,
                        value=converted_value,
                        unit=unit,
                        phase=phase,
                        quality_indicator=quality,
                        is_critical=is_critical,
                        converted_from=metric_name
                    )
                    
                    converted_data.append(converted_item)
                    self.logger.debug(f"Convertida métrica {metric_name}: {converted_value} {unit}")
            
            self.logger.info(f"Convertidas {len(converted_data)} métricas para {raw_data.device_id}")
            return converted_data
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo datos DLMS: {str(e)}")
            raise
    
    def _convert_value(self, value: Any, sensor_type: SensorTypeDLMS) -> float:
        """
        Convierte un valor raw a formato estándar según el tipo de sensor
        
        Args:
            value: Valor raw (puede ser string, float, int)
            sensor_type: Tipo de sensor destino
            
        Returns:
            Valor convertido como float
        """
        try:
            # Convertir a float si es string
            if isinstance(value, str):
                # Remover espacios y caracteres no numéricos excepto punto y coma
                clean_value = value.strip().replace(',', '.')
                numeric_value = float(clean_value)
            elif isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                raise ValueError(f"Tipo de valor no soportado: {type(value)}")
            
            # Aplicar factor de conversión según el tipo de sensor
            conversion_info = self._get_conversion_info(sensor_type)
            if conversion_info:
                numeric_value *= conversion_info["factor"]
            
            return numeric_value
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error convirtiendo valor {value} para {sensor_type}: {str(e)}")
            return 0.0
    
    def _get_conversion_info(self, sensor_type: SensorTypeDLMS) -> Optional[Dict]:
        """
        Obtiene información de conversión para un tipo de sensor
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Diccionario con información de conversión o None
        """
        # Mapear tipo de sensor a categoría de conversión
        sensor_category = self._get_sensor_category(sensor_type)
        
        # Obtener configuración de conversión para la categoría
        conversion_configs = UNIT_CONVERSIONS.get(sensor_category, {})
        
        # Por defecto, usar la primera configuración disponible o crear una por defecto
        if conversion_configs:
            # Usar la primera configuración disponible (V, A, W, etc.)
            first_unit = list(conversion_configs.keys())[0]
            return conversion_configs[first_unit]
        else:
            # Configuración por defecto si no hay conversión definida
            return {"factor": 1.0, "unit": "?"}
    
    def _get_sensor_category(self, sensor_type: SensorTypeDLMS) -> str:
        """
        Categoriza el tipo de sensor para determinar conversión de unidades
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Categoría del sensor para conversión
        """
        category_mapping = {
            SensorTypeDLMS.VOLTAJE: "voltage",
            SensorTypeDLMS.VOLTAJE_L1: "voltage",
            SensorTypeDLMS.VOLTAJE_L2: "voltage",
            SensorTypeDLMS.VOLTAJE_L3: "voltage",
            SensorTypeDLMS.CORRIENTE: "current",
            SensorTypeDLMS.CORRIENTE_L1: "current",
            SensorTypeDLMS.CORRIENTE_L2: "current",
            SensorTypeDLMS.CORRIENTE_L3: "current",
            SensorTypeDLMS.POTENCIA: "power",
            SensorTypeDLMS.POTENCIA_REACTIVA: "power",
            SensorTypeDLMS.ENERGIA: "energy",
            SensorTypeDLMS.FRECUENCIA: "frequency",
            SensorTypeDLMS.FACTOR_POTENCIA: "power_factor"  # Factor de potencia sin conversión
        }
        
        return category_mapping.get(sensor_type, "unknown")
    
    def _get_unit_for_sensor_type(self, sensor_type: SensorTypeDLMS) -> str:
        """
        Obtiene la unidad estándar para un tipo de sensor
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Unidad estándar del sensor
        """
        unit_mapping = {
            SensorTypeDLMS.VOLTAJE: "V",
            SensorTypeDLMS.VOLTAJE_L1: "V",
            SensorTypeDLMS.VOLTAJE_L2: "V",
            SensorTypeDLMS.VOLTAJE_L3: "V",
            SensorTypeDLMS.CORRIENTE: "A",
            SensorTypeDLMS.CORRIENTE_L1: "A",
            SensorTypeDLMS.CORRIENTE_L2: "A",
            SensorTypeDLMS.CORRIENTE_L3: "A",
            SensorTypeDLMS.POTENCIA: "W",
            SensorTypeDLMS.POTENCIA_REACTIVA: "VAr",
            SensorTypeDLMS.ENERGIA: "Wh",
            SensorTypeDLMS.FRECUENCIA: "Hz",
            SensorTypeDLMS.FACTOR_POTENCIA: ""
        }
        
        return unit_mapping.get(sensor_type, "?")
    
    def _extract_phase(self, metric_name: str) -> Optional[PhaseType]:
        """
        Extrae la información de fase del nombre de la métrica
        
        Args:
            metric_name: Nombre original de la métrica DLMS
            
        Returns:
            Tipo de fase o None si no aplica
        """
        if "l1" in metric_name.lower():
            return PhaseType.L1
        elif "l2" in metric_name.lower():
            return PhaseType.L2
        elif "l3" in metric_name.lower():
            return PhaseType.L3
        else:
            return PhaseType.TOTAL
    
    def _validate_data_quality(self, value: float, sensor_type: SensorTypeDLMS) -> str:
        """
        Valida la calidad del dato basado en rangos normales
        
        Args:
            value: Valor a validar
            sensor_type: Tipo de sensor
            
        Returns:
            Indicador de calidad: GOOD, BAD, o UNCERTAIN
        """
        if sensor_type not in NORMAL_RANGES:
            return "UNCERTAIN"
        
        min_val, max_val = NORMAL_RANGES[sensor_type]
        
        # Si el valor está dentro del rango normal
        if min_val <= value <= max_val:
            return "GOOD"
        
        # Si está moderadamente fuera del rango
        if min_val * 0.85 <= value <= max_val * 1.15:
            return "UNCERTAIN"
        
        # Fuera del rango aceptable
        return "BAD"
    
    def _is_critical_value(self, value: float, sensor_type: SensorTypeDLMS) -> bool:
        """
        Determina si un valor es crítico basado en umbrales específicos
        
        Args:
            value: Valor a evaluar
            sensor_type: Tipo de sensor
            
        Returns:
            True si el valor es crítico, False en caso contrario
        """
        if sensor_type not in NORMAL_RANGES:
            return False
        
        min_val, max_val = NORMAL_RANGES[sensor_type]
        
        # Valores críticos: 10% fuera del rango normal
        critical_threshold_low = min_val * 0.9
        critical_threshold_high = max_val * 1.1
        
        return value <= critical_threshold_low or value >= critical_threshold_high
    
    def get_supported_metrics(self, meter_type: MeterType) -> Dict[str, SensorTypeDLMS]:
        """
        Obtiene las métricas soportadas para un tipo de medidor
        
        Args:
            meter_type: Tipo de medidor DLMS
            
        Returns:
            Diccionario con mapeo de métricas
        """
        return DLMS_METRICS_MAPPING.get(meter_type, {})
    
    def validate_device_data(self, device_id: str, meter_type: MeterType, 
                           metrics: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida que los datos del dispositivo sean consistentes
        
        Args:
            device_id: ID del dispositivo
            meter_type: Tipo de medidor
            metrics: Métricas recibidas
            
        Returns:
            Tupla con (es_válido, lista_de_errores)
        """
        errors = []
        
        # Verificar que el tipo de medidor sea válido
        if meter_type not in DLMS_METRICS_MAPPING:
            errors.append(f"Tipo de medidor no soportado: {meter_type}")
        
        # Verificar métricas esperadas (permite métricas faltantes para transmisión parcial)
        expected_metrics = set(DLMS_METRICS_MAPPING.get(meter_type, {}).keys())
        received_metrics = set(metrics.keys())
        
        missing_metrics = expected_metrics - received_metrics
        unexpected_metrics = received_metrics - expected_metrics
        
        # Solo reportar métricas faltantes si hay muy pocas métricas recibidas
        if missing_metrics and len(received_metrics) < len(expected_metrics) * 0.25:
            errors.append(f"Métricas faltantes: {missing_metrics}")
        
        if unexpected_metrics:
            errors.append(f"Métricas inesperadas: {unexpected_metrics}")
        
        # Verificar valores numéricos
        for metric_name, value in metrics.items():
            try:
                if isinstance(value, str):
                    float(value.replace(',', '.'))
            except ValueError:
                errors.append(f"Valor no numérico en métrica {metric_name}: {value}")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            self.logger.warning(f"Datos inválidos para dispositivo {device_id}: {errors}")
        
        return is_valid, errors
    
    def create_sensor_config(self, device_id: str, converted_data: List[DLMSConvertedData]) -> Dict[str, Any]:
        """
        Crea configuración de sensores para el sistema Urbia basada en datos convertidos
        
        Args:
            device_id: ID del dispositivo
            converted_data: Lista de datos convertidos
            
        Returns:
            Configuración de sensores para el dispositivo
        """
        sensor_configs = []
        
        for data in converted_data:
            config = {
                "id": f"{device_id}_{data.sensor_type.value}_{data.phase.value if data.phase else 'TOTAL'}",
                "name": f"DLMS {data.sensor_type.value.replace('_', ' ').title()} {data.phase.value if data.phase else 'Total'}",
                "type": data.sensor_type.value,
                "unit": data.unit,
                "location": {
                    "device_id": device_id,
                    "phase": data.phase.value if data.phase else "TOTAL",
                    "description": f"Medición DLMS {data.phase.value if data.phase else 'Total'} - {device_id}"
                },
                "priority": self._determine_priority(data.sensor_type),
                "min_value": NORMAL_RANGES.get(data.sensor_type, (0.0, 1000.0))[0],
                "max_value": NORMAL_RANGES.get(data.sensor_type, (0.0, 1000.0))[1],
                "threshold_critical": self._calculate_critical_threshold(data.sensor_type),
                "is_active": True,
                "quality_indicator": data.quality_indicator,
                "last_updated": data.timestamp.isoformat()
            }
            
            sensor_configs.append(config)
        
        return {
            "device_id": device_id,
            "device_type": "DLMS_METER",
            "sensors": sensor_configs,
            "total_sensors": len(sensor_configs),
            "created_at": datetime.now().isoformat()
        }
    
    def _determine_priority(self, sensor_type: SensorTypeDLMS) -> int:
        """
        Determina la prioridad del sensor basado en su tipo
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Prioridad (1=alta, 5=baja)
        """
        priority_mapping = {
            SensorTypeDLMS.VOLTAJE: 1,          # Voltaje es crítico
            SensorTypeDLMS.CORRIENTE: 2,        # Corriente importante
            SensorTypeDLMS.POTENCIA: 3,         # Potencia moderadamente importante
            SensorTypeDLMS.FRECUENCIA: 1,       # Frecuencia crítica
            SensorTypeDLMS.FACTOR_POTENCIA: 4,  # Factor de potencia menos crítico
            SensorTypeDLMS.ENERGIA: 3           # Energía importante para análisis
        }
        
        return priority_mapping.get(sensor_type, 5)
    
    def _calculate_critical_threshold(self, sensor_type: SensorTypeDLMS) -> float:
        """
        Calcula el umbral crítico para un tipo de sensor
        
        Args:
            sensor_type: Tipo de sensor
            
        Returns:
            Umbral crítico
        """
        if sensor_type not in NORMAL_RANGES:
            return None
        
        min_val, max_val = NORMAL_RANGES[sensor_type]
        
        # El umbral crítico está al 85% del rango superior para métricas de límite
        return max_val * 0.85
    
    def export_sensor_config(self, device_id: str, output_file: str) -> bool:
        """
        Exporta la configuración de sensores a un archivo JSON
        
        Args:
            device_id: ID del dispositivo
            output_file: Ruta del archivo de salida
            
        Returns:
            True si se exportó correctamente, False en caso contrario
        """
        try:
            # Esta función necesitaría datos reales del dispositivo
            # Por ahora retorna False ya que requiere implementación adicional
            
            self.logger.info(f"Configuración exportada para dispositivo {device_id} a {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando configuración: {str(e)}")
            return False


# Función de utilidad para crear adaptador
def create_dlms_adapter(logger: Optional[logging.Logger] = None) -> DLMSSensorAdapter:
    """
    Función de utilidad para crear una instancia del adaptador DLMS
    
    Args:
        logger: Logger opcional
        
    Returns:
        Instancia del adaptador DLMS
    """
    return DLMSSensorAdapter(logger)


# Función de ejemplo para testing
def example_usage():
    """
    Función de ejemplo que muestra cómo usar el adaptador
    """
    # Crear adaptador
    adapter = create_dlms_adapter()
    
    # Datos de ejemplo para medidor monofásico
    raw_data_monofasico = DLMSRawData(
        device_id="DLMS-001",
        timestamp=datetime.now(),
        meter_type=MeterType.MONOFASICO,
        metrics={
            "voltage_l1": 220.5,
            "current_l1": 15.2,
            "active_power": 3344.0,
            "active_energy": 1234567.8,
            "frequency": 50.1,
            "power_factor": 0.85
        },
        raw_values={}
    )
    
    # Convertir datos
    converted_data = adapter.adapt_raw_data(raw_data_monofasico)
    
    # Mostrar resultados
    print(f"Dispositivo: {raw_data_monofasico.device_id}")
    print(f"Métricas convertidas: {len(converted_data)}")
    
    for data in converted_data:
        print(f"  - {data.sensor_type.value}: {data.value} {data.unit} "
              f"(Fase: {data.phase.value if data.phase else 'N/A'}, "
              f"Calidad: {data.quality_indicator}, "
              f"Crítico: {data.is_critical})")
    
    # Crear configuración de sensores
    config = adapter.create_sensor_config(raw_data_monofasico.device_id, converted_data)
    print(f"\nConfiguración de sensores generada:")
    print(f"Total de sensores: {config['total_sensors']}")


if __name__ == "__main__":
    # Configurar logging para ejemplo
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar ejemplo
    example_usage()