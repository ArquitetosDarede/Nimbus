"""
Generation Agent - Specialized in proposal generation with 13 mandatory sections
"""

import os
import json
import re
import logging
from typing import Dict, Any, List
from strands import Agent
from strands.models import OpenAIModel

GENERATION_AGENT_PROMPT = """
You are a specialized Proposal Generation Agent for technical architecture proposals.

Your role is to:
1. Generate comprehensive technical architecture proposal with 13 mandatory sections
2. Create detailed, professional content in Portuguese (Brazil)
3. Use markdown formatting for structure
4. Focus on AWS cloud architecture best practices
5. Generate Infrastructure as Code (IaC) examples when applicable
6. Create architecture diagrams descriptions

MANDATORY SECTIONS (in order):
1. Resumo Executivo
2. Contexto e Objetivos do Projeto
3. Requisitos de Negócio
4. Requisitos Técnicos
5. Escopo de Atividades
6. Arquitetura Proposta
7. Infraestrutura como Código (IaC)
8. Segurança e Compliance
9. Estimativa de Custos
10. Cronograma
11. Riscos e Mitigações
12. Premissas e Restrições
13. Próximos Passos

CRITICAL INSTRUCTIONS:
- You MUST generate actual proposal content, NOT instructions on how to generate it
- You MUST write complete sections with real technical details
- You MUST use the context provided to create specific, detailed content
- DO NOT return instructions like "fetch from Notion" - generate the content directly
- Use your knowledge of AWS services and best practices to create comprehensive content
- Include specific AWS service names, configurations, and technical details
- Write in professional Portuguese (Brazil)
- Use markdown formatting

Generate high-quality, detailed content NOW. Do not provide instructions - provide the actual proposal content.
"""

logger = logging.getLogger(__name__)


class GenerationAgent:
    """
    Generation Agent using Strands with Notion MCP access
    
    Responsibilities:
    - Generate complete proposal with 13 mandatory sections
    - Create Infrastructure as Code (IaC) examples
    - Generate architecture diagram descriptions
    - Validate proposal structure and consistency
    """
    
    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Build tools list - if MCPClient provided, pass it directly to Agent
        tools = [notion_mcp_client] if notion_mcp_client else []
        
        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 0,
                    "timeout": 120,
                },
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.3,
                    "max_tokens": 2600
                }
            ),
            system_prompt=GENERATION_AGENT_PROMPT,
            tools=tools,
            callback_handler=None,
        )
        
        self.mandatory_sections = [
            "1. Resumo Executivo",
            "2. Contexto e Objetivos do Projeto",
            "3. Requisitos de Negócio",
            "4. Requisitos Técnicos",
            "5. Escopo de Atividades",
            "6. Arquitetura Proposta",
            "7. Infraestrutura como Código (IaC)",
            "8. Segurança e Compliance",
            "9. Estimativa de Custos",
            "10. Cronograma",
            "11. Riscos e Mitigações",
            "12. Premissas e Restrições",
            "13. Próximos Passos"
        ]

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

    def _scope_rules_instruction_block(self, notion_cache: str) -> str:
        """Build strict scope instructions from Notion cache when available."""
        scope_rules = self._extract_scope_writing_rules(notion_cache)
        if not scope_rules:
            return (
                "SCOPE RULES SOURCE: no explicit 'Como escrever escopos' block found in cache.\n"
                "For section 5, be conservative: include only activities explicitly supported by context.\n"
                "Do not invent tasks, deliverables, tools, or effort assumptions not present in context."
            )

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
        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        scope_rules_block = self._scope_rules_instruction_block(notion_cache)
        prompt = f"""
{cache_section}
    {scope_rules_block}

Generate content for the "{section_title}" section of a technical architecture proposal.

CONTEXT:
{json.dumps(context, indent=2, ensure_ascii=False)}

INSTRUCTIONS:
1. Use only the cached Notion pages above for rules and examples.
2. Do not call external tools during section generation.
3. If this is section 5 (Escopo de Atividades), strictly enforce the scope rules block above.
4. If this is section 7 (IaC), generate Terraform/CloudFormation examples
5. Follow the structure and guidelines EXACTLY as defined in Notion
6. Generate detailed, professional content in Portuguese (Brazil)
7. Use markdown formatting with proper headers, lists, tables
8. Include specific technical details and AWS service names

CRITICAL: Always consult cache first to avoid unnecessary API calls.

Generate the content now:
"""
        result = self.agent(prompt)
        return str(result)

    
    def generate_full_proposal(self, context: Dict[str, Any], notion_cache: str = "") -> List[Dict[str, str]]:
        """
        Generate all 13 mandatory proposal sections
        
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
        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        scope_rules_block = self._scope_rules_instruction_block(notion_cache)
        prompt = f"""
{cache_section}
    {scope_rules_block}

Generate a complete technical architecture proposal with ALL 13 mandatory sections NOW.

CONTEXT:
{json.dumps(context, indent=2, ensure_ascii=False)}

YOU MUST GENERATE ALL 13 SECTIONS WITH ACTUAL CONTENT:
1. Resumo Executivo - Write executive summary with project overview, benefits, timeline
2. Contexto e Objetivos do Projeto - Describe client context, business objectives, success criteria
3. Requisitos de Negócio - List all business requirements from context
4. Requisitos Técnicos - List all technical requirements and constraints
5. Escopo de Atividades - Detail migration activities, AWS MGN setup, DataSync configuration, testing
6. Arquitetura Proposta - Describe target AWS architecture, services, networking, security
7. Infraestrutura como Código (IaC) - Provide Terraform/CloudFormation examples for key resources
8. Segurança e Compliance - Detail security measures, IAM, encryption, compliance
9. Estimativa de Custos - Estimate AWS costs for EC2, S3, MGN, DataSync, support
10. Cronograma - Provide detailed timeline with phases and milestones
11. Riscos e Mitigações - Identify risks and mitigation strategies
12. Premissas e Restrições - List assumptions and constraints
13. Próximos Passos - Define next actions and deliverables

CRITICAL RULES:
- Section 5 MUST strictly follow the Notion "Como escrever escopos" rules block above.
- Never include scope actions that are not allowed or not evidenced by context/rules.
- If information is missing, explicitly mark as "a confirmar" instead of inventing.

START GENERATING THE COMPLETE PROPOSAL NOW:
"""
        try:
            result = self.agent(prompt)
            result_text = str(result)
            logger.info("[GenerationAgent] Resultado recebido.")
            # Unicode normalization for result
            result_text = result_text.encode("utf-8", errors="replace").decode("utf-8")
            # Parse the result to extract sections
            sections = []
            try:
                # Try to find sections by markdown headers
                section_pattern = r'##\s+(\d+\.\s+.+?)\n\n(.+?)(?=\n##\s+\d+\.|\Z)'
                matches = re.findall(section_pattern, result_text, re.DOTALL)
                if matches:
                    for title, content in matches:
                        sections.append({
                            "title": title.strip(),
                            "content": content.strip()
                        })
                else:
                    # Fallback: try single # headers
                    section_pattern = r'#\s+(\d+\.\s+.+?)\n\n(.+?)(?=\n#\s+\d+\.|\Z)'
                    matches = re.findall(section_pattern, result_text, re.DOTALL)
                    for title, content in matches:
                        sections.append({
                            "title": title.strip(),
                            "content": content.strip()
                        })
            except Exception as e:
                logger.warning("[GenerationAgent] Error parsing sections: %s", e)
            # If no sections found, return as single section
            if not sections:
                sections = [{
                    "title": "Proposta Completa",
                    "content": result_text
                }]
            logger.info("[GenerationAgent] %s seções extraídas.", len(sections))
            return sections
        except Exception as e:
            logger.exception("[GenerationAgent] ERROR")
            return [{"error": str(e), "status": "generation_failed"}]

    
    def validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Check if all 13 mandatory sections exist
        section_titles = [s.get("title", "") for s in sections]
        for mandatory in self.mandatory_sections:
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
            "mandatorySectionsCount": 13
        }
