import os
import shutil
import subprocess
from pathlib import Path


def _find_libreoffice_binary() -> str | None:
    # Prefer PATH lookup, then common Windows install locations.
    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None

def convert_docx(input_path, output_path):
    libreoffice_bin = _find_libreoffice_binary()
    if not libreoffice_bin:
        raise RuntimeError(
            "LibreOffice is required for DOCX/PPTX/XLSX conversion but was not found. "
            "Install LibreOffice and ensure soffice is on PATH."
        )

    out_dir = os.path.dirname(output_path) or "."
    input_stem = Path(input_path).stem
    expected_pdf = os.path.join(out_dir, f"{input_stem}.pdf")

    result = subprocess.run(
        [
            libreoffice_bin,
            "--headless",
            "--convert-to",
            "pdf",
            input_path,
            "--outdir",
            out_dir,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "Unknown LibreOffice error").strip()
        raise RuntimeError(f"Office conversion failed: {error_text}")

    if not os.path.exists(expected_pdf):
        raise RuntimeError("Office conversion did not produce a PDF output file")

    # Normalize final filename to the API-selected output path.
    if expected_pdf != output_path:
        shutil.move(expected_pdf, output_path)