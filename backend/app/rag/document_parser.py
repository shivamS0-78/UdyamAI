import logging
import os

import pypdf
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)


class PDFParserError(Exception):
    """Base class for PDF parser exceptions."""

    pass


class CorruptedPDFError(PDFParserError):
    """Raised when the PDF file is corrupted."""

    pass


class EncryptedPDFError(PDFParserError):
    """Raised when the PDF file is encrypted."""

    pass


class EmptyPDFError(PDFParserError):
    """Raised when the PDF file is empty or has no pages."""

    pass


class ScannedPDFError(PDFParserError):
    """Raised when the PDF file is scanned/image-only (no extracted text)."""

    pass


def parse_pdf(file_path: str) -> list[dict]:
    """
    Extracts text page-by-page from a PDF file.

    Returns a list of dicts:
        [{"page_number": 1, "text": "page content"}, ...]

    Raises:
        FileNotFoundError
        EncryptedPDFError
        CorruptedPDFError
        EmptyPDFError
        ScannedPDFError
    """
    logger.info(f"Starting PDF extraction for: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"PDF extraction failed. File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        logger.error(f"PDF extraction failed. File is empty (0 bytes): {file_path}")
        raise EmptyPDFError("The PDF file is empty (0 bytes).")

    try:
        reader = pypdf.PdfReader(file_path)
    except PdfReadError as e:
        logger.error(f"PDF extraction failed. Corrupted PDF: {file_path}. Error: {str(e)}")
        raise CorruptedPDFError(f"Failed to parse corrupted PDF: {str(e)}") from e

    if reader.is_encrypted:
        logger.error(f"PDF extraction failed. PDF is encrypted: {file_path}")
        raise EncryptedPDFError("The PDF file is encrypted and cannot be parsed.")

    num_pages = len(reader.pages)
    if num_pages == 0:
        logger.error(f"PDF extraction failed. PDF has 0 pages: {file_path}")
        raise EmptyPDFError("The PDF file has 0 pages.")

    logger.info(f"PDF loaded successfully. Extracting {num_pages} pages...")

    pages_data = []
    total_text_length = 0

    for i, page in enumerate(reader.pages):
        page_num = i + 1
        try:
            text = page.extract_text() or ""
        except Exception as e:
            logger.warning(f"Failed to extract text on page {page_num} of {file_path}: {str(e)}")
            text = ""

        cleaned_text = text.strip()
        total_text_length += len(cleaned_text)

        pages_data.append({"page_number": page_num, "text": cleaned_text})

    # If the total extracted text across the entire PDF is empty, it is scanned/image-only
    if total_text_length == 0:
        logger.error(
            f"PDF extraction failed. PDF appears scanned/image-only (no text extracted): {file_path}"
        )
        raise ScannedPDFError(
            "The PDF file appears to be scanned or image-only (no text extracted)."
        )

    logger.info(f"PDF extraction completed. Total text characters extracted: {total_text_length}")
    return pages_data
