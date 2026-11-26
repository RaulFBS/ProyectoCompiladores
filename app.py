"""TramaLab Flask app."""
from __future__ import annotations
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from motor.compilador import analizar_fuente
from motor.modelos_automatas import construir_modelos_tokens
from motor.reportes import generar_pdf
app=Flask(__name__,static_folder="public",static_url_path="")
app.config["MAX_CONTENT_LENGTH"]=1*1024*1024
ALLOWED_EXTENSIONS={"txt","log","dsl"}
EJEMPLO='''DEF lote = "ALG01";
DEF meta = 500;
DEF produccion = 0;
INICIAR_TURNO NOCHE;
produccion = produccion + 150 * 2;
REGISTRAR produccion;
REPORTAR_MERMA 15;
SI (produccion >= meta) ENTONCES { EMITIR "META_CUMPLIDA"; } SINO { EMITIR "META_PENDIENTE"; }
DETENER_MAQUINA M2;'''
def extension_permitida(filename): return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS
def leer_entrada_formulario():
    uploaded=request.files.get("archivo")
    if uploaded and uploaded.filename:
        filename=secure_filename(uploaded.filename)
        if not extension_permitida(filename): return "","El archivo debe tener extensión .txt, .log o .dsl."
        raw=uploaded.read(1_048_577)
        if len(raw)>1_048_576: return "","El archivo supera el límite de 1 MB."
        try: code=raw.decode("utf-8-sig")
        except UnicodeDecodeError: return "","Guarda el archivo con codificación UTF-8."
        return (code,None) if code.strip() else ("","El archivo está vacío.")
    code=request.form.get("codigo","")
    return (code,None) if code.strip() else ("","Escribe código o carga un archivo DSL.")
@app.route("/",methods=["GET","POST"])
def index():
    resultado=None; codigo=EJEMPLO; error_formulario=None
    if request.method=="POST":
        codigo,error_formulario=leer_entrada_formulario()
        if error_formulario is None: resultado=analizar_fuente(codigo)
    return render_template("index.html",modelos=construir_modelos_tokens(),resultado=resultado,codigo=codigo,ejemplo=EJEMPLO,error_formulario=error_formulario)
@app.post("/reporte")
def reporte():
    codigo=request.form.get("codigo","")
    if not codigo.strip(): return "No hay código para generar el reporte.",400
    return send_file(generar_pdf(analizar_fuente(codigo)),mimetype="application/pdf",as_attachment=True,download_name="reporte_compilador_tramas.pdf")
@app.post("/api/compile")
def api_compile():
    data=request.get_json(silent=True) or {}; code=data.get("code","")
    if not isinstance(code,str) or len(code)>1_000_000: return jsonify({"error":"Código inválido o demasiado largo."}),400
    return jsonify(analizar_fuente(code))
@app.get("/health")
def health(): return {"status":"ok"}
@app.errorhandler(RequestEntityTooLarge)
def manejar_archivo_grande(_error):
    return render_template("index.html",modelos=construir_modelos_tokens(),resultado=None,codigo="",ejemplo=EJEMPLO,error_formulario="La solicitud supera el límite de 1 MB."),413
if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=True)
