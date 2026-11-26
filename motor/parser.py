"""Parser recursivo descendente de TramaDSL. El AST es serializable a JSON."""
from __future__ import annotations
from typing import Any

GRAMATICA = [
 ("program", "program → statement*"),
 ("statement", "statement → DEF IDENTIFICADOR = expression ; | IDENTIFICADOR = expression ;"),
 ("statement", "statement → command expression ; | SI ( expression ) ENTONCES { statement* } (SINO { statement* })?"),
 ("expression", "expression → comparison ( ( + | - ) comparison )*"),
 ("comparison", "comparison → term ( ( == | != | < | > | <= | >= ) term )?"),
 ("term", "term → factor ( ( * | / ) factor )*"),
 ("factor", "factor → NUMERO | CADENA | IDENTIFICADOR | ( expression ) | - factor"),
]
COMMANDS = {"INICIAR_TURNO", "REGISTRAR", "REPORTAR_MERMA", "DETENER_MAQUINA", "CAMBIAR_LOTE"}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.i = 0; self.errors = []
    def peek(self, offset=0):
        return self.tokens[self.i + offset] if self.i + offset < len(self.tokens) else None
    def is_(self, *values):
        t = self.peek(); return t is not None and (t["tipo"] in values or t["lexema"] in values)
    def take(self):
        t = self.peek()
        if t is not None: self.i += 1
        return t
    def error(self, msg, token=None):
        t = token or self.peek() or (self.tokens[-1] if self.tokens else {"linea":1,"columna":1})
        self.errors.append({"mensaje": msg, "linea": t.get("linea",1), "columna": t.get("columna",1)})
    def expect(self, value, message=None):
        if self.is_(value): return self.take()
        self.error(message or f"Se esperaba '{value}'.")
        raise ParseError()
    def synchronize(self, in_block=False):
        while self.peek():
            if self.is_("}"): return
            if self.is_(";"): self.take(); return
            if self.is_("DEF","SI",*COMMANDS,"EMITIR") or (self.peek()["tipo"] == "IDENTIFICADOR" and self.is_("=",) if False else False): return
            self.take()
    def program(self):
        body=[]
        while self.peek():
            before=self.i
            try: body.append(self.statement())
            except ParseError: self.synchronize()
            if before == self.i: self.take()
        return {"type":"Program","body":body,"line":1}
    def statement(self):
        t=self.peek()
        if self.is_("DEF"):
            self.take(); name=self.expect("IDENTIFICADOR", "DEF requiere un nombre de variable.")
            self.expect("=", "Se esperaba '=' en la declaración.")
            value=self.expression(); self.expect(";", "Falta ';' tras la declaración.")
            return {"type":"VarDecl","name":name["lexema"],"value":value,"line":t["linea"],"column":t["columna"]}
        if self.is_("SI"): return self.if_statement()
        if t and t["tipo"] in COMMANDS | {"EMITIR"}:
            command=self.take(); arg=self.expression(); self.expect(";", "Falta ';' tras el comando.")
            return {"type":"CommandStmt","command":command["tipo"],"argument":arg,"line":command["linea"],"column":command["columna"]}
        if t and t["tipo"] == "IDENTIFICADOR":
            name=self.take(); self.expect("=", "Se esperaba '=' tras el identificador.")
            value=self.expression(); self.expect(";", "Falta ';' tras la asignación.")
            return {"type":"Assign","name":name["lexema"],"value":value,"line":name["linea"],"column":name["columna"]}
        self.error("Se esperaba una declaración, asignación, condición o comando.", t)
        raise ParseError()
    def if_statement(self):
        start=self.take(); self.expect("("); test=self.expression(); self.expect(")")
        self.expect("ENTONCES"); self.expect("{")
        consequent=self.block()
        alternate=[]
        if self.is_("SINO"):
            self.take(); self.expect("{"); alternate=self.block()
        return {"type":"IfStmt","test":test,"consequent":consequent,"alternate":alternate,"line":start["linea"],"column":start["columna"]}
    def block(self):
        body=[]
        while self.peek() and not self.is_("}"):
            before=self.i
            try: body.append(self.statement())
            except ParseError: self.synchronize(True)
            if before == self.i: self.take()
        self.expect("}", "Falta '}' para cerrar el bloque.")
        return body
    def expression(self): return self.comparison()
    def comparison(self):
        node=self.term()
        if self.is_("==","!=","<",">","<=",">="):
            op=self.take(); node={"type":"BinaryExpr","operator":op["lexema"],"left":node,"right":self.term(),"line":op["linea"]}
        return node
    def term(self):
        node=self.factor()
        while self.is_("+","-"):
            op=self.take(); node={"type":"BinaryExpr","operator":op["lexema"],"left":node,"right":self.factor(),"line":op["linea"]}
        return node
    def factor(self):
        node=self.unary()
        while self.is_("*","/"):
            op=self.take(); node={"type":"BinaryExpr","operator":op["lexema"],"left":node,"right":self.unary(),"line":op["linea"]}
        return node
    def unary(self):
        if self.is_("-"):
            op=self.take(); return {"type":"UnaryExpr","operator":"-","operand":self.unary(),"line":op["linea"]}
        if self.is_("("):
            self.take(); node=self.expression(); self.expect(")"); return node
        t=self.take()
        if t is None: self.error("Expresión incompleta."); raise ParseError()
        if t["tipo"] == "NUMERO":
            return {"type":"NumberLiteral","value":float(t["lexema"]) if "." in t["lexema"] else int(t["lexema"]),"line":t["linea"]}
        if t["tipo"] == "CADENA":
            import json
            try: value=json.loads(t["lexema"]) if t["lexema"].startswith('"') else bytes(t["lexema"][1:-1],"utf8").decode("unicode_escape")
            except Exception: value=t["lexema"][1:-1]
            return {"type":"StringLiteral","value":value,"line":t["linea"]}
        if t["tipo"] == "IDENTIFICADOR": return {"type":"Identifier","name":t["lexema"],"line":t["linea"]}
        self.error("Se esperaba un número, cadena, variable o expresión entre paréntesis.", t); raise ParseError()

class ParseError(Exception): pass

def analizar_sintaxis(tokens):
    p=Parser(tokens); ast=p.program()
    return {"ast":ast,"errores":p.errors,"sentencias":ast["body"],"gramatica":[{"nombre":n,"produccion":r} for n,r in GRAMATICA],"ast_diagrama":""}

def generar_diagrama_ast(ast):
    return ast

def validar_semantica(sentencias):
    from .semantic import analizar_semantica
    return analizar_semantica({"type":"Program","body":sentencias})["errores"]
