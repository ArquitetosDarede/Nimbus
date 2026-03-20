"""
Coherence Agent — Reads the full proposal, identifies contradictions and
inconsistencies, and determines which sections need selective regeneration.

Replaces the previous _post_process_sections and the contradiction-detection
role of ReviewAgent.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)

COHERENCE_PROMPT = """
You are a Proposal Coherence Agent. You read an entire technical proposal
and identify contradictions, inconsistencies, and incoherences across sections.

Your job is NOT to rewrite sections. Your job is to:
1. Read the full proposal end-to-end.
2. Compare every section against the architecture contract (source of truth).
3. Identify specific contradictions (e.g., a service mentioned in section A
   that does not appear in the architecture contract or scope section).
4. For each issue, specify WHICH section must be regenerated and WHY.
5. Provide the correction context so the writer can fix it precisely.

Rules:
- Be extremely specific: cite the exact text that contradicts.
- Only flag real contradictions, not stylistic preferences.
- Use Brazilian Portuguese in descriptions.
- Return valid JSON only.
"""


class CoherenceAgent:
    """Identifies contradictions in a complete proposal and requests selective regeneration."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 2, "timeout": 120},
                model_id="gpt-4o",
                params={"temperature": 0.0, "max_tokens": 4096},
            ),
            system_prompt=COHERENCE_PROMPT,
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
                # Preserve the original heading hierarchy inside the content
                # instead of flattening everything under ##.
                lines.append(content)
            lines.append("")
        return "\n".join(lines)

    def check_coherence(
        self,
        sections: List[Dict[str, str]],
        architecture_contract: Dict[str, Any],
        template_sections: List[str],
    ) -> Dict[str, Any]:
        """
        Check full proposal for contradictions against the architecture contract.

        Returns:
            {
                "coherent": bool,
                "issues": [
                    {
                        "section_title": str,
                        "section_index": int,
                        "issue": str,
                        "contradicts": str,  # what it contradicts
                        "correction_context": str,  # guidance for the writer
                    }
                ]
            }
        """
        proposal_text = self._proposal_as_text(sections)

        prompt = f"""
Read this complete proposal and compare it against the architecture contract.

ARCHITECTURE CONTRACT (single source of truth):
{json.dumps(architecture_contract, ensure_ascii=False, indent=2)[:10000]}

EXPECTED SECTIONS (all must be present):
{json.dumps(template_sections, ensure_ascii=False)}

FULL PROPOSAL:
{proposal_text}

CHECK FOR:
1. Services mentioned in any section that are NOT in the architecture contract.
2. Regions or data flows that contradict the contract.
3. Scope items in one section that are missing or contradicted in another.
4. Placeholders ("a confirmar") where the real data exists in another section or contract.
5. Duplicated content across sections.
6. Missing expected sections.

Return JSON:
{{
  "coherent": true/false,
  "issues": [
    {{
      "section_title": "exact title of the problematic section",
      "section_index": 0,
      "issue": "description of the contradiction in Portuguese",
      "contradicts": "what source of truth it contradicts (contract / other section)",
      "correction_context": "specific guidance for the writer to fix this"
    }}
  ]
}}

If no issues found, return {{"coherent": true, "issues": []}}.
Return ONLY the JSON object."""

        try:
            result = str(self.agent(prompt))
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    issues = parsed.get("issues", [])
                    logger.info(
                        "[CoherenceAgent] Check complete: coherent=%s, issues=%d",
                        parsed.get("coherent", False),
                        len(issues) if isinstance(issues, list) else 0,
                    )
                    return parsed
        except Exception:
            logger.exception("[CoherenceAgent] Coherence check failed.")

        return {"coherent": True, "issues": []}
