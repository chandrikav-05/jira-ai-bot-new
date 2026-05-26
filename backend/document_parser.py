import fitz                          # PyMuPDF — for PDF
from docx import Document as DocxDoc  # python-docx — for Word
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    text = ""
    try:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        for page in pdf:
            text += page.get_text()
        pdf.close()
    except Exception as e:
        raise ValueError(f"Could not read PDF file: {e}")
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract all text from a Word (.docx) file."""
    text = ""
    try:
        doc = DocxDoc(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Could not read Word file: {e}")
    return text.strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from a plain text file."""
    try:
        return file_bytes.decode("utf-8").strip()
    except Exception:
        try:
            return file_bytes.decode("latin-1").strip()
        except Exception as e:
            raise ValueError(f"Could not read text file: {e}")


def parse_document(filename: str, file_bytes: bytes) -> str:
    """
    Route to the correct parser based on file extension.
    Returns the full extracted text.
    """
    name = filename.lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT.")