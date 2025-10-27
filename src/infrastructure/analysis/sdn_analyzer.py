"""Analizador Matemático del SDN"""
import time
import statistics
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Any
import threading

class SDNAnalyzer:
    def __init__(self):
        self.latency_history = deque(maxlen=100)
        self.throughput_history = deque(maxlen=100)
        self.packet_counts = defaultdict(int)
        self.sensor_metrics = {}
        self.gateway_metrics = defaultdict(lambda: {
            'packets': 0, 'bytes': 0, 'last_update': time.time()
        })
        self.strategy_counts = defaultdict(int)
        self.lock = threading.Lock()
        
    def record_packet(self, sensor_id: str, gateway: str, latency: float, 
                     strategy: str, packet_size: int = 128):
        with self.lock:
            self.latency_history.append(latency)
            self.packet_counts[sensor_id] += 1
            self.gateway_metrics[gateway]['packets'] += 1
            self.gateway_metrics[gateway]['bytes'] += packet_size
            self.gateway_metrics[gateway]['last_update'] = time.time()
            self.strategy_counts[strategy] += 1
            
            if sensor_id not in self.sensor_metrics:
                self.sensor_metrics[sensor_id] = {
                    'latencies': deque(maxlen=20),
                    'packet_count': 0,
                    'last_seen': time.time()
                }
            
            self.sensor_metrics[sensor_id]['latencies'].append(latency)
            self.sensor_metrics[sensor_id]['packet_count'] += 1
            self.sensor_metrics[sensor_id]['last_seen'] = time.time()
    
    def get_analysis(self) -> Dict[str, Any]:
        with self.lock:
            latencies = list(self.latency_history)
            avg_latency = statistics.mean(latencies) if latencies else 0
            
            now = time.time()
            throughput_north = 0
            throughput_south = 0
            
            for gw, metrics in self.gateway_metrics.items():
                elapsed = now - metrics['last_update']
                if elapsed < 5:
                    pps = metrics['packets'] / max(elapsed, 1)
                    if 'Norte' in gw:
                        throughput_north += pps
                    else:
                        throughput_south += pps
            
            total_throughput = throughput_north + throughput_south
            queue_size = int(avg_latency / 10) if avg_latency > 10 else 0
            congestion_pct = min(100, (avg_latency / 50) * 100)
            
            congestion_status = {
                'Ruta A (Larga)': min(100, throughput_north * 2),
                'Ruta B (Corta)': min(100, throughput_south * 2)
            }
            
            strategy_dist = [
                self.strategy_counts.get('round_robin', 0),
                self.strategy_counts.get('priority', 0),
                self.strategy_counts.get('load_balance', 0),
                self.strategy_counts.get('shortest_path', 0)
            ]
            
            sensor_data = []
            for sensor_id, metrics in self.sensor_metrics.items():
                sensor_latencies = list(metrics['latencies'])
                sensor_data.append({
                    'id': sensor_id,
                    'type': sensor_id.split('-')[0],
                    'interval': self._estimate_interval(metrics['packet_count']),
                    'packets_sent': metrics['packet_count'],
                    'latency': statistics.mean(sensor_latencies) if sensor_latencies else 0
                })
            
            stats = {
                'latency': self._compute_stats(latencies),
                'throughput': self._compute_stats([total_throughput] * max(len(latencies), 1))
            }
            
            return {
                'avg_latency': avg_latency,
                'total_throughput': total_throughput,
                'throughput_north': throughput_north,
                'throughput_south': throughput_south,
                'queue_size': queue_size,
                'congestion_pct': congestion_pct,
                'congestion_status': congestion_status,
                'strategy_distribution': strategy_dist,
                'sensors': sorted(sensor_data, key=lambda x: x['interval']),
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
    
    def _estimate_interval(self, packet_count: int) -> int:
        if packet_count > 50: return 1
        elif packet_count > 30: return 2
        elif packet_count > 20: return 5
        else: return 10
    
    def _compute_stats(self, data: List[float]) -> Dict[str, float]:
        if not data:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}
        return {
            'min': min(data),
            'max': max(data),
            'mean': statistics.mean(data),
            'std': statistics.stdev(data) if len(data) > 1 else 0
        }
