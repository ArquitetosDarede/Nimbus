"""
Writer Agent — Unified section writer for proposals.

Replaces the previous BusinessWritingAgent and TechnicalWritingAgent.
Specialization per section comes from the injected context:
- template_fragment (from Notion template)
- relevant_notion_content (from NotionRelevanceMapper)
- architecture_contract (single source of truth for services/regions/scope)
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)

WRITER_PROMPT = """
You are a specialized Proposal Writer Agent for AWS cloud architecture proposals
in Portuguese (Brazil).

You write ONE section at a time considering:
- The template fragment defines structure, style, and mandatory content.
- The architecture contract is the SINGLE SOURCE OF TRUTH for services, regions, scope.
- Relevant Notion pages provide domain rules and examples specific to this section.
- Already written sections must not be repeated.

Rules:
1. Write in professional Brazilian Portuguese.
2. Do not invent facts. Only use data from context, architecture contract, or Notion evidence.
3. NEVER contradict the architecture contract (services, regions, scope, assumptions).
4. Dates must use ONLY the date provided in the CURRENT_DATE field. Never generate dates.
5. If data is truly absent and not in the architecture contract, mark as "a confirmar".
6. Return only the section content body in markdown (without the section header).
7. NEVER start your output with a heading that repeats the section title.
   The caller already wraps your output with `## {section_title}`, so if you
   emit `## Title` or `### Title` again you create a duplicate heading.
   Start directly with the body content. You MAY use sub-headings (###, ####)
   for internal structure when the template fragment requires them, but those
   sub-headings must NOT repeat the section title.
8. HTML/XML comment tags like `<!-- ... -->` or `<!-- ... -→` and template
   tags like `<exemplo>`, `</exemplo>` are internal markers (categories,
   instructions, examples). Use them as CONTEXT to understand the template
   structure, but NEVER reproduce them in your output.
   Your output must contain only visible markdown content.
"""


class WriterAgent:
    """Generates any section of the proposal with context-driven specialization."""

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.agent = Agent(
            model=OpenAIModel(
                client_args={"max_retries": 2, "timeout": 110},
                model_id="gpt-4o-mini",
                params={"temperature": 0.15, "max_tokens": 4096},
            ),
            system_prompt=WRITER_PROMPT,
            tools=[],
            callback_handler=None,
        )

    def generate_section(
        self,
        section_title: str,
        context: Dict[str, Any],
        template_fragment: str = "",
        architecture_contract: str = "",
        relevant_notion_content: str = "",
        existing_sections_summary: str = "",
        review_feedback: str = "",
    ) -> str:
        """
        Generate one proposal section.

        Args:
            section_title: Title of the section to write.
            context: Analysis data, user input, and other structured context.
            template_fragment: Exact template instructions for this section from Notion.
            architecture_contract: JSON string of the architectural contract (authoritative).
            relevant_notion_content: Full Notion pages relevant to THIS section.
            existing_sections_summary: Summary of already written sections.
            review_feedback: Feedback from coherence/SCORE agents for regeneration.
        """
        current_date = datetime.now().strftime("%d/%m/%Y")

        template_block = (
            "\nSECTION TEMPLATE FRAGMENT (highest priority for structure and style):\n"
            + template_fragment + "\n"
        ) if template_fragment else ""

        arch_block = (
            "\nARCHITECTURE CONTRACT (single source of truth — never contradict):\n"
            + architecture_contract + "\n"
        ) if architecture_contract else ""

        notion_block = (
            "\nRELEVANT NOTION KNOWLEDGE (domain rules, examples, catalogues for this section):\n"
            + relevant_notion_content + "\n"
        ) if relevant_notion_content else ""

        existing_block = (
            "\nALREADY WRITTEN SECTIONS (do not repeat, only reference briefly if needed):\n"
            + existing_sections_summary + "\n"
        ) if existing_sections_summary else ""

        feedback_block = (
            "\nREVIEW FEEDBACK (must address these issues):\n"
            + review_feedback + "\n"
        ) if review_feedback else ""

        prompt = f"""
CURRENT_DATE: {current_date}
{template_block}
{arch_block}
{notion_block}
{existing_block}
{feedback_block}

Generate the section below.

SECTION: {section_title}

PROJECT CONTEXT:
{json.dumps(context, indent=2, ensure_ascii=False)[:6000]}

Additional rules for this section:
1. If SECTION TEMPLATE FRAGMENT includes instructions ("must", "always", "do not")
   or literal template blocks, obey them strictly.
2. All AWS services mentioned MUST appear in the ARCHITECTURE CONTRACT.
   Do not mention services that are not in the contract.
3. All regions, data flow, and security controls must match the contract.
4. Cover only what is unique to this section title.
5. If data is in the architecture contract or context, use it — never write
   "a confirmar" for data that exists.
6. Use the date from CURRENT_DATE for any date references. Never invent dates.
"""
        result = self.agent(prompt)
        text = str(result).strip()
        logger.info("[WriterAgent] Section generated: %s", section_title)
        return text
