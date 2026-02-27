import fitz
from pathlib import Path

def is_text_based_pdf(pdf_path: Path) -> bool:
    """
    Analyzes a PDF to determine if it is text-based (digital) or scanned/image-based.
    Checks for extractable text over the first few pages.
    """
    try:
        doc = fitz.open(str(pdf_path))
        if not doc.is_pdf:
            return False
            
        total_pages = len(doc)
        if total_pages == 0:
            return False

        # Check up to first 5 pages for substantial text
        pages_to_check = min(5, total_pages)
        text_found = False
        
        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text()
            # If we find more than 50 characters on a page, we consider it text-based
            if len(text.strip()) > 50:
                text_found = True
                break
                
        doc.close()
        return text_found
    except Exception as e:
        print(f"Error analyzing PDF {pdf_path}: {e}")
        # Default to scanned if there's an error parsing text softly
        return False
