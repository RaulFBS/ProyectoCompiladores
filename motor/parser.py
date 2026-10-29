"""Parser de TramaDSL, validación semántica y generación del árbol sintáctico."""
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


def _safe_label(value: Any) -> str:
    """Normaliza etiquetas para que el texto no rompa la sintaxis Mermaid."""
    return (
        str(value)
        .replace("&", " y ")
        .replace('"', "'")
        .replace("|", "¦")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
        .replace("<", "‹")
        .replace(">", "›")
        .replace("`", "'")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def generar_diagrama_ast(ast: dict[str, Any]) -> str:
    """Crea la fuente Mermaid del AST construido por el parser."""
    lines = [
        "flowchart TB",
        '    AST0(["Programa"])',
        "    classDef error fill:#fff1f2,stroke:#a52a35,color:#842029;",
        "    classDef command fill:#f8edef,stroke:#d9aeb3,color:#692029;",
    ]
    next_id = 1

    def add_node(parent_id: str, node: dict[str, Any]) -> None:
        nonlocal next_id
        current_id = f"AST{next_id}"
        next_id += 1

        node_type = node.get("tipo", "Nodo")
        line = node.get("linea")

        if node_type == "Sentencia":
            label = f"Sentencia · línea {line}"
        elif node_type in {"Error léxico", "Error sintáctico", "Error semántico"}:
            label = f"{node_type} · línea {line}: {node.get('mensaje', '')}"
        elif node_type == "Programa":
            label = "Programa"
        else:
            value = node.get("valor", "")
            label = f"{node_type}: {value}" if value != "" else node_type

        label = _safe_label(label)
        lines.append(f'    {current_id}["{label}"]')
        lines.append(f"    {parent_id} --> {current_id}")

        if node_type in {"Error léxico", "Error sintáctico", "Error semántico"}:
            lines.append(f"    class {current_id} error;")
        elif node_type in {"Comando", "Argumento", "Terminal"}:
            lines.append(f"    class {current_id} command;")

        for child in node.get("hijos", []):
            add_node(current_id, child)

    for child in ast.get("hijos", []):
        add_node("AST0", child)

    if len(lines) == 3:
        lines.append('    AST0note["Sin sentencias reconocidas"]')
        lines.append("    AST0 --> AST0note")

    return "\n".join(lines)


def analizar_sintaxis(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    errores: list[dict[str, Any]] = []
    sentencias: list[dict[str, Any]] = []
    ast_items: list[tuple[int, int, dict[str, Any]]] = []
    index = 0

    def error(mensaje: str, token: dict[str, Any] | None = None) -> None:
        linea = token.get("linea", 1) if token else (tokens[-1]["linea"] if tokens else 1)
        columna = token.get("columna", 1) if token else 1
        errores.append({"mensaje": mensaje, "linea": linea, "columna": columna})
        ast_items.append((linea, columna, {
            "tipo": "Error sintáctico",
            "mensaje": mensaje,
            "linea": linea,
            "columna": columna,
            "hijos": [],
        }))

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
        expected_type = ESPERADOS.get(command)
        index += 1

        if expected_type is None:
            error(f"Comando no reconocido por la gramática: {command}.", command_token)
            recuperar()
            continue

        if index >= len(tokens):
            error(f"Falta un argumento de tipo {expected_type} para {command}.", command_token)
            break

        value_token = tokens[index]
        if value_token["tipo"] != expected_type:
            error(
                f"{command} requiere un argumento {expected_type}; "
                f"se encontró {value_token['tipo']}.",
                value_token,
            )
            recuperar()
            continue

        value = value_token["lexema"]
        index += 1

        if index >= len(tokens) or tokens[index]["tipo"] != "PUNTO_Y_COMA":
            error(
                "Falta el punto y coma ';' al final de la instrucción.",
                tokens[index] if index < len(tokens) else value_token,
            )
            recuperar()
            continue

        semicolon_token = tokens[index]
        index += 1

        statement = {
            "comando": command,
            "valor": value,
            "linea": command_token["linea"],
            "columna": command_token["columna"],
        }
        sentencias.append(statement)

        ast_items.append((command_token["linea"], command_token["columna"], {
            "tipo": "Sentencia",
            "linea": command_token["linea"],
            "columna": command_token["columna"],
            "hijos": [
                {"tipo": "Comando", "valor": command, "hijos": []},
                {"tipo": "Argumento", "valor": value, "hijos": []},
                {"tipo": "Terminal", "valor": semicolon_token["lexema"], "hijos": []},
            ],
        }))

    ast_items.sort(key=lambda item: (item[0], item[1]))
    ast = {"tipo": "Programa", "hijos": [node for _, _, node in ast_items]}

    return {
        "errores": errores,
        "sentencias": sentencias,
        "gramatica": [
            {"nombre": name, "produccion": production}
            for name, production in GRAMATICA
        ],
        "ast": ast,
        "ast_diagrama": generar_diagrama_ast(ast),
    }


def validar_semantica(sentencias: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errores: list[dict[str, Any]] = []
    turnos_validos = {"MANANA", "MAÑANA", "TARDE", "NOCHE"}

    for sentencia in sentencias:
        command = sentencia["comando"]
        value = sentencia["valor"]
        error_message = None

        if command == "INICIAR_TURNO" and value.upper() not in turnos_validos:
            error_message = "El turno debe ser MANANA, MAÑANA, TARDE o NOCHE."
        elif command in {"REGISTRAR", "REPORTAR_MERMA"}:
            try:
                number = float(value)
                if number < 0:
                    error_message = "El valor numérico no puede ser negativo."
            except ValueError:
                error_message = "El valor debe ser numérico."

        if error_message:
            errores.append({
                "mensaje": error_message,
                "linea": sentencia["linea"],
                "columna": sentencia.get("columna", 1),
                "comando": command,
                "valor": value,
            })

    return errores
