"""Optimizador TAC: constant folding, propagación local y DCE de temporales."""
from __future__ import annotations
import operator
OPS={"+":operator.add,"-":operator.sub,"*":operator.mul,"/":operator.truediv,"==":operator.eq,"!=":operator.ne,"<":operator.lt,">":operator.gt,"<=":operator.le,">=":operator.ge}
def optimizar(codigo):
    before=[dict(i) for i in codigo]; code=[dict(i) for i in codigo]; constants={}; removed=0
    for ins in code:
        op=ins["op"]
        if op=="binary":
            a=constants.get(ins["left"],ins["left"]); b=constants.get(ins["right"],ins["right"])
            ins["left"],ins["right"]=a,b
            if not isinstance(a,str) and not isinstance(b,str):
                try:
                    value=OPS[ins["operator"]](a,b)
                    if isinstance(value,float) and value.is_integer(): value=int(value)
                    ins.clear(); ins.update({"op":"assign","target":ins.get("target","t"),"value":value})
                except (ZeroDivisionError,TypeError,KeyError): pass
        if op=="assign":
            value=ins.get("value")
            if ins["target"].startswith("t") and not isinstance(value,str): constants[ins["target"]]=value
            elif ins["target"].startswith("t"): constants.pop(ins["target"],None)
        if op=="if_false" and ins["condition"] in constants: ins["condition"]=constants[ins["condition"]]
    # DCE only for temporaries: user-visible variables and commands are retained.
    used=set()
    for ins in code:
        for key in ("left","right","value","condition"):
            v=ins.get(key)
            if isinstance(v,str) and v.startswith("t"): used.add(v)
    filtered=[]
    for ins in code:
        if ins["op"]=="assign" and ins["target"].startswith("t") and ins["target"] not in used:
            removed+=1; continue
        filtered.append(ins)
    for ins in filtered:
        if "text" in ins:
            from .ir_generator import _format
            ins["text"]=_format(ins)
    return {"antes":before,"despues":filtered,"optimizaciones":{"temporales_eliminados":removed,"constant_folding":sum(1 for a,b in zip(before,filtered) if a.get("op")=="binary" and b.get("op")=="assign")}}
