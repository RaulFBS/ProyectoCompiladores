"""Coordina el análisis léxico, sintáctico y semántico."""
from __future__ import annotations
from typing import Any
from .lexer import analizar_lexico
from .parser import analizar_sintaxis, validar_semantica


def analizar_fuente(codigo: str) -> dict[str, Any]:
    lexico = analizar_lexico(codigo)
    sintaxis = analizar_sintaxis(lexico["tokens"])
    semantic_errors = validar_semantica(sintaxis["sentencias"]) if not sintaxis["errores"] else []
    valido = not lexico["errores"] and not sintaxis["errores"] and not semantic_errors

    return {
        "codigo": codigo,
        "tokens": lexico["tokens"],
        "errores_lexicos": lexico["errores"],
        "sentencias": sintaxis["sentencias"],
        "errores_sintacticos": sintaxis["errores"],
        "errores_semanticos": semantic_errors,
        "gramatica": sintaxis["gramatica"],
        "valido": valido,
        "resumen": {
            "cantidad_tokens": len(lexico["tokens"]),
            "cantidad_sentencias": len(sintaxis["sentencias"]),
            "cantidad_errores": len(lexico["errores"]) + len(sintaxis["errores"]) + len(semantic_errors),
        },
    }
