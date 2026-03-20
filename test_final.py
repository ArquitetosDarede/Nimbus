import sys, os
sys.path.insert(0, 'src')

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

# Test X: Full prompt but describe JSON schema as a table instead of JSON literal
print("=== Test X: Large prompt WITHOUT JSON braces ===", flush=True)
prompt = """
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
INPUT:
Proposta backup 5TB Ciclope Corporations

INSTRUCTIONS:
1. Consult only the cached Notion pages above for rules, examples and templates.
2. Do not call external tools during this analysis.
3. Extract all key information from the input.
4. Use objective language and keep output compact.
5. Identify only CRITICAL data gaps (information absolutely needed to proceed).

Return a JSON object with these top-level keys:
- clientInfo: object with companyName, projectName, contactEmail, contactPerson (strings or null)
- businessRequirements: array of strings
- technicalRequirements: array of strings
- scope: object with "included" (array) and "excluded" (array)
- technologies: array of strings
- constraints: array of strings
- timeline: string or null
- budget: string or null
- notionScopes: array of objects each with id, title, description, hours, technologies
- confidence: number 0.0 to 1.0
- dataGaps: array of objects each with field, description, required (boolean), suggestedQuestions (array)

Note: minimize Notion API calls to conserve rate limits.
"""
print("Prompt length:", len(prompt), flush=True)
try:
    r = agent(prompt)
    import json, re
    text = str(r)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        data = json.loads(m.group())
        print("Test X SUCCESS. Company:", data.get("clientInfo", {}).get("companyName"), flush=True)
    else:
        print("Test X SUCCESS (no JSON found):", text[:200], flush=True)
except Exception as e:
    print(f"Test X ERROR: {type(e).__name__}: {e}", flush=True)

# Test Y: Full prompt WITH JSON braces (same schema, same size)
print("=== Test Y: Large prompt WITH JSON braces ===", flush=True)
prompt_with_braces = """
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
INPUT:
Proposta backup 5TB Ciclope Corporations

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
print("Prompt length:", len(prompt_with_braces), flush=True)
try:
    r = agent(prompt_with_braces)
    text = str(r)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        data = json.loads(m.group())
        print("Test Y SUCCESS. Company:", data.get("clientInfo", {}).get("companyName"), flush=True)
    else:
        print("Test Y SUCCESS (no JSON):", text[:200], flush=True)
except Exception as e:
    print(f"Test Y ERROR: {type(e).__name__}: {e}", flush=True)

print("DONE", flush=True)
