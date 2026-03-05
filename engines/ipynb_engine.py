import os
import subprocess
import sys
import textwrap
from pathlib import Path

import nbformat
from fpdf import FPDF


def _to_latin1_safe(text: str) -> str:
    # Keep PDF writing resilient even when notebook contains unsupported glyphs.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _prepare_text_for_pdf(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    cleaned = "".join(ch if ch == "\n" or ord(ch) >= 32 else " " for ch in normalized)
    safe = _to_latin1_safe(cleaned)

    wrapped_lines = []
    for line in safe.split("\n"):
        if not line:
            wrapped_lines.append("")
            continue

        wrapped_lines.extend(
            textwrap.wrap(
                line,
                width=110,
                break_long_words=True,
                break_on_hyphens=False,
            )
        )

    return "\n".join(wrapped_lines)


def _write_block(
    pdf: FPDF,
    text: str,
    *,
    style: str = "",
    size: int = 10,
    line_height: int = 5,
    fill: bool = False,
    fill_color: tuple[int, int, int] = (255, 255, 255),
    text_color: tuple[int, int, int] = (31, 41, 55),
    border: int = 0,
) -> None:
    prepared = _prepare_text_for_pdf(text)
    if not prepared:
        return

    pdf.set_font("Helvetica", style=style, size=size)
    pdf.set_fill_color(*fill_color)
    pdf.set_text_color(*text_color)
    pdf.multi_cell(
        0,
        line_height,
        prepared,
        border=border,
        new_x="LMARGIN",
        new_y="NEXT",
        fill=fill,
    )
    pdf.set_text_color(0, 0, 0)


def _render_markdown_cell(pdf: FPDF, source: str) -> None:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(1)
            continue

        if stripped.startswith("# "):
            _write_block(pdf, stripped[2:], style="B", size=15, line_height=7)
        elif stripped.startswith("## "):
            _write_block(pdf, stripped[3:], style="B", size=13, line_height=6)
        elif stripped.startswith("### "):
            _write_block(pdf, stripped[4:], style="B", size=11, line_height=6)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            _write_block(pdf, f"- {stripped[2:]}", size=10, line_height=5)
        else:
            _write_block(pdf, stripped, size=10, line_height=5)


def _collect_output_text(cell: dict) -> str:
    chunks = []

    for output in cell.get("outputs", []):
        output_type = output.get("output_type")

        if output_type == "stream":
            chunks.append(str(output.get("text", "")))
            continue

        if output_type in {"execute_result", "display_data"}:
            data = output.get("data", {})

            if "text/plain" in data:
                chunks.append(str(data.get("text/plain", "")))
            elif "image/png" in data:
                chunks.append("[Image output omitted in text-mode PDF]")

            continue

        if output_type == "error":
            traceback = output.get("traceback", [])
            chunks.append("\n".join(traceback))

    return "\n".join(chunk for chunk in chunks if str(chunk).strip())


def _write_notebook_structured_pdf(input_path: str, output_path: str) -> None:
    notebook = nbformat.read(input_path, as_version=4)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    for cell in notebook.cells:
        cell_type = (cell.get("cell_type") or "unknown").lower()
        source = str(cell.get("source", ""))

        if cell_type == "markdown":
            _render_markdown_cell(pdf, source)
        else:
            _write_block(
                pdf,
                "Code",
                style="B",
                size=9,
                line_height=5,
                fill=True,
                fill_color=(229, 231, 235),
                text_color=(31, 41, 55),
            )
            _write_block(
                pdf,
                source,
                size=9,
                line_height=5,
                fill=True,
                fill_color=(245, 247, 250),
                border=1,
            )

        if cell_type == "code":
            output_text = _collect_output_text(cell)
            if output_text.strip():
                _write_block(
                    pdf,
                    "Output",
                    style="B",
                    size=9,
                    line_height=5,
                    fill=True,
                    fill_color=(255, 243, 205),
                    text_color=(102, 60, 0),
                )
                _write_block(
                    pdf,
                    output_text,
                    style="I",
                    size=9,
                    line_height=5,
                    fill=True,
                    fill_color=(255, 249, 232),
                    border=1,
                )

        pdf.ln(2)

    pdf.output(output_path)

def convert_ipynb(input_path, output_path):
    structured_error = ""
    try:
        _write_notebook_structured_pdf(input_path, output_path)
        if os.path.exists(output_path):
            return
    except Exception as exc:
        structured_error = str(exc)

    output_dir = os.path.dirname(output_path) or "."
    output_stem = Path(output_path).stem

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "webpdf",
            "--allow-chromium-download",
            "--output",
            output_stem,
            "--output-dir",
            output_dir,
            input_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and os.path.exists(output_path):
        return

    webpdf_error = (result.stderr or result.stdout or "Unknown notebook conversion error").strip()

    raise RuntimeError(
        "IPYNB to PDF conversion failed. WebPDF backend error: "
        f"{webpdf_error}. Structured fallback error: {structured_error}. "
        "Fallback PDF was not generated."
    )