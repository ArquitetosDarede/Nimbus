"""
SCORE Evaluator Agent — Evaluates the final proposal against the "SCORE - Consulting"
page from Notion, which contains quality rules from the Delivery team's perspective.

Also performs structural validation (all sections present, no duplicates, valid markdown).
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)

SCORE_EVALUATOR_PROMPT = """
You are a Proposal Quality Evaluator using the SCORE methodology.

You evaluate proposals from the perspective of the Delivery team that will
implement the proposed solution. Your evaluation criteria come EXCLUSIVELY
from the SCORE - Consulting rules provided to you.

Rules:
- Evaluate strictly against SCORE criteria — do not invent your own criteria.
- Score from 0.0 to 10.0.
- For each issue, identify the SPECIFIC section that needs improvement.
- Provide actionable correction guidance per section.
- Use Brazilian Portuguese.
- Return valid JSON only.
"""


class ScoreEvaluatorAgent:
    """Evaluates proposal quality against SCORE - Consulting from Notion."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 2, "timeout": 120},
                model_id="gpt-4o",
                params={"temperature": 0.0, "max_tokens": 4096},
            ),
            system_prompt=SCORE_EVALUATOR_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def _proposal_as_text(self, sections: List[Dict[str, str]]) -> str:
        lines = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip()
            if title:
                lines.append(f"## {title}")
            if content:
                lines.append(content)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def validate_structure(
        sections: List[Dict[str, str]],
        template_sections: List[str],
    ) -> Dict[str, Any]:
        """
        Programmatic structural validation — no LLM needed.

        Checks:
        - All expected sections are present
        - No duplicate section titles
        - No empty section content
        """
        errors = []
        section_titles = []

        for section in sections:
            if not isinstance(section, dict):
                errors.append("Invalid section format (not a dict)")
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip()
            section_titles.append(title)

            if not title:
                errors.append("Section with empty title found")
            if not content:
                errors.append(f"Section '{title}' has empty content")

        # Check for expected sections
        title_lower_set = {t.lower() for t in section_titles}
        for expected in template_sections:
            # Match flexibly: section titles may have numbering prefix like "1. Resumo"
            found = any(
                expected.lower() in t for t in title_lower_set
            )
            if not found:
                errors.append(f"Missing expected section: '{expected}'")

        # Check for duplicates
        seen = set()
        for title in section_titles:
            normalized = title.lower().strip()
            if normalized in seen:
                errors.append(f"Duplicate section: '{title}'")
            seen.add(normalized)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "section_count": len(sections),
            "expected_count": len(template_sections),
        }

    def evaluate(
        self,
        sections: List[Dict[str, str]],
        score_page_content: str,
        architecture_contract: Dict[str, Any],
        template_sections: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluate proposal against SCORE - Consulting criteria.

        Args:
            sections: Full proposal sections.
            score_page_content: Complete content of the SCORE - Consulting Notion page.
            architecture_contract: The authoritative architecture contract.
            template_sections: Expected section titles.

        Returns:
            Evaluation result with score, issues, and per-section feedback.
        """
        proposal_text = self._proposal_as_text(sections)

        prompt = f"""
Evaluate this proposal using ONLY the SCORE criteria below.

SCORE - CONSULTING EVALUATION CRITERIA:
{score_page_content}

ARCHITECTURE CONTRACT (reference for factual accuracy):
{json.dumps(architecture_contract, ensure_ascii=False, indent=2)[:6000]}

EXPECTED SECTIONS:
{json.dumps(template_sections, ensure_ascii=False)}

FULL PROPOSAL:
{proposal_text}

EVALUATION PROCESS:
1. Read each SCORE criterion.
2. Check if the proposal satisfies it.
3. For each violation, identify the specific section that needs improvement.
4. Score: start at 10.0 and deduct based on severity of violations.

Scoring guide:
- Missing SCORE criterion entirely: -1.0
- Partially addressed criterion: -0.5
- Factual error vs architecture contract: -1.5
- Placeholder ("a confirmar") where fact exists in contract: -1.0

Return JSON:
{{
  "score": 8.5,
  "passed": true,
  "summary": "Overall evaluation summary in Portuguese",
  "issues": [
    {{
      "section_title": "section needing improvement",
      "section_index": 0,
      "criterion": "which SCORE criterion is violated",
      "severity": "critical|major|minor",
      "description": "what is wrong in Portuguese",
      "correction_guidance": "how to fix it in Portuguese"
    }}
  ]
}}

A proposal passes when score >= 8.0 AND no critical issues.
Return ONLY the JSON object."""

        try:
            result = str(self.agent(prompt))
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    logger.info(
                        "[ScoreEvaluator] Evaluation: score=%.1f, passed=%s, issues=%d",
                        float(parsed.get("score", 0)),
                        parsed.get("passed", False),
                        len(parsed.get("issues", [])),
                    )
                    return parsed
        except Exception:
            logger.exception("[ScoreEvaluator] Evaluation failed.")

        return {
            "score": 0.0,
            "passed": False,
            "summary": "Avaliação falhou",
            "issues": [],
        }
