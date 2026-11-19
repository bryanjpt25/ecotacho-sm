import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone  # noqa: E402

from logica import (  # noqa: E402
    Correlador,
    Pendiente,
    actualizar_alerta,
    armar_resumen,
    limites_periodo,
    parsear_fecha_iso,
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


class TestApi(unittest.TestCase):
    def test_alerta_con_historesis(self):
        a = False
        for vol, esperado in [(50, False), (84, False), (85, True), (80, True), (71, True), (70, False), (75, False), (90, True)]:
            a = actualizar_alerta(a, vol)
            self.assertEqual(a, esperado, vol)

    def test_fecha_iso(self):
        self.assertEqual(parsear_fecha_iso("2026-11-18T21:45:00Z"), datetime(2026, 11, 18, 21, 45, tzinfo=timezone.utc))
        self.assertEqual(parsear_fecha_iso("2026-11-18T16:45:00-05:00"), datetime(2026, 11, 18, 21, 45, tzinfo=timezone.utc))
        self.assertEqual(parsear_fecha_iso("2026-11-18"), datetime(2026, 11, 18, tzinfo=timezone.utc))
        for malo in ["ayer", "", "2026-13-45"]:
            with self.assertRaises(ValueError):
                parsear_fecha_iso(malo)

    def test_limites_periodo(self):
        ahora = datetime(2026, 11, 19, 20, 6, tzinfo=timezone.utc)  # 15:06 en Lima
        self.assertEqual(limites_periodo("dia", ahora), (datetime(2026, 11, 19, 5, 0, tzinfo=timezone.utc), ahora))
        self.assertEqual(limites_periodo("semana", ahora), (datetime(2026, 11, 13, 5, 0, tzinfo=timezone.utc), ahora))
        # 02:00 UTC del 19 todavía es el 18 en Lima
        madrugada = datetime(2026, 11, 19, 2, 0, tzinfo=timezone.utc)
        self.assertEqual(limites_periodo("dia", madrugada)[0], datetime(2026, 11, 18, 5, 0, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            limites_periodo("mes", ahora)

    def test_resumen(self):
        r = armar_resumen([{"_id": "plastico", "kg": 0.31, "n": 1}, {"_id": "sin_clasificar", "kg": 0.2, "n": 1}])
        self.assertEqual(r["depositos"], 2)
        self.assertEqual(r["total_kg"], 0.51)
        self.assertEqual(r["por_clase"], {"plastico": 0.31, "papel_carton": 0.0, "otros": 0.0, "no_seguro": 0.0, "sin_clasificar": 0.2})
        self.assertEqual(armar_resumen([])["total_kg"], 0.0)


if __name__ == "__main__":
    unittest.main()
