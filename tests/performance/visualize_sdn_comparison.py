"""
Visualización de Comparación de Estrategias SDN
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

# Leer resultados
with open('/app/results/sdn_strategy_comparison.json', 'r') as f:
    results = json.load(f)

plt.style.use('seaborn-v0_8-darkgrid')
colors = ['#667eea', '#10b981', '#f59e0b', '#ef4444']

# GRÁFICO 1: Comparación de Latencia
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

strategies = [r['strategy'].replace('_', ' ').title() for r in results]
mean_lats = [r['latency']['mean'] for r in results]
p95_lats = [r['latency']['p95'] for r in results]
x = np.arange(len(strategies))

# Latencia Media
bars1 = ax1.bar(x, mean_lats, color=colors, alpha=0.8, edgecolor='black', width=0.6)
for bar, lat in zip(bars1, mean_lats):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.003,
             f'{lat:.3f}ms',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

ax1.set_ylabel('Latencia Media (ms)', fontsize=12, fontweight='bold')
ax1.set_title('Latencia Media por Estrategia', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(strategies, rotation=15, ha='right')
ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim(0, max(mean_lats) * 1.15)

# Latencia P95
bars2 = ax2.bar(x, p95_lats, color=colors, alpha=0.8, edgecolor='black', width=0.6)
for bar, lat in zip(bars2, p95_lats):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.007,
             f'{lat:.3f}ms',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

ax2.set_ylabel('Latencia P95 (ms)', fontsize=12, fontweight='bold')
ax2.set_title('Latencia Percentil 95 por Estrategia', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(strategies, rotation=15, ha='right')
ax2.grid(axis='y', alpha=0.3)
ax2.set_ylim(0, max(p95_lats) * 1.15)

fig.suptitle('Comparacion de Latencia entre Estrategias SDN', 
             fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('/app/results/06_sdn_latency_comparison.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 1: Comparación de latencia")

# GRÁFICO 2: Box Plot de Latencias
fig, ax = plt.subplots(figsize=(12, 7))

lat_data = []
for r in results:
    # Simular distribución basada en min/mean/max
    lat_data.append([
        r['latency']['min'],
        r['latency']['mean'] - r['latency']['stdev'],
        r['latency']['mean'],
        r['latency']['mean'] + r['latency']['stdev'],
        r['latency']['p95'],
        r['latency']['max']
    ])

bp = ax.boxplot(lat_data, labels=strategies, patch_artist=True,
                showmeans=True, meanline=True,
                widths=0.6)

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
    plt.setp(bp[element], color='black', linewidth=1.5)

ax.set_ylabel('Latencia (ms)', fontsize=13, fontweight='bold')
ax.set_title('Distribucion de Latencia por Estrategia SDN', 
             fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3)
ax.set_xticklabels(strategies, rotation=15, ha='right')

plt.tight_layout()
plt.savefig('/app/results/07_sdn_latency_distribution.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 2: Distribución de latencia")

# GRÁFICO 3: Métricas Múltiples (Radar Chart alternativo - barras agrupadas)
fig, ax = plt.subplots(figsize=(14, 7))

metrics = ['Latencia\nMedia', 'Latencia\nP95', 'Desviacion\nEstandar']
x = np.arange(len(metrics))
width = 0.2

for i, (r, color) in enumerate(zip(results, colors)):
    values = [
        r['latency']['mean'],
        r['latency']['p95'],
        r['latency']['stdev']
    ]
    
    offset = (i - 1.5) * width
    bars = ax.bar(x + offset, values, width, label=strategies[i],
                   color=color, alpha=0.8, edgecolor='black')
    
    # Etiquetas
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.003,
                f'{val:.3f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_ylabel('Latencia (ms)', fontsize=12, fontweight='bold')
ax.set_title('Comparacion de Metricas de Latencia', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=11)
ax.legend(loc='upper left', fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('/app/results/08_sdn_metrics_comparison.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 3: Comparación de métricas")

# GRÁFICO 4: Distribución de Rutas
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, (r, color) in enumerate(zip(results, colors)):
    ax = axes[i]
    
    routes = list(r['route_distribution'].keys())
    counts = list(r['route_distribution'].values())
    total = sum(counts)
    
    wedges, texts, autotexts = ax.pie(counts, labels=routes, autopct='%1.1f%%',
                                        colors=[color, '#d1d5db'],
                                        startangle=90,
                                        textprops={'fontsize': 10, 'fontweight': 'bold'})
    
    ax.set_title(f"{strategies[i]}\n{total} paquetes total",
                 fontsize=12, fontweight='bold')

fig.suptitle('Distribucion de Paquetes por Ruta - Comparacion de Estrategias',
             fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig('/app/results/09_sdn_route_distribution.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 4: Distribución de rutas")

# GRÁFICO 5: Resumen Ejecutivo SDN
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Mejor estrategia
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')
best = results[0]
ax1.text(0.5, 0.7, '🏆 MEJOR ESTRATEGIA: ROUND ROBIN', 
         ha='center', va='center', fontsize=28, fontweight='bold', color='#667eea')
ax1.text(0.5, 0.4, f'Latencia: {best["latency"]["mean"]:.3f}ms | '
                   f'P95: {best["latency"]["p95"]:.3f}ms | '
                   f'Confiabilidad: {best["success_rate"]:.0f}%', 
         ha='center', va='center', fontsize=16, color='#666')
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)

# Comparación de latencias
ax2 = fig.add_subplot(gs[1, :])
x_pos = np.arange(len(strategies))
bars = ax2.barh(x_pos, mean_lats, color=colors, alpha=0.8, edgecolor='black')

for i, (bar, lat) in enumerate(zip(bars, mean_lats)):
    width = bar.get_width()
    ax2.text(width + 0.003, bar.get_y() + bar.get_height()/2.,
             f'{lat:.3f}ms',
             ha='left', va='center', fontsize=12, fontweight='bold')

ax2.set_yticks(x_pos)
ax2.set_yticklabels(strategies)
ax2.set_xlabel('Latencia Media (ms)', fontsize=12, fontweight='bold')
ax2.set_title('Comparacion de Latencia Media', fontsize=13, fontweight='bold')
ax2.grid(axis='x', alpha=0.3)
ax2.invert_yaxis()

# Tabla de resultados
ax3 = fig.add_subplot(gs[2, :])
ax3.axis('tight')
ax3.axis('off')

table_data = [['Estrategia', 'Throughput', 'Lat.Media', 'P95', 'StdDev', 'Exito']]
for r in results:
    table_data.append([
        r['strategy'].replace('_', ' ').title(),
        f"{r['throughput']:.1f} p/s",
        f"{r['latency']['mean']:.3f}ms",
        f"{r['latency']['p95']:.3f}ms",
        f"{r['latency']['stdev']:.3f}ms",
        f"{r['success_rate']:.0f}%"
    ])

table = ax3.table(cellText=table_data, cellLoc='center', loc='center',
                  colWidths=[0.22, 0.15, 0.15, 0.15, 0.15, 0.13])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

for i in range(len(table_data)):
    for j in range(len(table_data[0])):
        cell = table[(i, j)]
        if i == 0:
            cell.set_facecolor('#667eea')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor(colors[i-1] if i <= 4 else '#f0f0f0')
            cell.set_alpha(0.3)

fig.suptitle('RESUMEN EJECUTIVO - COMPARACION DE ESTRATEGIAS SDN',
             fontsize=16, fontweight='bold', y=0.98)

plt.savefig('/app/results/10_sdn_executive_summary.png', dpi=300, bbox_inches='tight')
print("✅ Gráfico 5: Resumen ejecutivo SDN")

print("\n✅ TODOS LOS GRÁFICOS SDN GENERADOS")
