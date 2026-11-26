"""Generador de TAC de tres direcciones a partir del AST semánticamente válido."""
from __future__ import annotations
import json

def generar_ir(ast):
    code=[]; temp=0; label=0
    def new_temp():
        nonlocal temp; temp+=1; return f"t{temp}"
    def new_label():
        nonlocal label; label+=1; return f"L{label}"
    def expr(node):
        kind=node["type"]
        if kind in ("NumberLiteral","StringLiteral"): return node["value"]
        if kind=="Identifier": return node["name"]
        if kind=="UnaryExpr":
            value=expr(node["operand"]); target=new_temp(); code.append({"op":"unary","target":target,"operator":node["operator"],"value":value}); return target
        if kind=="BinaryExpr":
            left=expr(node["left"]); right=expr(node["right"]); target=new_temp()
            code.append({"op":"binary","target":target,"left":left,"operator":node["operator"],"right":right}); return target
        return None
    def stmt(node):
        kind=node["type"]
        if kind in ("VarDecl","Assign"):
            code.append({"op":"assign","target":node["name"],"value":expr(node["value"])})
        elif kind=="CommandStmt":
            arg=node["argument"]
            # Turnos, máquinas y lotes sin comillas representan átomos de dominio.
            if node["command"] in ("INICIAR_TURNO","DETENER_MAQUINA","CAMBIAR_LOTE") and arg["type"]=="Identifier": value=arg["name"]
            else: value=expr(arg)
            code.append({"op":"command","command":node["command"],"value":value})
        elif kind=="IfStmt":
            test=expr(node["test"]); otherwise=new_label(); end=new_label()
            code.append({"op":"if_false","condition":test,"label":otherwise})
            for child in node["consequent"]: stmt(child)
            if node["alternate"]:
                code.append({"op":"goto","label":end})
            code.append({"op":"label","label":otherwise})
            for child in node["alternate"]: stmt(child)
            if node["alternate"]: code.append({"op":"label","label":end})
    for node in ast.get("body",[]): stmt(node)
    for i, ins in enumerate(code,1): ins["text"]=_format(ins)
    return code

def _format(i):
    op=i["op"]
    if op=="assign": return f"{i['target']} = {_v(i['value'])}"
    if op=="binary": return f"{i['target']} = {_v(i['left'])} {i['operator']} {_v(i['right'])}"
    if op=="unary": return f"{i['target']} = {i['operator']}{_v(i['value'])}"
    if op=="if_false": return f"IF_FALSE {_v(i['condition'])} GOTO {i['label']}"
    if op=="goto": return f"GOTO {i['label']}"
    if op=="label": return f"{i['label']}:"
    return f"{i['command']} {_v(i['value'])}"
def _v(v): return json.dumps(v,ensure_ascii=False) if isinstance(v,str) else str(v)
