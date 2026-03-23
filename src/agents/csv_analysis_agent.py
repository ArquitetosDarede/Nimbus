"""
CSV Analysis Agent - Specialized agent for CSV file analysis
"""

import logging
import csv
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CsvAnalysisAgent:
    """Specialized agent for CSV file analysis."""

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Extract data from CSV files."""
        data = []
        headers = []

        try:
            # Try to detect encoding and delimiter
            with open(file_path, 'r', encoding='utf-8') as file:
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                has_header = sniffer.has_header(sample)

                reader = csv.reader(file, delimiter=delimiter)

                for row_idx, row in enumerate(reader):
                    if row_idx == 0 and has_header:
                        headers = row
                    else:
                        data.append(row)

        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                reader = csv.reader(file)
                for row_idx, row in enumerate(reader):
                    if row_idx == 0 and not headers:
                        headers = row
                    else:
                        data.append(row)

        # Convert to text format for analysis
        text_content = []
        if headers:
            text_content.append("Headers: " + ", ".join(headers))

        text_content.append("Data:")
        for row in data[:10]:  # Limit to first 10 rows for text
            text_content.append(", ".join(row))

        if len(data) > 10:
            text_content.append(f"... and {len(data) - 10} more rows")

        return {
            "extracted_text": "\n\n".join(text_content),
            "extracted_data": {
                "data": data,
                "headers": headers,
                "metadata": {
                    "row_count": len(data),
                    "column_count": len(headers) if headers else (len(data[0]) if data else 0),
                    "has_headers": bool(headers)
                }
            }
        }