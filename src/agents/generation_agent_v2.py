"""
Generation Agent — Orchestrates per-section proposal generation using the
unified WriterAgent, NotionRelevanceMapper, and architecture contract.

Replaces the previous generation_agent.py which had classification logic,
business/technical split, post-processing, and truncated context.
"""

import json
import logging
import re
from typing import Any, Dict, List

from .writer_agent import WriterAgent

logger = logging.getLogger(__name__)


class GenerationAgent:
    """
    Generates all proposal sections using context-driven specialization.

    Key differences from previous version:
    - Single WriterAgent instead of business/technical split + classification
    - Architecture contract as authoritative source
    - Relevant Notion content per section (full, not truncated)
    - No _post_process_sections (replaced by CoherenceAgent downstream)
    """

    def __init__(self):
        self.writer = WriterAgent()

    def _resolve_template_sections(self, context: Dict[str, Any]) -> List[str]:
        """Resolve section order from template_sections in context."""
        sections = context.get("template_sections", []) if isinstance(context, dict) else []
        if isinstance(sections, list):
            cleaned = [s.strip() for s in sections if isinstance(s, str) and s.strip()]
            if cleaned:
                return cleaned
        logger.warning("[GenerationAgent] No template_sections found in context.")
        return []

    def _extract_template_fragment(self, template_text: str, section_title: str) -> str:
        """Extract the exact template fragment for a section using markdown heading boundaries."""
        if not isinstance(template_text, str) or not template_text.strip():
            return ""
        target = str(section_title or "").strip().lower()
        if not target:
            return ""

        lines = template_text.splitlines()
        start_idx = -1
        start_level = 0
        for i, raw in enumerate(lines):
            m = re.match(r"^(#{1,6})\s+(.+)$", str(raw).strip())
            if not m:
                continue
            title = m.group(2).strip().lower()
            if title == target:
                start_idx = i
                start_level = len(m.group(1))
                break

        if start_idx < 0:
            return ""

        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            m = re.match(r"^(#{1,6})\s+(.+)$", str(lines[i]).strip())
            if not m:
                continue
            level = len(m.group(1))
            if level <= start_level:
                end_idx = i
                break

        return "\n".join(lines[start_idx:end_idx]).strip()

    def _summarize_existing_sections(self, sections: List[Dict[str, str]], max_items: int = 12) -> str:
        """Create compact summary of previous sections to prevent repetition."""
        if not sections:
            return ""
        lines = []
        for section in sections[-max_items:]:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip().replace("\n", " ")
            if title and content:
                lines.append(f"- {title}: {content[:400]}")
        return "\n".join(lines)

    def _is_content_duplicate(self, content: str, sections: List[Dict[str, str]]) -> bool:
        """Detect high-overlap duplicated sections."""
        candidate = " ".join(str(content or "").lower().split())
        if len(candidate) < 80:
            return False
        prefix = candidate[:360]
        for section in sections:
            if not isinstance(section, dict):
                continue
            prev = " ".join(str(section.get("content", "")).lower().split())
            if len(prev) < 80:
                continue
            if prefix == prev[:360]:
                return True
        return False

    def generate_full_proposal(
        self,
        context: Dict[str, Any],
        relevance_map: Dict[str, str],
        architecture_contract: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Generate all proposal sections.

        Args:
            context: Contains analysis, user_input, template_text, template_sections.
            relevance_map: {section_title -> relevant Notion content string}.
            architecture_contract: Authoritative architecture contract dict.

        Returns:
            List of sections with title and content.
        """
        logger.info("[GenerationAgent] Generating full proposal...")

        template_sections = self._resolve_template_sections(context)
        template_text = context.get("template_text", "") if isinstance(context, dict) else ""
        arch_json = json.dumps(architecture_contract, ensure_ascii=False, indent=2)

        # Strip heavy fields from writer context
        writer_context = {
            k: v for k, v in context.items()
            if k not in ("template_text", "notion_cache", "template_sections",
                         "template_fragment", "relevance_map")
        } if isinstance(context, dict) else context

        sections = []
        for idx, section_title in enumerate(template_sections, start=1):
            logger.info(
                "[GenerationAgent] Section %s/%s: %s",
                idx, len(template_sections), section_title,
            )

            template_fragment = self._extract_template_fragment(template_text, section_title)
            relevant_notion = relevance_map.get(section_title, "")
            existing_summary = self._summarize_existing_sections(sections)
            review_feedback = context.get("review_feedback", "") if isinstance(context, dict) else ""

            content = self.writer.generate_section(
                section_title=section_title,
                context=writer_context,
                template_fragment=template_fragment,
                architecture_contract=arch_json,
                relevant_notion_content=relevant_notion,
                existing_sections_summary=existing_summary,
                review_feedback=review_feedback,
            )
            content = str(content).encode("utf-8", errors="replace").decode("utf-8").strip()

            if not content:
                logger.error("[GenerationAgent] Empty content for '%s'", section_title)
                content = "Conteúdo a ser desenvolvido."

            if self._is_content_duplicate(content, sections):
                logger.warning("[GenerationAgent] Duplicate detected in '%s'; regenerating.", section_title)
                content_retry = self.writer.generate_section(
                    section_title=section_title,
                    context=writer_context,
                    template_fragment=template_fragment,
                    architecture_contract=arch_json,
                    relevant_notion_content=relevant_notion,
                    existing_sections_summary=existing_summary,
                    review_feedback="Reescreva esta seção com foco exclusivo no título atual. Não repita conteúdo de seções anteriores.",
                )
                content_retry = str(content_retry).encode("utf-8", errors="replace").decode("utf-8").strip()
                if content_retry and not self._is_content_duplicate(content_retry, sections):
                    content = content_retry

            sections.append({
                "title": f"{idx}. {section_title}",
                "content": content,
            })

        logger.info("[GenerationAgent] %d sections generated.", len(sections))
        return sections
