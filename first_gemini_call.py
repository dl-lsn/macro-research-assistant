def validate_analysis(result):
    required_keys = {
        "summary",
        "topics",
        "rate_bias",
        "confidence",
    }

    missing_keys = required_keys - result.keys()

    if missing_keys:
        raise ValueError(f"Missing fields: {missing_keys}")

    if result["rate_bias"] not in {"hawkish", "neutral", "dovish"}:
        raise ValueError("Invalid rate_bias value")

    if not isinstance(result["topics"], list):
        raise ValueError("topics must be a list")

    if not 0 <= result["confidence"] <= 1:
        raise ValueError("confidence must be between 0 and 1")

    return result

import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

prompt = prompt = """
You are a careful financial analyst.

Analyse the following statement:

"The central bank expects inflation to remain above target for longer than
previously anticipated. It therefore indicates that interest rates may need
to remain restrictive."

We will later extract:
- a one-sentence summary,
- the main topics,
- whether the rate stance is hawkish, neutral or dovish,
- a confidence score between 0 and 1.

For now, explain your analysis in normal prose.
"""
response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string"
        },
        "topics": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "rate_bias": {
            "type": "string",
            "enum": ["hawkish", "neutral", "dovish"]
        },
        "confidence": {
            "type": "number"
        }
    },
    "required": [
        "summary",
        "topics",
        "rate_bias",
        "confidence"
    ]
}

token_count = client.models.count_tokens(
    model="gemini-3.5-flash-lite",
    contents=prompt,
)

print("Input tokens:", token_count.total_tokens)

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": response_schema,
    },
)

result = json.loads(response.text)
result = validate_analysis(result)

required_keys = {
    "summary",
    "topics",
    "rate_bias",
    "confidence",
}

missing_keys = required_keys - result.keys()

if missing_keys:
    raise ValueError(f"Missing fields: {missing_keys}")

if result["rate_bias"] not in {"hawkish", "neutral", "dovish"}:
    raise ValueError("Invalid rate_bias value")

if not isinstance(result["topics"], list):
    raise ValueError("topics must be a list")

if not 0 <= result["confidence"] <= 1:
    raise ValueError("confidence must be between 0 and 1")

print("Rate stance:", result["rate_bias"])
print("Confidence:", result["confidence"])
print("Topics:", ", ".join(result["topics"]))
#print(json.dumps(result, indent=2))
#print(result)
