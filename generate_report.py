import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


DATA_FILE = Path("macro_derived.csv")
ANALYSIS_FILE = Path(
    "structured_analysis.json"
)
VALIDATION_FILE = Path(
    "validation_report.txt"
)
FED_METADATA_FILE = Path(
    "fed_context_metadata.json"
)
OUTPUT_FILE = Path(
    "macro_research_report.md"
)


def load_data():
    """Load the derived macroeconomic dataset."""
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
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "The macroeconomic dataset is empty."
        )

    return df


def load_json_file(file_path):
    """Load a JSON file if it exists."""
    if not file_path.exists():
        return None

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )


def load_text_file(file_path):
    """Load a text file if it exists."""
    if not file_path.exists():
        return None

    return file_path.read_text(
        encoding="utf-8"
    )


def format_value(value, decimals=2):
    """Format numeric values for Markdown."""
    if pd.isna(value):
        return "N/A"

    if decimals == 0:
        return f"{value:,.0f}"

    return f"{value:,.{decimals}f}"


def latest_observation_section(latest):
    """Build the latest-observation section."""
    return f"""
## Latest observation

| Indicator | Value |
|---|---:|
| Date | {latest["date"].date()} |
| Federal funds rate | {format_value(latest["Federal funds rate (%)"])}% |
| CPI index | {format_value(latest["CPI index"])} |
| Monthly inflation | {format_value(latest["Monthly inflation (%)"])}% |
| Annual inflation | {format_value(latest["Annual inflation (%)"])}% |
| Payroll employment | {format_value(latest["Payrolls (thousands)"], 0)} thousand persons |
| Monthly payroll change | {format_value(latest["Monthly payroll change (thousands)"], 0)} thousand jobs |
| Unemployment rate | {format_value(latest["Unemployment rate (%)"])}% |
| 10-year Treasury average | {format_value(latest["10-year Treasury average (%)"])}% |
| 10-year Treasury month-end | {format_value(latest["10-year Treasury month-end (%)"])}% |
| 10-year minus federal funds spread | {format_value(latest["10-year minus federal funds spread (%)"])} percentage points |
""".strip()


def recent_data_section(df):
    """Build a recent-observations Markdown table."""
    columns = [
        "date",
        "Federal funds rate (%)",
        "Annual inflation (%)",
        "Monthly payroll change (thousands)",
        "Unemployment rate (%)",
        "10-year Treasury average (%)",
        "10-year minus federal funds spread (%)",
    ]

    recent = df[columns].tail(12).copy()

    recent["date"] = recent["date"].dt.strftime(
        "%Y-%m"
    )

    recent = recent.rename(
        columns={
            "date": "Month",
            "Federal funds rate (%)": "Fed funds (%)",
            "Annual inflation (%)": "Inflation YoY (%)",
            "Monthly payroll change (thousands)": "Payroll change (thousands)",
            "Unemployment rate (%)": "Unemployment (%)",
            "10-year Treasury average (%)": "10Y Treasury (%)",
            "10-year minus federal funds spread (%)": "10Y-Fed funds spread",
        }
    )

    return (
        "## Recent observations\n\n"
        + recent.to_markdown(
            index=False,
            floatfmt=".2f",
        )
    )


def analysis_section(analysis):
    """Build the structured-analysis section."""
    if not analysis:
        return (
            "## Gemini analysis\n\n"
            "No structured Gemini analysis was found."
        )

    sections = [
        ("Facts", "facts"),
        ("Calculations", "calculations"),
        ("Interpretation", "interpretation"),
        (
            "Uncertainty and limitations",
            "uncertainty_and_limitations",
        ),
        (
            "Missing information",
            "missing_information",
        ),
    ]

    lines = ["## Gemini analysis", ""]

    for heading, key in sections:
        lines.append(f"### {heading}")
        lines.append("")

        for item in analysis.get(key, []):
            lines.append(f"- {item}")

        lines.append("")

    lines.append("### Caveat")
    lines.append("")
    lines.append(analysis.get("caveat", "No caveat provided."))

    return "\n".join(lines).strip()


def source_section(fed_metadata):
    """Build the official-source section."""
    if not fed_metadata:
        return (
            "## Official Fed context\n\n"
            "No Federal Reserve metadata was found."
        )

    return f"""
## Official Fed context

- Document: {fed_metadata.get("document", "N/A")}
- Source type: {fed_metadata.get("source_type", "N/A")}
- Source URL: {fed_metadata.get("source_url", "N/A")}
- Retrieved at UTC: {fed_metadata.get("retrieved_at_utc", "N/A")}
""".strip()


def build_report(
    df,
    analysis,
    validation_text,
    fed_metadata,
):
    """Build the complete Markdown report."""
    latest = df.tail(1).iloc[0]

    generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    date_start = df["date"].min().date()
    date_end = df["date"].max().date()

    validation_status = (
        "Validation report available."
        if validation_text
        else "Validation report not found."
    )

    report_parts = [
        "# Macro Research Report",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "## Scope",
        "",
        (
            "This report summarizes the project's "
            "FRED-based macroeconomic indicators, "
            "derived metrics, official Federal Reserve "
            "context, and structured Gemini analysis."
        ),
        "",
        f"Data coverage: {date_start} to {date_end}",
        f"Observations: {len(df)}",
        "",
        latest_observation_section(latest),
        "",
        recent_data_section(df),
        "",
        "## Validation",
        "",
        validation_status,
        (
            "See `validation_report.txt` for detailed "
            "missing-value, date, numeric, range, and "
            "staleness checks."
        ),
        "",
        source_section(fed_metadata),
        "",
        analysis_section(analysis),
        "",
        "## Limitations",
        "",
        "- FRED observations may be revised.",
        "- Monthly and daily source data were aligned using documented aggregation rules.",
        "- Derived metrics depend on the available sample and calculation definitions.",
        "- One monthly observation is insufficient to establish a trend.",
        "- Correlation does not prove causation.",
        "- This report is for research and education, not investment advice.",
    ]

    return "\n".join(report_parts)


def main():
    df = load_data()

    analysis = load_json_file(
        ANALYSIS_FILE
    )

    validation_text = load_text_file(
        VALIDATION_FILE
    )

    fed_metadata = load_json_file(
        FED_METADATA_FILE
    )

    report = build_report(
        df,
        analysis,
        validation_text,
        fed_metadata,
    )

    OUTPUT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(f"Saved: {OUTPUT_FILE}")
    print(
        f"Report characters: {len(report)}"
    )


if __name__ == "__main__":
    main()