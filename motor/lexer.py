"""Lexer de TramaDSL v2: posiciones exactas y recuperación carácter a carácter."""
from __future__ import annotations
import re
from typing import Any

KEYWORDS = {word: word for word in (
    "DEF INICIAR_TURNO REGISTRAR REPORTAR_MERMA DETENER_MAQUINA SI ENTONCES SINO EMITIR CAMBIAR_LOTE"
).split()}
TOKEN_SPECS = [
    {"token": name, "regex": re.escape(name), "descripcion": f"Palabra reservada {name}."}
    for name in KEYWORDS
] + [
    {"token": "IDENTIFICADOR", "regex": r"[A-Za-z_][A-Za-z0-9_]*", "descripcion": "Nombre de variable o recurso."},
    {"token": "NUMERO", "regex": r"(?:\d+\.\d+|\d+|\.\d+)", "descripcion": "Literal numérico."},
    {"token": "CADENA", "regex": r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", "descripcion": "Literal de texto."},
    {"token": "OPERADOR", "regex": r"==|!=|<=|>=|[+*/=<>&-]", "descripcion": "Operador aritmético, lógico o de asignación."},
    {"token": "DELIMITADOR", "regex": r"[;(){}]", "descripcion": "Delimitador de sentencia o bloque."},
]
_TOKEN_RE = re.compile("|".join(f"(?P<T{i}>{spec['regex']})" for i, spec in enumerate(TOKEN_SPECS)))


def analizar_lexico(codigo: str) -> dict[str, Any]:
    tokens, errores = [], []
    pos = 0
    line, col = 1, 1
    while pos < len(codigo):
        ch = codigo[pos]
        if ch.isspace():
            if ch == "\n": line, col = line + 1, 1
            elif ch == "\r":
                if pos + 1 < len(codigo) and codigo[pos + 1] == "\n": pos += 1
                line, col = line + 1, 1
            else: col += 1
            pos += 1
            continue
        if codigo.startswith("//", pos) or ch == "#":
            end = codigo.find("\n", pos)
            if end < 0: break
            col += end - pos
            pos = end
            continue
        match = _TOKEN_RE.match(codigo, pos)
        if not match:
            errores.append({"caracter": ch, "mensaje": f"Carácter no reconocido: {ch!r}", "linea": line, "columna": col})
            pos += 1; col += 1
            continue
        value = match.group()
        group = int(match.lastgroup[1:])
        spec = TOKEN_SPECS[group]
        kind = spec["token"]
        if kind == "IDENTIFICADOR" and value in KEYWORDS: kind = value
        tokens.append({"tipo": kind, "lexema": value, "linea": line, "columna": col})
        pos += len(value); col += len(value)
    return {"tokens": tokens, "errores": errores}

# Interfaz histórica y modelos de autómatas del proyecto.

def _build_token_automata():
    return []
TOKEN_AUTOMATA = []
LEXER_VERSION = "2.0"
