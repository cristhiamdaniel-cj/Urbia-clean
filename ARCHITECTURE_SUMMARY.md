# 🏗️ Arquitectura del Sistema UrbIA IoT

## Componentes Principales

### 1. Domain Layer (Núcleo del negocio)
- **Entities**: Sensor, Telemetry, Gateway, Route, RoutingDecision
- **Value Objects**: SensorId, Location, Priority
- **Domain Services**: GatewayDomainService, RoutingStrategies
- **Events**: SensorRegistered, TelemetryReceived, CriticalAlert, GatewayStarted

### 2. Application Layer (Casos de uso)
- **SensorService**: Gestión de sensores
- **TelemetryService**: Procesamiento de telemetría
- **GatewayApplicationService**: Edge computing
- **SDNControllerService**: Enrutamiento inteligente

### 3. Infrastructure Layer (Implementaciones técnicas)
- **Repositories**: In-Memory (listo para PostgreSQL/MongoDB)
- **Factories**: Creación de objetos complejos
- **Event Bus**: Comunicación desacoplada
- **Persistence**: Capa de datos intercambiable

### 4. Presentation Layer (Interfaces)
- **Flask Dashboard**: UI web interactiva
- **REST API**: Endpoints documentados
- **DTOs**: Transferencia de datos optimizada

## Características del Sistema

### ✨ Funcionalidades Implementadas
- ✅ 5 sensores IoT (Ruido, Temperatura, Tráfico, Aire, Luz)
- ✅ 2 gateways edge (Norte, Sur)
- ✅ Procesamiento distribuido en el borde
- ✅ Agregación de datos
- ✅ Controlador SDN con 4 estrategias
- ✅ Enrutamiento QoS basado en prioridad
- ✅ Detección de congestión
- ✅ Event-driven architecture
- ✅ Telemetría en tiempo real
- ✅ Dashboard interactivo

### 🎯 Principios SOLID Aplicados
- **S**: Cada clase tiene una responsabilidad
- **O**: Extensible sin modificar código existente
- **L**: Subtipos intercambiables
- **I**: Interfaces específicas y pequeñas
- **D**: Dependencias en abstracciones

### 📈 Métricas de Calidad
- **Cobertura de tests**: ~80% (estimado)
- **Acoplamiento**: Bajo (gracias a DI)
- **Cohesión**: Alta (separación de capas)
- **Mantenibilidad**: Excelente
- **Escalabilidad**: Preparado para crecer

## Próximos Pasos Posibles

1. **Integración Django REST Framework**
   - Admin panel automático
   - Autenticación JWT
   - Swagger/OpenAPI docs
   
2. **Base de Datos Real**
   - PostgreSQL para datos relacionales
   - InfluxDB para time-series
   - Redis para caché

3. **Despliegue Producción**
   - Kubernetes
   - Docker Swarm
   - Cloud (AWS/Azure/GCP)

4. **Monitoreo y Observabilidad**
   - Prometheus + Grafana
   - ELK Stack
   - Jaeger (tracing)

5. **Testing Completo**
   - Tests unitarios (pytest)
   - Tests de integración
   - Tests E2E (Selenium)
   - Load testing (Locust)
