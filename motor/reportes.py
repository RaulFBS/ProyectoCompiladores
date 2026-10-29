"""Generación de un reporte PDF descargable."""
from __future__ import annotations
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted


def generar_pdf(resultado: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.7 * cm, leftMargin=1.7 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Reporte del compilador de tramas logísticas",
        author="Proyecto de Compiladores",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallCode", parent=styles["Code"], fontSize=8, leading=10, wordWrap="CJK"))
    story = [
        Paragraph("Reporte del compilador de tramas logísticas", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Estado: <b>{'VÁLIDO' if resultado['valido'] else 'REVISAR ERRORES'}</b>", styles["Heading2"]),
        Paragraph(
            f"Tokens: {resultado['resumen']['cantidad_tokens']} | "
            f"Instrucciones reconocidas: {resultado['resumen']['cantidad_sentencias']} | "
            f"Errores: {resultado['resumen']['cantidad_errores']}", styles["Normal"]
        ),
        Spacer(1, 10),
        Paragraph("Código de entrada", styles["Heading2"]),
        Preformatted(escape(resultado.get("codigo", "")), styles["SmallCode"]),
        Spacer(1, 10),
        Paragraph("Tokens y lexemas", styles["Heading2"]),
    ]

    token_data = [["Token", "Lexema", "Línea", "Columna"]]
    token_data.extend([
        [t["tipo"], escape(t["lexema"]), str(t["linea"]), str(t["columna"])]
        for t in resultado["tokens"]
    ])
    if len(token_data) == 1:
        token_data.append(["—", "No se reconocieron tokens", "—", "—"])
    token_table = Table(token_data, repeatRows=1, colWidths=[4.0*cm, 6.0*cm, 2.0*cm, 2.0*cm])
    token_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12304A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D2DCE5")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
    ]))
    story += [token_table, Spacer(1, 10)]

    sections = [
        ("Errores léxicos", resultado["errores_lexicos"]),
        ("Errores sintácticos", resultado["errores_sintacticos"]),
        ("Errores semánticos", resultado["errores_semanticos"]),
    ]
    for title, errors in sections:
        story.append(Paragraph(title, styles["Heading2"]))
        if errors:
            for item in errors:
                msg = escape(item.get("mensaje", str(item)))
                line = item.get("linea", "?")
                column = item.get("columna", "?")
                story.append(Paragraph(f"Línea {line}, columna {column}: {msg}", styles["BodyText"]))
        else:
            story.append(Paragraph("Sin errores registrados.", styles["BodyText"]))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Instrucciones reconocidas", styles["Heading2"]))
    if resultado["sentencias"]:
        statements = [["Comando", "Valor", "Línea"]]
        statements.extend([[s["comando"], escape(s["valor"]), str(s["linea"])] for s in resultado["sentencias"]])
        table = Table(statements, repeatRows=1, colWidths=[5*cm, 6*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#087E8B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D2DCE5")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No se reconocieron instrucciones completas.", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
