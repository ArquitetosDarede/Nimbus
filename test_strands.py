import sys, os
sys.path.insert(0, 'src')
from strands import Agent
from strands.models import OpenAIModel

# Same config as AnalysisAgent but standalone
agent = Agent(
    model=OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 1200}
    ),
    system_prompt="You are an expert analyst.",
    tools=[],
    callback_handler=None,
)

prompt = (
    "Analyze the following client input for creating a technical architecture proposal.\n\n"
    "INPUT TYPE: text\n"
    "INPUT:\n"
    "Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS (SP e us-east-1).\n\n"
    "Provide in JSON format:\n"
    '{"clientInfo": {"companyName": "string"}, "businessRequirements": ["req1"], "technologies": ["tech1"]}'
)

print("Prompt length:", len(prompt), flush=True)

for attempt in range(3):
    try:
        result = agent(prompt)
        print(f"Attempt {attempt+1} SUCCESS:", str(result)[:200], flush=True)
        break
    except Exception as e:
        print(f"Attempt {attempt+1} ERROR: {type(e).__name__}: {e}", flush=True)

print("DONE", flush=True)
