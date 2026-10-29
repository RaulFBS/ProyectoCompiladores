"""Representación tabular de la función de transición de un AFD."""
from .afd import AFD, agrupar_simbolos


def generar_tabla_transiciones(afd: AFD) -> dict:
    columns = agrupar_simbolos(afd)
    filas = []
    for state in range(len(afd.states)):
        row = {
            "estado": f"D{state}",
            "inicial": state == afd.start,
            "final": state in afd.finals,
            "transiciones": [],
        }
        for column in columns:
            representative = column["representante"]
            destination = afd.transitions.get(state, {}).get(representative)
            row["transiciones"].append(f"D{destination}" if destination is not None else "—")
        filas.append(row)
    return {
        "columnas": [str(column["label"]) for column in columns],
        "filas": filas,
    }
