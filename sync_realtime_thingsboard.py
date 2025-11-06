#!/usr/bin/env python3
"""
Sincronización en TIEMPO REAL con ThingsBoard UNAL
Requiere VPN activa a la Universidad Nacional
"""

import psycopg2
import time
import json
from datetime import datetime
from pathlib import Path
import sys

# Configuración de conexión a ThingsBoard UNAL (vía VPN)
THINGSBOARD_CONFIG = {
    'host': '192.168.46.124',  # IP del servidor vía VPN
    'port': 5432,
    'database': 'thingsboard',
    'user': 'postgres',
    'password': 'postgres'  # Confirmar con el equipo
}

# IDs reales de los dispositivos DLMS
DEVICE_IDS = {
    'DLMS-Meter-01': '49111400-b99f-11f0-b2a7-017993aa882e',
    'DLMS-Meter-02': '794f25e0-b9fd-11f0-bc69-cb99eafde0bd'
}

# Mapeo de códigos DLMS
DLMS_CODE_MAP = {
    "110": {"name": "active_energy_total", "unit": "kWh", "description": "Energía Activa Total"},
    "132": {"name": "active_energy_l1", "unit": "kWh", "description": "Energía Activa L1"},
    "133": {"name": "active_energy_l2", "unit": "kWh", "description": "Energía Activa L2"},
    "134": {"name": "active_energy_l3", "unit": "kWh", "description": "Energía Activa L3"},
    "135": {"name": "active_energy_phase", "unit": "kWh", "description": "Energía Activa por Fase"},
    "193": {"name": "reactive_energy_total", "unit": "kVARh", "description": "Energía Reactiva Total"},
    "194": {"name": "reactive_energy_l1", "unit": "kVARh", "description": "Energía Reactiva L1"},
    "195": {"name": "reactive_energy_l2", "unit": "kVARh", "description": "Energía Reactiva L2"},
    "196": {"name": "reactive_energy_l3", "unit": "kVARh", "description": "Energía Reactiva L3"},
}


class ThingsBoardRealTimeSync:
    """Sincronizador en tiempo real con ThingsBoard"""
    
    def __init__(self, output_dir="data/telemetry"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.connection = None
        
    def conectar(self):
        """Conecta a la base de datos de ThingsBoard"""
        try:
            print("🔌 Conectando a ThingsBoard UNAL...")
            self.connection = psycopg2.connect(**THINGSBOARD_CONFIG)
            print("✅ Conexión establecida")
            return True
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            print("💡 Verifica:")
            print("   1. VPN activa (./vpn_simple.sh)")
            print("   2. IP correcta: 192.168.46.124")
            print("   3. Credenciales correctas")
            return False
    
    def obtener_telemetria_actual(self):
        """Obtiene la telemetría actual de los dispositivos DLMS"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Query para obtener datos actuales
            query = """
            SELECT 
                d.name as device,
                ts.key as metric_code,
                ts.dbl_v as value,
                ts.ts
            FROM ts_kv_latest ts
            JOIN device d ON ts.entity_id = d.id
            WHERE d.type = 'DLMS Energy Meter' 
              AND ts.dbl_v IS NOT NULL
            ORDER BY d.name, ts.key;
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # Convertir a formato estructurado
            datos = []
            for row in results:
                datos.append({
                    'device': row[0],
                    'metric_code': str(row[1]),
                    'value': float(row[2]) if row[2] else 0.0,
                    'timestamp': str(row[3])
                })
            
            return datos
            
        except Exception as e:
            print(f"❌ Error al obtener datos: {e}")
            return []
    
    def convertir_a_formato_urbia(self, datos_raw):
        """Convierte datos DLMS a formato Urbia"""
        datos_urbia = []
        
        for dato in datos_raw:
            metric_code = dato['metric_code']
            
            if metric_code in DLMS_CODE_MAP:
                metric_info = DLMS_CODE_MAP[metric_code]
                
                # Timestamp
                try:
                    ts = int(dato['timestamp'])
                    dt = datetime.fromtimestamp(ts / 1000)
                except:
                    dt = datetime.now()
                
                dato_urbia = {
                    'id': f"{dato['device']}_{metric_info['name']}_{ts}",
                    'sensor_id': f"{dato['device']}_{metric_info['name']}",
                    'sensor_type': metric_info['name'],
                    'timestamp': dt.isoformat(),
                    'value': dato['value'],
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
                        'source': 'thingsboard_unal_realtime',
                        'real_data': True,
                        'sync_time': datetime.now().isoformat()
                    }
                }
                
                datos_urbia.append(dato_urbia)
        
        return datos_urbia
    
    def guardar_datos(self, datos):
        """Guarda datos en archivo JSON"""
        output_file = self.output_dir / "dlms_real_data.json"
        
        with open(output_file, 'w') as f:
            json.dump(datos, f, indent=2)
        
        return output_file
    
    def sincronizar_una_vez(self):
        """Ejecuta una sincronización"""
        print(f"\n⏰ Sincronizando... {datetime.now().strftime('%H:%M:%S')}")
        
        # Obtener datos
        datos_raw = self.obtener_telemetria_actual()
        
        if not datos_raw:
            print("⚠️  No se obtuvieron datos")
            return False
        
        print(f"📥 Obtenidos {len(datos_raw)} registros")
        
        # Convertir
        datos_urbia = self.convertir_a_formato_urbia(datos_raw)
        print(f"🔄 Convertidos {len(datos_urbia)} registros")
        
        # Guardar
        archivo = self.guardar_datos(datos_urbia)
        print(f"💾 Guardado en: {archivo}")
        
        # Mostrar resumen
        dispositivos = {}
        for dato in datos_urbia:
            device = dato['metadata']['device_name']
            if device not in dispositivos:
                dispositivos[device] = 0
            dispositivos[device] += 1
        
        for device, count in dispositivos.items():
            print(f"   🔌 {device}: {count} métricas")
        
        return True
    
    def sincronizar_continuo(self, intervalo_segundos=30):
        """Sincronización continua en tiempo real"""
        print("\n" + "="*70)
        print("🚀 SINCRONIZACIÓN EN TIEMPO REAL - THINGSBOARD UNAL")
        print("="*70)
        print(f"📡 Intervalo: {intervalo_segundos} segundos")
        print(f"📁 Salida: {self.output_dir}")
        print("⌨️  Presiona Ctrl+C para detener")
        print("="*70)
        
        contador = 0
        
        try:
            while True:
                contador += 1
                print(f"\n🔄 Ciclo #{contador}")
                
                exitoso = self.sincronizar_una_vez()
                
                if exitoso:
                    print(f"✅ Sincronización #{contador} completada")
                else:
                    print(f"⚠️  Sincronización #{contador} falló")
                
                print(f"⏳ Esperando {intervalo_segundos}s...")
                time.sleep(intervalo_segundos)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Sincronización detenida por el usuario")
            print(f"📊 Total de sincronizaciones: {contador}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.connection:
                self.connection.close()
                print("🔌 Conexión cerrada")
    
    def desconectar(self):
        """Cierra la conexión"""
        if self.connection:
            self.connection.close()
            print("🔌 Desconectado de ThingsBoard")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sincronización en tiempo real con ThingsBoard UNAL')
    parser.add_argument('--intervalo', type=int, default=30, help='Intervalo en segundos (default: 30)')
    parser.add_argument('--una-vez', action='store_true', help='Ejecutar solo una vez')
    args = parser.parse_args()
    
    sync = ThingsBoardRealTimeSync()
    
    # Conectar
    if not sync.conectar():
        print("\n❌ No se pudo conectar a ThingsBoard")
        print("\n💡 Pasos para conectar:")
        print("   1. Ejecuta: ./vpn_simple.sh")
        print("   2. Ingresa credenciales VPN")
        print("   3. Verifica: ping 192.168.46.124")
        print("   4. Ejecuta este script nuevamente")
        sys.exit(1)
    
    # Sincronizar
    if args.una_vez:
        print("\n📸 Modo: Una sola sincronización")
        sync.sincronizar_una_vez()
    else:
        print(f"\n🔄 Modo: Sincronización continua (cada {args.intervalo}s)")
        sync.sincronizar_continuo(args.intervalo)
    
    sync.desconectar()


if __name__ == "__main__":
    main()
