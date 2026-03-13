"""
Conversion Agent - Specialized in format conversion (Markdown to Word/PDF)
"""

import json
import os
import re
import logging
from datetime import datetime
from typing import Any, Dict

from strands import Agent
from strands.models import OpenAIModel

CONVERSION_AGENT_PROMPT = """
You are a specialized Format Conversion Agent.

Your role is to:
1. Convert proposals from Markdown to Word format
2. Convert proposals from Markdown to PDF format
3. Preserve formatting, tables, and diagrams
4. Generate table of contents
5. Apply corporate styling and branding

Ensure high-quality output with proper formatting.
"""

logger = logging.getLogger(__name__)


class ConversionAgent:
    """Prepares proposal metadata and structure for format conversion."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 0,
                    "timeout": 90,
                },
                model_id="gpt-4o",
                params={
                    "temperature": 0.1,
                    "max_tokens": 1200,
                },
            ),
            system_prompt=CONVERSION_AGENT_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def prepare_for_conversion(self, proposal: Dict[str, Any], target_format: str) -> Dict[str, Any]:
        """Generate conversion instructions and metadata for the target format."""
        logger.info("[ConversionAgent] Starting conversion preparation...")

        if not isinstance(proposal, dict) or not proposal:
            return self._fallback_result("Proposta Tecnica", "Invalid proposal input.")

        if not isinstance(target_format, str) or target_format.lower() not in {"word", "pdf"}:
            return self._fallback_result(
                proposal.get("title", "Proposta Tecnica"),
                "Invalid target_format. Expected 'word' or 'pdf'.",
            )

        try:
            proposal_text = json.dumps(proposal, indent=2, ensure_ascii=False)
            proposal_text = proposal_text.encode("utf-8", errors="replace").decode("utf-8")

            prompt = f"""
Prepare this proposal for conversion to {target_format.upper()} format.

PROPOSAL:
{proposal_text}

INSTRUCTIONS:
1. Generate table of contents with page numbers
2. Apply corporate styling guidelines
3. Format tables and lists properly
4. Handle diagrams and images
5. Add headers and footers
6. Include metadata (author, date, version)

Return JSON format:
{{
  "tableOfContents": [
    {{
      "title": "Section title",
      "page": 1,
      "level": 1
    }}
  ],
  "metadata": {{
    "title": "Proposal title",
    "author": "Author name",
    "date": "YYYY-MM-DD",
    "version": "1.0"
  }},
  "styling": {{
    "font": "Arial",
    "fontSize": 11,
    "lineSpacing": 1.5,
    "margins": "2.5cm"
  }}
}}
"""

            result = self.agent(prompt)
            result_text = str(result).encode("utf-8", errors="replace").decode("utf-8")

            conversion_data = self._extract_json_object(result_text)
            if isinstance(conversion_data, dict):
                return conversion_data

            return self._fallback_result(proposal.get("title", "Proposta Tecnica"), result_text[:500])
        except Exception as e:
            logger.exception("[ConversionAgent] Exception during conversion preparation")
            return self._fallback_result(proposal.get("title", "Proposta Tecnica"), f"Exception: {e}")

    def _extract_json_object(self, text: str) -> Dict[str, Any] | None:
        """Best-effort JSON extraction from model output."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            return json.loads(match.group())
        except Exception:
            return None

    def _fallback_result(self, title: str, result_text: str) -> Dict[str, Any]:
        """Default serializable conversion payload."""
        return {
            "tableOfContents": [],
            "metadata": {
                "title": title,
                "author": "Sistema de Propostas",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0",
            },
            "result_text": result_text,
        }
