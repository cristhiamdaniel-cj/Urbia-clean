#!/bin/bash

echo ""
echo "======================================================================"
echo "  🌐 UrbIA IoT - Clean Architecture System"
echo "======================================================================"
echo ""

# Limpiar
echo "🧹 Limpiando contenedores anteriores..."
docker-compose down 2>/dev/null

# Construir
echo ""
echo "🏗️  Construyendo imagen Docker..."
docker-compose build

# Iniciar
echo ""
echo "🚀 Iniciando sistema..."
docker-compose up -d

# Esperar
echo ""
echo "⏳ Esperando 15 segundos para inicialización..."
sleep 15

# Verificar
echo ""
echo "🔍 Verificando estado..."
docker-compose ps

echo ""
echo "======================================================================"
echo "  ✅ Sistema Iniciado"
echo "======================================================================"
echo ""
echo "  📱 Dashboard:  http://localhost:5000"
echo "  📊 API:        http://localhost:5000/api/sensors"
echo "  🔧 Ver logs:   docker-compose logs -f"
echo "  ⏹️  Detener:    docker-compose down"
echo ""
echo "======================================================================"
echo ""
