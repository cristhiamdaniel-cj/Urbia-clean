# Arquitectura Detallada del Sistema UrbIA IoT

## Diagrama de Arquitectura en Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   REST API   │  │  Web Dashboard│ │  CLI Tools   │           │
│  │  (Flask)     │  │   (HTML/JS)   │ │   (Python)   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Services: SensorService, TelemetryService, SDNService   │    │
│  │  DTOs: SensorDTO, TelemetryDTO                           │    │
│  │  Use Cases: RegisterSensor, ProcessTelemetry             │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Entities    │  │ Value Objects│  │ Repositories │           │
│  │  - Sensor    │  │  - Location  │  │ (Interfaces) │           │
│  │  - Gateway   │  │  - Priority  │  │              │           │
│  │  - Telemetry │  │  - SensorId  │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Domain Services: RoutingStrategy, GatewayService        │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Persistence  │  │   SDN/Edge   │  │   Analysis   │           │
│  │  - Memory    │  │  Controller  │  │   SDNAnalyzer│           │
│  │  - Loaders   │  │  - Routing   │  │  - Metrics   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │  Factories   │  │   Adapters   │                              │
│  │  - Sensor    │  │  - Legacy    │                              │
│  │  - Gateway   │  │              │                              │
│  └──────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Descripción de Cada Capa

### 1. Domain Layer (Núcleo del Negocio)

#### Entities (src/domain/entities/)

Objetos con identidad única y ciclo de vida propio.

| Entidad         | Responsabilidad               | Atributos Principales                    |
| --------------- | ----------------------------- | ---------------------------------------- |
| Sensor          | Representa un dispositivo IoT | id, name, type, location, priority       |
| Gateway         | Nodo Edge que agrupa sensores | id, name, location, sensors[]            |
| Telemetry       | Lectura de telemetría         | sensor_id, value, timestamp, is_critical |
| Route           | Ruta de red SDN               | id, name, latency, capacity              |
| RoutingDecision | Decisión de enrutamiento      | sensor_id, route, strategy, timestamp    |

#### Value Objects (src/domain/value_objects/)

Objetos inmutables sin identidad.

| Value Object | Propósito                          | Validaciones                          |
| ------------ | ---------------------------------- | ------------------------------------- |
| Location     | Representa coordenadas geográficas | lat, lng válidos (-90,90), (-180,180) |
| Priority     | Nivel de prioridad                 | Enum: CRITICAL, HIGH, NORMAL, LOW     |
| SensorId     | Identificador único                | Formato validado (ej. NOISE-001)      |

#### Repositories (Interfaces)

Abstracciones para el manejo de persistencia.

```python
# src/domain/repositories/sensor_repository.py
class SensorRepository(ABC):
    @abstractmethod
    def save(self, sensor: Sensor) -> None: pass
    
    @abstractmethod
    def find_by_id(self, sensor_id: str) -> Optional[Sensor]: pass
    
    @abstractmethod
    def find_all(self) -> List[Sensor]: pass
```

#### Domain Services

Contienen la lógica de negocio compleja que no pertenece a una sola entidad.

* RoutingStrategy: Estrategias de enrutamiento SDN.
* GatewayService: Lógica de asignación entre sensores y gateways.

---

### 2. Application Layer (Orquestación)

#### Services (src/application/services/)

Coordina los casos de uso y orquesta las operaciones del dominio.

| Servicio             | Responsabilidad              |
| -------------------- | ---------------------------- |
| SensorService        | Gestión CRUD de sensores     |
| TelemetryService     | Procesamiento de telemetría  |
| GatewayService       | Administración de gateways   |
| SDNControllerService | Control del enrutamiento SDN |

#### DTOs (Data Transfer Objects)

Objetos para transferencia de datos entre capas.

```python
# src/application/dto/sensor_dto.py
@dataclass
class SensorDTO:
    id: str
    name: str
    type: str
    location: Dict
    priority: str
    last_reading: Optional[Dict]
```

#### Use Cases (src/application/use_cases/)

Casos de uso específicos del negocio.

---

### 3. Infrastructure Layer (Implementaciones)

#### Persistence (src/infrastructure/persistence/)

Implementaciones concretas de los repositorios del dominio.

* MemorySensorRepository: Almacenamiento en memoria.
* MemoryGatewayRepository: Almacenamiento temporal de gateways.
* SensorLoader: Carga inicial desde JSON.
* AdvancedSensorLoader: Carga extendida de sensores avanzados.

#### Factories (src/infrastructure/factories/)

Creación de objetos complejos a partir de configuraciones.

```python
# sensor_factory.py
class SensorFactory:
    def create_noise_sensor(self, config: dict) -> Sensor
    def create_temperature_sensor(self, config: dict) -> Sensor
```

#### Analysis (src/infrastructure/analysis/)

Módulo de análisis estadístico y matemático en tiempo real.

Métricas principales:

* Latencia promedio, mínima y máxima.
* Throughput por gateway.
* Congestión por ruta.
* Distribución de estrategias.
* Estadísticas descriptivas generales.

#### Adapters (src/infrastructure/adapters/)

Adaptadores para integración con sistemas heredados.

* LegacySensorAdapter: Permite compatibilidad con sensores antiguos.

---

### 4. Presentation Layer (Interfaces)

#### API REST (src/presentation/api/routes/)

Endpoints disponibles:

```
GET  /api/sensors              - Lista de sensores
GET  /api/telemetry/current    - Telemetría actual
GET  /api/metrics              - Métricas del sistema
GET  /api/events               - Eventos SDN
GET  /api/sdn-analysis         - Análisis matemático
```

#### Web Dashboard (src/presentation/web/)

Aplicación Flask con vistas HTML y análisis de datos.

Templates principales:

* index_iot_filtered.html
* analysis_dashboard.html
* network_topology_dynamic.html
* api_documentation.html
* admin_panel.html

#### CLI (src/presentation/cli/)

Herramientas de línea de comandos para interacción avanzada.

---

## Shared Layer (Transversal)

### Events (src/shared/events/)

Definición de eventos del dominio.

```python
class DomainEvent(ABC): pass

class SensorRegistered(DomainEvent)
class TelemetryReceived(DomainEvent)
class CriticalAlertTriggered(DomainEvent)
```

### Exceptions (src/shared/exceptions/)

Excepciones controladas del dominio.

```python
class SensorNotFoundException(DomainException)
class InvalidSensorIdException(DomainException)
class TelemetryProcessingException(DomainException)
```

---

## Estrategia de Pruebas

### Unit Tests (tests/unit/)

* test_sensor_service.py
* test_telemetry_service.py
* test_sdn_controller.py
* test_sensor_factory.py

### Integration Tests (tests/integration/)

* test_api_endpoints.py

Cobertura actual: superior al 80%.

---

## Contribuciones a la Investigación

1. **Arquitectura Limpia en IoT**
   Implementación documentada de Clean Architecture aplicada a sistemas urbanos inteligentes.

2. **Controlador SDN para Smart Cities**
   Uso de estrategias adaptativas de enrutamiento (Round Robin, Shortest Path, Priority-Based, Load Balancing).

3. **Análisis Matemático en Tiempo Real**
   Sistema de métricas con análisis de latencia, throughput y congestión de red.

4. **Escalabilidad Demostrada**
   Pruebas con 15 sensores, intervalos de lectura variables y throughput superior a 1100 paquetes por segundo.

---

## Métricas del Proyecto

* Líneas de código Python: aproximadamente 3.000
* Archivos Python: más de 60
* Templates HTML: 11
* Capas arquitectónicas: 4
* Principios SOLID cumplidos: 5/5
* Cobertura de pruebas: superior al 80%

**Complejidad Arquitectónica:**

* Entidades del dominio: 5
* Value Objects: 3
* Servicios de aplicación: 4
* Repositorios: 3
* Factories: 2
* Estrategias SDN: 4

---

## Despliegue

### Docker

```yaml
services:
  urbia:
    build: .
    ports:
      - "5001:5000"
    volumes:
      - ./logs:/app/logs
```

### Inicio del Servicio

```bash
docker-compose up -d
```

Servicios disponibles:

* Dashboard: [http://localhost:5001/](http://localhost:5001/)
* API: [http://localhost:5001/api/](http://localhost:5001/api/)
* Documentación: [http://localhost:5001/api-docs](http://localhost:5001/api-docs)

---

## Referencias Bibliográficas Sugeridas

1. Martin, R. C. (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design.* Prentice Hall.
2. Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software.* Addison-Wesley.
3. Kreutz, D., Ramos, F., Verissimo, P., et al. (2015). *Software-defined networking: A comprehensive survey.* *Proceedings of the IEEE.*
4. Mineraud, J., Mazhelis, O., Su, X., & Tarkoma, S. (2016). *A gap analysis of Internet-of-Things platforms.* *Computer Communications.*

---

**Autor:** Doctorando en Ingeniería
**Universidad:** Universidad Nacional de Colombia – Sede Manizales
**Fecha:** Octubre de 2025

---
