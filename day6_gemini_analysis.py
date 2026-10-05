import os

import pandas as pd
from dotenv import load_dotenv
from google import genai


# Load API keys from the local .env file.
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY was not found in .env")


# Create the Gemini API client.
client = genai.Client(api_key=gemini_api_key)


# Load the cleaned FRED data created on Day 5.
df = pd.read_csv("fedfunds_clean.csv")

df["date"] = pd.to_datetime(df["date"])
df["value"] = pd.to_numeric(df["value"])
df["change"] = pd.to_numeric(df["change"], errors="coerce")


# Select the latest two observations for comparison.
latest = df.iloc[-1]
previous = df.iloc[-2]


# Build a prompt from calculated facts rather than sending the full dataset.
prompt = f"""
You are a macroeconomic research assistant.

Analyze this effective federal funds rate data:

Latest observation:
- Date: {latest["date"].date()}
- Rate: {latest["value"]:.2f}%

Previous observation:
- Date: {previous["date"].date()}
- Rate: {previous["value"]:.2f}%

Latest monthly change:
- {latest["change"]:.2f} percentage points

Historical average:
- {df["value"].mean():.2f}%

Historical minimum:
- {df["value"].min():.2f}%

Historical maximum:
- {df["value"].max():.2f}%

Write a concise research note with:
1. The latest effective federal funds rate.
2. The recent direction of change.
3. One important caveat explaining why this data alone does not predict future monetary policy.

Do not invent additional data.
"""


# Ask Gemini to interpret the calculated statistics.
for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        break
    except Exception as error:
        if attempt == 2:
            raise

        wait_seconds = 2 ** attempt
        print(
            f"Gemini is temporarily unavailable. "
            f"Retrying in {wait_seconds} seconds..."
        )
        time.sleep(wait_seconds)


# Print the generated research note.
print(response.text)