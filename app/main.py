from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import tempfile
import os
import traceback

from app.utils import save_upload_file_tmp, cleanup_files
from app.analyzer import is_text_based_pdf
from app.converter import convert_pdf_to_docx_libreoffice
from app.ocr import convert_scanned_pdf_to_docx_ocr


# --------------------------------------------------
# FastAPI App Init
# --------------------------------------------------

app = FastAPI(
    title="Hybrid PDF to DOCX Converter",
    description="Convert Text & Scanned PDFs into editable DOCX",
    version="1.0.0"
)


# --------------------------------------------------
# Health Check Route (Render uses this)
# --------------------------------------------------

@app.get("/")
async def root():
    return {"status": "running", "service": "PDF → DOCX Converter"}


# --------------------------------------------------
# MAIN CONVERSION ROUTE
# --------------------------------------------------

@app.post("/convert")
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    # ---------------------------
    # Validate File
    # ---------------------------
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    saved_pdf_path = None
    output_dir = None
    docx_path = None

    try:
        print(f"\n📄 Received File: {file.filename}")

        # ---------------------------
        # Save Upload
        # ---------------------------
        saved_pdf_path = await save_upload_file_tmp(file)

        # ---------------------------
        # Create temp output dir
        # Render-safe (/tmp storage)
        # ---------------------------
        output_dir = Path(tempfile.mkdtemp(dir="/tmp"))

        # ---------------------------
        # Detect PDF Type
        # ---------------------------
        is_text_pdf = is_text_based_pdf(saved_pdf_path)

        # ---------------------------
        # TEXT PDF → LibreOffice
        # ---------------------------
        if is_text_pdf:
            print("✅ TEXT PDF detected → LibreOffice pipeline")

            docx_path = await convert_pdf_to_docx_libreoffice(
                saved_pdf_path,
                output_dir
            )

        # ---------------------------
        # SCANNED PDF → OCR
        # ---------------------------
        else:
            print("🧠 SCANNED PDF detected → HuggingFace OCR")

            docx_path = await convert_scanned_pdf_to_docx_ocr(
                saved_pdf_path,
                output_dir
            )

        # ---------------------------
        # Validate Output
        # ---------------------------
        if not docx_path or not Path(docx_path).exists():
            raise Exception("DOCX generation failed")

        # ---------------------------
        # Background Cleanup
        # ---------------------------
        background_tasks.add_task(
            cleanup_files,
            saved_pdf_path,
            output_dir
        )

        print("✅ Conversion Successful")

        # ---------------------------
        # Return File
        # ---------------------------
        return FileResponse(
            path=docx_path,
            filename=f"{Path(file.filename).stem}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print("❌ Conversion Error")
        traceback.print_exc()

        if saved_pdf_path or output_dir:
            cleanup_files(saved_pdf_path, output_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )