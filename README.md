# ♻️ EcoTacho SM

Repositorio oficial para el desarrollo del prototipo de sistema inteligente de clasificación de residuos (**Eco Punto Smart**) para el Hackathon CITE - UNMSM[cite: 2].

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

## 📅 Hoja de Ruta de Desarrollo (4 Semanas) 

### 🔹 Semana 1: Arquitectura, Adquisición de Datasets y Pruebas de Concepto (PoC)
- **Álvaro:** Ensamblar protoboard del ESP32 estándar. Implementar divisores de tensión para lecturas lógicas de 5V a 3.3V (HC-SR04). Verificar lecturas RAW del HX711. Integrar y probar fuente de poder de 5V 5A (tipo adaptador).
- **Bryan:** Configurar IDE con la plataforma base ESP32-CAM MB (conexión directa por micro-USB). Habilitar cámara OV2640 y recopilar dataset de basura usando Edge Impulse Data Forwarder.
- **Sadith:** Levantar broker Mosquitto en red local/nube. Diseñar árbol de tópicos MQTT y definir políticas QoS.
- **Maricielo:** Aprovisionar VPS o entorno local. Desplegar contenedores Docker (Broker MQTT y MongoDB). Diseñar los esquemas de colecciones en Mongo (`telemetry_logs`, `classification_history`).
- **Milagros:** Diseñar wireframes (Figma) del dashboard enfocado en visualización de datos extraídos desde MongoDB.

### 🔹 Semana 2: Entrenamiento del Modelo AI, Ensamblaje de Hardware y Backend
- **Álvaro:** Migrar de protoboard a PCB perforada. Programar script en C++ con filtro de media móvil y rutina de tara.
- **Bryan:** Entrenar modelo en la nube (Edge Impulse). Aplicar cuantización INT8 y exportarlo como librería C++. Desplegar el código en la ESP32-CAM y probar inferencia por puerto serial.
- **Sadith:** Integrar librería `PubSubClient`. Implementar rutinas no bloqueantes con `millis()` y configurar el Last Will and Testament (LWT) para health-checks.
- **Maricielo:** Desarrollar API (Node.js/FastAPI) que actúe como puente: se suscribe al broker MQTT y ejecuta operaciones `insertOne()` y `find()` en MongoDB de manera asíncrona.
- **Milagros:** Maquetar componentes estáticos del dashboard (tarjetas de estado, gráficos de barras).

### 🔹 Semana 3: Integración de Sistemas (Nodos ESP32 + Nube) y Calibración
- **Álvaro:** Integrar sensores en el chasis. Calibrar factor de escala del HX711. Ajustar umbrales de "Tacho Lleno" (>85% volumen).
- **Bryan:** Conectar pantalla LCD 16x2 vía I2C a la ESP32-CAM. Programar lógica C++ para reflejar instrucción al usuario ("Plástico detectado") post-inferencia.
- **Sadith:** Establecer comunicación bidireccional estable vía Wi-Fi, asegurando que los fallos de lectura en MicroSD sean irrelevantes al derivar toda la data a la nube.
- **Maricielo:** Implementar servidor WebSocket puenteado a MongoDB/Broker para pushing en tiempo real hacia el frontend (sin necesidad de recargar la página).
- **Milagros:** Conectar frontend a la API/WebSockets. Consultar colecciones de MongoDB para poblar gráficos históricos de recolección mensual.

### 🔹 Semana 4: Desarrollo del Dashboard, Pruebas de Estrés y Preparación del Pitch
- **Álvaro & Bryan:** Pruebas de borde: variaciones de iluminación para la OV2640, confirmación de voltajes estables y ajuste de umbrales de confianza (>70%) para evitar falsos positivos. Gestión de cableado.
- **Sadith & Maricielo:** Pruebas de resiliencia Wi-Fi. Verificar reconexión automática y asegurar que el driver de MongoDB en el backend maneje correctamente los picos de ingesta de datos.
- **Milagros:** Pulido UI/UX. Ensayos cronometrados del pitch (3-5 minutos).

---

## 🎯 Módulos Demostrables Core (Demo Day)

1. **Inferencia Edge en Tiempo Real (Demo Local):** El juez aproxima un envase a la cámara. En fracciones de segundo, la rutina TinyML procesa la imagen usando solo RAM y PSRAM, mostrando "PLÁSTICO" en el LCD (latencia cercana a cero, sin depender de red).
2. **Sincronización Cloud con MongoDB (Data Pipeline):** Al clasificar y depositar el objeto, ambos ESP32 publican su telemetría. La API captura esto e inserta un nuevo documento en MongoDB. El Dashboard consulta la base de datos y actualiza las gráficas web en < 1 segundo.
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
├── .gitignore        # Reglas de exclusión de binarios, .env y temporales
├── app.py            # Servidor / API de integración local
└── requirements.txt  # Dependencias del proyecto