# sensors/traffic_generator.py

import socket
import time
import random
import argparse
from datetime import datetime

class TrafficGenerator:
    """
    Genera diferentes tipos de tráfico para probar el controlador SDN
    """
    
    def __init__(self, src_ip, dst_ip, dst_port):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.dst_port = dst_port
    
    def send_critical_traffic(self, count=10, interval=0.1):
        """
        Simula tráfico CRÍTICO (e.g., alertas MQTT en puerto 1883)
        """
        print(f"🔴 Generando tráfico CRÍTICO: {count} paquetes")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.dst_ip, 1883))  # Puerto MQTT
            
            for i in range(count):
                timestamp = datetime.now().isoformat()
                message = f"ALERT|{timestamp}|temp_critical|45.5C".encode()
                sock.sendall(message)
                print(f"  [{i+1}/{count}] Enviado: {message.decode()}")
                time.sleep(interval)
            
            sock.close()
        except Exception as e:
            print(f"Error: {e}")
    
    def send_normal_traffic(self, count=50, interval=0.5):
        """
        Simula tráfico NORMAL (e.g., telemetría en puerto 8080)
        """
        print(f"🟢 Generando tráfico NORMAL: {count} paquetes")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.dst_ip, 8080))  # Puerto HTTP
            
            for i in range(count):
                timestamp = datetime.now().isoformat()
                temp = random.uniform(20.0, 30.0)
                hum = random.uniform(40.0, 60.0)
                message = f"DATA|{timestamp}|temp={temp:.1f}|hum={hum:.1f}".encode()
                sock.sendall(message)
                if i % 10 == 0:
                    print(f"  [{i+1}/{count}] Enviando telemetría...")
                time.sleep(interval)
            
            sock.close()
        except Exception as e:
            print(f"Error: {e}")
    
    def send_bulk_traffic(self, count=100, interval=0.05):
        """
        Simula tráfico de BAJA PRIORIDAD (e.g., logs en puerto 9999)
        """
        print(f"⚪ Generando tráfico BULK: {count} paquetes")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.dst_ip, 9999))  # Puerto logs
            
            for i in range(count):
                timestamp = datetime.now().isoformat()
                message = f"LOG|{timestamp}|debug|routine_check_ok".encode()
                sock.sendall(message)
                if i % 20 == 0:
                    print(f"  [{i+1}/{count}] Enviando logs...")
                time.sleep(interval)
            
            sock.close()
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Generador de tráfico UrbIA')
    parser.add_argument('--src', default='10.0.0.10', help='IP origen')
    parser.add_argument('--dst', default='10.0.0.20', help='IP destino')
    parser.add_argument('--type', choices=['critical', 'normal', 'bulk', 'all'], 
                       default='all', help='Tipo de tráfico')
    
    args = parser.parse_args()
    
    generator = TrafficGenerator(args.src, args.dst, 8080)
    
    if args.type == 'critical' or args.type == 'all':
        generator.send_critical_traffic()
        time.sleep(2)
    
    if args.type == 'normal' or args.type == 'all':
        generator.send_normal_traffic()
        time.sleep(2)
    
    if args.type == 'bulk' or args.type == 'all':
        generator.send_bulk_traffic()


if __name__ == '__main__':
    main()
