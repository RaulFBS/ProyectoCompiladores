"""Casos del compilador TramaDSL v2."""
import unittest
from motor.compilador import analizar_fuente
class CompilerTests(unittest.TestCase):
 def test_full_pipeline(self):
  src='''DEF lote = "ALG01"; DEF meta = 500; DEF produccion = 0; INICIAR_TURNO NOCHE; produccion = produccion + 150 * 2; REGISTRAR produccion; SI (produccion >= meta) ENTONCES { EMITIR "META_CUMPLIDA"; } SINO { EMITIR "META_PENDIENTE"; }'''
  r=analizar_fuente(src); self.assertTrue(r['valido'],r); self.assertIn('META_CUMPLIDA',r['codigo_javascript']); self.assertTrue(r['tabla_simbolos']); self.assertTrue(r['tac_optimizado'])
 def test_undeclared_and_domain(self):
  r=analizar_fuente('REGISTRAR falta;'); self.assertFalse(r['valido']); self.assertGreaterEqual(len(r['errores_semanticos']),2)
 def test_types(self):
  r=analizar_fuente('DEF x = "a"; DEF y = x + 1;'); self.assertFalse(r['valido']); self.assertTrue(r['errores_semanticos'])
 def test_lexer_locations_and_operators(self):
  from motor.lexer import analizar_lexico
  r=analizar_lexico('DEF x = 1;\nSI (x >= 1) {}'); self.assertEqual(r['tokens'][0]['linea'],1); self.assertIn('>=',[t['lexema'] for t in r['tokens']])
 def test_legacy_domain_command(self):
  r=analizar_fuente('INICIAR_TURNO NOCHE; REGISTRAR 500; DETENER_MAQUINA M2;'); self.assertTrue(r['valido'],r)
if __name__=='__main__': unittest.main()
