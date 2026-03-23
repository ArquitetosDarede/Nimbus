"""
TXT Analysis Agent - Specialized agent for TXT file analysis
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TxtAnalysisAgent:
    """Specialized agent for TXT file analysis."""

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from TXT files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()

        # Basic text analysis
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "extracted_text": content,
            "extracted_data": {
                "metadata": {
                    "total_lines": len(lines),
                    "non_empty_lines": len(non_empty_lines),
                    "total_characters": len(content),
                    "encoding": "utf-8"
                }
            }
        }