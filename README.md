# AnyFile2PDF Backend

FastAPI backend service that accepts uploaded files and returns generated PDF files.

## Features

- File upload API (`POST /convert`)
- PDF download API (`GET /download/{filename}`)
- Conversion routing by file type
- Supported conversions:
  - Images: PNG, JPG, JPEG
  - Data: CSV
  - Office files: DOCX, PPTX, XLSX
  - Notebooks: IPYNB
- CORS configuration via environment variable

## Tech Stack

- FastAPI
- Uvicorn
- Pandas
- Pillow
- fpdf2
- LibreOffice (for DOCX/PPTX/XLSX conversion)

## Project Structure

- `main.py`: FastAPI app and endpoints
- `router.py`: file extension to engine routing
- `engines/`: conversion implementations
- `Dockerfile`: production container build
- `requirements.txt`: Python dependencies

## Local Development

### Prerequisites

- Python 3.11+
- pip
- LibreOffice installed and available (`soffice`) for Office conversions

### Setup and Run

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000`

### API Docs

- Swagger UI: `http://localhost:8000/docs`

## Environment Variables

- `CORS_ALLOW_ORIGINS`
  - Comma-separated allowed origins
  - Example: `https://your-frontend.vercel.app`
  - For testing only: `*`

## API Endpoints

### POST `/convert`

Uploads a file and converts it to PDF.

- Request: `multipart/form-data` with `file`
- Response:

```json
{
  "pdf_url": "https://<host>/download/<filename>.pdf"
}
```

### GET `/download/{filename}`

Downloads generated PDF file.

## Docker Deployment

Build image:

```bash
docker build -t anyfile2pdf-backend .
```

Run container:

```bash
docker run -p 8000:8000 -e CORS_ALLOW_ORIGINS=* anyfile2pdf-backend
```

## Render Deployment

1. Create a new Render Web Service from this repo.
2. Runtime: Docker.
3. Set environment variable:
   - `CORS_ALLOW_ORIGINS=https://your-frontend-domain`
4. Deploy.

## Repository

- Backend repo: `https://github.com/DevMahida/AnyFile2PDF-Backend`
