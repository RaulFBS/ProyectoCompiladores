import unittest
from motor.compilador import analizar_fuente
from motor.modelos_automatas import construir_modelos_tokens


class CompiladorTests(unittest.TestCase):
    def test_ejemplo_valido(self):
        source = "INICIAR_TURNO NOCHE;\nREGISTRAR 500;\nDETENER_MAQUINA M2;"
        result = analizar_fuente(source)
        self.assertTrue(result["valido"], result)
        self.assertEqual(result["resumen"]["cantidad_sentencias"], 3)
        self.assertEqual(result["resumen"]["cantidad_errores"], 0)

    def test_caracter_ilegal(self):
        result = analizar_fuente("REGISTRAR 10 @;")
        self.assertTrue(result["errores_lexicos"])
        self.assertFalse(result["valido"])

    def test_falta_punto_y_coma(self):
        result = analizar_fuente("REGISTRAR 10")
        self.assertTrue(result["errores_sintacticos"])
        self.assertFalse(result["valido"])

    def test_turno_no_permitido(self):
        result = analizar_fuente("INICIAR_TURNO MADRUGADA;")
        self.assertTrue(result["errores_semanticos"])
        self.assertFalse(result["valido"])

    def test_modelos_automatas(self):
        models = construir_modelos_tokens()
        self.assertGreaterEqual(len(models), 5)
        for model in models:
            self.assertIn("flowchart LR", model["afnd_diagrama"])
            self.assertIn("flowchart LR", model["afd_diagrama"])
            self.assertIn("Q", model["quintupla"])
            self.assertIn("filas", model["tabla"])


if __name__ == "__main__":
    unittest.main()
