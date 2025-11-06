#!/usr/bin/env python3
"""
Sincronización en tiempo real vía SSH
Para cuando no hay acceso directo a PostgreSQL pero sí hay SSH
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# Configuración SSH
SSH_CONFIG = {
    'host': '192.168.46.124',
    'user': 'pci',
    'password': 'banano2025'  # O usar SSH keys
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


class SSHThingsBoardSync:
    """Sincronizador vía SSH"""
    
    def __init__(self):
        self.ssh_host = f"{SSH_CONFIG['user']}@{SSH_CONFIG['host']}"
        self.output_dir = Path("data/telemetry")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def ejecutar_comando_ssh(self, comando):
        """Ejecuta un comando en el servidor vía SSH"""
        try:
            # Comando SSH completo
            ssh_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                self.ssh_host,
                comando
            ]
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"⚠️  Error SSH: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout al ejecutar comando SSH")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def obtener_telemetria_actual(self):
        """Obtiene telemetría actual del servidor"""
        print(f"⏰ Sincronizando... {datetime.now().strftime('%H:%M:%S')}")
        
        # Comando para ejecutar en el servidor
        comando = '''docker exec thingsboard-postgres-1 psql -U postgres -d thingsboard -t -A -F'|' -c "
SELECT 
    d.name,
    ts.key,
    ts.dbl_v,
    ts.ts
FROM ts_kv_latest ts
JOIN device d ON ts.entity_id = d.id
WHERE d.type = 'DLMS Energy Meter' AND ts.dbl_v IS NOT NULL
ORDER BY d.name, ts.key;"
'''
        
        print("📡 Ejecutando query en servidor remoto...")
        output = self.ejecutar_comando_ssh(comando)
        
        if not output:
            return []
        
        # Parsear resultado
        datos = []
        for linea in output.strip().split('\n'):
            if '|' in linea:
                partes = linea.split('|')
                if len(partes) >= 4:
                    try:
                        datos.append({
                            'device': partes[0].strip(),
                            'metric_code': partes[1].strip(),
                            'value': float(partes[2].strip()),
                            'timestamp': partes[3].strip()
                        })
                    except:
                        continue
        
        print(f"📥 Obtenidos {len(datos)} registros")
        return datos
    
    def convertir_a_formato_urbia(self, datos_raw):
        """Convierte a formato Urbia"""
        datos_urbia = []
        
        for dato in datos_raw:
            metric_code = dato['metric_code']
            
            if metric_code in DLMS_CODE_MAP:
                metric_info = DLMS_CODE_MAP[metric_code]
                
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
                    'priority': 'high',
                    'metadata': {
                        'device_name': dato['device'],
                        'dlms_code': metric_code,
                        'description': metric_info['description'],
                        'source': 'thingsboard_unal_ssh',
                        'real_data': True,
                        'sync_time': datetime.now().isoformat()
                    }
                }
                
                datos_urbia.append(dato_urbia)
        
        return datos_urbia
    
    def guardar_datos(self, datos):
        """Guarda datos en JSON"""
        output_file = self.output_dir / "dlms_real_data.json"
        
        with open(output_file, 'w') as f:
            json.dump(datos, f, indent=2)
        
        return output_file
    
    def sincronizar_una_vez(self):
        """Ejecuta una sincronización"""
        # Obtener datos
        datos_raw = self.obtener_telemetria_actual()
        
        if not datos_raw:
            print("⚠️  No se obtuvieron datos")
            return False
        
        # Convertir
        datos_urbia = self.convertir_a_formato_urbia(datos_raw)
        print(f"🔄 Convertidos {len(datos_urbia)} registros")
        
        # Guardar
        archivo = self.guardar_datos(datos_urbia)
        print(f"💾 Guardado en: {archivo}")
        
        # Resumen
        dispositivos = {}
        for dato in datos_urbia:
            device = dato['metadata']['device_name']
            dispositivos[device] = dispositivos.get(device, 0) + 1
        
        for device, count in dispositivos.items():
            print(f"   🔌 {device}: {count} métricas")
        
        return True
    
    def sincronizar_continuo(self, intervalo_segundos=30):
        """Sincronización continua"""
        print("\n" + "="*70)
        print("🚀 SINCRONIZACIÓN SSH EN TIEMPO REAL - THINGSBOARD UNAL")
        print("="*70)
        print(f"🌐 Servidor: {self.ssh_host}")
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
            print("\n\n⏹️  Sincronización detenida")
            print(f"📊 Total de sincronizaciones: {contador}")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sincronización SSH ThingsBoard UNAL')
    parser.add_argument('--intervalo', type=int, default=30, 
                       help='Intervalo en segundos (default: 30)')
    parser.add_argument('--una-vez', action='store_true', 
                       help='Ejecutar solo una vez')
    args = parser.parse_args()
    
    print("\n🎓 SINCRONIZACIÓN VÍA SSH - UNIVERSIDAD NACIONAL")
    print("="*70)
    
    sync = SSHThingsBoardSync()
    
    if args.una_vez:
        print("📸 Modo: Una sola sincronización\n")
        sync.sincronizar_una_vez()
    else:
        print(f"🔄 Modo: Sincronización continua (cada {args.intervalo}s)\n")
        sync.sincronizar_continuo(args.intervalo)
    
    print("\n✅ Proceso finalizado")


if __name__ == "__main__":
    main()
