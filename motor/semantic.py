"""Análisis semántico y tabla de símbolos de TramaDSL."""
from __future__ import annotations
from typing import Any

def analizar_semantica(ast: dict[str, Any]) -> dict[str, Any]:
    symbols: dict[str, dict[str, Any]] = {}; errors=[]; turno=False
    def err(msg,node): errors.append({"mensaje":msg,"linea":node.get("line",1),"columna":node.get("column",1)})
    def infer(node):
        kind=node.get("type")
        if kind == "NumberLiteral": return "NUMBER"
        if kind == "StringLiteral": return "STRING"
        if kind == "Identifier":
            entry=symbols.get(node["name"])
            if not entry: err(f"Variable '{node['name']}' no declarada con DEF.",node); return "UNKNOWN"
            return entry["tipo"]
        if kind == "UnaryExpr":
            typ=infer(node["operand"])
            if typ not in ("NUMBER","UNKNOWN"): err("El operador unario '-' requiere NUMBER.",node)
            return "NUMBER"
        if kind == "BinaryExpr":
            left=infer(node["left"]); right=infer(node["right"]); op=node["operator"]
            if op in ("+","-","*","/"):
                if left not in ("NUMBER","UNKNOWN") or right not in ("NUMBER","UNKNOWN"): err(f"El operador '{op}' requiere operandos NUMBER; no se puede operar STRING con NUMBER.",node)
                return "NUMBER"
            if left != right and "UNKNOWN" not in (left,right): err("La comparación requiere operandos del mismo tipo.",node)
            return "BOOLEAN"
        return "UNKNOWN"
    def walk(statements):
        nonlocal turno
        for node in statements:
            typ=node["type"]
            if typ == "VarDecl":
                valtype=infer(node["value"])
                if node["name"] in symbols: err(f"La variable '{node['name']}' ya fue declarada.",node)
                else:
                    value=node["value"].get("value")
                    symbols[node["name"]]={"nombre":node["name"],"tipo":valtype if valtype != "UNKNOWN" else "UNKNOWN","valor_inicial":value,"linea_declaracion":node.get("line",1),"estado":"declarada"}
            elif typ == "Assign":
                target=symbols.get(node["name"])
                if not target: err(f"Variable '{node['name']}' no declarada con DEF.",node)
                value_type=infer(node["value"])
                if target and target["tipo"] != value_type and value_type != "UNKNOWN": err(f"Asignación incompatible: '{node['name']}' es {target['tipo']} y recibe {value_type}.",node)
                if target: target["estado"]="asignada"
            elif typ == "CommandStmt":
                cmd=node["command"]; arg=node["argument"]
                if cmd in ("REGISTRAR","REPORTAR_MERMA"):
                    if not turno: err(f"{cmd} requiere haber ejecutado INICIAR_TURNO antes.",node)
                    argtype=infer(arg)
                    if argtype not in ("NUMBER","UNKNOWN"): err(f"{cmd} requiere un argumento NUMBER.",node)
                elif cmd == "EMITIR": infer(arg)
                elif cmd == "INICIAR_TURNO":
                    if arg.get("type") not in ("Identifier","StringLiteral"): err("INICIAR_TURNO requiere un nombre de turno.",node)
                    elif arg.get("type")=="Identifier" and arg.get("name","").upper() not in {"MANANA","MAÑANA","TARDE","NOCHE"}:
                        # Identificadores de turno son literales de dominio.
                        err("El turno debe ser MANANA, MAÑANA, TARDE o NOCHE.",node)
                    turno=True
                elif cmd in ("DETENER_MAQUINA","CAMBIAR_LOTE"):
                    if arg.get("type")=="Identifier": continue
                    infer(arg)
            elif typ == "IfStmt":
                ctype=infer(node["test"])
                if ctype not in ("BOOLEAN","UNKNOWN"): err("La condición de SI debe ser booleana.",node)
                prior=turno; walk(node["consequent"]); then=turno
                turno=prior; walk(node["alternate"]); other=turno
                turno=then and other if node["alternate"] else prior
    walk(ast.get("body",[]))
    return {"tabla_simbolos":list(symbols.values()),"errores":errors,"valido":not errors}

# Alias para integración antigua.
def validar_semantica_ast(ast): return analizar_semantica(ast)
