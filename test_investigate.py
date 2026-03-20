"""
Fresh investigation: isolate the exact failure condition.

Tests:
1. Short prompt via Strands Agent (known working)
2. Long prompt via Strands Agent (known failing)
3. Long prompt via sync openai.OpenAI (expected working)
4. Long prompt via async openai.AsyncOpenAI directly (bypass Strands)
5. Long prompt via Strands but with reduced max_tokens (less streaming)
"""
import sys, os, asyncio
sys.path.insert(0, "src")

from strands import Agent
from strands.models import OpenAIModel

SYSTEM = (
    "You are a specialized Requirements Analysis Agent for technical "
    "architecture proposals. Analyze input and return JSON."
)

SHORT_PROMPT = "Analyze: Backup 5TB Ciclope Corp to AWS. Return JSON with companyName and projectName."

LONG_PROMPT = """
Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
INPUT:
Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS.
Regioes: SP e us-east-1. Dados: video. Decomissionar on-premises apos migracao.

INSTRUCTIONS:
1. Extract all key information from the input.
2. Use objective language and keep output compact.
3. Identify only CRITICAL data gaps.

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
      "id": "scope_id",
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
"""


def make_agent(max_tokens=1200):
    m = OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": max_tokens},
    )
    return Agent(model=m, system_prompt=SYSTEM, tools=[], callback_handler=None)


# ---- Test 1: Short prompt via Strands ----
print("=== Test 1: Short prompt via Strands ===", flush=True)
try:
    a1 = make_agent()
    r1 = a1(SHORT_PROMPT)
    print(f"  PASS — {str(r1)[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 2: Long prompt via Strands ----
print(f"\n=== Test 2: Long prompt via Strands (prompt len={len(LONG_PROMPT)}) ===", flush=True)
try:
    a2 = make_agent()
    r2 = a2(LONG_PROMPT)
    print(f"  PASS — {str(r2)[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 3: Long prompt via sync OpenAI (no Strands) ----
print("\n=== Test 3: Long prompt via sync openai.OpenAI ===", flush=True)
try:
    import openai
    client = openai.OpenAI(max_retries=2, timeout=90)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": LONG_PROMPT},
        ],
    )
    print(f"  PASS — {resp.choices[0].message.content[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 4: Long prompt via AsyncOpenAI directly (no Strands) ----
print("\n=== Test 4: Long prompt via AsyncOpenAI (no Strands) ===", flush=True)
async def test_async():
    import openai
    client = openai.AsyncOpenAI(max_retries=2, timeout=90)
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": LONG_PROMPT},
        ],
    )
    return resp.choices[0].message.content

try:
    r4 = asyncio.run(test_async())
    print(f"  PASS — {r4[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 5: Long prompt via AsyncOpenAI with STREAMING (no Strands) ----
print("\n=== Test 5: Long prompt via AsyncOpenAI STREAMING (no Strands) ===", flush=True)
async def test_async_stream():
    import openai
    client = openai.AsyncOpenAI(max_retries=2, timeout=90)
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1200,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": LONG_PROMPT},
        ],
    )
    chunks = []
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            chunks.append(delta)
    return "".join(chunks)

try:
    r5 = asyncio.run(test_async_stream())
    print(f"  PASS — {r5[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 6: Long prompt via Strands with max_tokens=100 (less streaming) ----
print("\n=== Test 6: Long prompt via Strands, max_tokens=100 ===", flush=True)
try:
    a6 = make_agent(max_tokens=100)
    r6 = a6(LONG_PROMPT)
    print(f"  PASS — {str(r6)[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


# ---- Test 7: Long prompt via Strands with max_tokens=50 ----
print("\n=== Test 7: Long prompt via Strands, max_tokens=50 ===", flush=True)
try:
    a7 = make_agent(max_tokens=50)
    r7 = a7(LONG_PROMPT)
    print(f"  PASS — {str(r7)[:80]}", flush=True)
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}", flush=True)


print("\nDONE", flush=True)
