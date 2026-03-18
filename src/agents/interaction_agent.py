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
- Keep field paths exactly as requested (example: project.deadline).
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
        pending_fields: List[str] | None = None,
        questionnaire: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Extract a dictionary of field-path -> value from natural-language response."""
        if not isinstance(answer_text, str) or not answer_text.strip():
            return {
                "answers": {},
                "unresolved_fields": pending_fields or [],
                "status": "empty_answer",
            }

        pending_fields = [f for f in (pending_fields or []) if isinstance(f, str) and f.strip()]
        questionnaire = questionnaire if isinstance(questionnaire, dict) else {}

        prompt = f"""
Extract structured answers from user natural-language text.

PENDING_FIELDS:
{json.dumps(pending_fields, ensure_ascii=False, indent=2)}

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

Only include fields from PENDING_FIELDS in "answers".
"""

        try:
            result = self.agent(prompt)
            parsed = self._extract_json_object(str(result))
            if isinstance(parsed, dict):
                answers = parsed.get("answers", {})
                if not isinstance(answers, dict):
                    answers = {}

                normalized_pending = {
                    self._normalize_field_token(field): field for field in pending_fields
                }
                filtered: Dict[str, Any] = {}
                for key, value in answers.items():
                    if not isinstance(key, str) or value in (None, ""):
                        continue
                    canonical_key = normalized_pending.get(self._normalize_field_token(key))
                    if canonical_key:
                        filtered[canonical_key] = value

                if len(pending_fields) == 1 and not filtered and answer_text.strip():
                    filtered[pending_fields[0]] = answer_text.strip()

                unresolved = [f for f in pending_fields if f not in filtered]
                return {
                    "answers": filtered,
                    "unresolved_fields": unresolved,
                    "confidence": parsed.get("confidence", 0.0),
                    "notes": parsed.get("notes", []),
                    "status": "ok",
                }
        except Exception:
            logger.exception("[InteractionAgent] Failed to parse with model, applying heuristic fallback")

        fallback = self._heuristic_extract(answer_text, pending_fields)
        return {
            "answers": fallback,
            "unresolved_fields": [f for f in pending_fields if f not in fallback],
            "confidence": 0.3,
            "notes": ["fallback_heuristic_used"],
            "status": "fallback",
        }

    def _normalize_field_token(self, value: str) -> str:
        """Normalize a pending field label for stable comparison without hardcoded mappings."""
        if not isinstance(value, str):
            return ""
        return re.sub(r"\s+", " ", value.strip().lower())

    def _heuristic_extract(self, answer_text: str, pending_fields: List[str]) -> Dict[str, Any]:
        """Generic fallback that does not depend on hardcoded domain fields."""
        text = answer_text.strip()
        out: Dict[str, Any] = {}

        # Try to parse explicit "field: value" pairs and map only to missing fields.
        for line in re.split(r"[\n;]+", text):
            pair = re.match(r"^\s*([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)\s*[:=\-]\s*(.+?)\s*$", line)
            if not pair:
                continue
            key = pair.group(1).strip()
            value = pair.group(2).strip()
            if key in pending_fields and value:
                out[key] = value

        # If user answered just one missing field in free text, map directly.
        if len(pending_fields) == 1 and not out:
            only_field = pending_fields[0]
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
