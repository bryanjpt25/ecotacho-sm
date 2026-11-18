# ♻️ EcoTacho SM

Repositorio oficial para el desarrollo del prototipo de sistema inteligente de clasificación de residuos para el **Hackathon Smart City San Marcos 2026** (CITE / FIEE - UNMSM), desafío **Medio ambiente**. Evento presencial: **miércoles 2 de diciembre de 2026, 9:00–17:00**.

---

## 👥 Asignación de Roles y Responsabilidades

- **Álvaro** (`alvaro/`): **Electrónico 1 (HW / Sensors)** – Ensamblaje de hardware, divisores de tensión 5V/3.3V (HC-SR04), acondicionamiento de celda de carga HX711, filtro de media móvil en C++, fuente de alimentación (5V/5A), PCB perforada, calibración de escala y umbrales de llenado (>85%).
- **Bryan** (`bryan/`): **Electrónico 2 (Edge AI)** – Entorno ESP32-CAM MB, cámara OV2640, captura de dataset (Edge Impulse), entrenamiento/cuantización INT8 en C++, inferencia local TinyML en serie, pantalla LCD 16x2 I2C e integración de umbrales de confianza (>70%).
- **Sadith** (`sadith/`): **Telecom 1 (MQTT Network)** – Broker Mosquitto local/nube, arquitectura de tópicos MQTT, políticas QoS, integración de `PubSubClient`, tareas no bloqueantes (`millis()`), `Last Will and Testament` (LWT) y resiliencia de reconexión Wi-Fi.
- **Maricielo** (`maricielo/`): **Telecom 2 (Cloud Backend)** – Aprovisionamiento de VPS/servidor local, despliegue Docker (Mosquitto + MongoDB), esquemas de colecciones en Mongo (`telemetry_logs`, `classification_history`), API Node.js/FastAPI (bridge MQTT ➔ Mongo) y WebSocket server.
- **Milagros** (`milagros/`): **Telecom 3 (Full-Stack)** – Diseños UI/UX y wireframes en Figma, maquetación de tarjetas/gráficos estáticos, conexión frontend a WebSockets/API de MongoDB, visualización de métricas en tiempo real y preparación del Pitch de 3 a 5 minutos.

---

## 🏗️ Arquitectura del Sistema IoT & Data Pipeline

```text
[ ENTORNO FÍSICO (NODO ECO PUNTO) ]                                 [ CLOUD & WEB (BACKEND) ]
                                                                             
      +-------------------------+                                     +--------------------------+
      |      EDGE AI NODE       |                                     |      SMART CITY VPS      |
      |  (ESP32-CAM MB Base)    |          MQTT (WiFi)                |                          |
[O]===| OV2640 Camera           |===========================\         |  +--------------------+  |
      | TinyML (Edge Impulse)   |                           |         |  | MQTT Broker (QoS 1)|  |
      | LCD 16x2 I2C (Local)    |                           |========>|  | (Mosquitto/EMQX)   |  |
      +-------------------------+                           |         |  +---------+----------+  |
                                                            |         |            |             |
      +-------------------------+                           |         |  +---------v----------+  |
      |    TELEMETRY NODE       |          MQTT (WiFi)      |         |  |   Ingestion API    |  |
      |       (ESP32)           |                           |         |  | (FastAPI/Node.js)  |  |
      | HC-SR04 (Ultrasonico)   |===========================/         |  +----+----------+----+  |
      | HX711 + Celdas de Carga |                                     |       |          |       |
      | Filtro de Media Móvil   |                                     | +-----v---+ +----v-----+ |
      | Fuente 5V 5A (Estable)  |                                     | | MongoDB | | WebSocket| |
      +-------------------------+                                     | |(Atlas/  | |  Server  | |
                                                                      | | Local)  | |          | |
                                                                      | +---------+ +----+-----+ |
                                                                      +------------------|-------+
                                                                                         | 
                                                                               [ PRESENTATION ]
                                                                      +------------------v-------+
                                                                      |   DASHBOARD WEB (UI)     |
                                                                      | (React / Streamlit)      |
                                                                      +--------------------------+
```

## 📅 Plan y documentación

La hoja de ruta de 4 semanas fue reemplazada por un plan de **14 días** (el evento es el 2 de dic). Todo está en `docs/`:

| Documento | Contenido |
|-----------|-----------|
| [`docs/contratos.md`](docs/contratos.md) | **Fuente de verdad:** tópicos MQTT, JSON, MongoDB, REST, WebSocket (esquemas en `contracts/`) |
| [`docs/02-hardware-pinout.md`](docs/02-hardware-pinout.md) | Pinout corregido, energía, calibración, comprobaciones |
| [`docs/03-plan-14-dias.md`](docs/03-plan-14-dias.md) | Hitos, gates y matriz *funciona / se simula / falta* |
| [`docs/04-bom-y-costos.md`](docs/04-bom-y-costos.md) | BOM estimada (reemplazar con boletas reales) |
| [`docs/05-impacto-y-linea-base.md`](docs/05-impacto-y-linea-base.md) | Línea base, KPIs, cálculo de impacto sin inventar cifras |
| [`docs/06-ficha-del-proyecto.md`](docs/06-ficha-del-proyecto.md) | Borrador de la ficha pedida por las bases |
| [`docs/07-pitch-y-declaracion-ia.md`](docs/07-pitch-y-declaracion-ia.md) | Guion, rúbrica oficial, preguntas del jurado, declaración de IA |

Validar contratos: `pip install jsonschema && python contracts/validate_examples.py`.

> **Repositorio público:** nunca subir SSID, contraseñas ni claves. Usar `secrets.h` / `.env` (ignorados) y archivos `*.example`.

---

## 🎯 Módulos Demostrables Core (Demo Day)

1. **Inferencia Edge en Tiempo Real (Demo Local):** El juez aproxima un envase a la cámara. En fracciones de segundo, la rutina TinyML procesa la imagen usando solo RAM y PSRAM, mostrando "PLÁSTICO" en el LCD (sin depender de red; latencia a medir).
2. **Sincronización Cloud con MongoDB (Data Pipeline):** Al clasificar y depositar el objeto, ambos nodos publican sus eventos y el backend los correlaciona. La API captura esto e inserta un nuevo documento en MongoDB. El Dashboard consulta la base de datos y actualiza las gráficas web (meta: < 2 s en red local).
3. **Resiliencia y Health-Checks:** Si el módulo pierde Wi-Fi, no se bloquea. Cuando la red vuelve, el sistema se reconecta automáticamente, garantizando que el flujo de datos hacia MongoDB se retome sin resetear hardware.

---

## 📁 Estructura del Repositorio

```text
├── alvaro/           # Sensores, PCB, HX711, HC-SR04 y alimentación (Electrónico 1)
├── bryan/            # ESP32-CAM, TinyML (INT8), OV2640 e LCD 16x2 (Electrónico 2)
├── maricielo/        # Docker, MongoDB, API Node.js/FastAPI y WebSockets (Telecom 2)
├── milagros/         # Figma, UI/UX Frontend, WebSockets client y Pitch (Telecom 3)
├── sadith/           # MQTT Broker Mosquitto, PubSubClient, LWT y Wi-Fi (Telecom 1)
├── data/             # Datasets de prueba locales y logs (excluidos por .gitignore)
├── docs/             # Contratos, plan, BOM, impacto, ficha y pitch
├── contracts/        # JSON Schemas y ejemplos validables
├── .gitignore        # Reglas de exclusión de binarios, .env y temporales
├── app.py            # Servidor / API de integración local
└── requirements.txt  # Dependencias del proyecto
```
