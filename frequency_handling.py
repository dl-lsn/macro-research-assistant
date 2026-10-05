from pathlib import Path

import pandas as pd


DATA_FILES = {
    "fed_funds": Path("fedfunds_clean.csv"),
    "cpi": Path("cpi_clean.csv"),
    "employment": Path("employment_clean.csv"),
    "treasury": Path("treasury_clean.csv"),
}


def load_csv(path):
    """Load a CSV and standardize its date column."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    df = pd.read_csv(path)

    if "date" not in df.columns:
        raise ValueError(f"{path} does not contain a date column")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    return df


def monthly_key(df):
    """Create a common month-start date."""
    result = df.copy()
    result["month"] = (
        result["date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    return result


def prepare_fed_funds(df):
    """Convert federal funds observations to monthly averages."""
    df = monthly_key(df)

    value_column = "value"

    monthly = (
        df.groupby("month", as_index=False)[value_column]
        .mean()
        .rename(
            columns={
                value_column: "fed_funds_rate"
            }
        )
    )

    return monthly


def prepare_cpi(df):
    """Keep the final CPI observation for each month."""
    df = monthly_key(df)

    df = df.sort_values("date")

    monthly = (
        df.groupby("month", as_index=False)
        .tail(1)
        .rename(
            columns={
                "value": "cpi_index",
                "monthly_inflation": "monthly_inflation",
                "annual_inflation": "annual_inflation",
            }
        )
    )

    columns = [
        "month",
        "cpi_index",
        "monthly_inflation",
        "annual_inflation",
    ]

    return monthly[columns].reset_index(drop=True)


def prepare_employment(df):
    """Keep the latest labor-market observation for each month."""
    df = monthly_key(df)

    df = df.sort_values("date")

    monthly = (
        df.groupby("month", as_index=False)
        .tail(1)
    )

    columns = [
        "month",
        "payrolls_thousands",
        "unemployment_rate",
        "payroll_change",
        "payroll_growth_yoy",
    ]

    available_columns = [
        column for column in columns if column in monthly.columns
    ]

    return monthly[available_columns].reset_index(drop=True)


def prepare_treasury(df):
    """Convert daily 10-year Treasury yields to monthly averages."""
    df = monthly_key(df)

    value_column = "yield_10y"

    monthly = (
        df.groupby("month", as_index=False)[value_column]
        .agg(
            treasury_10y_average="mean",
            treasury_10y_end="last",
        )
    )

    return monthly


def main():
    fed_funds_df = load_csv(DATA_FILES["fed_funds"])
    cpi_df = load_csv(DATA_FILES["cpi"])
    employment_df = load_csv(DATA_FILES["employment"])
    treasury_df = load_csv(DATA_FILES["treasury"])

    fed_monthly = prepare_fed_funds(fed_funds_df)
    cpi_monthly = prepare_cpi(cpi_df)
    employment_monthly = prepare_employment(employment_df)
    treasury_monthly = prepare_treasury(treasury_df)

    aligned_df = (
        fed_monthly
        .merge(cpi_monthly, on="month", how="outer")
        .merge(employment_monthly, on="month", how="outer")
        .merge(treasury_monthly, on="month", how="outer")
        .sort_values("month")
        .reset_index(drop=True)
    )

    rows_before = len(aligned_df)

    aligned_df = (
        aligned_df
        .dropna()
        .reset_index(drop=True)
    )

    rows_after = len(aligned_df)
    rows_removed = rows_before - rows_after

    aligned_df.to_csv(
        "frequency_aligned.csv",
        index=False,
    )

    summary_lines = [
        "Frequency handling summary",
        "==========================",
        "",
        "Common date key: month-start timestamp",
        "",
        "Aggregation rules:",
        "- Federal funds rate: monthly average",
        "- CPI: last available observation in each month",
        "- Payrolls and unemployment: latest monthly observation",
        "- 10-year Treasury yield: monthly average and month-end value",
        "",
        "Input frequencies:",
        f"- Federal funds rows: {len(fed_funds_df)}",
        f"- CPI rows: {len(cpi_df)}",
        f"- Employment rows: {len(employment_df)}",
        f"- Treasury rows: {len(treasury_df)}",
        "",
        f"Rows before filtering: {rows_before}",
        f"Rows after filtering: {rows_after}",
        f"Rows removed: {rows_removed}",
        "",
        f"Complete date range: {aligned_df['month'].min()} "
        f"to {aligned_df['month'].max()}",
        "",
        "Missing values after filtering:",
        aligned_df.isna().sum().to_string(),
    ]

    Path("frequency_summary.txt").write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print("Saved: frequency_aligned.csv")
    print("Saved: frequency_summary.txt")
    print(f"Rows before filtering: {rows_before}")
    print(f"Rows after filtering: {rows_after}")
    print(f"Rows removed: {rows_removed}")
    print("\nLatest complete observations:")
    print(aligned_df.tail(12).to_string(index=False))


if __name__ == "__main__":
    main()