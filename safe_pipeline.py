import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types


DATA_FILE = Path("macro_derived.csv")
FED_CONTEXT_FILE = Path("fed_context.txt")
ANALYSIS_FILE = Path("structured_analysis.json")
LOG_FILE = Path("pipeline_errors.log")


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(message)s"
    ),
)


def check_file(path):
    """Validate that a file exists and is non-empty."""
    if not path.exists():
        return False, f"missing: {path}"

    if path.stat().st_size == 0:
        return False, f"empty: {path}"

    return True, f"ok: {path}"


def check_macro_data():
    """Validate the macroeconomic dataset."""
    ok, message = check_file(DATA_FILE)

    if not ok:
        return False, message

    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as error:
        return False, f"cannot read {DATA_FILE}: {error}"

    if df.empty:
        return False, "macro_derived.csv has no rows"

    required_columns = {
        "date",
        "Federal funds rate (%)",
        "Annual inflation (%)",
        "Unemployment rate (%)",
    }

    missing = required_columns - set(df.columns)

    if missing:
        return False, (
            "missing columns: "
            + ", ".join(sorted(missing))
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    if df["date"].isna().any():
        return False, "macro_derived.csv contains invalid dates"

    if df["date"].duplicated().any():
        return False, "macro_derived.csv contains duplicate dates"

    numeric_columns = [
        column
        for column in df.columns
        if column != "date"
    ]

    for column in numeric_columns:
        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if converted.isna().all():
            return False, (
                f"column contains no numeric values: {column}"
            )

    return True, (
        f"ok: {len(df)} rows, "
        f"{df['date'].min().date()} to "
        f"{df['date'].max().date()}"
    )


def run_fast_check():
    """Run checks without making any network call."""
    print("Running fast check...\n")

    checks = [
        check_macro_data(),
        check_file(FED_CONTEXT_FILE),
    ]

    load_dotenv()

    if os.getenv("GEMINI_API_KEY"):
        checks.append(
            (True, "ok: GEMINI_API_KEY is present")
        )
    else:
        checks.append(
            (False, "missing: GEMINI_API_KEY")
        )

    failures = 0

    for passed, message in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {message}")

        if not passed:
            failures += 1

    print()

    if failures:
        print(f"Fast check failed: {failures} issue(s).")
        return 1

    print("Fast check passed.")
    return 0


def create_gemini_client():
    """Create a Gemini client with bounded request behavior."""
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from .env"
        )

    http_options = types.HttpOptions(
        timeout=30_000,
        retry_options=types.HttpRetryOptions(
            attempts=1,
        ),
    )

    return genai.Client(
        api_key=api_key,
        http_options=http_options,
    )


def build_prompt(df, fed_context):
    """Build a compact prompt from the latest row."""
    latest = df.sort_values("date").tail(1).iloc[0]

    data = {
        key: str(value)
        for key, value in latest.to_dict().items()
    }

    return f"""
Analyze this latest macroeconomic observation.

Data:
{json.dumps(data, indent=2)}

Official Federal Reserve context:
{fed_context[:6000]}

Return valid JSON with exactly these keys:
facts
calculations
interpretation
uncertainty_and_limitations
missing_information
caveat

Each value should be a list of short strings, except caveat,
which should be a single string.

Use only supplied evidence.
Do not invent data.
Do not claim causation.
Do not provide investment advice.
""".strip()


def run_analysis():
    """Run Gemini analysis only after local checks pass."""
    passed = run_fast_check()

    if passed:
        return passed

    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])

    fed_context = FED_CONTEXT_FILE.read_text(
        encoding="utf-8"
    )

    print("\nCreating Gemini client...", flush=True)
    client = create_gemini_client()

    prompt = build_prompt(
        df,
        fed_context,
    )

    print(
        "Calling Gemini with a 30-second timeout...",
        flush=True,
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    ANALYSIS_FILE.write_text(
        response.text,
        encoding="utf-8",
    )

    print(f"Saved analysis to {ANALYSIS_FILE}")
    return 0


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--check",
        action="store_true",
        help="Run local checks only; never call Gemini.",
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run checks and then call Gemini.",
    )

    args = parser.parse_args()

    try:
        if args.check:
            sys.exit(run_fast_check())

        if args.analyze:
            sys.exit(run_analysis())

        parser.print_help()

    except Exception as error:
        logging.exception("Pipeline failed")
        print(f"Pipeline failed: {error}")
        print(f"Details saved to {LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()