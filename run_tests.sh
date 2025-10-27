#!/bin/bash
echo "🧪 Ejecutando Tests Unitarios y de Integración"
echo "=============================================="
echo ""

# Instalar pytest si no está
pip install pytest pytest-cov --break-system-packages 2>/dev/null

# Ejecutar tests
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo ""
echo "✅ Tests completados"
