import sys, os
sys.path.insert(0, 'src')

# Use the EXACT same setup as AnalysisAgent
from agents.analysis_agent import ANALYSIS_AGENT_PROMPT
from strands import Agent
from strands.models import OpenAIModel

agent = Agent(
    model=OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 1200}
    ),
    system_prompt=ANALYSIS_AGENT_PROMPT,
    tools=[],
    callback_handler=None,
)

print("System prompt length:", len(ANALYSIS_AGENT_PROMPT), flush=True)

# Use the exact prompt from analyze()
input_text = "Proposta backup 5TB Ciclope Corporations"
prompt = f"""
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
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
  "confidence": 0.0,
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

print("Full prompt length:", len(prompt), flush=True)

try:
    result = agent(prompt)
    print("SUCCESS:", str(result)[:300], flush=True)
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("DONE", flush=True)
