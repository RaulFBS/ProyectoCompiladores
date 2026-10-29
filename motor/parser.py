"""Analizador sintáctico y validaciones semánticas del lenguaje de tramas."""
from __future__ import annotations
from typing import Any

ESPERADOS = {
    "INICIAR_TURNO": "IDENTIFICADOR",
    "REGISTRAR": "NUMERO",
    "DETENER_MAQUINA": "IDENTIFICADOR",
    "REPORTAR_MERMA": "NUMERO",
    "CAMBIAR_LOTE": "IDENTIFICADOR",
}

GRAMATICA = [
    ("programa", "programa → sentencia*"),
    ("sentencia", "sentencia → INICIAR_TURNO IDENTIFICADOR ;"),
    ("sentencia", "sentencia → REGISTRAR NUMERO ;"),
    ("sentencia", "sentencia → DETENER_MAQUINA IDENTIFICADOR ;"),
    ("sentencia", "sentencia → REPORTAR_MERMA NUMERO ;"),
    ("sentencia", "sentencia → CAMBIAR_LOTE IDENTIFICADOR ;"),
]


def analizar_sintaxis(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    errores: list[dict[str, Any]] = []
    sentencias: list[dict[str, Any]] = []
    index = 0

    def error(mensaje: str, token: dict[str, Any] | None = None) -> None:
        errores.append({
            "mensaje": mensaje,
            "linea": token.get("linea", 1) if token else (tokens[-1]["linea"] if tokens else 1),
            "columna": token.get("columna", 1) if token else 1,
        })

    def recuperar() -> None:
        nonlocal index
        while index < len(tokens) and tokens[index]["tipo"] != "PUNTO_Y_COMA":
            index += 1
        if index < len(tokens):
            index += 1

    while index < len(tokens):
        command_token = tokens[index]
        if command_token["tipo"] != "COMANDO":
            error("Se esperaba un comando al inicio de la instrucción.", command_token)
            recuperar()
            continue

        command = command_token["lexema"]
        index += 1
        expected_type = ESPERADOS[command]

        if index >= len(tokens):
            error(f"Falta un argumento de tipo {expected_type} para {command}.", command_token)
            break

        value_token = tokens[index]
        if value_token["tipo"] != expected_type:
            error(
                f"{command} requiere un argumento {expected_type}; se encontró {value_token['tipo']}.",
                value_token,
            )
            recuperar()
            continue

        value = value_token["lexema"]
        index += 1
        if index >= len(tokens) or tokens[index]["tipo"] != "PUNTO_Y_COMA":
            error("Falta el punto y coma ';' al final de la instrucción.", tokens[index] if index < len(tokens) else value_token)
            recuperar()
            continue

        index += 1
        sentencias.append({
            "comando": command,
            "valor": value,
            "linea": command_token["linea"],
        })

    return {
        "errores": errores,
        "sentencias": sentencias,
        "gramatica": [{"nombre": name, "produccion": production} for name, production in GRAMATICA],
    }


def validar_semantica(sentencias: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errores: list[dict[str, Any]] = []
    turnos_validos = {"MANANA", "TARDE", "NOCHE"}

    for sentencia in sentencias:
        command = sentencia["comando"]
        value = sentencia["valor"]
        error = None

        if command == "INICIAR_TURNO" and value.upper() not in turnos_validos:
            error = "El turno debe ser MANANA, TARDE o NOCHE."
        elif command in {"REGISTRAR", "REPORTAR_MERMA"}:
            try:
                number = float(value)
                if number < 0:
                    error = "El valor numérico no puede ser negativo."
            except ValueError:
                error = "El valor debe ser numérico."

        if error:
            errores.append({
                "mensaje": error,
                "linea": sentencia["linea"],
                "comando": command,
                "valor": value,
            })
    return errores
