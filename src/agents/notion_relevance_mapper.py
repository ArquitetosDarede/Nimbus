"""
Notion Relevance Mapper

Single LLM pass that maps proposal template sections to the most relevant
Notion pages, producing a reusable relevance map for the entire generation loop.
"""

import json
import logging
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)


class NotionRelevanceMapper:
    """Maps template sections to relevant Notion pages in a single LLM pass."""

    def __init__(self):
        self.agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 2, "timeout": 120},
                model_id="gpt-4o-mini",
                params={"temperature": 0.0, "max_tokens": 4096},
            ),
            system_prompt=(
                "You are a relevance mapping agent. You receive a list of proposal "
                "template sections and a catalogue of Notion pages with summaries. "
                "Your job is to map each section to the Notion pages that are most "
                "relevant for writing that section. Return valid JSON only."
            ),
            tools=[],
            callback_handler=None,
        )

    def _build_page_catalogue(self, notion_cache: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build a lightweight catalogue of all Notion pages (id + title + first ~500 chars)."""
        catalogue = []
        for page_id, info in notion_cache.items():
            if not isinstance(info, dict):
                continue
            title = str(info.get("title", "")).strip()
            text = str(info.get("text", "")).strip()
            summary = text[:500] if text else ""
            if title:
                catalogue.append({
                    "page_id": str(page_id),
                    "title": title,
                    "summary": summary,
                })
        return catalogue

    def build_relevance_map(
        self,
        template_sections: List[str],
        notion_cache: Dict[str, Any],
        user_context: str = "",
    ) -> Dict[str, List[str]]:
        """
        Produce a map: {section_title -> [page_id, ...]} in a single LLM pass.

        Args:
            template_sections: Ordered list of section titles from the template.
            notion_cache: Full Notion cache dict {page_id: {title, text}}.
            user_context: Brief summary of what the proposal is about.

        Returns:
            Dict mapping each section title to a list of relevant page_ids.
        """
        catalogue = self._build_page_catalogue(notion_cache)
        if not catalogue or not template_sections:
            logger.warning("[RelevanceMapper] Empty catalogue or sections — returning empty map.")
            return {s: [] for s in template_sections}

        prompt = f"""You have a proposal with the following sections to write:

SECTIONS:
{json.dumps(template_sections, ensure_ascii=False, indent=2)}

PROPOSAL CONTEXT:
{user_context[:1000] if user_context else 'General technical proposal'}

Below is a catalogue of all available Notion knowledge-base pages.
Each entry has a page_id, title, and a short summary of its content.

NOTION PAGE CATALOGUE:
{json.dumps(catalogue, ensure_ascii=False, indent=2)}

TASK:
For each section, identify which Notion pages contain relevant content that would help
write that specific section. A page is relevant if it contains:
- Writing rules, structure, or instructions for that type of section
- Examples or templates for that section
- Domain knowledge referenced by that section (e.g., scope catalogue for scope sections,
  hour estimates for estimation sections, SCORE methodology for executive summaries)

Return JSON mapping each section to its relevant page_ids (max 5 per section):
{{
  "Section Title 1": ["page_id_a", "page_id_b"],
  "Section Title 2": ["page_id_c"],
  ...
}}

If no pages are relevant for a section, return an empty list.
Return ONLY the JSON object, no other text."""

        try:
            result = str(self.agent(prompt))
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    # Validate page_ids exist in cache
                    valid_ids = set(str(k) for k in notion_cache.keys())
                    relevance_map = {}
                    for section in template_sections:
                        page_ids = parsed.get(section, [])
                        if isinstance(page_ids, list):
                            relevance_map[section] = [
                                pid for pid in page_ids
                                if isinstance(pid, str) and pid in valid_ids
                            ]
                        else:
                            relevance_map[section] = []
                    logger.info(
                        "[RelevanceMapper] Map built: %d sections, avg %.1f pages/section",
                        len(relevance_map),
                        sum(len(v) for v in relevance_map.values()) / max(1, len(relevance_map)),
                    )
                    return relevance_map
        except Exception:
            logger.exception("[RelevanceMapper] Failed to build relevance map.")

        return {s: [] for s in template_sections}

    def get_relevant_content(
        self,
        section_title: str,
        relevance_map: Dict[str, List[str]],
        notion_cache: Dict[str, Any],
    ) -> str:
        """Retrieve full content of relevant Notion pages for a specific section."""
        page_ids = relevance_map.get(section_title, [])
        if not page_ids:
            return ""

        fragments = []
        for pid in page_ids:
            info = notion_cache.get(pid)
            if not isinstance(info, dict):
                continue
            title = str(info.get("title", "")).strip()
            text = str(info.get("text", "")).strip()
            if text:
                fragments.append(f"--- {title} ---\n{text}")

        return "\n\n".join(fragments)
