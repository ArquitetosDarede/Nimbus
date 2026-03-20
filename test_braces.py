import sys, os
sys.path.insert(0, 'src')

from strands import Agent
from strands.models import OpenAIModel

agent = Agent(
    model=OpenAIModel(
        client_args={"max_retries": 2, "timeout": 90},
        model_id="gpt-4o-mini",
        params={"temperature": 0.3, "max_tokens": 300}
    ),
    system_prompt="You are an analyst. Always respond in JSON.",
    tools=[],
    callback_handler=None,
)

# Test A: NO braces at all - just describe the format
print("=== Test A: Describe format textually ===", flush=True)
try:
    r = agent("Analyze backup project. Return JSON with keys: companyName, technologies (array).")
    print("Test A SUCCESS:", str(r)[:150], flush=True)
except Exception as e:
    print(f"Test A ERROR: {type(e).__name__}: {e}", flush=True)

# Test B: Braces inside code fence
print("=== Test B: Braces inside code fence ===", flush=True)
try:
    r = agent("Analyze backup. Return JSON like:\n```json\n{\"companyName\": \"test\"}\n```")
    print("Test B SUCCESS:", str(r)[:150], flush=True)
except Exception as e:
    print(f"Test B ERROR: {type(e).__name__}: {e}", flush=True)

# Test C: Raw single brace
print("=== Test C: Raw single brace ===", flush=True)
try:
    r = agent("Return this JSON: { \"test\": 1 }")
    print("Test C SUCCESS:", str(r)[:150], flush=True)
except Exception as e:
    print(f"Test C ERROR: {type(e).__name__}: {e}", flush=True)

# Test D: Just a lone brace in text
print("=== Test D: Lone brace ===", flush=True)
try:
    r = agent("What is 2+2? Just the number, no { or } please.")
    print("Test D SUCCESS:", str(r)[:150], flush=True)
except Exception as e:
    print(f"Test D ERROR: {type(e).__name__}: {e}", flush=True)

print("DONE", flush=True)
