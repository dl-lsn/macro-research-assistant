from pathlib import Path

import pandas as pd


INPUT_FILE = Path("frequency_aligned.csv")
OUTPUT_FILE = Path("macro_context.csv")
LATEST_FILE = Path("macro_context_latest.txt")


def load_aligned_data():
    """Load the complete frequency-aligned dataset."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing required file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "month",
        "fed_funds_rate",
        "cpi_index",
        "monthly_inflation",
        "annual_inflation",
        "payrolls_thousands",
        "unemployment_rate",
        "payroll_change",
        "payroll_growth_yoy",
        "treasury_10y_average",
        "treasury_10y_end",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns: "
            + ", ".join(missing_columns)
        )

    df["month"] = pd.to_datetime(df["month"])

    return df[required_columns].copy()


def build_context_table(df):
    """Rename columns for a readable research context table."""
    context_df = df.rename(
        columns={
            "month": "date",
            "fed_funds_rate": "Federal funds rate (%)",
            "cpi_index": "CPI index",
            "monthly_inflation": "Monthly inflation (%)",
            "annual_inflation": "Annual inflation (%)",
            "payrolls_thousands": (
                "Payrolls (thousands)"
            ),
            "unemployment_rate": (
                "Unemployment rate (%)"
            ),
            "payroll_change": (
                "Monthly payroll change (thousands)"
            ),
            "payroll_growth_yoy": (
                "Payroll growth YoY (%)"
            ),
            "treasury_10y_average": (
                "10-year Treasury average (%)"
            ),
            "treasury_10y_end": (
                "10-year Treasury month-end (%)"
            ),
        }
    )

    return context_df.sort_values("date").reset_index(
        drop=True
    )


def write_latest_summary(context_df):
    """Save the latest complete macroeconomic observation."""
    latest_row = context_df.tail(1).T

    summary_lines = [
        "Latest complete macroeconomic observation",
        "=========================================",
        "",
        latest_row.to_string(
            header=False,
            index=True,
        ),
        "",
        "All indicators are available for this date.",
    ]

    LATEST_FILE.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )


def main():
    aligned_df = load_aligned_data()
    context_df = build_context_table(aligned_df)

    context_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    write_latest_summary(context_df)

    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {LATEST_FILE}")
    print(f"Rows: {len(context_df)}")
    print(
        f"Date range: {context_df['date'].min()} "
        f"to {context_df['date'].max()}"
    )
    print("\nLatest context row:")
    print(context_df.tail(1).to_string(index=False))


if __name__ == "__main__":
    main()