"""Analizador léxico que reconoce lexemas mediante los AFD generados."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

from .afnd import construir_afnd
from .afd import construir_afd, longitud_maxima_afd


@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# El orden es la prioridad en caso de empate: COMANDO antes que IDENTIFICADOR.
TOKEN_SPECS: list[dict[str, str]] = [
    {
        "token": "COMANDO",
        "regex": "INICIAR_TURNO|REGISTRAR|DETENER_MAQUINA|REPORTAR_MERMA|CAMBIAR_LOTE",
        "python_regex": r"(?:INICIAR_TURNO|REGISTRAR|DETENER_MAQUINA|REPORTAR_MERMA|CAMBIAR_LOTE)\b",
        "descripcion": "Palabra reservada que identifica una operación logística.",
    },
    {
        "token": "IDENTIFICADOR",
        "regex": r"[A-Za-z_][A-Za-z0-9_]*",
        "python_regex": r"[A-Za-z_][A-Za-z0-9_]*",
        "descripcion": "Nombre de turno, máquina o lote.",
    },
    {
        "token": "NUMERO",
        "regex": r"[0-9]+(\.[0-9]+)?",
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
        "descripcion": "Operador reservado para futuras extensiones.",
    },
]


def _build_token_automata() -> list[tuple[dict[str, str], Any]]:
    """Construye una vez el AFD de cada tipo de token."""
    result = []
    for spec in TOKEN_SPECS:
        afnd = construir_afnd(spec["regex"])
        afd = construir_afd(afnd)
        result.append((spec, afd))
    return result


# Estos mismos AFD se usan en el analizador léxico y en la visualización web.
TOKEN_AUTOMATA = _build_token_automata()


def _actualizar_posicion(fragmento: str, linea: int, columna: int) -> tuple[int, int]:
    """Actualiza línea y columna luego de consumir un lexema o carácter."""
    line_breaks = fragmento.count("\n")
    if line_breaks:
        linea += line_breaks
        columna = len(fragmento.rsplit("\n", 1)[-1]) + 1
    else:
        columna += len(fragmento)
    return linea, columna


def analizar_lexico(codigo: str) -> dict[str, Any]:
    """Tokeniza por máxima coincidencia usando los AFD, no re.match()."""
    tokens: list[Token] = []
    errores: list[dict[str, Any]] = []
    pos = 0
    linea = 1
    columna = 1

    while pos < len(codigo):
        char = codigo[pos]

        if char.isspace():
            # Trata CRLF como un solo salto de línea.
            if char == "\r":
                if pos + 1 < len(codigo) and codigo[pos + 1] == "\n":
                    pos += 2
                else:
                    pos += 1
                linea += 1
                columna = 1
            elif char == "\n":
                pos += 1
                linea += 1
                columna = 1
            else:
                pos += 1
                columna += 1
            continue

        mejor_final: int | None = None
        mejor_spec: dict[str, str] | None = None

        # Máxima coincidencia: gana el lexema más largo; si hay empate,
        # prevalece el token que aparece primero en TOKEN_SPECS.
        for spec, afd in TOKEN_AUTOMATA:
            final = longitud_maxima_afd(afd, codigo, pos)
            if final is not None and final > pos:
                if mejor_final is None or final > mejor_final:
                    mejor_final = final
                    mejor_spec = spec

        if mejor_final is not None and mejor_spec is not None:
            lexema = codigo[pos:mejor_final]
            tokens.append(Token(
                tipo=mejor_spec["token"],
                lexema=lexema,
                linea=linea,
                columna=columna,
            ))
            pos = mejor_final
            linea, columna = _actualizar_posicion(lexema, linea, columna)
            continue

        errores.append({
            "caracter": char,
            "mensaje": f"Carácter no reconocido: {char!r}",
            "linea": linea,
            "columna": columna,
        })
        pos += 1
        linea, columna = _actualizar_posicion(char, linea, columna)

    return {
        "tokens": [token.to_dict() for token in tokens],
        "errores": errores,
    }
