"""Aplicación web Flask del compilador configurable de tramas logísticas."""
from __future__ import annotations
from io import BytesIO
from flask import Flask, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from motor.compilador import analizar_fuente
from motor.modelos_automatas import construir_modelos_tokens
from motor.reportes import generar_pdf

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB por solicitud
ALLOWED_EXTENSIONS = {"txt", "log", "dsl"}

EJEMPLO = """INICIAR_TURNO NOCHE;
REGISTRAR 500;
DETENER_MAQUINA M2;
REPORTAR_MERMA 15;
CAMBIAR_LOTE ALG01;"""


def extension_permitida(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def leer_entrada_formulario() -> tuple[str, str | None]:
    """Devuelve (código, error). Si se sube un archivo, este tiene prioridad."""
    uploaded = request.files.get("archivo")
    if uploaded and uploaded.filename:
        filename = secure_filename(uploaded.filename)
        if not extension_permitida(filename):
            return "", "El archivo debe tener extensión .txt, .log o .dsl."
        raw = uploaded.read(1_048_577)
        if len(raw) > 1_048_576:
            return "", "El archivo supera el límite de 1 MB."
        try:
            code = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return "", "No se pudo leer el archivo. Guárdalo con codificación UTF-8."
        if not code.strip():
            return "", "El archivo está vacío."
        return code, None

    code = request.form.get("codigo", "")
    if not code.strip():
        return "", "Escribe una trama o carga un archivo para analizar."
    return code, None


@app.route("/", methods=["GET", "POST"])
def index():
    modelos = construir_modelos_tokens()
    resultado = None
    codigo = EJEMPLO
    error_formulario = None

    if request.method == "POST":
        codigo, error_formulario = leer_entrada_formulario()
        if error_formulario is None:
            resultado = analizar_fuente(codigo)

    return render_template(
        "index.html",
        modelos=modelos,
        resultado=resultado,
        codigo=codigo,
        ejemplo=EJEMPLO,
        error_formulario=error_formulario,
    )


@app.post("/reporte")
def reporte():
    codigo = request.form.get("codigo", "")
    if not codigo.strip():
        return "No hay código para generar el reporte.", 400
    resultado = analizar_fuente(codigo)
    pdf = generar_pdf(resultado)
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte_compilador_tramas.pdf",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.errorhandler(RequestEntityTooLarge)
def manejar_archivo_grande(_error):
    modelos = construir_modelos_tokens()
    return render_template(
        "index.html",
        modelos=modelos,
        resultado=None,
        codigo="",
        ejemplo=EJEMPLO,
        error_formulario="La solicitud supera el límite de 1 MB. Reduce el tamaño del archivo.",
    ), 413


if __name__ == "__main__":
    # debug=True solo para ejecución local; en producción se usa Gunicorn.
    app.run(host="127.0.0.1", port=5000, debug=True)
