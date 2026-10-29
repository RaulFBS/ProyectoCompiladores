"""Genera los modelos formales y las fuentes Mermaid para cada token."""
from .lexer import TOKEN_SPECS
from .afnd import construir_afnd, afnd_a_mermaid
from .afd import construir_afd, afd_a_mermaid, quintupla
from .transiciones import generar_tabla_transiciones


def construir_modelos_tokens() -> list[dict]:
    modelos = []
    for spec in TOKEN_SPECS:
        afnd = construir_afnd(spec["regex"])
        afd = construir_afd(afnd)
        modelos.append({
            "token": spec["token"],
            "regex": spec["regex"],
            "descripcion": spec["descripcion"],
            "afnd_diagrama": afnd_a_mermaid(afnd),
            "afd_diagrama": afd_a_mermaid(afd),
            "quintupla": quintupla(afd),
            "tabla": generar_tabla_transiciones(afd),
            "cantidad_estados_afnd": len(afnd.states),
            "cantidad_estados_afd": len(afd.states),
            "afnd_inicial": f"N{afnd.start}",
            "afnd_final": f"N{afnd.accept}",
            "afd_inicial": f"D{afd.start}",
            "afd_finales": [f"D{state}" for state in sorted(afd.finals)],
        })
    return modelos
