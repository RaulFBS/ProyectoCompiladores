"""Analizador léxico para el lenguaje de tramas logísticas de ejemplo."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Mantener el orden: los comandos se reconocen antes que los identificadores.
TOKEN_SPECS: list[dict[str, str]] = [
    {
        "token": "COMANDO",
        "regex": "INICIAR_TURNO|REGISTRAR|DETENER_MAQUINA|REPORTAR_MERMA|CAMBIAR_LOTE",
        "python_regex": r"(?:INICIAR_TURNO|REGISTRAR|DETENER_MAQUINA|REPORTAR_MERMA|CAMBIAR_LOTE)\b",
        "descripcion": "Palabra reservada que identifica una operación logística.",
    },
    {
        "token": "IDENTIFICADOR",
        "regex": "[A-Za-z_][A-Za-z0-9_]*",
        "python_regex": r"[A-Za-z_][A-Za-z0-9_]*",
        "descripcion": "Nombre de turno, máquina o lote.",
    },
    {
        "token": "NUMERO",
        "regex": "[0-9]+(\\.[0-9]+)?",
        "python_regex": r"[0-9]+(?:\.[0-9]+)?",
        "descripcion": "Número entero o decimal no negativo.",
    },
    {
        "token": "PUNTO_Y_COMA",
        "regex": ";",
        "python_regex": r";",
        "descripcion": "Final de una instrucción.",
    },
    {
        "token": "IGUAL",
        "regex": "=",
        "python_regex": r"=",
        "descripcion": "Operador de asignación reservado para futuras extensiones.",
    },
]

COMPILED_SPECS = [
    (spec, re.compile(spec["python_regex"])) for spec in TOKEN_SPECS
]


def analizar_lexico(codigo: str) -> dict[str, Any]:
    """Devuelve tokens y errores con ubicación de línea y columna."""
    tokens: list[Token] = []
    errores: list[dict[str, Any]] = []
    pos = 0
    linea = 1
    columna = 1

    while pos < len(codigo):
        char = codigo[pos]

        if char.isspace():
            if char == "\n":
                linea += 1
                columna = 1
            else:
                columna += 1
            pos += 1
            continue

        coincidencia = None
        spec_encontrada = None
        for spec, regex in COMPILED_SPECS:
            coincidencia = regex.match(codigo, pos)
            if coincidencia:
                spec_encontrada = spec
                break

        if coincidencia and spec_encontrada:
            lexema = coincidencia.group(0)
            tokens.append(Token(
                tipo=spec_encontrada["token"],
                lexema=lexema,
                linea=linea,
                columna=columna,
            ))
            pos += len(lexema)
            columna += len(lexema)
            continue

        errores.append({
            "caracter": char,
            "mensaje": f"Carácter no reconocido: {char!r}",
            "linea": linea,
            "columna": columna,
        })
        pos += 1
        columna += 1

    return {
        "tokens": [token.to_dict() for token in tokens],
        "errores": errores,
    }
