# EcoTacho SM — Contratos Técnicos e Interfaces (v1.5)

| Campo | Valor |
|---|---|
| Versión | 1.5 (borrador) |
| Fecha | 18-nov-2026 |
| Autor | Bryan |
| Estado | Borrador; los puntos marcados **(propuesta)** son decisiones de diseño ajustables |

Identificador de tacho por defecto: `tacho-unmsm-01`

## 0. Convenciones

* JSON en UTF-8, claves en `snake_case`, un objeto por mensaje.
* `tacho_id` se toma **del tópico**, no del JSON.
* Los nodos **no envían fecha/hora**. El backend agrega `received_at` (UTC, ISO-8601).
* `uptime_ms` solo sirve para ordenar eventos de un mismo nodo; no es hora.
* Valores de `{nodo}`: `sensores` (ESP32: HX711 + HC-SR04) y `vision` (ESP32-CAM + LCD).
* Hora de Lima (UTC−5) solo se aplica al mostrar en el dashboard.

---

## 1. Tópicos MQTT (QoS 0)

| Tópico | Dirección | Descripción |
| :--- | :--- | :--- |
| `ecotacho/{id}/vision/evento` | ESP32-CAM → Broker | Clasificación estable de un objeto |
| `ecotacho/{id}/peso/evento` | ESP32 → Broker | Variación de peso ya estabilizada |
| `ecotacho/{id}/telemetria` | ESP32 → Broker | Peso total y volumen, cada 5 s |
| `ecotacho/{id}/estado/{nodo}` | Nodo → Broker | LWT / estado, *retained* |

Los eventos usan QoS 0 (PubSubClient); la pérdida se compensa con `event_id` único y deduplicación en el backend.

---

## 2. Esquemas JSON

### 2.1 Visión (`ecotacho/{id}/vision/evento`)
```json
{
  "event_id": "v-3fa9-000123",
  "clase": "plastico",
  "confianza": 0.82,
  "fuente": "ia",
  "uptime_ms": 123456
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `event_id` | string | Prefijo `v-` + nonce hexa de arranque (4–8 caracteres) + `-` + contador de 6 dígitos |
| `clase` | string | `vacio`, `plastico`, `papel_carton`, `otros`, `no_seguro` |
| `confianza` | número 0–1, o `null` | `null` si `fuente` es `manual` |
| `fuente` | string | `ia` o `manual` (Plan B con botones) |
| `uptime_ms` | entero ≥ 0 | Milisegundos desde el arranque del nodo |

Reglas de publicación:
* Se publica una clase solo tras **≥ 3 cuadros seguidos** con `confianza ≥ 0.70`, después de un `vacio`.
* Con `confianza < 0.70` se publica `clase: "no_seguro"` con la confianza medida.
* **(propuesta)** Un solo evento por objeto: no se publica otro hasta volver a ver `vacio`.
* La clase `vacio` se publica como evento, pero no se correlaciona con peso.

### 2.2 Peso (`ecotacho/{id}/peso/evento`)
```json
{
  "event_id": "p-91c2-000087",
  "delta_kg": 0.31,
  "peso_total_kg": 1.25,
  "uptime_ms": 123900
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `event_id` | string | Prefijo `p-` + nonce + contador, igual que en visión |
| `delta_kg` | número | **Positivo** = depósito; **negativo** = retiro o vaciado |
| `peso_total_kg` | número ≥ 0 | Peso total tras estabilizarse (≥ 2 s) |
| `uptime_ms` | entero ≥ 0 | Igual que en visión |

El nodo publica solo cuando el peso se estabiliza y el cambio supera el umbral de ruido medido en calibración.

### 2.3 Telemetría (`ecotacho/{id}/telemetria`)
```json
{
  "volumen_pct": 45,
  "peso_total_kg": 1.25,
  "uptime_ms": 124000
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `volumen_pct` | número 0–100 | Estimación por ultrasonido (mediana de 5 muestras) |
| `peso_total_kg` | número ≥ 0 | Peso actual |
| `uptime_ms` | entero ≥ 0 | |

`alerta_llenado` **no** la calcula el nodo: la calcula el backend (se activa en 85 % y se limpia en 70 %).

### 2.4 Estado (`ecotacho/{id}/estado/{nodo}`)

Payload en **texto plano**, sin JSON: `online` u `offline`. Mensaje *retained*; `offline` lo publica el broker como LWT.

Los mensajes retenidos que el broker repite al reconectar el backend actualizan `estado`, pero **no** `last_seen`: solo un mensaje recibido en vivo lo actualiza. Si el estado de un nodo se conoce únicamente por un mensaje retenido, `last_seen` es `null`. Un retenido se difunde por WebSocket solo si cambia el estado. Los demás tópicos no deben publicarse como retained; el backend ignora los que lleguen así.

---

## 3. Lógica de correlación (backend)

1. **Ventana:** 8 s configurables entre `vision/evento` y `peso/evento`.
2. **Cola FIFO (propuesta):** las visiones pendientes (clase distinta de `vacio`) se ordenan por llegada; cada `peso/evento` con `delta_kg` positivo consume la más antigua dentro de la ventana.
3. **Resultados:**
   * Visión + peso en ventana → `deposits` con `clase` y `delta_kg`; la visión queda `correlacionado`.
   * Peso sin visión previa → `deposits` con `clase: "sin_clasificar"`.
   * Visión sin peso tras 8 s → `classification_events` con `estado_correlacion: "sin_peso"`.
   * Visión con `no_seguro` → se correlaciona normalmente y el depósito queda con `clase: "no_seguro"`.
4. **Peso negativo (propuesta):** no crea depósito; se registra en `telemetry_logs` con `evento: "retiro"`.
5. **Deduplicación:** un `event_id` ya procesado se ignora (índices únicos, sección 4).
6. **Validación:** un mensaje con JSON malformado o campos fuera de rango se descarta y se registra en el log; no detiene el servicio.
7. **Timestamp:** el backend inyecta `received_at` (UTC, ISO-8601) en todo documento guardado.

Límite declarado: un objeto a la vez en la demo.

---

## 4. Colecciones MongoDB

* `telemetry_logs`: `{ tacho_id, volumen_pct, peso_total_kg, uptime_ms, evento?, delta_kg?, event_id?, received_at }` (los campos opcionales solo aparecen en registros de `evento: "retiro"`, donde `volumen_pct` es `null`)
* `classification_events`: `{ tacho_id, event_id, clase, confianza, fuente, uptime_ms, received_at, estado_correlacion }`
* `deposits`: `{ tacho_id, event_id_vision, event_id_peso, clase, delta_kg, peso_total_kg, fuente, received_at }`
* `node_status`: `{ tacho_id, nodo, estado, last_seen }` (`last_seen` puede ser `null`)

`estado_correlacion`: `pendiente`, `correlacionado`, `sin_peso`; es `null` para eventos de clase `vacio`.

En `deposits` con `clase: "sin_clasificar"`, `event_id_vision` y `fuente` son `null`.

Índices:
* Todas: `(tacho_id, received_at)`.
* `classification_events.event_id`: **único**.
* `deposits.event_id_peso`: **único**.
* `deposits.event_id_vision`: único **parcial** (solo cuando no es nulo; en `sin_clasificar` es nulo).
* `node_status`: único por `(tacho_id, nodo)`.

---

## 5. Endpoints REST (`/api/v1`)

Fechas en ISO-8601 UTC con `Z` (`2026-11-18T21:45:00Z`); si se envía un desplazamiento como `+00:00`, el signo `+` debe ir codificado (`%2B`). Una fecha sin zona horaria se interpreta como UTC. Los endpoints sin `{id}` en la ruta aceptan el parámetro opcional `tacho_id` (por defecto `tacho-unmsm-01`). Errores con el formato:
```json
{ "error": { "codigo": "parametro_invalido", "mensaje": "desde debe ser ISO-8601" } }
```
Códigos HTTP: 200; 400 con `codigo: "parametro_invalido"`; 404 con `codigo: "tacho_no_encontrado"` (el tacho aún no tiene telemetría ni estado de nodos); 503 con `codigo: "mongo_no_disponible"`.

### `GET /api/v1/tachos/{id}/estado`
```json
{
  "tacho_id": "tacho-unmsm-01",
  "volumen_pct": 45,
  "peso_total_kg": 1.25,
  "alerta_llenado": false,
  "nodos": {
    "sensores": { "estado": "online", "last_seen": "2026-11-18T21:45:00Z" },
    "vision":   { "estado": "online", "last_seen": "2026-11-18T21:44:58Z" }
  },
  "actualizado_en": "2026-11-18T21:45:00Z"
}
```

### `GET /api/v1/depositos?desde=&hasta=&limite=`
`desde` y `hasta` son opcionales e inclusivos; si `desde` es posterior a `hasta`, responde 400. `limite` por defecto 50, entre 1 y 500; orden por `received_at` descendente. `total` cuenta **todos** los depósitos que cumplen el filtro, aunque `items` esté recortado por `limite`.
```json
{
  "total": 1,
  "items": [
    {
      "event_id_vision": "v-3fa9-000123",
      "event_id_peso": "p-91c2-000087",
      "clase": "plastico",
      "delta_kg": 0.31,
      "peso_total_kg": 1.25,
      "fuente": "ia",
      "received_at": "2026-11-18T21:45:00Z"
    }
  ]
}
```

### `GET /api/v1/resumen?periodo=semana`
`periodo`: `dia` o `semana` (por defecto `semana`). Los límites siguen el calendario de **Lima**: `dia` va desde las 00:00 de hoy hasta el momento de la consulta; `semana` desde las 00:00 de hace 6 días (hoy incluido). `desde` y `hasta` se devuelven en UTC. `por_clase` siempre trae las cinco claves, con `0` cuando no hay depósitos.
```json
{
  "periodo": "semana",
  "desde": "2026-11-12T00:00:00Z",
  "hasta": "2026-11-18T23:59:59Z",
  "depositos": 14,
  "total_kg": 4.82,
  "por_clase": {
    "plastico": 1.90,
    "papel_carton": 1.40,
    "otros": 1.20,
    "no_seguro": 0.12,
    "sin_clasificar": 0.20
  }
}
```

### Notas de `GET /api/v1/tachos/{id}/estado`
`volumen_pct`, `peso_total_kg` y `actualizado_en` son `null` si todavía no hay telemetría. Cada nodo (`sensores`, `vision`) trae `estado: "desconocido"` y `last_seen: null` si aún no ha reportado. `alerta_llenado` usa histéresis (se activa en 85 %, se limpia en 70 %).

### `GET /api/v1/salud`
```json
{ "status": "ok", "mongo": "ok", "mqtt": "ok" }
```

---

## 6. Eventos WebSocket (`/ws/tacho`)

URL: `ws://{host}:8000/ws/tacho?tacho_id=tacho-unmsm-01` (`tacho_id` es opcional y por defecto es `tacho-unmsm-01`). Cada cliente recibe solo los eventos de su tacho. El servidor ignora lo que envíe el cliente.

Formato único: `{ "tipo": "...", "data": { ... } }`. Tipos soportados: `telemetria`, `deposito`, `estado_nodo`.

Al conectarse, el servidor envía **primero** un `estado_nodo` por cada nodo (`sensores` y `vision`, con `desconocido` si aún no han reportado) y, si existe, la última `telemetria`, para que el dashboard no inicie vacío. Después envía cada evento en cuanto el backend lo procesa:

* `telemetria`: por cada mensaje de telemetría (cada 5 s), con `alerta_llenado` calculada por el backend.
* `deposito`: por cada depósito creado, incluidos los `sin_clasificar` (con `fuente: null`).
* `estado_nodo`: por cada cambio de estado de un nodo (incluye el LWT `offline`).

Si MongoDB no está disponible al conectarse, el servidor cierra con el código `1011`. Si un cliente es lento y su cola de 100 mensajes se llena, los mensajes nuevos se descartan para ese cliente.

```json
{ "tipo": "telemetria",
  "data": { "volumen_pct": 45, "peso_total_kg": 1.25, "alerta_llenado": false,
            "received_at": "2026-11-18T21:45:00Z" } }
```
```json
{ "tipo": "deposito",
  "data": { "clase": "plastico", "delta_kg": 0.31, "peso_total_kg": 1.25,
            "fuente": "ia", "received_at": "2026-11-18T21:45:00Z" } }
```
```json
{ "tipo": "estado_nodo",
  "data": { "nodo": "vision", "estado": "online",
            "last_seen": "2026-11-18T21:44:58Z" } }
```

---

## 7. Control de cambios

* Cualquier cambio de un tópico, un campo o un endpoint se hace en este archivo, con una línea en el registro de cambios y subiendo la versión.
* **v1.5:** los mensajes de estado retenidos no actualizan `last_seen`; el backend ignora retenidos en tópicos que no son de estado.
* **v1.4:** WebSocket implementado: parámetro `tacho_id`, mensajes iniciales con `desconocido`, eventos que se difunden y cierre `1011`.
* **v1.3:** endpoints REST implementados (`estado`, `depositos`, `resumen`): parámetro `tacho_id`, significado de `total`, ventanas de `resumen` en hora de Lima, valores `desconocido` y códigos de error.
* **v1.2:** detalles de persistencia (`vacio`, retiros y depósitos sin clasificar).
* **v1.1:** respuestas REST con ejemplos y errores; eventos WebSocket completos; reglas de campos y rangos; `nodo`, payload de `estado` y `estado_correlacion` definidos; peso negativo, cola FIFO y deduplicación con índices; alerta de llenado calculada en backend.

## 8. Puntos abiertos

* Framework del backend (el contrato no lo exige).
* Librería MQTT y QoS real de los nodos (PubSubClient solo publica QoS 0).
* Umbral mínimo de peso: se fija tras la calibración de la balanza.
