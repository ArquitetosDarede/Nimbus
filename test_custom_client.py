"""Test different httpx/client configurations to work around httpcore.ReadError."""
import sys, os
sys.path.insert(0, 'src')

import httpx
import openai
from strands import Agent
from strands.models import OpenAIModel

# Test 1: Inject a custom AsyncOpenAI client with custom transport
print("=== Test 1: Custom AsyncOpenAI with timeout tweaks ===", flush=True)
try:
    custom_client = openai.AsyncOpenAI(
        max_retries=2,
        timeout=httpx.Timeout(90.0, connect=30.0, read=90.0, write=30.0),
    )
    model = OpenAIModel(
        client=custom_client,
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 1200},
    )
    agent = Agent(
        model=model,
        system_prompt="You are a specialized Requirements Analysis Agent for technical architecture proposals.\n\nYour role is to:\n1. Analyze client input (text, requirements, business needs)\n2. Extract key information: project name, client name, technologies, scope, timeline\n3. Consult Notion cache for validated scopes and rules when supplied\n4. Identify data gaps that need clarification\n5. Structure the analysis in a clear JSON format",
        tools=[],
        callback_handler=None,
    )

    prompt = (
        "Analyze the following client input for creating a technical architecture proposal.\n\n"
        "INPUT TYPE: text\nINPUT:\n"
        "Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS.\n"
        "Regioes: SP e us-east-1. Dados: video. Decomissionar on-premises apos migracao.\n\n"
        "Return a JSON object with keys: companyName, projectName, technologies, businessRequirements, dataGaps.\n"
    )
    print("Prompt length:", len(prompt), flush=True)
    result = agent(prompt)
    print("Test 1 SUCCESS:", str(result)[:200], flush=True)
except Exception as e:
    print(f"Test 1 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 2: Custom httpx transport with longer keepalive
print("=== Test 2: Custom httpx AsyncClient with keepalive ===", flush=True)
try:
    transport = httpx.AsyncHTTPTransport(retries=2)
    http_client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(120.0, connect=30.0, read=120.0, write=30.0),
    )
    custom_client2 = openai.AsyncOpenAI(
        http_client=http_client,
        max_retries=0,  # httpx transport handles retries
    )
    model2 = OpenAIModel(
        client=custom_client2,
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 1200},
    )
    agent2 = Agent(
        model=model2,
        system_prompt="You are a specialized Requirements Analysis Agent for technical architecture proposals.\n\nYour role is to:\n1. Analyze client input\n2. Extract key information\n3. Structure the analysis in JSON format",
        tools=[],
        callback_handler=None,
    )
    result2 = agent2(prompt)
    print("Test 2 SUCCESS:", str(result2)[:200], flush=True)
except Exception as e:
    print(f"Test 2 ERROR: {type(e).__name__}: {e}", flush=True)

# Test 3: Use sync approach - bypass Strands entirely
print("=== Test 3: Direct sync OpenAI call (no Strands) ===", flush=True)
try:
    sync_client = openai.OpenAI(max_retries=2, timeout=90)
    r = sync_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a specialized Requirements Analysis Agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1200,
    )
    print("Test 3 SUCCESS:", r.choices[0].message.content[:200], flush=True)
except Exception as e:
    print(f"Test 3 ERROR: {type(e).__name__}: {e}", flush=True)

print("DONE", flush=True)
