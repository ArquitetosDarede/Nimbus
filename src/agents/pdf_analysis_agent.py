"""
PDF Analysis Agent - Specialized agent for PDF file analysis
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Optional imports
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class PDFAnalysisAgent:
    """Specialized agent for PDF file analysis."""

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Extract text and tables from PDF files."""
        if not HAS_PYPDF2:
            raise ImportError("PyPDF2 not available for PDF extraction")

        text_content = []
        tables = []

        # Try pdfplumber first (better for tables)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        # Extract text
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)

                        # Extract tables
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table in page_tables:
                                if table and len(table) > 1:  # Skip empty tables
                                    tables.append({
                                        "page": page.page_number,
                                        "data": table,
                                        "headers": table[0] if table else []
                                    })
            except Exception as e:
                logger.warning(f"pdfplumber failed, falling back to PyPDF2: {e}")

        # Fallback to PyPDF2
        if not text_content:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)

        return {
            "extracted_text": "\n\n".join(text_content),
            "extracted_data": {
                "tables": tables,
                "metadata": {
                    "pages": len(text_content),
                    "has_tables": len(tables) > 0
                }
            }
        }