import os
import json
import re
import logging
from typing import Dict, Any
from strands import Agent
from strands.models import OpenAIModel

SECURITY_AGENT_PROMPT = """
You are a specialized Security and Compliance Agent.
Your job is to scan technical proposals for security vulnerabilities, compliance gaps, and best practice violations.
Focus on AWS, PII, encryption, IAM, network, logging, and compliance (LGPD, SOC 2, ISO 27001).
Always provide actionable recommendations and return results in structured JSON.
"""

logger = logging.getLogger(__name__)

class SecurityAgent:
  """
  Security Agent for proposal scanning and compliance validation
  """
  def __init__(self):
    if not os.getenv("OPENAI_API_KEY"):
      raise ValueError("OPENAI_API_KEY environment variable is required")
    self.agent = Agent(
      model=OpenAIModel(
        client_args={
          "max_retries": 0,
          "timeout": 90,
        },
        model_id="gpt-4o",
        params={
          "temperature": 0.2,
          "max_tokens": 1400
        }
      ),
      system_prompt=SECURITY_AGENT_PROMPT,
      tools=[],
      callback_handler=None
    )

  def scan_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan proposal for security issues and compliance gaps
    """
    logger.info("[SecurityAgent] Starting security scan...")
    if not proposal or not isinstance(proposal, dict):
      logger.warning("[SecurityAgent] Invalid proposal input. Returning empty scan result.")
      return {
        "overallRisk": "unknown",
        "findings": [],
        "result_text": "Invalid proposal input.",
        "summary": {
          "totalFindings": 0,
          "critical": 0,
          "high": 0,
          "medium": 0,
          "low": 0
        }
      }
    try:
      proposal_text = json.dumps(proposal, indent=2, ensure_ascii=False)
      prompt = f"""
Scan this technical proposal for:
1. Security vulnerabilities and misconfigurations
2. PII exposure
3. AWS security best practices
4. IAM and permissions issues
5. Network security (VPC, security groups, NACLs)
6. Data encryption (at rest and in transit)
7. Secrets management
8. Compliance (LGPD, SOC 2, ISO 27001)
9. Logging and monitoring gaps

PROPOSAL:
{proposal_text}

Return JSON format:
{{
  "overallRisk": "low|medium|high|critical",
  "findings": [{{
  "id": "finding_1",
  "severity": "low|medium|high|critical",
  "category": "category_name",
  "title": "Finding title",
  "description": "Detailed description",
  "location": "Section or component",
  "recommendation": "How to fix",
  "references": ["AWS doc link"]
  }}],
  "summary": {{
  "totalFindings": 0,
  "critical": 0,
  "high": 0,
  "medium": 0,
  "low": 0
  }},
  "compliance": {{
  "lgpd": "compliant|non-compliant|partial",
  "soc2": "compliant|non-compliant|partial",
  "iso27001": "compliant|non-compliant|partial"
  }}
}}
"""
      logger.info("[SecurityAgent] Prompt prepared. Invoking agent...")
      result = self.agent(prompt)
      result_text = str(result)
      logger.info("[SecurityAgent] Agent response received.")
      scan_result = None
      try:
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
          scan_result = json.loads(json_match.group())
      except Exception as e:
        logger.warning("[SecurityAgent] Could not parse JSON from security scan: %s", e)
      if scan_result and isinstance(scan_result, dict):
        logger.info("[SecurityAgent] Scan result parsed successfully.")
        return scan_result
      else:
        logger.info("[SecurityAgent] Scan result parsing failed. Returning fallback result.")
        return {
          "overallRisk": "unknown",
          "findings": [],
          "result_text": result_text[:500],
          "summary": {
            "totalFindings": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
          }
        }
    except Exception as e:
      logger.exception("[SecurityAgent] Exception during scan")
      return {
        "overallRisk": "unknown",
        "findings": [],
        "result_text": f"Exception: {e}",
        "summary": {
          "totalFindings": 0,
          "critical": 0,
          "high": 0,
          "medium": 0,
          "low": 0
        }
      }
