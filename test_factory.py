"""Quick test: factory model + long prompt identical to AnalysisAgent.analyze()."""
import sys, os
sys.path.insert(0, "src")

from models import create_openai_model
from strands import Agent

m = create_openai_model(model_id="gpt-4o-mini", temperature=0.3, max_tokens=1200, timeout=90)
a = Agent(
    model=m,
    system_prompt=(
        "You are a specialized Requirements Analysis Agent for technical architecture proposals.\n\n"
        "Your role is to:\n"
        "1. Analyze client input (text, requirements, business needs)\n"
        "2. Extract key information: project name, client name, technologies, scope, timeline\n"
        "3. Consult Notion cache for validated scopes and rules when supplied\n"
        "4. Identify data gaps that need clarification\n"
        "5. Structure the analysis in a clear JSON format\n\n"
        "IMPORTANT: You have access to Notion via tools, but the orchestrator will "
        "usually pass cached page content.  Use the cache first and avoid new API "
        "queries unless you truly need to."
    ),
    tools=[],
    callback_handler=None,
)

prompt = """
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
INPUT:
Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS.
Regioes: SP e us-east-1. Dados: video. Decomissionar on-premises apos migracao.

INSTRUCTIONS:
1. Consult only the cached Notion pages above for rules, examples and templates.
2. Do not call external tools during this analysis.
3. Extract all key information from the input.
4. Use objective language and keep output compact.
5. Identify only CRITICAL data gaps (information absolutely needed to proceed).

Provide your analysis in JSON format:
{
  "clientInfo": {
    "companyName": "string or null",
    "projectName": "string or null",
    "contactEmail": "string or null",
    "contactPerson": "string or null"
  },
  "businessRequirements": ["requirement1", "requirement2"],
  "technicalRequirements": ["requirement1", "requirement2"],
  "scope": {
    "included": ["item1", "item2"],
    "excluded": ["item1", "item2"]
  },
  "technologies": ["tech1", "tech2"],
  "constraints": ["constraint1", "constraint2"],
  "timeline": "string or null",
  "budget": "string or null",
  "notionScopes": [
    {
      "id": "scope_id_from_notion",
      "title": "Scope title",
      "description": "Scope description",
      "hours": 0,
      "technologies": ["tech1"]
    }
  ],
  "confidence": 0.0,
  "dataGaps": [
    {
      "field": "field_name",
      "description": "why this is needed",
      "required": true,
      "suggestedQuestions": ["question1", "question2"]
    }
  ]
}

Note: minimize Notion API calls to conserve rate limits.
"""

print(f"Prompt length: {len(prompt)}", flush=True)
print(f"Model custom client: {a.model._custom_client}", flush=True)
try:
    r = a(prompt)
    print(f"SUCCESS: {str(r)[:300]}", flush=True)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
