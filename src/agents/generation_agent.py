"""
Generation Agent - Specialized in template-driven proposal generation.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List

from strands import Agent
from strands.models import OpenAIModel

from .business_writing_agent import BusinessWritingAgent
from .technical_writing_agent import TechnicalWritingAgent

logger = logging.getLogger(__name__)


class GenerationAgent:
    """
    Generation Agent using Strands with Notion MCP access
    
    Responsibilities:
    - Generate complete proposal following template-defined sections
    - Create Infrastructure as Code (IaC) examples
    - Generate architecture diagram descriptions
    - Validate proposal structure and consistency
    """
    
    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.business_agent = BusinessWritingAgent(notion_mcp_client=notion_mcp_client)
        self.technical_agent = TechnicalWritingAgent(notion_mcp_client=notion_mcp_client)

    def _resolve_template_sections(self, context: Dict[str, Any]) -> List[str]:
        """Resolve section order exclusively from Notion-provided template_sections in context."""
        sections = context.get("template_sections", []) if isinstance(context, dict) else []
        if isinstance(sections, list):
            cleaned: list[str] = []
            for item in sections:
                if not isinstance(item, str):
                    continue
                title = item.strip()
                if not title:
                    continue
                cleaned.append(title)
            if cleaned:
                return cleaned
        logger.warning("[GenerationAgent] Nenhuma template_section encontrada no contexto; retornando lista vazia.")
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

        fragment = "\n".join(lines[start_idx:end_idx]).strip()
        return fragment

    def _extract_scope_writing_rules(self, notion_cache: str) -> str:
        """Extract the most relevant snippet around 'Como escrever escopos' from Notion cache."""
        if not isinstance(notion_cache, str) or not notion_cache.strip():
            return ""

        cache_text = notion_cache
        lowered = cache_text.lower()
        anchor = "como escrever escopos"
        idx = lowered.find(anchor)

        if idx == -1:
            return ""

        # Keep a bounded window around the anchor to reduce token pressure.
        start = max(0, idx - 600)
        end = min(len(cache_text), idx + 2400)
        snippet = cache_text[start:end].strip()
        return snippet

    def _extract_section_guidance(self, notion_cache: str, section_title: str) -> str:
        """Extract a bounded section-specific guidance snippet from Notion cache."""
        if not isinstance(notion_cache, str) or not notion_cache.strip():
            return ""
        title = str(section_title or "").strip().lower()
        if not title:
            return ""

        lowered = notion_cache.lower()
        idx = lowered.find(title)
        if idx < 0:
            return ""

        start = max(0, idx - 420)
        end = min(len(notion_cache), idx + 1400)
        return notion_cache[start:end].strip()

    def _extract_score_guidance(self, notion_cache: str) -> str:
        """Extract a bounded SCORE-related snippet from Notion cache when present."""
        if not isinstance(notion_cache, str) or not notion_cache.strip():
            return ""

        lowered = notion_cache.lower()
        anchors = ["score", "situação", "situation", "complication", "opportunity", "resolution"]
        for anchor in anchors:
            idx = lowered.find(anchor)
            if idx < 0:
                continue
            start = max(0, idx - 500)
            end = min(len(notion_cache), idx + 2200)
            return notion_cache[start:end].strip()
        return ""

    def _summarize_existing_sections(self, sections: List[Dict[str, str]], max_items: int = 8) -> str:
        """Create compact summary of previous sections to prevent repeated writing."""
        if not isinstance(sections, list) or not sections:
            return ""

        lines: list[str] = []
        for section in sections[-max_items:]:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip().replace("\n", " ")
            if not title or not content:
                continue
            lines.append(f"- {title}: {content[:220]}")
        return "\n".join(lines)

    def _is_content_duplicate(self, content: str, sections: List[Dict[str, str]]) -> bool:
        """Detect high-overlap duplicated sections using normalized prefix comparison."""
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

    def _scope_rules_instruction_block(self, notion_cache: str) -> str:
        """Build strict scope instructions from Notion cache when available."""
        scope_rules = self._extract_scope_writing_rules(notion_cache)
        if not scope_rules:
            return ""

        return f"""
SCOPE RULES SOURCE (Notion - "Como escrever escopos"):
{scope_rules}

STRICT ENFORCEMENT FOR SECTION 5 (Escopo de Atividades):
1. Follow ONLY the rules and structure defined in the block above.
2. Do NOT add activities that are outside those definitions.
3. Use wording and granularity aligned with the Notion rules.
4. If context lacks required details, keep placeholders explicit instead of inventing content.
5. Respect included vs excluded boundaries from context and Notion definitions.
"""

    def _post_process_sections(
        self,
        sections: List[Dict[str, str]],
        analysis_context: Dict[str, Any],
        notion_cache: str,
        template_sections: List[str],
    ) -> List[Dict[str, str]]:
        """Single LLM pass to improve consistency, section distinctiveness, and SCORE adherence.

        This pass is allowed to rewrite sections only when needed to:
        - replace placeholders with known facts already present elsewhere,
        - remove cross-section contradictions,
        - differentiate sections that overlap semantically,
        - materialize SCORE-related guidance already present in Notion cache.
        It must not invent new facts.
        """
        if not sections:
            return sections

        section_map = "\n\n".join(
            f"### {s.get('title', '')}\n{str(s.get('content', '')).strip()[:1400]}"
            for s in sections
        )

        agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 0, "timeout": 120},
                model_id="gpt-4o-mini",
                params={"temperature": 0.1, "max_tokens": 16000},
            ),
            system_prompt="You are a proposal consistency editor. Return only valid JSON.",
            tools=[],
            callback_handler=None,
        )

        prompt = f"""You received a complete commercial proposal in Portuguese (Brazil) with {len(sections)} sections.

TASK: Repair the proposal so each section matches its title-specific purpose and the overall document adheres better to the Notion template and SCORE guidance.
- If a section contains a placeholder like "A definir", "A confirmar", "a confirmar", "pendente de detalhamento", "Em avaliação"
  AND the real information for that placeholder already appears in ANOTHER section of the same proposal OR in ANALYSIS FACTS below,
  replace the placeholder with the correct real data.
- If two sections are semantically too similar, rewrite the weaker one so it covers only the unique intent implied by its title and the template.
- If a section is too generic and mostly repeats the project summary, rewrite it to address the specific question implied by its title.
- Use SCORE/NOTION GUIDANCE below to materialize required success criteria, assumptions, risks, outcomes, or decision-support content in the most appropriate sections, but only when supported by existing facts.
- Do NOT invent or guess any value not present elsewhere in the proposal or ANALYSIS FACTS.
- Do NOT restructure, shorten, or rewrite sections that are already correct and distinct.
- The section at index 0 (Resumo Executivo) often summarizes data defined later; fix it last.

EXPECTED SECTION ORDER:
{json.dumps(template_sections or [], ensure_ascii=False)}

SCORE/NOTION GUIDANCE:
{self._extract_score_guidance(notion_cache)[:4000]}

ANALYSIS FACTS (ground truth from client questionnaire):
{json.dumps(analysis_context or {{}}, ensure_ascii=False)[:5000]}

PROPOSAL SECTIONS:
{section_map[:22000]}

Return JSON with ALL {len(sections)} sections in original order:
{{
  "sections": [
    {{"title": "...", "content": "...", "changed": true}},
    ...
  ]
}}
Only set "changed": true for sections whose content was actually modified."""

        try:
            result = agent(prompt)
            text = str(result)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                new_sections = parsed.get("sections", [])
                if isinstance(new_sections, list) and len(new_sections) == len(sections):
                    changed = sum(1 for s in new_sections if s.get("changed"))
                    if changed:
                        logger.info("[GenerationAgent] Post-process: %d seções corrigidas por consistência.", changed)
                    return [
                        {"title": s.get("title", ""), "content": s.get("content", "")}
                        for s in new_sections
                        if isinstance(s, dict)
                    ]
                else:
                    logger.warning(
                        "[GenerationAgent] Post-process retornou %d seções; esperadas %d. Mantendo originais.",
                        len(new_sections) if isinstance(new_sections, list) else -1,
                        len(sections),
                    )
        except Exception:
            logger.exception("[GenerationAgent] Post-process falhou; retornando seções originais.")

        return sections

    def _classify_section_owner(
        self,
        section_title: str,
        section_guidance: str,
        notion_cache: str,
    ) -> str:
        """Classify section ownership using Notion guidance instead of hardcoded keywords."""
        agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 0, "timeout": 45},
                model_id="gpt-4o-mini",
                params={"temperature": 0.0, "max_tokens": 20},
            ),
            system_prompt=(
                "You classify proposal sections for writer ownership. "
                "Return exactly one token: business or technical."
            ),
            tools=[],
            callback_handler=None,
        )

        prompt = f"""
Use ONLY the Notion-derived evidence below.

SECTION TITLE:
{section_title}

SECTION GUIDANCE:
{section_guidance[:2000] if isinstance(section_guidance, str) else ''}

NOTION CACHE EXCERPT:
{notion_cache[:2000] if isinstance(notion_cache, str) else ''}

Decision rule:
- Return business when the section intent is executive/commercial/scope-boundary/outcomes/assumptions/exclusions.
- Return technical when the section intent is architecture/implementation/security/operations/infrastructure/cost mechanics/effort estimation.

Output exactly one word:
business
or
technical
"""

        try:
            result = str(agent(prompt)).strip().lower()
            if "technical" in result:
                return "technical"
            if "business" in result:
                return "business"
        except Exception:
            logger.exception("[GenerationAgent] Section owner classification failed.")
            raise RuntimeError("section_owner_classification_failed")
        raise RuntimeError("section_owner_classification_ambiguous")
    
    def generate_section(self, section_title: str, context: Dict[str, Any], notion_cache: str = "") -> str:
        """
        Generate a specific proposal section
        
        Args:
            section_title: Title of section to generate
            context: Context with analysis, answers, and requirements
            notion_cache: Cached Notion content to reference
        
        Returns:
            Section content in Markdown
        """
        scope_rules_block = self._scope_rules_instruction_block(notion_cache)
        section_guidance = context.get("section_guidance", "") if isinstance(context, dict) else ""
        template_fragment = context.get("template_fragment", "") if isinstance(context, dict) else ""
        score_guidance = context.get("score_guidance", "") if isinstance(context, dict) else ""
        existing_sections_summary = context.get("existing_sections_summary", "") if isinstance(context, dict) else ""
        review_feedback = context.get("review_feedback", "") if isinstance(context, dict) else ""

        # Strip heavy bulk fields from the context before passing to writers;
        # template/cache content is already forwarded via dedicated parameters.
        writer_context = {
            k: v for k, v in context.items()
            if k not in ("template_text", "notion_cache", "template_sections",
                         "template_fragment", "section_guidance", "score_guidance",
                         "existing_sections_summary", "review_feedback")
        } if isinstance(context, dict) else context

        # Truncate notion_cache for writer prompts; section-specific data
        # is already provided via template_fragment and section_guidance.
        notion_cache_truncated = notion_cache[:3000] if isinstance(notion_cache, str) else ""

        section_owner = self._classify_section_owner(section_title, section_guidance, notion_cache)

        if section_owner == "technical":
            return self.technical_agent.generate_section(
                section_title=section_title,
                context=writer_context,
                notion_cache=notion_cache_truncated,
                section_guidance=section_guidance,
                template_fragment=template_fragment,
                score_guidance=score_guidance,
                existing_sections_summary=existing_sections_summary,
                scope_rules_block=scope_rules_block,
                review_feedback=review_feedback,
            )

        return self.business_agent.generate_section(
            section_title=section_title,
            context=writer_context,
            notion_cache=notion_cache_truncated,
            section_guidance=section_guidance,
            template_fragment=template_fragment,
            score_guidance=score_guidance,
            existing_sections_summary=existing_sections_summary,
            review_feedback=review_feedback,
        )

    
    def generate_full_proposal(self, context: Dict[str, Any], notion_cache: str = "") -> List[Dict[str, str]]:
        """
        Generate all proposal sections following template order
        
        Args:
            context: Complete context with analysis and answers
            notion_cache: Cached Notion content to reference
        
        Returns:
            List of sections with title and content
        """
        logger.info("[GenerationAgent] Gerando proposta completa...")
        if not isinstance(context, dict):
            logger.warning("[GenerationAgent] context deve ser um dicionário.")
            return [{"error": "context must be a dict", "status": "generation_failed"}]

        template_sections = self._resolve_template_sections(context)
        template_text = context.get("template_text", "") if isinstance(context, dict) else ""
        try:
            sections = []
            for idx, section_title in enumerate(template_sections, start=1):
                logger.info("[GenerationAgent] Gerando seção %s/%s: %s", idx, len(template_sections), section_title)
                section_context = dict(context)
                template_fragment = self._extract_template_fragment(template_text, section_title)
                section_context["template_fragment"] = template_fragment
                section_context["section_guidance"] = template_fragment or self._extract_section_guidance(notion_cache, section_title)
                section_context["score_guidance"] = self._extract_score_guidance(notion_cache)
                section_context["existing_sections_summary"] = self._summarize_existing_sections(sections)

                content = self.generate_section(section_title, section_context, notion_cache=notion_cache)
                content = str(content).encode("utf-8", errors="replace").decode("utf-8").strip()
                if not content:
                    raise RuntimeError(f"empty_section_content: {section_title}")

                if self._is_content_duplicate(content, sections):
                    logger.warning("[GenerationAgent] Conteudo duplicado detectado em '%s'; tentando regeneracao unica.", section_title)
                    section_context["review_feedback"] = (
                        str(context.get("review_feedback", ""))
                        + "\nReescreva esta secao com foco exclusivo no titulo atual e sem repetir secoes anteriores."
                    ).strip()
                    content_retry = self.generate_section(section_title, section_context, notion_cache=notion_cache)
                    content_retry = str(content_retry).encode("utf-8", errors="replace").decode("utf-8").strip()
                    if content_retry and not self._is_content_duplicate(content_retry, sections):
                        content = content_retry

                sections.append(
                    {
                        "title": f"{idx}. {section_title}",
                        "content": content,
                    }
                )

            logger.info("[GenerationAgent] %s seções geradas. Iniciando passo de consistência.", len(sections))
            analysis_ctx = context.get("analysis", {}) if isinstance(context, dict) else {}
            sections = self._post_process_sections(sections, analysis_ctx, notion_cache, template_sections)
            logger.info("[GenerationAgent] Passo de consistência concluído.")
            return sections
        except Exception as e:
            logger.exception("[GenerationAgent] ERROR")
            return [{"error": str(e), "status": "generation_failed"}]

    
    def validate_proposal(self, proposal: Dict[str, Any], expected_sections: List[str] | None = None) -> Dict[str, Any]:
        """
        Validate proposal structure and consistency
        
        Args:
            proposal: Generated proposal with sections
        
        Returns:
            Validation result with errors and warnings
        """
        sections = proposal.get("sections", [])
        
        # Structural validation
        errors = []
        warnings = []
        
        # Check if all expected sections exist
        section_titles = [s.get("title", "") for s in sections]
        required_sections = expected_sections if isinstance(expected_sections, list) and expected_sections else []
        for mandatory in required_sections:
            found = any(mandatory.lower() in title.lower() for title in section_titles)
            if not found:
                errors.append({
                    "type": "missing_section",
                    "message": f"Seção obrigatória ausente: {mandatory}"
                })
        
        # Check for empty sections
        for section in sections:
            if not section.get("content", "").strip():
                warnings.append({
                    "type": "empty_section",
                    "message": f"Seção vazia: {section.get('title', 'Unknown')}"
                })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sectionsCount": len(sections),
            "mandatorySectionsCount": len(required_sections)
        }
