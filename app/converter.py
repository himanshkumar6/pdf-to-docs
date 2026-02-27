from pdf2docx import Converter
from pathlib import Path
import asyncio


async def convert_pdf_to_docx_libreoffice(pdf_path, output_dir):

    output_file = Path(output_dir) / "output.docx"

    def run_conversion():
        cv = Converter(str(pdf_path))
        cv.convert(str(output_file))
        cv.close()

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_conversion)

    return output_file