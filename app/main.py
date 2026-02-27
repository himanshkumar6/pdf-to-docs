from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile
import traceback

from app.utils import save_upload_file_tmp, cleanup_files
from app.analyzer import is_text_based_pdf
from app.converter import convert_pdf_to_docx_libreoffice


# --------------------------------------------------
# FastAPI App Init
# --------------------------------------------------

app = FastAPI(
    title="PDF to DOCX Converter",
    description="Convert text-based PDFs into editable DOCX files",
    version="1.0.0"
)

# --------------------------------------------------
# ✅ CORS CONFIGURATION (VERY IMPORTANT)
# --------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://compresspdfto200kb.online",
    "https://www.compresspdfto200kb.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# --------------------------------------------------
# Health Check Route
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "PDF → DOCX Converter",
        "ocr": "disabled (Render Free Plan)"
    }


# --------------------------------------------------
# MAIN CONVERSION ROUTE
# --------------------------------------------------

@app.post("/convert")
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    saved_pdf_path = None
    output_dir = None
    docx_path = None

    try:
        print(f"\n📄 Received File: {file.filename}")

        # Save uploaded file
        saved_pdf_path = await save_upload_file_tmp(file)

        # Temp output directory
        output_dir = Path(tempfile.mkdtemp(dir="/tmp"))

        # Detect PDF type
        is_text_pdf = is_text_based_pdf(saved_pdf_path)

        if not is_text_pdf:
            print("⚠️ Scanned PDF detected — OCR disabled")
            raise HTTPException(
                status_code=400,
                detail="Scanned PDFs are currently not supported."
            )

        print("✅ TEXT PDF detected → Conversion started")

        # Convert
        docx_path = await convert_pdf_to_docx_libreoffice(
            saved_pdf_path,
            output_dir
        )

        if not docx_path or not Path(docx_path).exists():
            raise Exception("DOCX generation failed")

        # Cleanup after response
        background_tasks.add_task(
            cleanup_files,
            saved_pdf_path,
            output_dir
        )

        print("✅ Conversion Successful")

        # ✅ IMPORTANT: FileResponse with headers
        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{Path(file.filename).stem}.docx",
            headers={
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        print("❌ Conversion Error")
        traceback.print_exc()

        if saved_pdf_path or output_dir:
            cleanup_files(saved_pdf_path, output_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )