"""
Generador de Gráficos - VERSIÓN CORREGIDA
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

# Leer resultados
with open('/app/results/load_test_results.json', 'r') as f:
    results = json.load(f)

plt.style.use('seaborn-v0_8-darkgrid')

# GRÁFICO 4: Tasa de Éxito (CORREGIDO)
fig, ax = plt.subplots(figsize=(10, 6))

labels = [r['label'] for r in results]
success_rates = [r['performance']['success_rate'] for r in results]

# CORREGIR: Un color por barra
bar_colors = ['#667eea', '#10b981', '#f59e0b'][:len(labels)]

bars = ax.barh(range(len(labels)), success_rates, color=bar_colors, 
               alpha=0.8, edgecolor='black')

for i, (bar, rate) in enumerate(zip(bars, success_rates)):
    width = bar.get_width()
    ax.text(width - 2, bar.get_y() + bar.get_height()/2.,
            f'{rate:.1f}%',
            ha='right', va='center', fontsize=12, fontweight='bold', color='white')

ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
ax.set_xlabel('Tasa de Exito (%)', fontsize=12, fontweight='bold')
ax.set_title('Confiabilidad del Sistema bajo Carga', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, 105)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('/app/results/04_success_rate.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 4: Tasa de éxito guardado")

# GRÁFICO 5: Resumen Ejecutivo (SIMPLIFICADO)
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

sensors = [r['config']['sensors'] for r in results]
throughputs = [r['performance']['throughput'] for r in results]
latencies = [r['latency']['mean'] for r in results]

# Métrica 1: Throughput máximo
ax1 = fig.add_subplot(gs[0, 0])
max_tput = max(throughputs)
ax1.text(0.5, 0.5, f'{max_tput:.1f}', 
         ha='center', va='center', fontsize=48, fontweight='bold', color='#667eea')
ax1.text(0.5, 0.15, 'pkt/s maximo', 
         ha='center', va='center', fontsize=14, color='#666')
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.axis('off')
ax1.set_title('Throughput Maximo', fontsize=12, fontweight='bold')

# Métrica 2: Latencia mínima
ax2 = fig.add_subplot(gs[0, 1])
min_lat = min(latencies)
ax2.text(0.5, 0.5, f'{min_lat:.2f}', 
         ha='center', va='center', fontsize=48, fontweight='bold', color='#10b981')
ax2.text(0.5, 0.15, 'ms latencia', 
         ha='center', va='center', fontsize=14, color='#666')
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.axis('off')
ax2.set_title('Latencia Minima', fontsize=12, fontweight='bold')

# Métrica 3: Sensores máximos
ax3 = fig.add_subplot(gs[0, 2])
max_sensors = max(sensors)
ax3.text(0.5, 0.5, f'{max_sensors}', 
         ha='center', va='center', fontsize=48, fontweight='bold', color='#f59e0b')
ax3.text(0.5, 0.15, 'sensores probados', 
         ha='center', va='center', fontsize=14, color='#666')
ax3.set_xlim(0, 1)
ax3.set_ylim(0, 1)
ax3.axis('off')
ax3.set_title('Capacidad Probada', fontsize=12, fontweight='bold')

# Gráfico de throughput
ax4 = fig.add_subplot(gs[1, :])
bar_colors = ['#667eea', '#10b981', '#f59e0b']
bars = ax4.bar(sensors, throughputs, color=bar_colors, alpha=0.8, edgecolor='black', width=5)
for bar, t in zip(bars, throughputs):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{t:.1f}',
             ha='center', va='bottom', fontsize=11, fontweight='bold')
ax4.set_xlabel('Numero de Sensores', fontsize=12, fontweight='bold')
ax4.set_ylabel('Throughput (pkt/s)', fontsize=12, fontweight='bold')
ax4.set_title('Rendimiento bajo Diferentes Cargas', fontsize=12, fontweight='bold')
ax4.grid(axis='y', alpha=0.3)

# Tabla de resultados
ax5 = fig.add_subplot(gs[2, :])
ax5.axis('tight')
ax5.axis('off')

table_data = []
table_data.append(['Sensores', 'Duracion', 'Throughput', 'Latencia', 'Exito'])
for r in results:
    table_data.append([
        f"{r['config']['sensors']}",
        f"{r['config']['duration']}s",
        f"{r['performance']['throughput']:.1f} pkt/s",
        f"{r['latency']['mean']:.2f}ms",
        f"{r['performance']['success_rate']:.1f}%"
    ])

table = ax5.table(cellText=table_data, cellLoc='center', loc='center',
                  colWidths=[0.15, 0.15, 0.25, 0.20, 0.15])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Estilo
for i in range(len(table_data)):
    for j in range(len(table_data[0])):
        cell = table[(i, j)]
        if i == 0:
            cell.set_facecolor('#667eea')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor(['#f0f0f0', 'white'][i % 2])

fig.suptitle('RESUMEN EJECUTIVO - PRUEBAS DE CARGA UrbIA IoT',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig('/app/results/05_executive_summary.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 5: Resumen ejecutivo guardado")

print("\n✅ GRÁFICOS 4 Y 5 GENERADOS")
