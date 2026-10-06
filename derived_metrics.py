from pathlib import Path

import pandas as pd


INPUT_FILE = Path("macro_context.csv")
OUTPUT_FILE = Path("macro_derived.csv")


def load_context_data():
    """Load the complete macroeconomic context table."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing required file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date").reset_index(drop=True)

    return df


def add_rate_changes(df):
    """Add changes in interest rates."""
    df["Federal funds rate change (percentage points)"] = (
        df["Federal funds rate (%)"].diff()
    )

    df["10-year Treasury change (percentage points)"] = (
        df["10-year Treasury average (%)"].diff()
    )

    df["Federal funds rate change YoY (percentage points)"] = (
        df["Federal funds rate (%)"]
        - df["Federal funds rate (%)"].shift(12)
    )

    df["10-year Treasury change YoY (percentage points)"] = (
        df["10-year Treasury average (%)"]
        - df["10-year Treasury average (%)"].shift(12)
    )

    return df


def add_term_spread(df):
    """Calculate the spread between the 10-year and federal funds rates."""
    df["10-year minus federal funds spread (%)"] = (
        df["10-year Treasury average (%)"]
        - df["Federal funds rate (%)"]
    )

    return df


def add_rolling_averages(df):
    """Calculate three-month rolling averages."""
    df["Annual inflation 3-month average (%)"] = (
        df["Annual inflation (%)"]
        .rolling(window=3, min_periods=3)
        .mean()
    )

    df["Unemployment 3-month average (%)"] = (
        df["Unemployment rate (%)"]
        .rolling(window=3, min_periods=3)
        .mean()
    )

    df["10-year Treasury 3-month average (%)"] = (
        df["10-year Treasury average (%)"]
        .rolling(window=3, min_periods=3)
        .mean()
    )

    return df


def add_z_scores(df):
    """Standardize selected indicators over the available sample."""
    columns = {
        "Annual inflation (%)": (
            "Annual inflation z-score"
        ),
        "Unemployment rate (%)": (
            "Unemployment rate z-score"
        ),
        "10-year Treasury average (%)": (
            "10-year Treasury z-score"
        ),
        "10-year minus federal funds spread (%)": (
            "Term spread z-score"
        ),
    }

    for source_column, output_column in columns.items():
        mean = df[source_column].mean()
        standard_deviation = df[source_column].std()

        df[output_column] = (
            (df[source_column] - mean)
            / standard_deviation
        )

    return df


def main():
    df = load_context_data()

    df = add_rate_changes(df)
    df = add_term_spread(df)
    df = add_rolling_averages(df)
    df = add_z_scores(df)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(f"Saved: {OUTPUT_FILE}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nLatest derived metrics:")
    print(df.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()