# TramaLab — compilador TramaDSL v2.0

Aplicación Flask que implementa un pipeline modular de seis fases: lexer con ubicación de tokens, parser y AST JSON con recuperación, análisis semántico y tabla de símbolos, generación de TAC, optimización (constant folding y eliminación de temporales) y generación Python/JavaScript. La UI presenta cada fase y permite descargar el código generado. El botón de ejecución corre únicamente el JS generado en un Web Worker desechable con límite de tiempo.

## Ejecutar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visita http://127.0.0.1:5000. Pruebas: `python -m unittest discover -s tests -v`.

## Gramática resumida

```text
program → statement*
statement → DEF IDENTIFICADOR = expression ;
          | IDENTIFICADOR = expression ;
          | command expression ;
          | SI ( expression ) ENTONCES { statement* } (SINO { statement* })?
command → INICIAR_TURNO | REGISTRAR | REPORTAR_MERMA | DETENER_MAQUINA | EMITIR
expression → literales, identificadores, paréntesis y operadores + - * / == != < > <= >=
```

Ejemplo disponible en el editor. Los comandos `REGISTRAR` y `REPORTAR_MERMA` requieren turno iniciado previamente. Las palabras de turno, máquina y lote sin comillas son átomos de dominio (por ejemplo `NOCHE`, `M2`, `ALG01`). `CAMBIAR_LOTE` se conserva por compatibilidad con programas anteriores.

## Vercel

Incluye `vercel.json` para desplegar Flask con `@vercel/python`. Configura el proyecto para usar Python y la raíz del repositorio. La app no guarda cargas de archivos. La ejecución aislada de código destino se realiza en el cliente mediante Worker; no se ejecuta Python arbitrario en el servidor.

## Módulos

`motor/lexer.py`, `parser.py`, `semantic.py`, `ir_generator.py`, `optimizer.py`, `codegen.py` y `compilador.py`; UI en `templates/index.html` y `public/`.
