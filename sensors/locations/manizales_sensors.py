"""
Configuración de sensores en Manizales
Compatible con Clean Architecture
"""

MANIZALES_SENSORS = [
    {
        'id': 'NOISE-001',
        'nombre': 'Monitor de Ruido - Parque Caldas',
        'tipo': 'RUIDO',
        'ubicacion': {
            'lat': 5.0689,
            'lng': -75.5174,
            'direccion': 'Parque Caldas, Centro',
            'ciudad': 'Manizales'
        },
        'prioridad': 'CRITICA',
        'intervalo': 10
    },
    {
        'id': 'TEMP-001',
        'nombre': 'Sensor de Temperatura - Universidad Nacional',
        'tipo': 'TEMPERATURA',
        'ubicacion': {
            'lat': 5.0536,
            'lng': -75.4909,
            'direccion': 'Universidad Nacional, Palogrande',
            'ciudad': 'Manizales'
        },
        'prioridad': 'NORMAL',
        'intervalo': 30
    },
    {
        'id': 'TRAFFIC-001',
        'nombre': 'Monitor de Tráfico - Av. Santander',
        'tipo': 'TRAFICO',
        'ubicacion': {
            'lat': 5.0702,
            'lng': -75.5138,
            'direccion': 'Avenida Santander',
            'ciudad': 'Manizales'
        },
        'prioridad': 'CRITICA',
        'intervalo': 5
    },
    {
        'id': 'AIR-001',
        'nombre': 'Calidad del Aire - Cable Aéreo',
        'tipo': 'CALIDAD_AIRE',
        'ubicacion': {
            'lat': 5.0407,
            'lng': -75.4813,
            'direccion': 'Estación Cable, Los Cámbulos',
            'ciudad': 'Manizales'
        },
        'prioridad': 'NORMAL',
        'intervalo': 60
    },
    {
        'id': 'LIGHT-001',
        'nombre': 'Iluminación Pública - Chipre',
        'tipo': 'LUZ',
        'ubicacion': {
            'lat': 5.0629,
            'lng': -75.5048,
            'direccion': 'Barrio Chipre',
            'ciudad': 'Manizales'
        },
        'prioridad': 'BAJA',
        'intervalo': 120
    }
]
