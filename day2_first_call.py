import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

prompt = """
Explain how a stronger Swiss franc affects:
1. Swiss exporters.
2. Swiss importers.
3. The Swiss National Bank.
Use no more than 120 words.
"""

token_count = client.models.count_tokens(
    model="gemini-3.5-flash-lite",
    contents=prompt,
)

print("Input tokens:", token_count.total_tokens)

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt,
    config={
        "temperature": 0.2
        
    },
)

print(response.text)
