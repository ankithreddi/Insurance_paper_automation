import pdfplumber
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    return text
