import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def create_history_pdf(history, user_variables, filename=None):
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluate_expressions_history_{timestamp}.pdf"

    output_dir = os.path.join(os.getcwd(), "static", "exports")
    os.makedirs(output_dir, exist_ok=True)

    pdf_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    subtitle_style = styles["Heading2"]
    normal_style = styles["Normal"]

    history_style = ParagraphStyle(
        "HistoryStyle", parent=normal_style, fontSize=10, leading=14, spaceAfter=8
    )

    elements = []

    elements.append(Paragraph("ExprEval - Expression History", title_style))
    elements.append(Spacer(1, 12))

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated on: {date_str}", normal_style))
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("Variables", subtitle_style))
    elements.append(Spacer(1, 8))

    var_data = [["Variable", "Value"]]
    for name, value in user_variables.items():
        if name == name.upper() and name.startswith("NUM"):
            var_data.append([name, str(value)])

    if len(var_data) > 1:
        var_table = Table(var_data, colWidths=[100, 100])
        var_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lavender),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(var_table)
    else:
        elements.append(Paragraph("No variables defined.", normal_style))

    elements.append(Spacer(1, 24))

    elements.append(Paragraph("Expression History", subtitle_style))
    elements.append(Spacer(1, 8))

    if history:
        for idx, entry in enumerate(history):
            elements.append(Paragraph(f"{idx + 1}. {entry}", history_style))
    else:
        elements.append(Paragraph("No history entries.", normal_style))

    doc.build(elements)

    return pdf_path, f"/static/exports/{filename}"


def clean_old_pdfs(max_age_hours=24):
    export_dir = os.path.join(os.getcwd(), "static", "exports")
    if not os.path.exists(export_dir):
        return

    now = datetime.datetime.now()

    for filename in os.listdir(export_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(export_dir, filename)

            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

            age = now - file_time

            if age.total_seconds() > max_age_hours * 3600:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove old PDF {filename}: {e}")
