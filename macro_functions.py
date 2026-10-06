from pathlib import Path

import pandas as pd


def load_csv_file(file_path):
    """Load a CSV file and return a DataFrame."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return pd.read_csv(file_path)


def parse_date_column(df, column_name="date"):
    """Convert one DataFrame column to datetime."""
    if column_name not in df.columns:
        raise ValueError(
            f"Missing date column: {column_name}"
        )

    result = df.copy()

    result[column_name] = pd.to_datetime(
        result[column_name],
        errors="coerce",
    )

    invalid_dates = int(
        result[column_name].isna().sum()
    )

    if invalid_dates > 0:
        raise ValueError(
            f"{invalid_dates} invalid dates found "
            f"in column: {column_name}"
        )

    return result


def validate_required_columns(
    df,
    required_columns,
):
    """Check that all required columns exist."""
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )


def load_context_data(file_path="macro_context.csv"):
    """Load and validate the macro context table."""
    required_columns = [
        "date",
        "Federal funds rate (%)",
        "CPI index",
        "Monthly inflation (%)",
        "Annual inflation (%)",
        "Payrolls (thousands)",
        "Unemployment rate (%)",
        "Monthly payroll change (thousands)",
        "Payroll growth YoY (%)",
        "10-year Treasury average (%)",
        "10-year Treasury month-end (%)",
    ]

    df = load_csv_file(file_path)

    validate_required_columns(
        df,
        required_columns,
    )

    df = parse_date_column(df)

    df = df.sort_values("date")
    df = df.reset_index(drop=True)

    return df


def load_derived_data(file_path="macro_derived.csv"):
    """Load and validate the derived metrics table."""
    df = load_csv_file(file_path)

    if "date" not in df.columns:
        raise ValueError(
            "Derived data must contain a date column"
        )

    df = parse_date_column(df)

    df = df.sort_values("date")
    df = df.reset_index(drop=True)

    return df


def save_dataframe(df, file_path):
    """Save a DataFrame to CSV."""
    file_path = Path(file_path)

    df.to_csv(
        file_path,
        index=False,
    )

    print(f"Saved: {file_path}")