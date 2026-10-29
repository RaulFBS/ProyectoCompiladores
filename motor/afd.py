"""Determinización por construcción de subconjuntos y render del AFD."""
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


def construir_afd(afnd: AFND) -> AFD:
    start_set = frozenset(cierre_epsilon(afnd, {afnd.start}))
    states: list[frozenset[int]] = [start_set]
    state_ids = {start_set: 0}
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
            if not destinations:
                continue
            target_set = frozenset(cierre_epsilon(afnd, destinations))
            if target_set not in state_ids:
                state_ids[target_set] = len(states)
                states.append(target_set)
            transitions[cursor][symbol] = state_ids[target_set]
        cursor += 1

    return AFD(start=0, finals=finals, transitions=transitions, states=states, alphabet=afnd.alphabet)


def agrupar_simbolos(afd: AFD) -> list[dict[str, object]]:
    """Agrupa caracteres con el mismo comportamiento de transición en todos los estados."""
    grouped: dict[tuple[int | None, ...], list[str]] = {}
    for char in afd.alphabet:
        signature = tuple(afd.transitions.get(state, {}).get(char) for state in range(len(afd.states)))
        grouped.setdefault(signature, []).append(char)
    return [
        {"chars": chars, "label": compactar_caracteres(chars), "representante": chars[0]}
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
        if char == " ":
            return "espacio"
        if char == "\n":
            return "\\n"
        if char == "\t":
            return "\\t"
        return char

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


def afd_a_mermaid(afd: AFD) -> str:
    lines = ["flowchart LR", "    Inicio([Inicio])", f"    Inicio --> D{afd.start}"]
    for state in range(len(afd.states)):
        if state in afd.finals:
            lines.append(f"    D{state}(((D{state})))")
        else:
            lines.append(f"    D{state}((D{state}))")

    grouped: dict[tuple[int, int], list[str]] = {}
    for origin, by_symbol in afd.transitions.items():
        for symbol, destination in by_symbol.items():
            grouped.setdefault((origin, destination), []).append(symbol)
    for (origin, destination), chars in grouped.items():
        label = compactar_caracteres(chars)
        if len(label) > 48:
            label = label[:45] + "..."
        label = label.replace('"', "'").replace("|", "\\|")
        lines.append(f"    D{origin} -->|\"{label}\"| D{destination}")
    return "\n".join(lines)


def quintupla(afd: AFD) -> dict[str, object]:
    columns = agrupar_simbolos(afd)
    delta_entries = []
    for origin in sorted(afd.transitions):
        for symbol, destination in sorted(afd.transitions[origin].items()):
            visible = {"\n": r"\\n", "\t": r"\\t", " ": "espacio"}.get(symbol, symbol)
            delta_entries.append(f"δ(D{origin}, {visible}) = D{destination}")
    return {
        "Q": [f"D{i}" for i in range(len(afd.states))],
        "Sigma": [column["label"] for column in columns],
        "delta": "{ " + "; ".join(delta_entries) + " }",
        "q0": f"D{afd.start}",
        "F": [f"D{i}" for i in sorted(afd.finals)],
    }
