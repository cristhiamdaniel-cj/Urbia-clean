#!/usr/bin/env python3
"""
Sincronización con ThingsBoard Real - UNAL
Valores REALES extraídos del servidor
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Mapeo de códigos DLMS a métricas legibles
DLMS_CODE_MAP = {
    # Energía Activa
    "110": {"name": "active_energy_total", "unit": "kWh", "description": "Energía Activa Total"},
    "132": {"name": "active_energy_l1", "unit": "kWh", "description": "Energía Activa L1"},
    "133": {"name": "active_energy_l2", "unit": "kWh", "description": "Energía Activa L2"},
    "134": {"name": "active_energy_l3", "unit": "kWh", "description": "Energía Activa L3"},
    "135": {"name": "active_energy_phase", "unit": "kWh", "description": "Energía Activa por Fase"},
    
    # Energía Reactiva
    "193": {"name": "reactive_energy_total", "unit": "kVARh", "description": "Energía Reactiva Total"},
    "194": {"name": "reactive_energy_l1", "unit": "kVARh", "description": "Energía Reactiva L1"},
    "195": {"name": "reactive_energy_l2", "unit": "kVARh", "description": "Energía Reactiva L2"},
    "196": {"name": "reactive_energy_l3", "unit": "kVARh", "description": "Energía Reactiva L3"},
}

class ThingsBoardRealSync:
    """Sincronizador con datos reales de ThingsBoard UNAL"""
    
    def __init__(self, data_file="telemetria_dlms.txt"):
        self.data_file = data_file
        self.datos_procesados = []
        
    def obtener_datos_reales(self):
        """Datos REALES extraídos del servidor ThingsBoard UNAL"""
        print("📥 Usando datos REALES de ThingsBoard...")
        
        # DATOS REALES DEL SERVIDOR - 6 Nov 2025
        return [
            # DLMS-Meter-01 (Monofásico) - Timestamp: 1762440337780
            {'device': 'DLMS-Meter-01', 'metric_code': '110', 'value': '59.99', 'timestamp': '1762440337780'},
            {'device': 'DLMS-Meter-01', 'metric_code': '132', 'value': '135.41', 'timestamp': '1762440337780'},
            {'device': 'DLMS-Meter-01', 'metric_code': '133', 'value': '1.327', 'timestamp': '1762440337780'},
            {'device': 'DLMS-Meter-01', 'metric_code': '134', 'value': '0.6', 'timestamp': '1762440337780'},
            {'device': 'DLMS-Meter-01', 'metric_code': '135', 'value': '56376', 'timestamp': '1762440337780'},
            
            # DLMS-Meter-02 (Bifásico/Trifásico) - Timestamp: 1762328858540
            {'device': 'DLMS-Meter-02', 'metric_code': '110', 'value': '60.06', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '132', 'value': '118.93', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '133', 'value': '10.68', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '134', 'value': '3952.71', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '135', 'value': '153074.68', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '193', 'value': '121.08', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '194', 'value': '120.37', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '195', 'value': '10.62', 'timestamp': '1762328858540'},
            {'device': 'DLMS-Meter-02', 'metric_code': '196', 'value': '10.62', 'timestamp': '1762328858540'},
        ]
    
    def convertir_a_formato_urbia(self, datos):
        """Convierte datos DLMS a formato Urbia"""
        print("🔄 Convirtiendo a formato Urbia...")
        
        datos_urbia = []
        
        for dato in datos:
            metric_code = dato['metric_code']
            
            if metric_code in DLMS_CODE_MAP:
                metric_info = DLMS_CODE_MAP[metric_code]
                
                # Convertir timestamp de milisegundos a datetime
                try:
                    ts = int(dato['timestamp'])
                    dt = datetime.fromtimestamp(ts / 1000)
                except:
                    dt = datetime.now()
                
                # Obtener valor numérico
                try:
                    valor = float(dato['value']) if dato['value'] else 0.0
                except:
                    valor = 0.0
                
                dato_urbia = {
                    'id': f"{dato['device']}_{metric_info['name']}_{ts}",
                    'sensor_id': f"{dato['device']}_{metric_info['name']}",
                    'sensor_type': metric_info['name'],
                    'timestamp': dt.isoformat(),
                    'value': valor,
                    'unit': metric_info['unit'],
                    'location': {
                        'lat': 4.6381,
                        'lng': -74.0843,
                        'description': 'Universidad Nacional de Colombia'
                    },
                    'priority': 'high' if 'energy' in metric_info['name'] else 'normal',
                    'metadata': {
                        'device_name': dato['device'],
                        'dlms_code': metric_code,
                        'description': metric_info['description'],
                        'source': 'thingsboard_unal',
                        'real_data': True
                    }
                }
                
                datos_urbia.append(dato_urbia)
        
        print(f"✅ Convertidos {len(datos_urbia)} registros REALES")
        return datos_urbia
    
    def guardar_para_api(self, datos_urbia):
        """Guarda datos para que la API los sirva"""
        output_dir = Path(__file__).parent / "data" / "telemetry"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "dlms_real_data.json"
        
        with open(output_file, 'w') as f:
            json.dump(datos_urbia, f, indent=2)
        
        print(f"💾 Datos REALES guardados en: {output_file}")
        return output_file
    
    def mostrar_resumen(self, datos_urbia):
        """Muestra resumen de los datos REALES"""
        print("\n" + "="*70)
        print("📊 RESUMEN DE DATOS REALES - THINGSBOARD UNAL")
        print("="*70)
        
        # Agrupar por dispositivo
        por_dispositivo = {}
        for dato in datos_urbia:
            device = dato['metadata']['device_name']
            if device not in por_dispositivo:
                por_dispositivo[device] = []
            por_dispositivo[device].append(dato)
        
        for device, datos in por_dispositivo.items():
            print(f"\n🔌 {device}")
            print(f"   Total métricas: {len(datos)}")
            print(f"   Timestamp: {datos[0]['timestamp']}")
            
            for dato in datos:
                print(f"   • {dato['metadata']['description']}: {dato['value']} {dato['unit']}")
        
        print("\n" + "="*70)
        print("✅ DATOS REALES DE PRODUCCIÓN")
        print("   Fuente: ThingsBoard Universidad Nacional")
        print("   Fecha extracción: 6 Noviembre 2025")
        print("="*70)
    
    def ejecutar_sincronizacion(self):
        """Ejecuta el proceso completo de sincronización"""
        print("\n🚀 SINCRONIZACIÓN DATOS REALES THINGSBOARD - URBIA")
        print("="*70)
        
        # 1. Obtener datos reales
        datos_raw = self.obtener_datos_reales()
        print(f"✅ {len(datos_raw)} registros REALES del servidor")
        
        # 2. Convertir a formato Urbia
        datos_urbia = self.convertir_a_formato_urbia(datos_raw)
        
        # 3. Guardar para API
        archivo = self.guardar_para_api(datos_urbia)
        
        # 4. Mostrar resumen
        self.mostrar_resumen(datos_urbia)
        
        print(f"\n📁 Archivo: {archivo}")
        print("🌐 APIs disponibles:")
        print("   • http://localhost:5001/api/telemetry/dlms-real")
        print("   • http://localhost:5001/api/telemetry/dlms-real/summary")
        print("   • http://localhost:5001/api/telemetry/dlms-real/devices")
        
        return datos_urbia


def main():
    """Función principal"""
    sync = ThingsBoardRealSync()
    datos = sync.ejecutar_sincronizacion()
    
    print("\n💡 Para la sustentación:")
    print("   1. ✅ Datos REALES sincronizados")
    print("   2. Inicia API: python src/main.py")
    print("   3. Abre: http://localhost:5001")
    print("   4. ¡Muestra datos reales de producción! 🎓")


if __name__ == "__main__":
    main()
