# TramaLab — Compilador configurable de tramas logísticas

Prototipo académico construido con Python, Flask, HTML, CSS y JavaScript. La interfaz puede analizar un código de ejemplo o un archivo `.txt`, `.log` o `.dsl`, mostrar tokens y lexemas, revisar la gramática, y generar representaciones de AFND, AFD, quíntupla y tabla de transiciones desde el código.

## 1. Requisitos

- Python 3.10 o superior (recomendado: Python 3.11).
- Navegador moderno.
- Conexión a Internet para cargar Mermaid desde CDN y visualizar los gráficos.

## 2. Ejecutar localmente

Abre una terminal dentro de la carpeta `proyecto_compilador_tramas`.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Si PowerShell bloquea la activación, puedes ejecutar directamente el intérprete del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000 en el navegador. La ruta `/health` devuelve el estado de la aplicación.

## 3. Ejemplo del lenguaje

```text
INICIAR_TURNO NOCHE;
REGISTRAR 500;
DETENER_MAQUINA M2;
REPORTAR_MERMA 15;
CAMBIAR_LOTE ALG01;
```

Cada instrucción termina con `;`.

- `INICIAR_TURNO` recibe un identificador; semánticamente se aceptan `MANANA`, `TARDE` o `NOCHE`.
- `REGISTRAR` recibe un número no negativo.
- `DETENER_MAQUINA` recibe un identificador de máquina.
- `REPORTAR_MERMA` recibe un número no negativo.
- `CAMBIAR_LOTE` recibe un identificador de lote.

## 4. Estructura

```text
app.py                         Rutas Flask y carga de archivos
motor/lexer.py                 Análisis léxico
motor/expresiones_regulares.py Definiciones de ER por token
motor/afnd.py                  Parser de ER y construcción AFND por Thompson
motor/afd.py                   Conversión AFND → AFD y quíntupla
motor/transiciones.py          Tabla de transiciones
motor/parser.py                Análisis sintáctico y reglas semánticas
motor/compilador.py            Coordinación del análisis
motor/modelos_automatas.py     Creación de modelos y fuentes Mermaid
motor/reportes.py              Reporte PDF
templates/index.html           GUI
static/css/styles.css          Estilos
static/js/app.js               Interacción y diagramas Mermaid
tests/                         Pruebas básicas
```

## 5. Publicar en Render

El repositorio incluye `render.yaml`. Puedes conectar el repositorio de GitHub con Render y crear el servicio web desde el blueprint o configurar manualmente:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Health check path: `/health`

Los archivos cargados se procesan en memoria y no se guardan en el servidor. El límite de solicitud es 1 MB. En planes gratuitos el servicio puede entrar en reposo tras un periodo sin actividad.

## 6. Alcance y limitaciones actuales

- Es un prototipo inicial de un lenguaje de dominio logístico, no un compilador de Python.
- Las expresiones regulares configuradas son deliberadamente acotadas a los tokens definidos en `motor/lexer.py`.
- El constructor AFND admite literales, clases de caracteres, rangos, agrupación, alternancia y cuantificadores `*`, `+`, `?`.
- El análisis sintáctico reconoce las cinco instrucciones incluidas en la gramática base.
- Mermaid representa los gráficos a partir de texto que genera el servidor; necesita cargar su librería JavaScript en el navegador.
- El proyecto calcula los autómatas por separado para la expresión regular de cada token. La tokenización de la trama completa la hace el analizador léxico.

## 7. Pruebas

```bash
python -m unittest discover -s tests -v
```
