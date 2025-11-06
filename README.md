# 🏙️ UrbIA-Clean  
**Arquitectura Modular IoT–SDN–Edge para Monitoreo Urbano Inteligente**

---

## 📘 Descripción general

**UrbIA-Clean** es una arquitectura modular, abierta y escalable diseñada para integrar **Internet de las Cosas (IoT)**, **Edge/Fog Computing** y **Software Defined Networking (SDN)**.  
El sistema forma parte del proyecto doctoral de **Cristhiam Daniel Campos Julca**, desarrollado con fines académicos, experimentales y de transferencia tecnológica hacia plataformas urbanas inteligentes.

Su propósito es mejorar la **eficiencia energética**, la **gestión de tráfico de datos** y la **resiliencia de redes urbanas**, validando métricas como **latencia**, **throughput**, **tolerancia a fallos** y **consumo energético**.

---

## 🧩 Arquitectura en capas

| Capa | Componentes principales | Descripción |
|------|--------------------------|--------------|
| **Sensorial** | Sensores físicos y simulados (C++, Python) | Generan telemetría ambiental y urbana |
| **Edge/Fog** | Raspberry Pi + router TP-Link ER605 | Procesamiento local, filtrado y reenvío |
| **SDN** | Controlador Ryu + Open vSwitch | Ruteo dinámico y políticas adaptativas |
| **IoT Platform** | ThingsBoard CE + PostgreSQL + MQTT | Gestión de dispositivos, dashboards y persistencia |
| **Presentación** | Flask / Streamlit / CLI Java | Visualización, control y análisis de métricas |

---

## 🧠 Objetivos del sistema

- Implementar una **arquitectura IoT–SDN–Edge replicable** para ciudades intermedias.  
- Validar experimentalmente **latencia y throughput** frente a una arquitectura IoT tradicional.  
- Proveer una base de referencia abierta para futuras líneas de investigación en **automatización**, **energía** y **redes programables**.

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/cristhiamdaniel-cj/Urbia-clean.git
cd Urbia-clean
````

### 2. Crear el archivo `.env`

Duplica el archivo `.env.example` y ajusta tus credenciales locales:

```bash
cp .env.example .env
```

### 3. Levantar el entorno con Docker

```bash
docker-compose up --build
```

Esto iniciará:

* La base de datos PostgreSQL
* La plataforma ThingsBoard CE
* El broker MQTT
* El dashboard Flask/Streamlit del sistema UrbIA

---

## 🧪 Pruebas y validación

El proyecto incluye scripts automatizados de prueba y generación de métricas:

```bash
bash run_tests.sh
```

Los resultados se almacenan en `/results` e incluyen:

* `01_throughput_comparison.png`
* `02_latency_analysis.png`
* `03_scalability.png`
* `04_success_rate.png`
* `05_executive_summary.png`

---

## 🧰 Estructura principal

```
Urbia-clean/
├── config/                # Configuración general
├── sensors/               # Simuladores y tipos de sensores
├── src/                   # Código fuente modular (Domain, Application, Infrastructure, Presentation)
├── dashboard/             # Interfaces y dashboards HTML
├── tests/                 # Pruebas unitarias, integración y rendimiento
├── results/               # Métricas y gráficos generados
├── docs/                  # Diagramas UML y documentación técnica
└── docker-compose.yml     # Orquestación del entorno experimental
```

---

## 🤝 Colaboradores y contexto académico

Este desarrollo se realiza con la colaboración de estudiantes de **Ingeniería Automática, Ingeniería Eléctrica e Ingeniería de Redes**, bajo la tutoría interdisciplinaria de docentes en ambas áreas.

**Autor:** Cristhiam Daniel Campos Julca
**Institución:** Universidad Nacional de Colombia
**Proyecto:** *UrbIA – Arquitectura IoT–SDN–Edge para la gestión energética urbana*
**Licencia:** MIT – Uso académico y de investigación

---



