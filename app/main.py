from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import tempfile
from pathlib import Path

from app.utils import save_upload_file_tmp, cleanup_files
from app.analyzer import is_text_based_pdf
from app.converter import convert_pdf_to_docx_libreoffice
from app.ocr import convert_scanned_pdf_to_docx_ocr

app = FastAPI(title="Hybrid PDF to DOCX Converter", description="Converts PDFs to DOCX natively or via OCR")

@app.get("/")
async def root():
    return {"message": "Hybrid PDF to DOCX Converter API is running"}

@app.post("/convert")
async def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    saved_pdf_path = None
    output_dir = None
    docx_path = None
    
    try:
        # Save uploaded file securely
        saved_pdf_path = await save_upload_file_tmp(file)
        
        # Create dedicated output directory
        output_dir = Path(tempfile.mkdtemp())
        
        # Analyze PDF type
        is_text = is_text_based_pdf(saved_pdf_path)
        
        # Convert based on analysis
        if is_text:
            print(f"[{file.filename}] Detected as TEXT-BASED. Using LibreOffice.")
            docx_path = await convert_pdf_to_docx_libreoffice(saved_pdf_path, output_dir)
        else:
            print(f"[{file.filename}] Detected as SCANNED. Using TrOCR.")
            docx_path = await convert_scanned_pdf_to_docx_ocr(saved_pdf_path, output_dir)
            
        # Schedule cleanup to run after the response is sent
        background_tasks.add_task(cleanup_files, saved_pdf_path, output_dir)
        
        return FileResponse(
            path=docx_path, 
            filename=f"{Path(file.filename).stem}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except Exception as e:
        # Ensure cleanup if an error occurs mid-process
        cleanup_files(saved_pdf_path, output_dir)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
