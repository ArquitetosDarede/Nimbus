"""
Technical Writing Agent - Dedicated to technical proposal sections.
"""

import json
import logging
import os
from typing import Any, Dict

from strands import Agent
from strands.models import OpenAIModel

TECHNICAL_WRITING_PROMPT = """
You are a specialized Technical Writing Agent for AWS architecture proposals in Portuguese (Brazil).

Focus on technical precision, architecture decisions, security, operations, and implementation details.
Do not invent facts. Use only supplied context and cache evidence.
When possible, cite concrete AWS services and practical implementation steps.
"""

logger = logging.getLogger(__name__)


class TechnicalWritingAgent:
    """Generates technical-focused sections of the proposal."""

    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 2,
                    "timeout": 110,
                },
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.2,
                    "max_tokens": 4096,
                },
            ),
            system_prompt=TECHNICAL_WRITING_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def generate_section(
        self,
        section_title: str,
        context: Dict[str, Any],
        notion_cache: str = "",
        section_guidance: str = "",
        template_fragment: str = "",
        score_guidance: str = "",
        existing_sections_summary: str = "",
        scope_rules_block: str = "",
        review_feedback: str = "",
    ) -> str:
        """Generate one technical-oriented section."""
        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        guidance_block = ("\nSECTION GUIDANCE (Notion):\n" + section_guidance + "\n") if section_guidance else ""
        template_fragment_block = (
            "\nSECTION TEMPLATE FRAGMENT (authoritative source from Notion cache):\n"
            + template_fragment
            + "\n"
        ) if template_fragment else ""
        score_block = ("\nSCORE GUIDANCE (Notion):\n" + score_guidance + "\n") if score_guidance else ""
        existing_block = (
            "\nALREADY WRITTEN SECTIONS (do not repeat):\n" + existing_sections_summary + "\n"
        ) if existing_sections_summary else ""
        prompt = f"""
{cache_section}
{guidance_block}
{template_fragment_block}
{score_block}
{existing_block}

{scope_rules_block}

Generate only the technical section below.

SECTION:
{section_title}

CONTEXT:
{json.dumps(context, indent=2, ensure_ascii=False)}

REVIEW FEEDBACK (apply if relevant):
{review_feedback}

Rules:
1. Follow template language and section intent from Notion cache guidance first.
2. Treat SECTION TEMPLATE FRAGMENT as the highest-priority specification for structure, bullet style, punctuation, and mandatory text.
3. If SECTION TEMPLATE FRAGMENT includes instructions like "must", "always", "do not", or literal template blocks, obey them strictly.
4. For architecture, include service topology, security controls, and operational concerns.
5. For IaC-related content, provide concrete Terraform or CloudFormation-oriented guidance.
6. When scope_rules_block is provided, enforce it strictly.
7. Cover only what is unique to this section title; do not restate the full project summary unless the title explicitly asks for a summary or proposal information recap.
8. If the context already contains a concrete fact, do not output placeholders such as "a confirmar" or "a definir" for that fact.
9. If data is truly absent in context and not inferable from Notion guidance, mark as "a confirmar".
10. Materialize relevant SCORE guidance in the most natural way for this section when supported by context, especially success criteria, assumptions, risks, and decision drivers.
11. Do NOT duplicate content already covered in previous sections; only reference it briefly when needed.
12. Return only the section content body in markdown (without repeating the section header).
"""
        result = self.agent(prompt)
        text = str(result).strip()
        logger.info("[TechnicalWritingAgent] Section generated: %s", section_title)
        return text
