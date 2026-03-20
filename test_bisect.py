"""Bisect: is it prompt LENGTH or prompt CONTENT that triggers the error?"""
import sys, os
sys.path.insert(0, "src")
import openai

client = openai.OpenAI(max_retries=0, timeout=90)
SYSTEM = "Return OK and the word count."


def test(label, prompt):
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=50,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        print(f"  PASS  {label} (len={len(prompt)}) — {r.choices[0].message.content[:60]}", flush=True)
    except Exception as e:
        print(f"  FAIL  {label} (len={len(prompt)}) — {type(e).__name__}: {e}", flush=True)


# Test A: Short text
test("A short", "Hello world")

# Test B: Medium text (500 chars of lorem ipsum)
test("B 500ch", "Lorem ipsum dolor sit amet " * 20)

# Test C: 1000 chars
test("C 1000ch", "Lorem ipsum dolor sit amet " * 37)

# Test D: 1500 chars
test("D 1500ch", "Lorem ipsum dolor sit amet " * 56)

# Test E: 2000 chars
test("E 2000ch", "Lorem ipsum dolor sit amet " * 74)

# Test F: JSON braces (the actual analysis prompt content)
test("F json", '{"clientInfo": {"companyName": "test"}, "array": [1, 2, 3]}')

# Test G: The long prompt without the JSON template
test("G noJSON", """Analyze the following client input for creating a technical architecture proposal.

INPUT TYPE: text
INPUT:
Proposta para Ciclope Corporations. Backup de 5TB de dados on-premises em Recife para AWS.
Regioes: SP e us-east-1. Dados: video. Decomissionar on-premises apos migracao.

INSTRUCTIONS:
1. Extract all key information from the input.
2. Use objective language and keep output compact.
3. Identify only CRITICAL data gaps.

Return your analysis as JSON.
""")

# Test H: Just the JSON template part
test("H jsonTpl", """{
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
  "confidence": 0.0,
  "dataGaps": [
    {
      "field": "field_name",
      "description": "why this is needed",
      "required": true,
      "suggestedQuestions": ["question1", "question2"]
    }
  ]
}""")

print("\nDONE", flush=True)
