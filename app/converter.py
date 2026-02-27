import asyncio
import os
from pathlib import Path

async def convert_pdf_to_docx_libreoffice(input_pdf: Path, output_dir: Path) -> Path:
    """
    Converts a text-based PDF to DOCX using LibreOffice in headless mode.
    """
    try:
        # Avoid creating zombie processes
        process = await asyncio.create_subprocess_exec(
            "soffice",
            "--headless",
            "--invisible",
            "--nologo",
            "--nodefault",
            "--convert-to", "docx",
            "--outdir", str(output_dir),
            str(input_pdf),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"LibreOffice conversion failed: {error_msg}")
            
        # Determine the expected output path
        expected_output = output_dir / f"{input_pdf.stem}.docx"
        if not expected_output.exists():
            raise FileNotFoundError(f"DOCX not generated at {expected_output}")
            
        return expected_output
    except Exception as e:
        raise RuntimeError(f"LibreOffice conversion error: {e}")
