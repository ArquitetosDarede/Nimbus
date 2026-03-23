"""
Architecture Agent — Produces the architectural contract (single source of truth)
for the entire proposal and identifies data gaps.

The architectural contract defines:
- AWS services in scope
- Regions and data flow
- Architectural patterns and decisions
- Security controls
- Estimated complexity

All writers reference this contract to ensure cross-section coherence.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from strands import Agent
from strands.models import OpenAIModel

logger = logging.getLogger(__name__)

ARCHITECTURE_AGENT_PROMPT = """
You are a specialized AWS Solutions Architect Agent for technical proposals.

Your role is to:
1. Analyze client requirements and produce a concrete architectural solution.
2. Define which AWS services are needed and WHY (no gratuitous services).
3. Specify regions, data flow, and replication strategy.
4. Identify security controls, compliance requirements, and operational patterns.
5. Estimate complexity (low/medium/high) for each component.
6. Identify information gaps that would improve the solution quality.

Rules:
- Output must be valid JSON.
- Only recommend AWS services that directly serve the stated requirements.
- Every service must have a clear justification tied to a requirement.
- If information is missing, list it as a data_gap with a clear question.
- Data gaps are OPPORTUNITIES, not blockers — the solution must still be complete.
- Use Brazilian Portuguese for descriptions and gap questions.
- Be precise: specify service configurations, not just service names.
"""


class ArchitectureAgent:
    """Produces the architectural contract and identifies enrichment gaps."""

    def __init__(self, aws_mcp_client=None, aws_knowledge_mcp_client=None):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

        tools = []
        if aws_mcp_client:
            tools.append(aws_mcp_client)
        if aws_knowledge_mcp_client:
            tools.append(aws_knowledge_mcp_client)

        try:
            self.agent = Agent(
                model=OpenAIModel(
                    client_args={"max_retries": 2, "timeout": 120},
                    model_id="gpt-4o",
                    params={"temperature": 0.15, "max_tokens": 4096},
                ),
                system_prompt=ARCHITECTURE_AGENT_PROMPT,
                tools=tools,
                callback_handler=None,
            )
        except (ValueError, Exception):
            if aws_mcp_client:
                logger.warning("[ArchitectureAgent] AWS MCP tools failed to load — falling back without them.")
                self.agent = Agent(
                    model=OpenAIModel(
                        client_args={"max_retries": 2, "timeout": 120},
                        model_id="gpt-4o",
                        params={"temperature": 0.15, "max_tokens": 4096},
                    ),
                    system_prompt=ARCHITECTURE_AGENT_PROMPT,
                    tools=[],
                    callback_handler=None,
                )
            else:
                raise

    def generate_architecture(
        self,
        analysis: Dict[str, Any],
        user_input: str,
        notion_context: str = "",
    ) -> Dict[str, Any]:
        """
        Generate the architectural contract from analysis results.

        Args:
            analysis: Structured analysis from AnalysisAgent.
            user_input: Original user message for additional context.
            notion_context: Relevant Notion content (scope catalogue, etc.).

        Returns:
            Architectural contract dict with services, regions, data_gaps, etc.
        """
        logger.info("[ArchitectureAgent] Generating architectural contract...")

        notion_block = (
            f"\nNOTION KNOWLEDGE BASE (scope catalogue, patterns, reference architectures):\n{notion_context}\n"
            if notion_context else ""
        )

        prompt = f"""
Based on the analysis below, produce a complete architectural solution.

USER REQUEST:
{user_input[:2000]}

ANALYSIS:
{json.dumps(analysis, ensure_ascii=False, indent=2)[:6000]}
{notion_block}

If you have access to AWS documentation tools, use them to validate service
recommendations and find best practices relevant to this architecture.

Return a JSON object with this exact structure:
{{
  "solution_summary": "Brief description of the proposed architecture in Portuguese",
  "services": [
    {{
      "service": "AWS service name",
      "purpose": "Why this service is needed (tied to a requirement)",
      "configuration": "Key configuration details (e.g., storage class, instance type)",
      "region": "Region where this runs",
      "justification": "Which requirement this addresses"
    }}
  ],
  "regions": [
    {{
      "region": "AWS region code",
      "purpose": "Why this region (latency, compliance, DR)"
    }}
  ],
  "data_flow": "Description of how data moves between components and regions",
  "security_controls": [
    {{
      "control": "Security measure",
      "scope": "What it protects",
      "implementation": "How to implement"
    }}
  ],
  "patterns": ["List of architectural patterns used (e.g., hub-spoke, active-passive DR)"],
  "complexity_estimate": {{
    "overall": "low|medium|high",
    "components": [
      {{"component": "name", "complexity": "low|medium|high", "reason": "why"}}
    ]
  }},
  "data_gaps": [
    {{
      "question": "Question in Portuguese about missing information",
      "impact": "How this information would improve the architecture",
      "priority": "high|medium|low",
      "default_assumption": "What we assume if the user doesn't answer"
    }}
  ],
  "assumptions": ["List of assumptions made due to missing information"]
}}

IMPORTANT: The solution must be COMPLETE even with gaps. Gaps are enrichment
opportunities, not blockers. State your assumptions clearly."""

        try:
            result = str(self.agent(prompt))
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    logger.info(
                        "[ArchitectureAgent] Contract generated: %d services, %d gaps",
                        len(parsed.get("services", [])),
                        len(parsed.get("data_gaps", [])),
                    )
                    return parsed
        except Exception:
            logger.exception("[ArchitectureAgent] Failed to generate architecture.")

        return {
            "error": "architecture_generation_failed",
            "solution_summary": "",
            "services": [],
            "regions": [],
            "data_flow": "",
            "security_controls": [],
            "patterns": [],
            "complexity_estimate": {"overall": "unknown", "components": []},
            "data_gaps": [],
            "assumptions": [],
        }

    def evaluate_security(
        self,
        architecture: Dict[str, Any],
        user_input: str = "",
    ) -> Dict[str, Any]:
        """
        Pre-generation security evaluation of the proposed architecture.

        Returns security findings and additional data gaps related to compliance/security.
        """
        logger.info("[ArchitectureAgent] Running security evaluation on architecture...")

        prompt = f"""
Evaluate the following AWS architecture for security and compliance concerns.

ARCHITECTURE:
{json.dumps(architecture, ensure_ascii=False, indent=2)[:8000]}

USER CONTEXT:
{user_input[:1000]}

Check for:
1. Data encryption at rest and in transit
2. IAM and access control gaps
3. Network security (VPC, security groups, endpoints)
4. Compliance (LGPD, SOC 2 if applicable)
5. Logging and monitoring coverage
6. Disaster recovery and backup validation
7. Secrets management

Return JSON:
{{
  "overall_risk": "low|medium|high",
  "findings": [
    {{
      "category": "encryption|iam|network|compliance|monitoring|dr|secrets",
      "severity": "critical|high|medium|low",
      "description": "Description in Portuguese",
      "recommendation": "Recommended action in Portuguese"
    }}
  ],
  "security_gaps": [
    {{
      "question": "Security-related question for the user in Portuguese",
      "impact": "How this affects the security posture",
      "priority": "high|medium|low",
      "default_assumption": "What we assume if not answered"
    }}
  ]
}}"""

        try:
            result = str(self.agent(prompt))
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, dict):
                    logger.info(
                        "[ArchitectureAgent] Security eval: risk=%s, findings=%d, gaps=%d",
                        parsed.get("overall_risk", "unknown"),
                        len(parsed.get("findings", [])),
                        len(parsed.get("security_gaps", [])),
                    )
                    return parsed
        except Exception:
            logger.exception("[ArchitectureAgent] Security evaluation failed.")

        return {
            "overall_risk": "unknown",
            "findings": [],
            "security_gaps": [],
        }
