from PyPDF2 import PdfReader
from typing import Union
from io import BytesIO

def extract_text_from_pdf(pdf_file: Union[str, BytesIO]) -> str:
    """
    Extracts and returns text from all pages of a PDF using PyPDF2.

    Args:
        pdf_file (str or BytesIO): File path or file-like object (e.g. UploadFile.file)

    Returns:
        str: Combined text from all pages
    """
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""
    
    return text.strip()
