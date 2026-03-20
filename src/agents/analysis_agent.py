"""
Analysis Agent - Specialized in requirements analysis and data extraction
"""

import os
import json
import re
import logging
from typing import Dict, Any
from datetime import datetime
from strands import Agent
from strands.models import OpenAIModel

ANALYSIS_AGENT_PROMPT = """
You are a specialized Requirements Analysis Agent for technical architecture proposals.

Your role is to:
1. Analyze client input (text, requirements, business needs)
2. Extract key information: project name, client name, technologies, scope, timeline
3. Consult Notion cache for validated scopes and rules when supplied
4. Identify data gaps that need clarification
5. Structure the analysis in a clear JSON format

IMPORTANT: You have access to Notion via tools, but the orchestrator will
usually pass cached page content.  Use the cache first and avoid new API
queries unless you truly need to.
"""

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """
    Analysis Agent using Strands with optional Notion MCP access
    
    Responsibilities:
    - Process multiple input formats (text, transcripts, emails)
    - Extract key information (project, client, technologies, scope)
    - Fetch validated scopes from Notion when necessary
    - Identify data gaps
    """
    
    def __init__(self, notion_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Build tools list - if MCPClient provided, pass it directly to Agent
        tools = [notion_mcp_client] if notion_mcp_client else []
        
        self.agent = Agent(
            model=OpenAIModel(
                client_args={
                    "max_retries": 2,
                    "timeout": 90,
                },
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.3,
                    "max_tokens": 1200
                }
            ),
            system_prompt=ANALYSIS_AGENT_PROMPT,
            tools=tools,
            callback_handler=None,
        )

    def analyze(self, input_text: str, input_type: str = "text", notion_cache: str = "") -> Dict[str, Any]:
        """
        Analyze input and extract requirements
        
        Args:
            input_text: Client input to analyze
            input_type: Type of input (text, transcript, email, etc.)
            notion_cache: Pre-fetched Notion content that can be used as reference
        
        Returns:
            Analysis result with extracted info, Notion scopes, and data gaps
        """
        logger.info("[AnalysisAgent] Iniciando análise...")
        # Edge case: input_text must be non-empty string
        if not isinstance(input_text, str) or not input_text.strip():
            logger.warning("[AnalysisAgent] input_text vazio ou inválido.")
            return {"error": "input_text must be a non-empty string", "status": "analysis_failed"}
        # Unicode normalization
        input_text = input_text.encode("utf-8", errors="replace").decode("utf-8")
        logger.info("[AnalysisAgent] Input normalizado para UTF-8.")
        # attach cache to prompt if available
        cache_section = ("\nNOTION CACHE:\n" + notion_cache + "\n") if notion_cache else ""
        prompt = f"""
{cache_section}
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: {input_type}
INPUT:
{input_text}

INSTRUCTIONS:
1. Consult only the cached Notion pages above for rules, examples and templates.
2. Do not call external tools during this analysis.
3. Extract all key information from the input.
4. Use objective language and keep output compact.
5. Identify only CRITICAL data gaps (information absolutely needed to proceed).

Provide your analysis in JSON format:
{{
  "clientInfo": {{
    "companyName": "string or null",
    "projectName": "string or null",
    "contactEmail": "string or null",
    "contactPerson": "string or null"
  }},
  "businessRequirements": ["requirement1", "requirement2"],
  "technicalRequirements": ["requirement1", "requirement2"],
  "scope": {{
    "included": ["item1", "item2"],
    "excluded": ["item1", "item2"]
  }},
  "technologies": ["tech1", "tech2"],
  "constraints": ["constraint1", "constraint2"],
  "timeline": "string or null",
  "budget": "string or null",
  "notionScopes": [
    {{
      "id": "scope_id_from_notion",
      "title": "Scope title",
      "description": "Scope description",
      "hours": 0,
      "technologies": ["tech1"]
    }}
  ],
  "confidence": 0.0-1.0,
  "dataGaps": [
    {{
      "field": "field_name",
      "description": "why this is needed",
      "required": true,
      "suggestedQuestions": ["question1", "question2"]
    }}
  ]
}}

Note: minimize Notion API calls to conserve rate limits.
"""
        try:
            result = self.agent(prompt)
            result_text = str(result)
            logger.info("[AnalysisAgent] Resultado recebido.")
            # Try to extract JSON from result
            analysis_data = None
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
            except Exception as e:
                logger.warning("[AnalysisAgent] Could not parse JSON from result: %s", e)
            # Return serializable data
            if analysis_data and isinstance(analysis_data, dict):
                logger.info("[AnalysisAgent] JSON extraído com sucesso.")
                return {
                    "analysis": analysis_data,
                    "input_text": input_text,
                    "input_type": input_type,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.info("[AnalysisAgent] JSON não extraído, retornando texto bruto.")
                return {
                    "analysis": result_text,
                    "input_text": input_text,
                    "input_type": input_type,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.exception("[AnalysisAgent] ERROR — %s: %s", type(e).__name__, e)
            # Log the full exception chain for diagnosing connection errors
            cause = e.__cause__ or e.__context__
            while cause:
                logger.error("[AnalysisAgent]   caused by %s: %s", type(cause).__name__, cause)
                cause = getattr(cause, '__cause__', None) or getattr(cause, '__context__', None)
            return {"error": str(e), "status": "analysis_failed"}
