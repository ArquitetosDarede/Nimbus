"""
Chat Policy Agent

Builds user questions dynamically using evidence from Notion cache.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)

CHAT_POLICY_PROMPT = """
You are a Chat Policy Agent for technical proposal discovery.

Your job is to generate the NEXT BEST QUESTIONS to ask the user based on:
- Missing required fields and data gaps
- Evidence snippets retrieved from Notion template/content cache
- Matched pages and contextual examples from previous materials

Rules:
1. Questions must be in Brazilian Portuguese.
2. Do not ask generic hardcoded questions when a specific evidence-based one is possible.
3. Prioritize what most increases proposal quality based on Notion evidence.
4. Be concise, objective and professional.
5. Return valid JSON only.
"""


class ChatPolicyAgent:
    """Creates dynamic questionnaire prompts from context and evidence."""

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
                    "max_tokens": 1400,
                },
            ),
            system_prompt=CHAT_POLICY_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def build_questionnaire(
        self,
        user_input: str,
        data_gaps: List[Dict[str, Any]],
        notion_guidance: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate questionnaire from gaps plus Notion evidence."""
        prompt = f"""
Generate a discovery questionnaire for a technical proposal workflow.

USER_INPUT:
{user_input}

DATA_GAPS:
{json.dumps(data_gaps, ensure_ascii=False, indent=2)}

NOTION_GUIDANCE:
{json.dumps(notion_guidance, ensure_ascii=False, indent=2)}

Return strict JSON:
{{
  "id": "questionnaire_x",
  "questions": [
    {{
      "id": "q1",
      "field": "field.path",
      "text": "Pergunta em portugues",
      "required": true,
      "priority": "critical|important|optional",
    "reason": "por que esta pergunta aumenta qualidade com base no template",
      "expectedFormat": "formato esperado",
      "exampleAnswer": "exemplo de resposta",
      "evidence": [
        {{"source": "NOTION_CACHE", "title": "...", "snippet": "..."}}
      ],
      "validation": {{"minLength": 3, "maxLength": 2000, "pattern": ".+"}}
    }}
  ],
  "estimatedTime": 10
}}

Constraints:
- Include only fields that appear in DATA_GAPS.
- Max 8 questions.
- Use evidence whenever available.
"""

        try:
            response = self.agent(prompt)
            parsed = self._extract_json(str(response))
            if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
                return parsed
        except Exception:
            logger.exception("[ChatPolicyAgent] Failed to generate questionnaire")

        return {
            "id": "questionnaire_fallback",
            "questions": [],
            "estimatedTime": max(5, len(data_gaps) * 2),
        }

    def _extract_json(self, text: str) -> Dict[str, Any] | None:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            return json.loads(match.group())
        except Exception:
            return None
