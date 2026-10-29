"""Determinización, completado formal del AFD y representación visual."""
from __future__ import annotations
from dataclasses import dataclass
from .afnd import AFND, cierre_epsilon, mover


@dataclass
class AFD:
    start: int
    finals: set[int]
    transitions: dict[int, dict[str, int]]
    states: list[frozenset[int]]
    alphabet: list[str]
    sink_state: int | None = None


def construir_afd(afnd: AFND) -> AFD:
    """Construye el AFD por subconjuntos y hace total delta sobre Sigma.

    El subconjunto vacío, cuando es alcanzable, funciona como estado
    sumidero: no es final y tiene bucles para todos los símbolos.
    """
    start_set = frozenset(cierre_epsilon(afnd, {afnd.start}))
    states: list[frozenset[int]] = [start_set]
    state_ids: dict[frozenset[int], int] = {start_set: 0}
    transitions: dict[int, dict[str, int]] = {}
    finals: set[int] = set()
    cursor = 0

    while cursor < len(states):
        current = states[cursor]
        transitions[cursor] = {}
        if afnd.accept in current:
            finals.add(cursor)

        for symbol in afnd.alphabet:
            destinations = mover(afnd, set(current), symbol)
            target_set = frozenset(cierre_epsilon(afnd, destinations))

            if target_set not in state_ids:
                state_ids[target_set] = len(states)
                states.append(target_set)

            transitions[cursor][symbol] = state_ids[target_set]

        cursor += 1

    sink_state = state_ids.get(frozenset())

    # Comprobación defensiva: cada estado tiene transición para cada símbolo.
    # La construcción anterior ya satisface esto dentro de Sigma.
    for state in range(len(states)):
        for symbol in afnd.alphabet:
            if symbol not in transitions.setdefault(state, {}):
                if sink_state is None:
                    sink_state = len(states)
                    states.append(frozenset())
                    state_ids[frozenset()] = sink_state
                    transitions[sink_state] = {char: sink_state for char in afnd.alphabet}
                transitions[state][symbol] = sink_state

    return AFD(
        start=0,
        finals=finals,
        transitions=transitions,
        states=states,
        alphabet=list(afnd.alphabet),
        sink_state=sink_state,
    )


def agrupar_simbolos(afd: AFD) -> list[dict[str, object]]:
    """Agrupa caracteres cuyas columnas de transición son equivalentes."""
    grouped: dict[tuple[int | None, ...], list[str]] = {}
    for char in afd.alphabet:
        signature = tuple(
            afd.transitions.get(state, {}).get(char)
            for state in range(len(afd.states))
        )
        grouped.setdefault(signature, []).append(char)

    return [
        {
            "chars": chars,
            "label": compactar_caracteres(chars),
            "representante": chars[0],
        }
        for chars in sorted(grouped.values(), key=lambda chars: chars[0])
    ]


def compactar_caracteres(chars: list[str]) -> str:
    chars = sorted(set(chars), key=ord)
    if not chars:
        return "∅"

    ranges: list[str] = []
    start = previous = ord(chars[0])

    def display(code: int) -> str:
        char = chr(code)
        return {" ": "espacio", "\n": r"\n", "\t": r"\t", "\r": r"\r"}.get(char, char)

    for char in chars[1:]:
        code = ord(char)
        if code == previous + 1:
            previous = code
            continue
        ranges.append(_range_label(start, previous, display))
        start = previous = code

    ranges.append(_range_label(start, previous, display))
    return ", ".join(ranges)


def _range_label(start: int, end: int, display) -> str:
    if end - start >= 2 and chr(start).isalnum() and chr(end).isalnum():
        return f"{display(start)}-{display(end)}"
    if start == end:
        return display(start)
    return ", ".join(display(code) for code in range(start, end + 1))


def _mermaid_escape(value: str) -> str:
    """Evita que labels con caracteres especiales alteren el código Mermaid."""
    return (
        str(value)
        .replace('"', "'")
        .replace("|", "¦")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
        .replace("<", "‹")
        .replace(">", "›")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def afd_a_mermaid(afd: AFD) -> str:
    lines = ["flowchart LR", "    Inicio([Inicio])", f"    Inicio --> D{afd.start}"]

    for state in range(len(afd.states)):
        if state == afd.sink_state:
            lines.append(f'    D{state}["D{state} · sumidero"]')
        elif state in afd.finals:
            lines.append(f"    D{state}(((D{state})))")
        else:
            lines.append(f"    D{state}((D{state}))")

    grouped: dict[tuple[int, int], list[str]] = {}
    for origin, by_symbol in afd.transitions.items():
        for symbol, destination in by_symbol.items():
            grouped.setdefault((origin, destination), []).append(symbol)

    for (origin, destination), chars in grouped.items():
        label = compactar_caracteres(chars)
        if len(label) > 65:
            label = label[:62] + "..."
        label = _mermaid_escape(label)
        lines.append(f'    D{origin} -->|"{label}"| D{destination}')

    if afd.sink_state is not None:
        lines.append("    classDef sink fill:#f3f3f3,stroke:#777,color:#444;")
        lines.append(f"    class D{afd.sink_state} sink;")

    return "\n".join(lines)


def quintupla(afd: AFD) -> dict[str, object]:
    """Devuelve la quíntupla M=(Q, Sigma, delta, q0, F)."""
    columns = agrupar_simbolos(afd)
    delta_entries = []

    for origin in sorted(afd.transitions):
        # Comprime símbolos que desde este estado conducen al mismo destino.
        by_destination: dict[int, list[str]] = {}
        for symbol, destination in sorted(afd.transitions[origin].items()):
            by_destination.setdefault(destination, []).append(symbol)

        for destination, chars in sorted(by_destination.items()):
            label = _mermaid_escape(compactar_caracteres(chars))
            delta_entries.append(f"δ(D{origin}, {{{label}}}) = D{destination}")

    return {
        "Q": [f"D{i}" for i in range(len(afd.states))],
        "Sigma": [str(column["label"]) for column in columns],
        "delta": "{ " + "; ".join(delta_entries) + " }",
        "q0": f"D{afd.start}",
        "F": [f"D{state}" for state in sorted(afd.finals)],
        "sumidero": f"D{afd.sink_state}" if afd.sink_state is not None else None,
    }


def simular_afd(afd: AFD, texto: str) -> bool:
    """Determina si el AFD acepta exactamente todo el texto proporcionado."""
    state = afd.start
    for char in texto:
        destination = afd.transitions.get(state, {}).get(char)
        if destination is None:
            return False
        state = destination
        if afd.sink_state is not None and state == afd.sink_state:
            return False
    return state in afd.finals


def longitud_maxima_afd(afd: AFD, texto: str, inicio: int = 0) -> int | None:
    """Devuelve el índice final del prefijo más largo aceptado, o None."""
    state = afd.start
    position = inicio
    last_accept: int | None = inicio if state in afd.finals else None

    while position < len(texto):
        char = texto[position]
        destination = afd.transitions.get(state, {}).get(char)
        if destination is None:
            break

        state = destination
        position += 1

        if state in afd.finals:
            last_accept = position

        if afd.sink_state is not None and state == afd.sink_state:
            break

    return last_accept
