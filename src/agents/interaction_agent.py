"""
Interaction Agent - Extracts structured questionnaire answers from natural language.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

INTERACTION_AGENT_PROMPT = """
You are a specialized Interaction Agent for proposal workflows.

Your role is to:
1. Read the user's natural-language response.
2. Extract structured values for required fields.
3. Keep only factual values from the user message.
4. Avoid inventing missing data.

Rules:
- Output must be valid JSON.
- Keep field paths exactly as requested (example: clientInfo.contactPhone).
- If a field is not present, do not fill it.
- Portuguese (Brazil) understanding is required.
"""

logger = logging.getLogger(__name__)


class InteractionAgent:
    """Parses natural language answers into structured required fields."""

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
                    "temperature": 0.0,
                    "max_tokens": 900,
                },
            ),
            system_prompt=INTERACTION_AGENT_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def extract_answers(
        self,
        answer_text: str,
        missing_fields: List[str] | None = None,
        questionnaire: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Extract a dictionary of field-path -> value from natural-language response."""
        if not isinstance(answer_text, str) or not answer_text.strip():
            return {
                "answers": {},
                "unresolved_fields": missing_fields or [],
                "status": "empty_answer",
            }

        missing_fields = [f for f in (missing_fields or []) if isinstance(f, str) and f.strip()]
        questionnaire = questionnaire if isinstance(questionnaire, dict) else {}

        prompt = f"""
Extract structured answers from user natural-language text.

MISSING_FIELDS:
{json.dumps(missing_fields, ensure_ascii=False, indent=2)}

QUESTIONNAIRE:
{json.dumps(questionnaire, ensure_ascii=False, indent=2)}

USER_ANSWER_TEXT:
{answer_text}

Return STRICT JSON format:
{{
  "answers": {{
    "field.path": "value"
  }},
  "unresolved_fields": ["field.path"],
  "confidence": 0.0,
  "notes": ["short note"]
}}

Only include fields from MISSING_FIELDS in "answers".
"""

        try:
            result = self.agent(prompt)
            parsed = self._extract_json_object(str(result))
            if isinstance(parsed, dict):
                answers = parsed.get("answers", {})
                if not isinstance(answers, dict):
                    answers = {}
                filtered = {
                    k: v
                    for k, v in answers.items()
                    if isinstance(k, str)
                    and k in missing_fields
                    and v not in (None, "")
                }
                unresolved = [f for f in missing_fields if f not in filtered]
                return {
                    "answers": filtered,
                    "unresolved_fields": unresolved,
                    "confidence": parsed.get("confidence", 0.0),
                    "notes": parsed.get("notes", []),
                    "status": "ok",
                }
        except Exception:
            logger.exception("[InteractionAgent] Failed to parse with model, applying heuristic fallback")

        fallback = self._heuristic_extract(answer_text, missing_fields)
        return {
            "answers": fallback,
            "unresolved_fields": [f for f in missing_fields if f not in fallback],
            "confidence": 0.3,
            "notes": ["fallback_heuristic_used"],
            "status": "fallback",
        }

    def _heuristic_extract(self, answer_text: str, missing_fields: List[str]) -> Dict[str, Any]:
        """Basic regex fallback for common contact fields."""
        text = answer_text.strip()
        out: Dict[str, Any] = {}

        if "clientInfo.contactEmail" in missing_fields:
            email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if email_match:
                out["clientInfo.contactEmail"] = email_match.group(0)

        if "clientInfo.contactPhone" in missing_fields:
            phone_match = re.search(r"\+?\d[\d\s()\-]{7,}\d", text)
            if phone_match:
                out["clientInfo.contactPhone"] = phone_match.group(0).strip()

        if "timeline" in missing_fields:
            timeline_match = re.search(r"\b(\d+\s*(dias|semanas|meses|months|weeks|days))\b", text, re.IGNORECASE)
            if timeline_match:
                out["timeline"] = timeline_match.group(1)

        if "budget" in missing_fields:
            budget_match = re.search(r"(R\$\s?[\d\.,]+|\$\s?[\d\.,]+|\d+[\d\.,]*\s?(mil|mi|milhoes|milhão|k))", text, re.IGNORECASE)
            if budget_match:
                out["budget"] = budget_match.group(1)

        if "clientInfo.contactPerson" in missing_fields and "clientInfo.contactPerson" not in out:
            person_match = re.search(r"(?:contato|responsavel|responsável|pessoa)\s*[:\-]\s*([^,;\n]+)", text, re.IGNORECASE)
            if person_match:
                out["clientInfo.contactPerson"] = person_match.group(1).strip()

        # If user answered just one missing field in free text, map directly.
        if len(missing_fields) == 1 and not out:
            only_field = missing_fields[0]
            if text:
                out[only_field] = text

        return out

    def _extract_json_object(self, text: str) -> Dict[str, Any] | None:
        """Best-effort JSON extraction from model output."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            return json.loads(match.group())
        except Exception:
            return None
