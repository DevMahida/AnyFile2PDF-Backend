import pandas as pd
from fpdf import FPDF


def _to_latin1_safe(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _truncate_cell(value: str, max_len: int = 24) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 1] + "..."

def convert_csv(input_path, output_path):

    df = pd.read_csv(input_path)
    safe_df = df.fillna("").astype(str)
    columns = [str(col) for col in safe_df.columns]

    if not columns:
        raise ValueError("CSV file has no columns to convert")

    # Switch to landscape automatically for wider CSV files.
    orientation = "L" if len(columns) > 6 else "P"
    pdf = FPDF(orientation=orientation)
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, _to_latin1_safe("CSV to PDF"), ln=1)
    pdf.ln(2)

    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_width = usable_width / len(columns)
    line_height = 8

    # Header row
    pdf.set_fill_color(229, 231, 235)
    pdf.set_font("Helvetica", style="B", size=9)
    for col in columns:
        header_text = _to_latin1_safe(_truncate_cell(col))
        pdf.cell(col_width, line_height, header_text, border=1, align="L", fill=True)
    pdf.ln(line_height)

    # Data rows
    pdf.set_font("Helvetica", size=9)
    for _, row in safe_df.iterrows():
        for col in columns:
            cell_text = _to_latin1_safe(_truncate_cell(str(row[col])))
            pdf.cell(col_width, line_height, cell_text, border=1, align="L")
        pdf.ln(line_height)

    if safe_df.empty:
        pdf.cell(0, 8, _to_latin1_safe("(CSV has headers but no data rows)"), ln=1)

    pdf.output(output_path)