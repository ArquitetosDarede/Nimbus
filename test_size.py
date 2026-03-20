import sys, os
sys.path.insert(0, 'src')

from agents.analysis_agent import ANALYSIS_AGENT_PROMPT
from strands import Agent
from strands.models import OpenAIModel

# Test 1: Large prompt, SMALL max_tokens
print("=== Test 1: Large prompt, max_tokens=100 ===", flush=True)
agent1 = Agent(
    model=OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 100}
    ),
    system_prompt=ANALYSIS_AGENT_PROMPT,
    tools=[],
    callback_handler=None,
)
prompt = (
    "Analyze the following client input for creating a technical architecture proposal.\n\n"
    "INPUT TYPE: text\nINPUT:\n"
    "Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS.\n"
    "Regioes: SP e us-east-1. Dados: video. Decomissionar on-premises apos migracao.\n\n"
    "Return a JSON object with keys: companyName, projectName, technologies, businessRequirements, dataGaps.\n"
    "Be very brief."
)
print("Prompt length:", len(prompt), flush=True)
try:
    r = agent1(prompt)
    print("Test 1 SUCCESS:", str(r)[:200], flush=True)
except Exception as e:
    print(f"Test 1 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 2: Short prompt, LARGE max_tokens
print("=== Test 2: Short prompt, max_tokens=2000 ===", flush=True)
agent2 = Agent(
    model=OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 2000}
    ),
    system_prompt=ANALYSIS_AGENT_PROMPT,
    tools=[],
    callback_handler=None,
)
try:
    r = agent2("Analyze the project for Ciclope Corporations: backup 5TB video data from Recife to AWS SP and us-east-1. Return detailed JSON analysis.")
    print("Test 2 SUCCESS:", str(r)[:200], flush=True)
except Exception as e:
    print(f"Test 2 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 3: Check if strands-agents has streaming config
print("=== Test 3: Check Strands streaming config ===", flush=True)
try:
    import inspect
    src = inspect.getsource(OpenAIModel.__init__)
    if 'stream' in src.lower():
        print("OpenAIModel.__init__ references 'stream'", flush=True)
    src2 = inspect.getsource(OpenAIModel.format_request)
    if 'stream' in src2.lower():
        for line in src2.split('\n'):
            if 'stream' in line.lower():
                print("  format_request:", line.strip(), flush=True)
except Exception as e:
    print(f"Test 3: {e}", flush=True)

print("DONE", flush=True)
