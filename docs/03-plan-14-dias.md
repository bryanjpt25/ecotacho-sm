# 03 · Plan de 14 días y estado funciona / se simula / falta

> La hoja de ruta de 4 semanas de la guía original queda **reemplazada**. Según las bases oficiales, el evento es el **miércoles 2 de diciembre de 2026 (9:00–17:00, FIEE-UNMSM, presencial)**.
> El cronograma día a día y las rutas por integrante están en la **guía técnica v4** (`EcoTacho_SM_Guia_tecnica_operativa_v4`). Este archivo conserva solo los hitos y la matriz que se actualiza a diario, para que no haya dos calendarios distintos.

## 1. Hitos (coinciden con la guía v4)

| Fecha | Hito |
|-------|------|
| Jue 19 nov | `docs/contratos.md` v1 cerrado; BOM y compras (límite); solicitar autorización de línea base/piloto; pedir al CITE el formato de ficha, el programa y la duración de exposición |
| Vie 20 nov | `docker-compose.yml` (Mosquitto + MongoDB + backend); BOM final |
| Sáb 21 | Plantilla de red (`firmware/common/`); sensores leyendo; dashboard con datos mock según contrato |
| Dom 22 | Broker con autenticación y LWT; simulador de nodos (`sadith/simulador/`) |
| Mar 24 – Jue 26 | Línea base (3 días, con autorización); correlación; visión publicando por MQTT |
| **Vie 27** | **Gate 1:** demo extremo a extremo; decisión de **Plan B de IA** (pulsadores) si la precisión < meta |
| Dom 29 | Pruebas T4–T9 (resiliencia, 30 depósitos seguidos) |
| **Lun 30** | **Congelar código** por la noche; video de respaldo; ficha final |
| Mar 1 dic | 3 ensayos cronometrados; checklist de traslado |
| **Mié 2 dic** | Evento. No empezar nada nuevo |

Inscripción: según el equipo, **ya realizada** (las bases cerraban el 20 nov). Guardar la constancia y confirmar integrantes, representante y desafío.

## 2. Matriz funciona / se simula / falta (actualizar cada día; se dice al jurado)

| Componente | Estado al 18 nov | Meta al 2 dic | Si no llega |
|------------|------------------|---------------|-------------|
| Nodo visión: mock en serial (`bryan/`) | Funciona (solo simulado) | Modelo real en la placa | Plan B: clase con 3 pulsadores, marcada `manual` |
| Dashboard Next.js (datos simulados) | Funciona con datos de ejemplo (`milagros/`) | Conectado a REST/WS reales | Modo `?modo=sim` con banner permanente "SIMULACIÓN" |
| Sensores peso/volumen | No iniciado | Funciona (T1, T2) | — (es el núcleo) |
| Broker + backend + MongoDB | Solo `app.py` esqueleto | Funciona local (Docker) | Simulador de nodos declarado |
| Correlación visión + peso | No iniciado | ≥ 90 % de 30 depósitos (T4) | `sin_clasificar` declarado |
| LCD 16x2 | No iniciado | Funciona | Mensaje solo en dashboard |
| Varios tachos, LoRaWAN, alertas por reporte | Fuera de alcance | — | Trabajo futuro con el CITE |

## 3. Reglas de equipo

- Rama por persona y PR revisado por otra persona. `main` siempre arranca.
- Repositorio **público**: nunca subir SSID, contraseñas ni claves (`secrets.h`, `.env` ignorados; solo `*.example`).
- Reunión diaria de 10–15 min. Si algo está bloqueado más de 2 h, se avisa.
- Si algo no funciona 24 h antes del evento, **se simula y se declara**; las bases piden identificar qué funciona, qué se simula y qué falta.
