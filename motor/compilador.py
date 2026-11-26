"""Orquestación del pipeline del compilador TramaDSL de seis fases."""
from __future__ import annotations
from typing import Any
from .lexer import analizar_lexico
from .parser import analizar_sintaxis
from .semantic import analizar_semantica
from .ir_generator import generar_ir
from .optimizer import optimizar
from .codegen import generar_codigo

def analizar_fuente(codigo: str) -> dict[str, Any]:
    lex=analizar_lexico(codigo); syn=analizar_sintaxis(lex["tokens"])
    semantic=analizar_semantica(syn["ast"]) if not syn["errores"] else {"tabla_simbolos":[],"errores":[],"valido":False}
    errors=lex["errores"]+syn["errores"]+semantic["errores"]
    tac=[]; optimization={"antes":[],"despues":[],"optimizaciones":{}}
    targets={"python":"","javascript":""}
    valid=not errors
    if valid:
        tac=generar_ir(syn["ast"]); optimization=optimizar(tac); targets=generar_codigo(optimization["despues"])
    return {"codigo":codigo,"tokens":lex["tokens"],"errores_lexicos":lex["errores"],"errores_sintacticos":syn["errores"],"errores_semanticos":semantic["errores"],"tabla_simbolos":semantic["tabla_simbolos"],"ast":syn["ast"],"ast_json":syn["ast"],"ast_diagrama":"","sentencias":syn["ast"].get("body",[]),"gramatica":syn["gramatica"],"tac":tac,"tac_optimizado":optimization["despues"],"optimizacion":optimization,"codigo_python":targets["python"],"codigo_javascript":targets["javascript"],"valido":valid,"resumen":{"cantidad_tokens":len(lex["tokens"]),"cantidad_sentencias":len(syn["ast"].get("body",[])),"cantidad_errores":len(errors)}}
