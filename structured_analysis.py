import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

from prompt_builder import build_macro_prompt


OUTPUT_FILE = Path("structured_analysis.json")


class MacroAnalysis(BaseModel):
    """Expected structure of the Gemini research note."""

    facts: list[str] = Field(
        description=(
            "Statements directly supported by the supplied data."
        )
    )

    calculations: list[str] = Field(
        description=(
            "Descriptions of calculated changes or relationships."
        )
    )

    interpretation: list[str] = Field(
        description=(
            "Cautious economic interpretations."
        )
    )

    uncertainty_and_limitations: list[str] = Field(
        description=(
            "Limitations and uncertainty in the analysis."
        )
    )

    missing_information: list[str] = Field(
        description=(
            "Additional information that would improve analysis."
        )
    )

    caveat: str = Field(
        description=(
            "A two-sentence caveat explaining that one "
            "monthly observation cannot establish a trend."
        )
    )


def load_latest_row():
    """Load the latest complete macroeconomic observation."""
    input_file = Path("macro_derived.csv")

    if not input_file.exists():
        raise FileNotFoundError(
            f"Missing required file: {input_file}"
        )

    df = pd.read_csv(input_file)

    if "date" not in df.columns:
        raise ValueError(
            "macro_derived.csv must contain a date column"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    return df.tail(1).iloc[0]


def validate_analysis(analysis):
    """Validate the required structure and caveat."""
    sections = [
        analysis.facts,
        analysis.calculations,
        analysis.interpretation,
        analysis.uncertainty_and_limitations,
        analysis.missing_information,
    ]

    for section in sections:
        if not section:
            raise ValueError(
                "Every analysis section must contain "
                "at least one item."
            )

    sentence_count = (
        analysis.caveat.count(".")
        + analysis.caveat.count("!")
        + analysis.caveat.count("?")
    )

    if sentence_count < 2:
        raise ValueError(
            "The caveat should contain at least two sentences."
        )


def save_analysis(analysis):
    """Save the validated analysis as formatted JSON."""
    OUTPUT_FILE.write_text(
        json.dumps(
            analysis.model_dump(),
            indent=4,
        ),
        encoding="utf-8",
    )

    print(f"Saved: {OUTPUT_FILE}")


def main():
    load_dotenv()

    gemini_api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY was not found in .env"
        )

    latest_row = load_latest_row()

    prompt = build_macro_prompt(
        latest_row
    )

    client = genai.Client(
        api_key=gemini_api_key
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": MacroAnalysis,
        },
    )

    analysis = response.parsed

    if analysis is None:
        raise ValueError(
            "Gemini returned no parsed structured output."
        )

    validate_analysis(analysis)
    save_analysis(analysis)

    print("\nStructured analysis:")
    print(
        json.dumps(
            analysis.model_dump(),
            indent=4,
        )
    )


if __name__ == "__main__":
    main()