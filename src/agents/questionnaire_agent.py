"""
Questionnaire Agent - Specialized in dynamic questionnaire generation
"""

import json
import os
import re
import logging
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

QUESTIONNAIRE_AGENT_PROMPT = """
You are a specialized Questionnaire Generation Agent.

Your role is to:
1. Analyze data gaps identified by the Analysis Agent
2. Generate clear, specific questions to collect missing information
3. Prioritize questions by importance (critical, important, optional)
4. Provide helpful context and examples for each question
5. Validate user answers for completeness and consistency

Generate questions in Portuguese (Brazil).
Be concise and professional.
Always provide validation rules for answers.
"""

logger = logging.getLogger(__name__)


class QuestionnaireAgent:
    """Creates and validates questionnaires for missing requirement fields."""

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
                    "temperature": 0.2,
                    "max_tokens": 1200,
                },
            ),
            system_prompt=QUESTIONNAIRE_AGENT_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def generate_questionnaire(self, data_gaps: List[Dict[str, Any]], notion_cache: str = "") -> Dict[str, Any]:
        """Generate questionnaire from identified data gaps."""
        logger.info("[QuestionnaireAgent] Gerando questionario...")

        if not isinstance(data_gaps, list):
            return {"error": "data_gaps must be a list", "status": "questionnaire_failed"}

        normalized_gaps = []
        for gap in data_gaps:
            if isinstance(gap, dict):
                clean_gap = dict(gap)
                if "description" in clean_gap and isinstance(clean_gap["description"], str):
                    clean_gap["description"] = clean_gap["description"].encode("utf-8", errors="replace").decode("utf-8")
                normalized_gaps.append(clean_gap)

        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        prompt = f"""
{cache_section}
Generate a questionnaire to collect the following missing information.

DATA GAPS:
{json.dumps(normalized_gaps, indent=2, ensure_ascii=False)}

INSTRUCTIONS:
1. Use cached Notion content to guide wording and scope.
2. Create clear and specific questions in Portuguese (Brazil).
3. Prioritize questions by importance (critical, important, optional).
4. Include help text and validation rules.
5. Keep response objective and practical.

Return JSON format:
{{
  "id": "questionnaire_id",
  "questions": [
    {{
      "id": "q1",
      "text": "Question text",
      "type": "text|number|date|choice|multiple-choice",
      "required": true,
      "priority": "critical|important|optional",
      "helpText": "Helpful context",
      "options": ["option1", "option2"],
      "validation": {{
        "minLength": 0,
        "maxLength": 0,
        "pattern": "regex"
      }}
    }}
  ],
  "estimatedTime": 10
}}
"""

        try:
            result = self.agent(prompt)
            result_text = str(result)
            parsed = self._extract_json_object(result_text)
            if isinstance(parsed, dict):
                return parsed

            return {
                "id": "questionnaire_fallback",
                "questions": [],
                "estimatedTime": 5,
                "result_text": result_text[:500],
            }
        except Exception as e:
            logger.exception("[QuestionnaireAgent] ERROR")
            return {"error": str(e), "status": "questionnaire_failed"}

    def validate_answers(self, questionnaire: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate user answers against the questionnaire."""
        if not isinstance(questionnaire, dict) or not isinstance(answers, list):
            return {
                "valid": False,
                "completeness": 0.0,
                "errors": [{"message": "Invalid questionnaire or answers payload"}],
                "remainingGaps": [],
            }

        prompt = f"""
Validate the user answers against this questionnaire.

QUESTIONNAIRE:
{json.dumps(questionnaire, indent=2, ensure_ascii=False)}

ANSWERS:
{json.dumps(answers, indent=2, ensure_ascii=False)}

Return JSON format:
{{
  "valid": true,
  "completeness": 1.0,
  "errors": [
    {{
      "questionId": "q1",
      "message": "Error description"
    }}
  ],
  "remainingGaps": [
    {{
      "field": "field_name",
      "description": "why this is needed"
    }}
  ]
}}
"""

        try:
            result = self.agent(prompt)
            result_text = str(result)
            parsed = self._extract_json_object(result_text)
            if isinstance(parsed, dict):
                return parsed

            return {
                "valid": False,
                "completeness": 0.0,
                "errors": [],
                "remainingGaps": [],
                "result_text": result_text[:500],
            }
        except Exception as e:
            logger.exception("[QuestionnaireAgent] ERROR")
            return {
                "valid": False,
                "completeness": 0.0,
                "errors": [{"message": str(e)}],
                "remainingGaps": [],
            }

    def _extract_json_object(self, text: str) -> Dict[str, Any] | None:
        """Best-effort JSON extraction from model output."""
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            return json.loads(match.group())
        except Exception:
            return None
