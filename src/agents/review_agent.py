"""
Review Agent - Evaluates proposal adherence to template and SCORE guidance.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

REVIEW_AGENT_PROMPT = """
You are a specialized Proposal Review Agent for cloud/infrastructure proposals in Portuguese (Brazil).

Your role is to:
1. Evaluate proposal quality against provided template sections and SCORE guidance from Notion
2. Return an objective score from 0.0 to 10.0
3. Identify missing or weak sections
4. Provide concise corrective actions that another generation pass can apply

SCORING PENALTIES (apply each that is found):
- Each missing expected template section: -0.8
- Placeholder text ("A definir", "A confirmar", "pendente de detalhamento", "Em avaliação") still present
  while the real value IS AVAILABLE in another section or in ANALYSIS FACTS CONTEXT: -1.0 per occurrence
- Cross-section contradiction (e.g., section 1 says "A confirmar" but section 17 has the real hours): -0.8
- Section with content clearly copied from a different section (duplicate): -1.0
- Missing a required SCORE block explicitly listed in SCORE/NOTION CACHE CONTEXT: -0.5 each
- Invented data not supported by context or ANALYSIS FACTS: -1.5

A proposal PASSES (passed=true) only when score >= 8.0 AND no critical contradictions.

Return valid JSON only.
"""

logger = logging.getLogger(__name__)


class ReviewAgent:
    """Reviews generated proposals and produces structured quality feedback."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 0,
                    "timeout": 90,
                },
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.1,
                    "max_tokens": 1400,
                },
            ),
            system_prompt=REVIEW_AGENT_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def _proposal_as_text(self, proposal: Dict[str, Any]) -> str:
        """Flatten proposal sections for review context."""
        if not isinstance(proposal, dict):
            return ""
        lines: list[str] = []
        for section in proposal.get("sections", []):
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip()
            if title:
                lines.append(f"## {title}")
            if content:
                lines.append(content)
            lines.append("")
        return "\n".join(lines).strip()

    def review_proposal(
        self,
        proposal: Dict[str, Any],
        template_sections: List[str],
        notion_cache: str = "",
        analysis_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Review proposal and return score + fix guidance."""
        if not isinstance(proposal, dict):
            return {
                "score": 0.0,
                "passed": False,
                "missing_sections": [],
                "weak_sections": [],
                "actions": ["Proposta invalida para revisao."],
            }

        expected = [s for s in template_sections if isinstance(s, str) and s.strip()]
        proposal_text = self._proposal_as_text(proposal)

        prompt = f"""
Evaluate this proposal against template and SCORE criteria.

EXPECTED TEMPLATE SECTIONS (all must appear in order):
{json.dumps(expected, ensure_ascii=False, indent=2)}

SCORE/NOTION CACHE CONTEXT (extract required blocks, writing rules, and checklist from here):
{notion_cache[:7000] if isinstance(notion_cache, str) else ''}

ANALYSIS FACTS CONTEXT (client questionnaire answers — treat as ground truth):
{json.dumps(analysis_context or {}, ensure_ascii=False, indent=2)[:8000]}

PROPOSAL TEXT:
{proposal_text[:24000]}

EVALUATION CHECKLIST (apply each item; deduct points per REVIEW_AGENT_PROMPT rules):
1. All expected template sections present and in correct order?
2. Any placeholder text ("A definir", "A confirmar", "pendente de detalhamento", "Em avaliação") present
   while the real value exists in ANALYSIS FACTS CONTEXT or in another section of this proposal?
3. Does section 1 (Resumo Executivo) contradict sections that provide real data (e.g., scope, hours)?
4. Are all required SCORE blocks from NOTION CACHE CONTEXT present (e.g., critérios de sucesso, riscos, premissas)?
5. Any section whose content is a near-copy of another section?
6. Any invented data (not supported by ANALYSIS FACTS or NOTION CACHE)?

Return JSON only:
{{
  "score": 0.0,
  "passed": true,
  "missing_sections": ["..."],
  "weak_sections": [{{"section": "...", "reason": "..."}}],
  "actions": ["..."],
  "summary": "short summary"
}}

Rules:
- passed=true only if score >= 8.0 and no missing critical sections and no unresolved contradictions.
- Each action must be a direct rewrite instruction (e.g., "Atualizar seção 1 para refletir as inclusões detalhadas na seção 6").
- Flag every placeholder that contradicts a known fact as a separate action item.
"""

        try:
            result = self.agent(prompt)
            text = str(result)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    parsed.setdefault("score", 0.0)
                    parsed.setdefault("passed", False)
                    parsed.setdefault("missing_sections", [])
                    parsed.setdefault("weak_sections", [])
                    parsed.setdefault("actions", [])
                    return parsed
        except Exception:
            logger.exception("[ReviewAgent] Failed to parse review response")

        return {
            "score": 0.0,
            "passed": False,
            "missing_sections": [],
            "weak_sections": [],
            "actions": ["Falha na revisao automatica; executar revisao manual."],
            "summary": "Nao foi possivel interpretar a revisao automaticamente.",
        }
