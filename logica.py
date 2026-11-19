"""Lógica pura del backend EcoTacho SM (sin dependencias externas).

Validación de mensajes MQTT y correlación visión + peso, según docs/contratos.md.
"""
from collections import deque
from dataclasses import dataclass

VENTANA_S = 8.0
CLASES = {"vacio", "plastico", "papel_carton", "otros", "no_seguro"}
FUENTES = {"ia", "manual"}
NODOS = {"sensores", "vision"}


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
