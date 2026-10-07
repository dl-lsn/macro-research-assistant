import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
import random
import time


DATA_FILE = Path("macro_derived.csv")
FED_CONTEXT_FILE = Path("fed_context.txt")
SOURCE_REGISTRY_FILE = Path(
    "source_registry.json"
)
OUTPUT_FILE = Path(
    "research_question_output.txt"
)


def load_latest_data():
    """Load the latest complete macro observation."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Missing data file: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    return df.tail(1).iloc[0]


def load_text_file(file_path):
    """Load a UTF-8 text file."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Missing file: {file_path}"
        )

    return file_path.read_text(
        encoding="utf-8"
    )


def format_latest_data(row):
    """Format the latest data for the prompt."""
    data_lines = []

    for column, value in row.items():
        if column == "date":
            data_lines.append(
                f"{column}: {value}"
            )
            continue

        if pd.isna(value):
            formatted_value = "missing"
        elif isinstance(value, float):
            formatted_value = f"{value:.3f}"
        else:
            formatted_value = str(value)

        data_lines.append(
            f"{column}: {formatted_value}"
        )

    return "\n".join(data_lines)


def build_question_prompt(
    question,
    latest_data,
    fed_context,
    source_registry,
):
    """Build a source-disciplined research prompt."""
    return f"""
<role>
You are a careful macroeconomic research assistant.
</role>

<research_question>
{question}
</research_question>

<latest_quantitative_data>
The following values come from the project's
frequency-aligned and derived FRED data:

{latest_data}
</latest_quantitative_data>

<official_fed_context>
The following text comes from an official Federal Reserve
document saved by the project:

{fed_context}
</official_fed_context>

<source_registry>
{source_registry}
</source_registry>

<instructions>
Answer the research question using the supplied evidence.

Separate your response into:

1. Direct answer
2. Relevant data observations
3. Calculations and relationships
4. Federal Reserve context
5. Interpretation
6. Uncertainty and limitations
7. Information that would improve the answer

Source discipline rules:

- Treat FRED values as observed or project-derived data.
- Treat the Federal Reserve text as official policy context.
- Treat interpretations as analysis, not facts.
- Do not invent missing data.
- Do not use GDP or any other indicator not supplied here.
- Do not claim causation from correlation.
- Do not give investment advice.
- If the evidence is insufficient, say so clearly.
</instructions>

<output_format>
Use Markdown headings.
Use concise paragraphs and bullet points.
Answer the specific research question directly.
Keep the answer below 700 words.
</output_format>
""".strip()


def generate_answer(prompt):
    """Send the research prompt to Gemini with retries."""
    load_dotenv()

    gemini_api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY was not found in .env"
        )

    client = genai.Client(
        api_key=gemini_api_key
    )

    max_attempts = 5

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as error:
            error_text = str(error).lower()

            retryable_error = any(
                phrase in error_text
                for phrase in [
                    "high demand",
                    "overloaded",
                    "503",
                    "unavailable",
                    "429",
                    "resource exhausted",
                    "rate limit",
                ]
            )

            if not retryable_error:
                raise

            if attempt == max_attempts - 1:
                raise RuntimeError(
                    "Gemini remained unavailable after "
                    f"{max_attempts} attempts.\n"
                    f"Last error: {error}"
                ) from error

            delay = min(
                60,
                2 ** attempt,
            )

            delay += random.uniform(
                0,
                1,
            )

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {delay:.1f} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError(
        "Gemini request failed unexpectedly."
    )


def save_output(
    question,
    answer,
):
    """Save the question, timestamp, and answer."""
    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    output = (
        "# Macro Research Question\n\n"
        f"**Question:** {question}\n\n"
        f"**Generated at UTC:** {timestamp}\n\n"
        "## Answer\n\n"
        f"{answer}\n"
    )

    OUTPUT_FILE.write_text(
        output,
        encoding="utf-8",
    )


def main():
    question = input(
        "Enter your macroeconomic question: "
    ).strip()

    if not question:
        raise ValueError(
            "The research question cannot be empty."
        )

    latest_row = load_latest_data()

    fed_context = load_text_file(
        FED_CONTEXT_FILE
    )

    source_registry = load_text_file(
        SOURCE_REGISTRY_FILE
    )

    latest_data = format_latest_data(
        latest_row
    )

    prompt = build_question_prompt(
        question,
        latest_data,
        fed_context,
        source_registry,
    )

    answer = generate_answer(prompt)

    save_output(
        question,
        answer,
    )

    print(f"\nSaved: {OUTPUT_FILE}")
    print("\nAnswer:\n")
    print(answer)


if __name__ == "__main__":
    main()