# EcoTacho SM — Contratos Técnicos e Interfaces (v1)

Identificador de tacho por defecto: `tacho-unmsm-01`

---

## 1. Tópicos MQTT (QoS 0)

| Tópico | Dirección | Descripción |
| :--- | :--- | :--- |
| `ecotacho/{id}/vision/evento` | ESP32-CAM → Broker | Publicación de clasificación estable |
| `ecotacho/{id}/peso/evento` | ESP32 → Broker | Publicación de variación de peso estabilizada |
| `ecotacho/{id}/telemetria` | ESP32 → Broker | Lectura periódica de peso y volumen (cada 5 s) |
| `ecotacho/{id}/estado/{nodo}` | Ambos → Broker | Mensaje LWT / Estado (`online` / `offline`, retained) |

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
* **clase**: `vacio`, `plastico`, `papel_carton`, `otros`, `no_seguro`.
* **fuente**: `ia` o `manual`.
* **event_id**: Prefijo `v-` + nonce hexa de arranque (4-8 caracteres) + contador de 6 dígitos.

### 2.2 Peso (`ecotacho/{id}/peso/evento`)
```json
{
  "event_id": "p-91c2-000087",
  "delta_kg": 0.31,
  "peso_total_kg": 1.25,
  "uptime_ms": 123900
}
```

### 2.3 Telemetría (`ecotacho/{id}/telemetria`)
```json
{
  "volumen_pct": 45,
  "peso_total_kg": 1.25,
  "uptime_ms": 124000
}
```

---

## 3. Lógica de Correlación Backend

1. **Ventana temporal**: 8 segundos entre `vision/evento` y `peso/evento`.
2. **Registro de Depósito (`deposits`)**:
   * Si llega visión (no `vacio`) y dentro de 8 s llega delta de peso → Registro exitoso con `clase` y `delta_kg`.
   * Si llega peso sin visión previa → `clase: "sin_clasificar"`.
   * Si llega visión sin peso tras 8 s → Guarda en `classification_events` con marca `sin_peso`.
3. **Deduplicación**: Si el backend recibe un `event_id` ya procesado, lo ignora.
4. **Timestamp**: El backend inyecta `received_at` en formato UTC ISO-8601 a todo documento guardado en MongoDB.

---

## 4. Colecciones MongoDB

* `telemetry_logs`: `{ tacho_id, volumen_pct, peso_total_kg, uptime_ms, received_at }`
* `classification_events`: `{ tacho_id, event_id, clase, confianza, fuente, uptime_ms, received_at, estado_correlacion }`
* `deposits`: `{ tacho_id, event_id_vision, event_id_peso, clase, delta_kg, peso_total_kg, fuente, received_at }`
* `node_status`: `{ tacho_id, nodo, estado, last_seen }`

---

## 5. Endpoints REST (FastAPI)

* `GET /api/v1/tachos/{id}/estado`: Retorna estado de nodos, volumen actual y peso total.
* `GET /api/v1/depositos?desde=&hasta=`: Retorna historial de depósitos acumulados.
* `GET /api/v1/resumen?periodo=semana`: Retorna kg segregados por tipo de residuo.
* `GET /api/v1/salud`: Verificación de estado del backend y MongoDB (`status: ok`).

---

## 6. Eventos WebSocket (`/ws/tacho`)

El backend emitirá eventos en tiempo real hacia el dashboard en este formato:
```json
{
  "tipo": "deposito",
  "data": {
    "clase": "plastico",
    "delta_kg": 0.31,
    "peso_total_kg": 1.25,
    "fuente": "ia",
    "received_at": "2026-11-18T21:45:00Z"
  }
}
```
Tipos soportados: `telemetria`, `deposito`, `estado_nodo`.