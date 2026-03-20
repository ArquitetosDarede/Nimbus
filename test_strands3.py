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

# Test 1: Simple prompt, same agent config
print("=== Test 1: Simple prompt ===", flush=True)
try:
    r = agent("Analyze: backup 5TB Ciclope Corporations. Return JSON with clientInfo.companyName.")
    print("Test 1 SUCCESS:", str(r)[:100], flush=True)
except Exception as e:
    print(f"Test 1 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 2: Same prompt but with the JSON template (double braces)
print("=== Test 2: With JSON template ===", flush=True)
prompt2 = (
    "Analyze: backup 5TB Ciclope Corporations.\n\n"
    "Return JSON:\n"
    "{\n"
    '  "clientInfo": {"companyName": "string"},\n'
    '  "technologies": ["tech1"]\n'
    "}\n"
)
try:
    r = agent(prompt2)
    print("Test 2 SUCCESS:", str(r)[:100], flush=True)
except Exception as e:
    print(f"Test 2 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 3: Large JSON template with escaped braces
print("=== Test 3: Large JSON template with escaped braces ===", flush=True)
prompt3 = """Analyze the following client input for a proposal.

INPUT: Proposta backup 5TB Ciclope Corporations

Provide your analysis in JSON format:
{{
  "clientInfo": {{
    "companyName": "string or null",
    "projectName": "string or null"
  }},
  "businessRequirements": ["requirement1"],
  "technologies": ["tech1"],
  "dataGaps": [
    {{
      "field": "field_name",
      "description": "why this is needed"
    }}
  ]
}}
"""
try:
    r = agent(prompt3)
    print("Test 3 SUCCESS:", str(r)[:100], flush=True)
except Exception as e:
    print(f"Test 3 ERROR: {type(e).__name__}: {e}", flush=True)

print("DONE", flush=True)
