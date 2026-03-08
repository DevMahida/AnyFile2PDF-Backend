from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
import shutil
import uuid
import os
import re
import tempfile
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

def _safe_stem(filename: str) -> str:
    # Keep user-visible names readable while preventing invalid path characters.
    original_name = Path(filename).name
    stem = Path(original_name).stem
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", stem).strip(" .")
    return cleaned or "converted_file"


def _cleanup_temp_dir(temp_dir: str) -> None:
    # Delete request-scoped conversion artifacts after the response is sent.
    shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):

    file_id = str(uuid.uuid4())
    original_filename = Path(file.filename or "uploaded_file").name
    safe_input_name = re.sub(r"[^A-Za-z0-9._ -]", "_", original_filename)
    pdf_filename = f"{_safe_stem(original_filename)}.pdf"

    temp_dir = tempfile.mkdtemp(prefix="convert_")
    input_path = os.path.join(temp_dir, f"{file_id}_{safe_input_name}")
    output_path = os.path.join(temp_dir, pdf_filename)

    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        route_conversion(input_path, output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=pdf_filename,
            background=BackgroundTask(_cleanup_temp_dir, temp_dir),
        )
    except Exception as exc:
        _cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()