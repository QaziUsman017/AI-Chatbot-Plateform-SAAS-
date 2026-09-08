"""Utilities for extracting text from TXT, PDF, and DOCX documents."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text(file_path: str | Path) -> str:
    """Extract and return text from TXT, PDF, or DOCX files."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    extension = path.suffix.lower()

    # ==========================================
    # TXT
    # ==========================================

    if extension == ".txt":
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return text.strip()

    # ==========================================
    # PDF
    # ==========================================

    if extension == ".pdf":
        reader = PdfReader(str(path))

        pages: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        return "\n\n".join(pages).strip()

    # ==========================================
    # DOCX
    # ==========================================

    if extension == ".docx":
        document = Document(str(path))

        paragraphs: list[str] = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs).strip()

    # ==========================================
    # Unsupported
    # ==========================================

    raise ValueError(
        f"Unsupported file type: {extension}"
    )