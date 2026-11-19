import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logica import (  # noqa: E402
    Correlador,
    Pendiente,
    parsear_topico,
    validar_peso,
    validar_telemetria,
    validar_vision,
)

VISION = {"event_id": "v-3fa9-000123", "clase": "plastico", "confianza": 0.82, "fuente": "ia", "uptime_ms": 123456}
PESO = {"event_id": "p-91c2-000087", "delta_kg": 0.31, "peso_total_kg": 1.25, "uptime_ms": 123900}
TELE = {"volumen_pct": 45, "peso_total_kg": 1.25, "uptime_ms": 124000}


class TestValidacion(unittest.TestCase):
    def test_vision_valida(self):
        self.assertIsNone(validar_vision(VISION))

    def test_vision_manual_sin_confianza(self):
        self.assertIsNone(validar_vision({**VISION, "fuente": "manual", "confianza": None}))

    def test_vision_ia_sin_confianza(self):
        self.assertIsNotNone(validar_vision({**VISION, "confianza": None}))

    def test_vision_errores(self):
        self.assertIsNotNone(validar_vision({**VISION, "event_id": "x-1"}))
        self.assertIsNotNone(validar_vision({**VISION, "clase": "vidrio"}))
        self.assertIsNotNone(validar_vision({**VISION, "clase": ["plastico"]}))
        self.assertIsNotNone(validar_vision({**VISION, "confianza": 1.5}))
        self.assertIsNotNone(validar_vision({**VISION, "confianza": True}))
        self.assertIsNotNone(validar_vision({**VISION, "uptime_ms": -1}))

    def test_peso(self):
        self.assertIsNone(validar_peso(PESO))
        self.assertIsNone(validar_peso({**PESO, "delta_kg": -0.5}))
        self.assertIsNotNone(validar_peso({**PESO, "delta_kg": "0.3"}))
        self.assertIsNotNone(validar_peso({**PESO, "peso_total_kg": -1}))
        self.assertIsNotNone(validar_peso({**PESO, "event_id": "v-1"}))

    def test_telemetria(self):
        self.assertIsNone(validar_telemetria(TELE))
        self.assertIsNotNone(validar_telemetria({**TELE, "volumen_pct": 101}))
        self.assertIsNotNone(validar_telemetria({**TELE, "uptime_ms": 1.5}))


class TestTopicos(unittest.TestCase):
    def test_validos(self):
        self.assertEqual(parsear_topico("ecotacho/t1/vision/evento"), ("t1", "vision", None))
        self.assertEqual(parsear_topico("ecotacho/t1/peso/evento"), ("t1", "peso", None))
        self.assertEqual(parsear_topico("ecotacho/t1/telemetria"), ("t1", "telemetria", None))
        self.assertEqual(parsear_topico("ecotacho/t1/estado/vision"), ("t1", "estado", "vision"))

    def test_invalidos(self):
        for t in ["otro/t1/vision/evento", "ecotacho//telemetria", "ecotacho/t1/vision",
                  "ecotacho/t1/estado/otro", "ecotacho/t1/telemetria/x", "ecotacho"]:
            self.assertIsNone(parsear_topico(t), t)


class TestCorrelador(unittest.TestCase):
    def test_fifo(self):
        c = Correlador(8.0)
        c.agregar(Pendiente("t1", "v-a-1", "plastico", "ia", 0.0))
        c.agregar(Pendiente("t1", "v-a-2", "otros", "ia", 1.0))
        self.assertEqual(c.siguiente("t1").event_id, "v-a-1")
        c.quitar_primero("t1")
        self.assertEqual(c.siguiente("t1").event_id, "v-a-2")

    def test_vencimiento(self):
        c = Correlador(8.0)
        c.agregar(Pendiente("t1", "v-a-1", "plastico", "ia", 0.0))
        c.agregar(Pendiente("t1", "v-a-2", "otros", "ia", 5.0))
        self.assertEqual(c.vencidos(8.0), [])
        self.assertEqual([p.event_id for p in c.vencidos(8.5)], ["v-a-1"])
        self.assertEqual(c.siguiente("t1").event_id, "v-a-2")
        self.assertEqual([p.event_id for p in c.vencidos(14.0)], ["v-a-2"])
        self.assertEqual(c.total(), 0)

    def test_tachos_independientes(self):
        c = Correlador(8.0)
        c.agregar(Pendiente("t1", "v-a-1", "plastico", "ia", 0.0))
        self.assertIsNone(c.siguiente("t2"))
        c.quitar_primero("t2")  # no debe fallar
        self.assertEqual(c.total(), 1)


if __name__ == "__main__":
    unittest.main()
