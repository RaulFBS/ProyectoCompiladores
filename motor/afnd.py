"""Conversión de una expresión regular a un AFND mediante construcción de Thompson.

Sintaxis de expresiones admitida: literales, clases como [A-Z], rangos,
agrupación (), alternancia | y cuantificadores *, +, ?.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


ASCII_PRINTABLE = set(chr(i) for i in range(32, 127))


class RegexSyntaxError(ValueError):
    pass


@dataclass
class AFND:
    start: int
    accept: int
    transitions: dict[int, list[tuple[str | None, int]]]
    states: list[int]
    alphabet: list[str]


class RegexParser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def parse(self) -> Any:
        node = self._alternation()
        if self.pos != len(self.pattern):
            raise RegexSyntaxError(f"Símbolo inesperado en posición {self.pos}: {self.pattern[self.pos]!r}")
        return node

    def _alternation(self) -> Any:
        parts = [self._concatenation()]
        while self._peek() == "|":
            self.pos += 1
            parts.append(self._concatenation())
        return parts[0] if len(parts) == 1 else ("alt", parts)

    def _concatenation(self) -> Any:
        parts = []
        while self.pos < len(self.pattern) and self._peek() not in ")|":
            parts.append(self._quantified())
        if not parts:
            return ("chars", set())
        return parts[0] if len(parts) == 1 else ("concat", parts)

    def _quantified(self) -> Any:
        atom = self._atom()
        while self._peek() in ("*", "+", "?") and self.pos < len(self.pattern):
            operator = self._peek()
            self.pos += 1
            atom = ({"*": "star", "+": "plus", "?": "optional"}[operator], atom)
        return atom

    def _atom(self) -> Any:
        if self.pos >= len(self.pattern):
            raise RegexSyntaxError("Se esperaba un símbolo.")
        char = self._peek()
        if char == "(":
            self.pos += 1
            node = self._alternation()
            if self._peek() != ")":
                raise RegexSyntaxError("Falta cerrar un paréntesis.")
            self.pos += 1
            return node
        if char == "[":
            return ("chars", self._character_class())
        if char == "\\":
            self.pos += 1
            if self.pos >= len(self.pattern):
                raise RegexSyntaxError("La expresión termina con una barra inversa.")
            escaped = self.pattern[self.pos]
            self.pos += 1
            if escaped == "d":
                return ("chars", set("0123456789"))
            if escaped == "w":
                return ("chars", set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"))
            if escaped == "s":
                return ("chars", set(" \t\r\n"))
            return ("chars", {escaped})
        if char in "*+?)":
            raise RegexSyntaxError(f"Cuantificador o cierre sin operando: {char!r}")
        self.pos += 1
        if char == ".":
            return ("chars", set(ASCII_PRINTABLE))
        return ("chars", {char})

    def _character_class(self) -> set[str]:
        self.pos += 1  # [
        negate = self._peek() == "^"
        if negate:
            self.pos += 1
        chars: set[str] = set()
        have_first = False
        while self.pos < len(self.pattern) and self._peek() != "]":
            first = self._class_char()
            have_first = True
            if self._peek() == "-" and self.pos + 1 < len(self.pattern) and self.pattern[self.pos + 1] != "]":
                self.pos += 1
                last = self._class_char()
                if ord(first) > ord(last):
                    raise RegexSyntaxError(f"Rango inválido: {first}-{last}")
                chars.update(chr(code) for code in range(ord(first), ord(last) + 1))
            else:
                chars.add(first)
        if self._peek() != "]":
            raise RegexSyntaxError("Falta cerrar una clase de caracteres.")
        self.pos += 1
        if not have_first:
            raise RegexSyntaxError("La clase de caracteres está vacía.")
        if negate:
            chars = ASCII_PRINTABLE - chars
        return chars

    def _class_char(self) -> str:
        char = self._peek()
        if char == "\\":
            self.pos += 1
            if self.pos >= len(self.pattern):
                raise RegexSyntaxError("Escape incompleto dentro de una clase.")
            char = self.pattern[self.pos]
            self.pos += 1
            return {"n": "\n", "t": "\t", "r": "\r"}.get(char, char)
        self.pos += 1
        return char

    def _peek(self) -> str:
        return self.pattern[self.pos] if self.pos < len(self.pattern) else ""


class ThompsonBuilder:
    def __init__(self):
        self.next_state = 0
        self.transitions: dict[int, list[tuple[str | None, int]]] = {}

    def _state(self) -> int:
        state = self.next_state
        self.next_state += 1
        self.transitions[state] = []
        return state

    def _edge(self, origin: int, symbol: str | None, destination: int) -> None:
        self.transitions[origin].append((symbol, destination))

    def compile(self, node: Any) -> tuple[int, int]:
        kind = node[0]
        if kind == "chars":
            start, end = self._state(), self._state()
            for char in sorted(node[1]):
                self._edge(start, char, end)
            return start, end
        if kind == "concat":
            fragments = [self.compile(child) for child in node[1]]
            for (_, previous_end), (next_start, _) in zip(fragments, fragments[1:]):
                self._edge(previous_end, None, next_start)
            return fragments[0][0], fragments[-1][1]
        if kind == "alt":
            start, end = self._state(), self._state()
            for child in node[1]:
                child_start, child_end = self.compile(child)
                self._edge(start, None, child_start)
                self._edge(child_end, None, end)
            return start, end
        if kind in ("star", "plus", "optional"):
            start, end = self._state(), self._state()
            child_start, child_end = self.compile(node[1])
            self._edge(start, None, child_start)
            if kind in ("star", "optional"):
                self._edge(start, None, end)
            self._edge(child_end, None, end)
            if kind in ("star", "plus"):
                self._edge(child_end, None, child_start)
            return start, end
        raise RegexSyntaxError(f"Tipo de nodo no soportado: {kind}")


def construir_afnd(pattern: str) -> AFND:
    ast = RegexParser(pattern).parse()
    builder = ThompsonBuilder()
    start, accept = builder.compile(ast)
    alphabet = sorted({symbol for edges in builder.transitions.values() for symbol, _ in edges if symbol is not None})
    return AFND(
        start=start,
        accept=accept,
        transitions=builder.transitions,
        states=list(range(builder.next_state)),
        alphabet=alphabet,
    )


def cierre_epsilon(afnd: AFND, states: set[int]) -> set[int]:
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        for symbol, destination in afnd.transitions.get(state, []):
            if symbol is None and destination not in closure:
                closure.add(destination)
                stack.append(destination)
    return closure


def mover(afnd: AFND, states: set[int], symbol: str) -> set[int]:
    destinations: set[int] = set()
    for state in states:
        for edge_symbol, destination in afnd.transitions.get(state, []):
            if edge_symbol == symbol:
                destinations.add(destination)
    return destinations


def afnd_a_mermaid(afnd: AFND) -> str:
    lines = ["flowchart LR", "    Inicio([Inicio])", f"    Inicio --> N{afnd.start}"]
    for state in afnd.states:
        if state == afnd.accept:
            lines.append(f"    N{state}(((q{state})))")
        else:
            lines.append(f"    N{state}((q{state}))")
    grouped: dict[tuple[int, int], list[str]] = {}
    for origin, edges in afnd.transitions.items():
        for symbol, destination in edges:
            label = "ε" if symbol is None else _visible_symbol(symbol)
            grouped.setdefault((origin, destination), []).append(label)
    for (origin, destination), labels in grouped.items():
        label = _compact_display(labels)
        lines.append(f"    N{origin} -->|\"{_mermaid_escape(label)}\"| N{destination}")
    return "\n".join(lines)


def _visible_symbol(char: str) -> str:
    return {"\n": "\\n", "\r": "\\r", "\t": "\\t", " ": "espacio"}.get(char, char)


def _compact_display(labels: list[str]) -> str:
    unique = sorted(set(labels), key=lambda value: (len(value), value))
    if len(unique) > 14:
        return ", ".join(unique[:12]) + ", …"
    return ", ".join(unique)


def _mermaid_escape(value: str) -> str:
    return value.replace('"', "'").replace("|", "\\|").replace("[", "(").replace("]", ")")
