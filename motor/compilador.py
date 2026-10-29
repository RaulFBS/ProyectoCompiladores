"""Coordina los AFD léxicos, parser, AST y análisis semántico."""
from __future__ import annotations
from typing import Any

from .lexer import analizar_lexico
from .parser import analizar_sintaxis, validar_semantica, generar_diagrama_ast


def analizar_fuente(codigo: str) -> dict[str, Any]:
    lexico = analizar_lexico(codigo)
    sintaxis = analizar_sintaxis(lexico["tokens"])
    errores_semanticos = (
        validar_semantica(sintaxis["sentencias"])
        if not sintaxis["errores"]
        else []
    )

    ast = sintaxis["ast"]

    # Agrega los errores léxicos al árbol como nodos de diagnóstico para
    # que también se visualicen cuando el texto contiene caracteres ilegales.
    for error in lexico["errores"]:
        ast["hijos"].append({
            "tipo": "Error léxico",
            "mensaje": error["mensaje"],
            "linea": error["linea"],
            "columna": error["columna"],
            "hijos": [],
        })

    # Los errores semánticos señalan la instrucción correspondiente.
    for error in errores_semanticos:
        ast["hijos"].append({
            "tipo": "Error semántico",
            "mensaje": error["mensaje"],
            "linea": error["linea"],
            "columna": error.get("columna", 1),
            "hijos": [],
        })

    ast["hijos"].sort(
        key=lambda node: (
            node.get("linea", 1),
            node.get("columna", 1),
        )
    )
    ast_diagrama = generar_diagrama_ast(ast)

    cantidad_errores = (
        len(lexico["errores"])
        + len(sintaxis["errores"])
        + len(errores_semanticos)
    )
    valido = cantidad_errores == 0

    return {
        "codigo": codigo,
        "tokens": lexico["tokens"],
        "errores_lexicos": lexico["errores"],
        "sentencias": sintaxis["sentencias"],
        "errores_sintacticos": sintaxis["errores"],
        "errores_semanticos": errores_semanticos,
        "gramatica": sintaxis["gramatica"],
        "ast": ast,
        "ast_diagrama": ast_diagrama,
        "valido": valido,
        "resumen": {
            "cantidad_tokens": len(lexico["tokens"]),
            "cantidad_sentencias": len(sintaxis["sentencias"]),
            "cantidad_errores": cantidad_errores,
        },
    }
