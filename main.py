from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
import os
import re
from pathlib import Path

from router import route_conversion

app = FastAPI()

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _safe_stem(filename: str) -> str:
    # Keep user-visible names readable while preventing invalid path characters.
    original_name = Path(filename).name
    stem = Path(original_name).stem
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", stem).strip(" .")
    return cleaned or "converted_file"


def _next_available_pdf_name(base_stem: str) -> str:
    candidate = f"{base_stem}.pdf"
    counter = 1

    while os.path.exists(os.path.join(OUTPUT_DIR, candidate)):
        candidate = f"{base_stem}_{counter}.pdf"
        counter += 1

    return candidate


@app.post("/convert")
async def convert_file(request: Request, file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    original_filename = Path(file.filename or "uploaded_file").name
    safe_input_name = re.sub(r"[^A-Za-z0-9._ -]", "_", original_filename)
    pdf_filename = _next_available_pdf_name(_safe_stem(original_filename))

    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{safe_input_name}")
    output_path = os.path.join(OUTPUT_DIR, pdf_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        route_conversion(input_path, output_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    download_url = request.url_for("download_file", filename=pdf_filename)

    return {
        "pdf_url": str(download_url)
    }


@app.get("/download/{filename}")
def download_file(filename: str):

    path = f"{OUTPUT_DIR}/{filename}"

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename
    )