# Contratos técnicos v1 (fuente de verdad)

> Todo cambio de tópico, JSON, colección o endpoint se propone por PR a este archivo, lo aprueban Sadith y Maricielo y se anuncia al equipo.
> Los esquemas están en `contracts/schemas/`; validar ejemplos con `python contracts/validate_examples.py`.
> Este contrato adopta la nomenclatura de la **guía técnica v4** (tópicos en español) e incorpora las correcciones de esta revisión (ver §9).

## 1. Identificadores

- `tacho_id`: `tacho-{sede}-{NN}`, p. ej. `tacho-unmsm-01`. **Va en el tópico**, no en el payload.
- `nodo`: `vision` (ESP32-CAM) o `sensores` (ESP32 de peso/volumen).
- `client_id` MQTT: `tacho01-vision`, `tacho01-sensores` (únicos).
- **Los dispositivos no envían hora.** El backend asigna `received_at` (UTC, BSON Date) al recibir. `uptime_ms` solo ordena eventos de un mismo nodo.

## 2. Tópicos MQTT

| Tópico | Publica | QoS | Retain | Frecuencia | Esquema |
|--------|---------|-----|--------|-----------|---------|
| `ecotacho/{id}/vision/evento` | ESP32-CAM | 0 | no | por evento | `vision_evento.json` |
| `ecotacho/{id}/peso/evento` | ESP32 sensores | 0 | no | por evento | `peso_evento.json` |
| `ecotacho/{id}/telemetria` | ESP32 sensores | 0 | no | cada 5 s | `telemetria.json` |
| `ecotacho/{id}/estado/{nodo}` | cada nodo (+LWT) | 0 | **sí** | al conectar / LWT | `estado.json` |

**QoS:** `PubSubClient` solo publica en QoS 0. La entrega no está garantizada; se compensa con `event_id` único y deduplicación en el backend. Si las pruebas T4/T6 muestran pérdidas, Sadith evalúa otra librería antes del Gate 1 (vie 27).

**Buffer:** `client.setBufferSize(512)`. **Keep-alive:** 60 s. **LWT:** `{"estado":"offline"}`, retained, en `estado/{nodo}`.

## 3. `event_id` (corrección importante)

Formato: `v-<nonce>-<contador>` (visión) y `p-<nonce>-<contador>` (peso), p. ej. `v-3fa9-000123`.

- `nonce`: 4–8 hex generados con `esp_random()` **en cada arranque**.
- `contador`: 6 dígitos, incrementa por evento.
- Motivo: si el ID fuera solo `v-000123`, tras reiniciar el nodo el contador volvería a 1 y el backend **descartaría eventos nuevos como duplicados**.
- Clave de deduplicación: `(tacho_id, nodo, event_id)`.

## 4. Correlación en el backend

Ventana configurable `CORRELATION_WINDOW_S` (por defecto **8 s**; ajustar tras medir latencia real de visión + estabilización del peso).

1. `vision/evento` con `clase` ∉ {`vacio`,`no_seguro`} → queda **pendiente** (se guarda en `classification_events`).
2. `peso/evento` con `delta_kg` > umbral de ruido dentro de la ventana → documento en `deposits` con `clase` + `delta_kg` + `correlada=true`; se consume el pendiente.
3. Peso sin visión → `deposits` con `clase:"sin_clasificar"`, `correlada=false`.
4. Visión sin peso al vencer la ventana → `classification_events` con `sin_peso=true`.
5. `delta_kg` fuertemente negativo (limpieza vació el tacho) → se guarda como `vaciado` en `node_events`, **no suma** a los kg depositados.
6. Evento duplicado (§3) → se descarta.

## 5. MongoDB (base `ecotacho`)

| Colección | Contenido | Índices | Retención |
|-----------|-----------|---------|-----------|
| `telemetry_logs` | cada `telemetria` + `received_at`, `sensor_ok` | `{tacho_id:1, received_at:-1}` | TTL 30 días |
| `classification_events` | cada `vision/evento` + `received_at`, `sin_peso` | `{tacho_id:1, received_at:-1}`, único `{tacho_id,nodo,event_id}` | — |
| `deposits` | depósito correlacionado | `{tacho_id:1, received_at:-1}`, `{clase:1, received_at:-1}` | — |
| `node_status` | último estado por nodo (upsert) | único `{tacho_id:1, nodo:1}` | — |
| `node_events` | vaciados, reconexiones, errores | `{tacho_id:1, received_at:-1}` | TTL 90 días |

Todo en UTC; el dashboard convierte a `America/Lima`.

## 6. REST (prefijo `/api/v1`)

| Ruta | Devuelve |
|------|----------|
| `GET /salud` | `{"estado":"ok","mongo":true,"mqtt":true}` |
| `GET /tachos/{id}/estado` | volumen, peso, estado online/offline por nodo, `lleno` (≥ 85 %, limpia en 70 %) |
| `GET /depositos?desde=&hasta=&tacho_id=` | depósitos (con `clase`, `delta_kg`, `fuente`, `correlada`) |
| `GET /resumen?periodo=semana` | `total_kg`, `n_depositos`, `kg_por_clase{}`, `pct_clasificacion_valida` |

CORS explícito por variable de entorno (`ALLOWED_ORIGINS`).

## 7. WebSocket (`/ws`)

`{ "tipo": ..., "datos": {...} }` con tipos `telemetria`, `deposito`, `estado_nodo`, más un `snapshot` al conectar. El cliente reconecta solo y conserva el último estado.

## 8. Etiquetas y umbrales

- Modelo v1: `vacio`, `plastico`, `papel_carton`, `otros`. `organico` reservada (Nivel 3). `no_seguro` si `confianza < 0.70`.
- Publicar clase solo tras ≥ 3 cuadros consecutivos con la misma clase y confianza ≥ 0.70 tras un `vacio`. El LCD puede mostrar la clase provisional antes de publicar.
- `fuente`: `ia` o `manual` (Plan B con pulsadores). El dashboard distingue `ia` / `manual` / `simulado`.
- El dashboard debe usar **exactamente** estas etiquetas (hoy usa "vidrio" y "metal": `vidrio`/`metal` se agrupan en `otros`).

## 9. Registro de cambios respecto a revisiones anteriores

| Cambio | Motivo |
|--------|--------|
| QoS 1 → **QoS 0** en publicaciones | `PubSubClient` solo publica QoS 0 |
| `event_id` con nonce de arranque | Evitar descarte de eventos nuevos tras reinicio |
| `tacho_id` solo en el tópico | Menos redundancia, un campo menos que desincronizar |
| Tópicos/colecciones/rutas en español | Alineado con la guía técnica v4 |
| `ts` del dispositivo eliminado | Un solo origen de tiempo (backend) |
