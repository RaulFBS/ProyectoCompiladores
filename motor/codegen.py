"""Generación de código objeto Python/JavaScript a partir del TAC optimizado."""
from __future__ import annotations
import json

def generar_codigo(codigo_ir):
    labels={ins["label"]:i for i,ins in enumerate(codigo_ir) if ins["op"]=="label"}
    py=["# TramaDSL v2.0 — generado por TramaLab", "import json", "_pc = 0", f"_n = {len(codigo_ir)}", "while _pc < _n:"]
    js=["// TramaDSL v2.0 — generado por TramaLab",f"let _pc = 0;",f"const _n = {len(codigo_ir)};","while (_pc < _n) {"]
    for idx,ins in enumerate(codigo_ir):
        py.extend([f"    if _pc == {idx}:",*[_p for _p in _python_case(ins,labels,idx)],"        continue"])
        js.extend([f"  if (_pc === {idx}) {{",*[_j for _j in _js_case(ins,labels,idx)],"    continue;","  }"])
    py += ["    _pc += 1"]
    js += ["  _pc += 1;","}"]
    return {"python":"\n".join(py)+"\n","javascript":"\n".join(js)+"\n"}
def _lit(v): return json.dumps(v,ensure_ascii=False) if isinstance(v,str) else repr(v)
def _python_case(i,labels,n):
    op=i["op"]
    if op=="label": return [f"        _pc = {n+1}"]
    if op=="goto": return [f"        _pc = {labels[i['label']]}"]
    if op=="assign": return [f"        {i['target']} = {_lit(i['value'])}",f"        _pc = {n+1}"]
    if op=="binary": return [f"        {i['target']} = {i['left']} {i['operator']} {i['right']}",f"        _pc = {n+1}"]
    if op=="unary": return [f"        {i['target']} = {i['operator']}{i['value']}",f"        _pc = {n+1}"]
    if op=="if_false": return [f"        _pc = {n+1} if {i['condition']} else {labels[i['label']]}"]
    return _py_command(i,n)
def _py_command(i,n):
    cmd=i["command"]; value=i["value"]
    expr=_lit(value) if isinstance(value,str) or not isinstance(value,str) and cmd in ("INICIAR_TURNO","DETENER_MAQUINA","CAMBIAR_LOTE") else str(value)
    # Strings in REGISTRAR only possible on invalid DSL and are blocked before codegen.
    if cmd=="EMITIR": line=f"print({expr})"
    elif cmd=="INICIAR_TURNO": line=f"print('Turno iniciado: ' + str({expr}))"
    elif cmd=="REGISTRAR": line=f"print('Producción registrada: ' + str({expr}))"
    elif cmd=="REPORTAR_MERMA": line=f"print('Merma reportada: ' + str({expr}))"
    elif cmd=="DETENER_MAQUINA": line=f"print('Máquina detenida: ' + str({expr}))"
    else: line=f"print('Lote cambiado: ' + str({expr}))"
    return [f"        {line}",f"        _pc = {n+1}"]
def _js_case(i,labels,n):
    op=i["op"]
    if op=="label": return [f"    _pc = {n+1};"]
    if op=="goto": return [f"    _pc = {labels[i['label']]};"]
    if op=="assign": return [f"    {i['target']} = {_lit(i['value'])};",f"    _pc = {n+1};"]
    if op=="binary": return [f"    {i['target']} = {i['left']} {i['operator']} {i['right']};",f"    _pc = {n+1};"]
    if op=="unary": return [f"    {i['target']} = {i['operator']}{i['value']};",f"    _pc = {n+1};"]
    if op=="if_false": return [f"    _pc = {i['condition']} ? {n+1} : {labels[i['label']]};"]
    cmd=i["command"]; value=i["value"]
    expr=_lit(value) if isinstance(value,str) else str(value)
    messages={"EMITIR":expr,"INICIAR_TURNO":f"'Turno iniciado: ' + {expr}","REGISTRAR":f"'Producción registrada: ' + {expr}","REPORTAR_MERMA":f"'Merma reportada: ' + {expr}","DETENER_MAQUINA":f"'Máquina detenida: ' + {expr}","CAMBIAR_LOTE":f"'Lote cambiado: ' + {expr}"}
    return [f"    console.log({messages[cmd]});",f"    _pc = {n+1};"]
