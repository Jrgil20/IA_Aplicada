#!/usr/bin/env python3
"""Pruebas de regresión del cálculo de penalidades (problema 8).

Uso:
    python3 scripts/probar_penalidades.py

Solo biblioteca estándar. No escribe en salidas/ ni en documentos/.
"""

import datetime
import importlib.util
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE_DIR, "scripts", "calcular_penalidades.py")

spec = importlib.util.spec_from_file_location("calcular_penalidades", SCRIPT)
calc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc)


class PruebasPenalidades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pedidos, cls.subtotales, cls.total = calc.calcular()
        cls.por_pedido = {p["pedido"]: p for p in cls.pedidos}

    def test_total_y_cantidad(self):
        self.assertEqual(len(self.pedidos), 15)
        self.assertAlmostEqual(self.total, 11343.33, places=2)

    def test_po_1365_usa_tasa_p06_de_0_2(self):
        p = self.por_pedido["PO-1365"]
        self.assertAlmostEqual(p["tasa_diaria_pct"], 0.2, places=4)
        self.assertAlmostEqual(p["monto_penalidad"], 12.87, places=2)

    def test_po_1314_tope_del_6(self):
        self.assertAlmostEqual(self.por_pedido["PO-1314"]["monto_penalidad"], 1152.40, places=2)

    def test_subtotal_p04(self):
        self.assertAlmostEqual(self.subtotales["P04"]["penalidad_total"], 6480.83, places=2)

    def test_regla_p04_antes_de_julio(self):
        regla = calc.regla_para("P04", datetime.date(2026, 6, 30))
        self.assertAlmostEqual(regla["tasa_diaria"], 0.005)
        self.assertEqual(regla["dias_gracia"], 7)
        self.assertAlmostEqual(regla["tope_maximo"], 0.10)
        self.assertIsNone(regla["adenda"])

    def test_regla_p04_desde_julio(self):
        regla = calc.regla_para("P04", datetime.date(2026, 7, 1))
        self.assertAlmostEqual(regla["tasa_diaria"], 0.010)
        self.assertEqual(regla["dias_gracia"], 3)
        self.assertAlmostEqual(regla["tope_maximo"], 0.15)
        self.assertEqual(regla["adenda"], "AD-2026-P04-01")

    def test_tasas_de_los_contratos(self):
        esperado = {
            "P01": (0.005, 5, 0.10),
            "P02": (0.003, 2, 0.05),
            "P03": (0.004, 5, 0.08),
            "P04": (0.010, 3, 0.15),
            "P05": (0.006, 5, 0.12),
            "P06": (0.002, 10, 0.06),
        }
        for prov, (tasa, gracia, tope) in esperado.items():
            with self.subTest(proveedor=prov):
                regla = calc.PROVEEDORES_INFO[prov]
                self.assertAlmostEqual(regla["tasa_diaria"], tasa)
                self.assertEqual(regla["dias_gracia"], gracia)
                self.assertAlmostEqual(regla["tope_maximo"], tope)

    def test_rifs_de_los_contratos(self):
        esperado = {
            "P01": "J-40118273-5",
            "P02": "J-31277014-0",
            "P03": "J-29880341-2",
            "P04": "J-30561982-7",
            "P05": "J-41002567-9",
            "P06": "J-38845120-4",
        }
        for prov, rif in esperado.items():
            with self.subTest(proveedor=prov):
                self.assertEqual(calc.PROVEEDORES_INFO[prov]["rif"], rif)

    def test_escape_de_html(self):
        self.assertEqual(calc.esc("<b>HOLA</b>"), "&lt;b&gt;HOLA&lt;/b&gt;")
        self.assertEqual(calc.esc('Monitores 24"'), "Monitores 24&quot;")

    def test_todos_superan_el_corte_de_10_dias(self):
        for p in self.pedidos:
            with self.subTest(pedido=p["pedido"]):
                self.assertGreater(p["dias_atraso"], 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
