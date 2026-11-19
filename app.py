"""EcoTacho SM — backend: ingesta MQTT -> MongoDB, correlación visión + peso y API.

Contratos: docs/contratos.md. Este archivo implementa la ingesta, la correlación
y /api/v1/salud; los demás endpoints REST y el WebSocket son el siguiente paso.
"""
import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from logica import (
    Correlador,
    Pendiente,
    parsear_topico,
    validar_peso,
    validar_telemetria,
    validar_vision,
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

TICK = "__tick__"

mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=2000)
db = mongo_client["ecotacho_db"]
correlador = Correlador()

loop = None
cola = None
indices_listos = None

# --- MQTT (corre en el hilo de paho; solo encola mensajes hacia asyncio) ---------------
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="backend_service")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[MQTT] Conexión rechazada: {reason_code}")
        return
    print("[MQTT] Conectado al broker")
    client.subscribe("ecotacho/#")  # se re-suscribe en cada reconexión


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"[MQTT] Desconectado: {reason_code}")


def _encolar(item):
    try:
        cola.put_nowait(item)
    except asyncio.QueueFull:
        print("[Cola] llena: mensaje descartado")


def on_message(client, userdata, msg):
    if loop is not None and cola is not None:
        loop.call_soon_threadsafe(_encolar, (msg.topic, bytes(msg.payload)))


mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message


# --- Persistencia ---------------------------------------------------------------------
async def preparar_indices():
    while True:
        try:
            await db.telemetry_logs.create_index([("tacho_id", 1), ("received_at", 1)])
            await db.classification_events.create_index([("tacho_id", 1), ("received_at", 1)])
            await db.classification_events.create_index("event_id", unique=True)
            await db.deposits.create_index([("tacho_id", 1), ("received_at", 1)])
            await db.deposits.create_index("event_id_peso", unique=True)
            await db.deposits.create_index(
                "event_id_vision",
                unique=True,
                partialFilterExpression={"event_id_vision": {"$type": "string"}},
            )
            await db.node_status.create_index([("tacho_id", 1), ("nodo", 1)], unique=True)
            indices_listos.set()
            print("[Mongo] Índices listos")
            return
        except Exception as e:
            print(f"[Mongo] Esperando a MongoDB: {e}")
            await asyncio.sleep(3)


async def expirar_vencidos():
    for p in correlador.vencidos(time.monotonic()):
        await db.classification_events.update_one(
            {"event_id": p.event_id}, {"$set": {"estado_correlacion": "sin_peso"}}
        )
        print(f"[Correlación] {p.event_id} ({p.clase}) sin peso en la ventana")


async def procesar_vision(tacho_id, d, recibido):
    error = validar_vision(d)
    if error:
        print(f"[Ingesta] vision descartado: {error}")
        return
    clase = d["clase"]
    doc = {
        "tacho_id": tacho_id,
        "event_id": d["event_id"],
        "clase": clase,
        "confianza": d.get("confianza"),
        "fuente": d["fuente"],
        "uptime_ms": d["uptime_ms"],
        "received_at": recibido,
        "estado_correlacion": None if clase == "vacio" else "pendiente",
    }
    try:
        await db.classification_events.insert_one(doc)
    except DuplicateKeyError:
        print(f"[Ingesta] {d['event_id']} duplicado: ignorado")
        return
    print(f"[Ingesta] vision {d['event_id']} -> {clase}")
    if clase != "vacio":
        correlador.agregar(Pendiente(tacho_id, d["event_id"], clase, d["fuente"], time.monotonic()))


async def procesar_peso(tacho_id, d, recibido):
    error = validar_peso(d)
    if error:
        print(f"[Ingesta] peso descartado: {error}")
        return
    await expirar_vencidos()
    delta = float(d["delta_kg"])
    if delta < 0:  # retiro o vaciado: no crea depósito
        await db.telemetry_logs.insert_one(
            {
                "tacho_id": tacho_id,
                "volumen_pct": None,
                "peso_total_kg": d["peso_total_kg"],
                "uptime_ms": d["uptime_ms"],
                "evento": "retiro",
                "delta_kg": delta,
                "event_id": d["event_id"],
                "received_at": recibido,
            }
        )
        print(f"[Ingesta] retiro {d['event_id']} ({delta} kg)")
        return
    if delta == 0:
        print(f"[Ingesta] {d['event_id']} con delta_kg = 0: ignorado")
        return
    if await db.deposits.find_one({"event_id_peso": d["event_id"]}, {"_id": 1}):
        print(f"[Ingesta] {d['event_id']} duplicado: ignorado")
        return
    pend = correlador.siguiente(tacho_id)
    deposito = {
        "tacho_id": tacho_id,
        "event_id_vision": pend.event_id if pend else None,
        "event_id_peso": d["event_id"],
        "clase": pend.clase if pend else "sin_clasificar",
        "delta_kg": delta,
        "peso_total_kg": d["peso_total_kg"],
        "fuente": pend.fuente if pend else None,
        "received_at": recibido,
    }
    try:
        await db.deposits.insert_one(deposito)
    except DuplicateKeyError:
        print(f"[Ingesta] {d['event_id']} duplicado en índices: ignorado")
        return
    if pend:
        correlador.quitar_primero(tacho_id)
        await db.classification_events.update_one(
            {"event_id": pend.event_id}, {"$set": {"estado_correlacion": "correlacionado"}}
        )
    print(f"[Correlación] depósito {deposito['clase']} {delta} kg")


async def procesar(topic, raw):
    ruta = parsear_topico(topic)
    if ruta is None:
        print(f"[Ingesta] tópico ignorado: {topic}")
        return
    tacho_id, tipo, nodo = ruta
    recibido = datetime.now(timezone.utc)

    if tipo == "estado":  # texto plano, no JSON
        estado = raw.decode("utf-8", errors="replace").strip()
        if estado not in ("online", "offline"):
            print(f"[Ingesta] estado inválido en {topic}: {estado!r}")
            return
        await db.node_status.update_one(
            {"tacho_id": tacho_id, "nodo": nodo},
            {"$set": {"estado": estado, "last_seen": recibido}},
            upsert=True,
        )
        print(f"[Estado] {nodo}: {estado}")
        return

    try:
        datos = json.loads(raw.decode("utf-8"))
    except ValueError:
        print(f"[Ingesta] JSON malformado en {topic}: descartado")
        return
    if not isinstance(datos, dict):
        print(f"[Ingesta] {topic}: se esperaba un objeto JSON")
        return

    if tipo == "vision":
        await procesar_vision(tacho_id, datos, recibido)
    elif tipo == "peso":
        await procesar_peso(tacho_id, datos, recibido)
    elif tipo == "telemetria":
        error = validar_telemetria(datos)
        if error:
            print(f"[Ingesta] telemetria descartada: {error}")
            return
        await db.telemetry_logs.insert_one(
            {
                "tacho_id": tacho_id,
                "volumen_pct": datos["volumen_pct"],
                "peso_total_kg": datos["peso_total_kg"],
                "uptime_ms": datos["uptime_ms"],
                "received_at": recibido,
            }
        )


async def trabajador():
    """Único consumidor de la cola: procesa los mensajes uno por uno (sin condiciones de carrera)."""
    await indices_listos.wait()
    while True:
        topic, raw = await cola.get()
        try:
            if topic == TICK:
                await expirar_vencidos()
            else:
                await procesar(topic, raw)
        except Exception as e:
            print(f"[Ingesta] Error procesando {topic}: {e}")


async def ticker():
    while True:
        await asyncio.sleep(1)
        _encolar((TICK, b""))


# --- Aplicación -----------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):
    global loop, cola, indices_listos
    loop = asyncio.get_running_loop()
    cola = asyncio.Queue(maxsize=1000)
    indices_listos = asyncio.Event()
    tareas = [
        asyncio.create_task(preparar_indices()),
        asyncio.create_task(trabajador()),
        asyncio.create_task(ticker()),
    ]
    try:
        mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()  # reintenta la conexión inicial por su cuenta
    except Exception as e:
        print(f"[Startup] No se pudo iniciar el cliente MQTT: {e}")
    yield
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    for t in tareas:
        t.cancel()
    mongo_client.close()


app = FastAPI(title="EcoTacho SM Backend", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/salud")
async def salud():
    try:
        await db.command("ping")
        mongo = "ok"
    except Exception:
        mongo = "error"
    mqtt_estado = "ok" if mqtt_client.is_connected() else "error"
    return {
        "status": "ok" if mongo == "ok" and mqtt_estado == "ok" else "degradado",
        "mongo": mongo,
        "mqtt": mqtt_estado,
    }
