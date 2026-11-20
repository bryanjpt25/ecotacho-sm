"""Lógica pura del backend EcoTacho SM (sin dependencias externas).

Validación de mensajes MQTT y correlación visión + peso, según docs/contratos.md.
"""
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

VENTANA_S = 8.0
CLASES = {"vacio", "plastico", "papel_carton", "otros", "no_seguro"}
FUENTES = {"ia", "manual"}
NODOS = {"sensores", "vision"}
LIMA = timezone(timedelta(hours=-5))  # Lima no usa horario de verano
ALERTA_ALTA = 85  # % de llenado que activa la alerta
ALERTA_BAJA = 70  # % de llenado que la limpia (histéresis)
CLASES_RESUMEN = ("plastico", "papel_carton", "otros", "no_seguro", "sin_clasificar")


def es_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def es_entero(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _event_id_valido(valor, prefijo):
    return isinstance(valor, str) and valor.startswith(prefijo) and len(valor) > len(prefijo)


def _uptime_valido(valor):
    return es_entero(valor) and valor >= 0


def validar_vision(d):
    """Devuelve None si el mensaje cumple el contrato, o un texto con el error."""
    if not _event_id_valido(d.get("event_id"), "v-"):
        return "event_id inválido (debe empezar con 'v-')"
    clase = d.get("clase")
    if not isinstance(clase, str) or clase not in CLASES:
        return "clase inválida"
    fuente = d.get("fuente")
    if not isinstance(fuente, str) or fuente not in FUENTES:
        return "fuente inválida"
    conf = d.get("confianza")
    if conf is None:
        if fuente != "manual":
            return "confianza requerida cuando fuente es 'ia'"
    elif not es_numero(conf) or not 0 <= conf <= 1:
        return "confianza fuera del rango 0-1"
    if not _uptime_valido(d.get("uptime_ms")):
        return "uptime_ms inválido"
    return None


def validar_peso(d):
    if not _event_id_valido(d.get("event_id"), "p-"):
        return "event_id inválido (debe empezar con 'p-')"
    if not es_numero(d.get("delta_kg")):
        return "delta_kg inválido"
    peso = d.get("peso_total_kg")
    if not es_numero(peso) or peso < 0:
        return "peso_total_kg inválido"
    if not _uptime_valido(d.get("uptime_ms")):
        return "uptime_ms inválido"
    return None


def validar_telemetria(d):
    vol = d.get("volumen_pct")
    if not es_numero(vol) or not 0 <= vol <= 100:
        return "volumen_pct fuera del rango 0-100"
    peso = d.get("peso_total_kg")
    if not es_numero(peso) or peso < 0:
        return "peso_total_kg inválido"
    if not _uptime_valido(d.get("uptime_ms")):
        return "uptime_ms inválido"
    return None


def parsear_topico(topic):
    """'ecotacho/{id}/vision/evento' -> (id, 'vision', None). None si no es un tópico válido."""
    p = topic.split("/")
    if len(p) < 3 or p[0] != "ecotacho" or not p[1]:
        return None
    tacho_id, tipo = p[1], p[2]
    if tipo in ("vision", "peso") and len(p) == 4 and p[3] == "evento":
        return tacho_id, tipo, None
    if tipo == "telemetria" and len(p) == 3:
        return tacho_id, tipo, None
    if tipo == "estado" and len(p) == 4 and p[3] in NODOS:
        return tacho_id, tipo, p[3]
    return None


@dataclass
class Pendiente:
    tacho_id: str
    event_id: str
    clase: str
    fuente: str
    t: float  # segundos (reloj monotónico) en que llegó la visión


class Correlador:
    """Cola FIFO de visiones pendientes de recibir su evento de peso (ventana de 8 s)."""

    def __init__(self, ventana_s=VENTANA_S):
        self.ventana_s = ventana_s
        self._colas = {}

    def agregar(self, pendiente):
        self._colas.setdefault(pendiente.tacho_id, deque()).append(pendiente)

    def vencidos(self, ahora):
        """Quita y devuelve las visiones cuya ventana ya expiró (quedan 'sin_peso')."""
        salida = []
        for cola in self._colas.values():
            while cola and ahora - cola[0].t > self.ventana_s:
                salida.append(cola.popleft())
        return salida

    def siguiente(self, tacho_id):
        cola = self._colas.get(tacho_id)
        return cola[0] if cola else None

    def quitar_primero(self, tacho_id):
        cola = self._colas.get(tacho_id)
        if cola:
            cola.popleft()

    def total(self):
        return sum(len(c) for c in self._colas.values())


# --- Utilidades de la API REST -------------------------------------------------------
def actualizar_alerta(actual, volumen_pct, alta=ALERTA_ALTA, baja=ALERTA_BAJA):
    """Alerta de llenado con histéresis: se activa en >= alta y se limpia en <= baja."""
    if volumen_pct >= alta:
        return True
    if volumen_pct <= baja:
        return False
    return actual


def parsear_fecha_iso(texto):
    """ISO-8601 -> datetime con zona UTC. Sin zona horaria se asume UTC. ValueError si es inválida."""
    d = datetime.fromisoformat(texto)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def limites_periodo(periodo, ahora_utc):
    """'dia' = desde las 00:00 de hoy (hora de Lima); 'semana' = desde las 00:00 de hace 6 días.

    Devuelve (desde, hasta) en UTC; hasta es el momento de la consulta.
    """
    if periodo == "dia":
        dias_atras = 0
    elif periodo == "semana":
        dias_atras = 6
    else:
        raise ValueError("periodo debe ser 'dia' o 'semana'")
    ahora_lima = ahora_utc.astimezone(LIMA)
    inicio = (ahora_lima - timedelta(days=dias_atras)).replace(hour=0, minute=0, second=0, microsecond=0)
    return inicio.astimezone(timezone.utc), ahora_utc


def armar_resumen(grupos):
    """grupos: [{'_id': clase, 'kg': suma, 'n': cantidad}] -> resumen con todas las clases (0 si no hay)."""
    por_clase = {c: 0.0 for c in CLASES_RESUMEN}
    total = 0.0
    cantidad = 0
    for g in grupos:
        kg = float(g["kg"])
        por_clase[g["_id"]] = por_clase.get(g["_id"], 0.0) + kg
        total += kg
        cantidad += int(g["n"])
    return {
        "depositos": cantidad,
        "total_kg": round(total, 3),
        "por_clase": {k: round(v, 3) for k, v in por_clase.items()},
    }


def resolver_estado(previo, estado, retenido, recibido):
    """Decide qué hacer con un mensaje de estado de un nodo.

    Un mensaje retenido es la repetición que el broker entrega al reconectar: no indica cuándo se
    vio por última vez al nodo, así que no toca `last_seen`. Devuelve (last_seen, difundir).
    """
    if not retenido:
        return recibido, True
    last_seen = previo.get("last_seen") if previo else None
    cambio = previo is None or previo.get("estado") != estado
    return last_seen, cambio
