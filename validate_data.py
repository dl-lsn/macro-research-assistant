from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("macro_derived.csv")
REPORT_FILE = Path("validation_report.txt")


REQUIRED_COLUMNS = [
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


RATE_COLUMNS = [
    "Federal funds rate (%)",
    "Annual inflation (%)",
    "Unemployment rate (%)",
    "10-year Treasury average (%)",
    "10-year Treasury month-end (%)",
]


EXPECTED_MISSING_RULES = {
    # diff(periods=1) compares each row with the previous
    # row. The first row has no previous observation,
    # so exactly 1 value is expected to be missing.
    "Federal funds rate change (percentage points)": {
        "expected_count": 1,
        "reason": (
            "diff(periods=1) needs one previous row; "
            "the first row has no prior month."
        ),
    },
    "10-year Treasury change (percentage points)": {
        "expected_count": 1,
        "reason": (
            "diff(periods=1) needs one previous row; "
            "the first row has no prior month."
        ),
    },

    # shift(periods=12) compares each month with the
    # same month one year earlier. The first 12 rows
    # have no 12-month-earlier observation.
    "Federal funds rate change YoY (percentage points)": {
        "expected_count": 12,
        "reason": (
            "shift(periods=12) requires 12 earlier "
            "monthly observations; the first 12 rows "
            "have no one-year comparison."
        ),
    },
    "10-year Treasury change YoY (percentage points)": {
        "expected_count": 12,
        "reason": (
            "shift(periods=12) requires 12 earlier "
            "monthly observations; the first 12 rows "
            "have no one-year comparison."
        ),
    },

    # rolling(window=3, min_periods=3) requires three
    # observations. The first two rows do not yet
    # contain a complete three-month window.
    "Annual inflation 3-month average (%)": {
        "expected_count": 2,
        "reason": (
            "rolling(window=3, min_periods=3) requires "
            "three observations; the first 2 rows do "
            "not contain a complete window."
        ),
    },
    "Unemployment 3-month average (%)": {
        "expected_count": 2,
        "reason": (
            "rolling(window=3, min_periods=3) requires "
            "three observations; the first 2 rows do "
            "not contain a complete window."
        ),
    },
    "10-year Treasury 3-month average (%)": {
        "expected_count": 2,
        "reason": (
            "rolling(window=3, min_periods=3) requires "
            "three observations; the first 2 rows do "
            "not contain a complete window."
        ),
    },
}


def load_data():
    """Load and prepare the derived macroeconomic data."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing required file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    return df


def validate_dates(df):
    """Check missing, duplicate, and unsorted dates."""
    return {
        "missing_dates": int(
            df["date"].isna().sum()
        ),
        "duplicate_dates": int(
            df["date"].duplicated().sum()
        ),
        "dates_sorted": bool(
            df["date"].is_monotonic_increasing
        ),
    }


def calculate_expected_missing(df):
    """Calculate expected missing values from documented rules."""
    expected = {}

    for column, rule in EXPECTED_MISSING_RULES.items():
        expected_count = rule["expected_count"]
        reason = rule["reason"]

        if column not in df.columns:
            expected[column] = {
                "expected": expected_count,
                "actual": None,
                "matches": False,
                "reason": reason,
            }
            continue

        actual_count = int(
            df[column].isna().sum()
        )

        expected[column] = {
            "expected": expected_count,
            "actual": actual_count,
            "matches": (
                actual_count == expected_count
            ),
            "reason": reason,
        }

    return expected


def validate_missing_values(df, expected_missing):
    """Separate expected from unexpected missing values."""
    missing_by_column = df.isna().sum()
    unexpected_missing = {}

    for column, count in missing_by_column.items():
        if count == 0:
            continue

        expected_count = expected_missing.get(
            column,
            {},
        ).get("expected", 0)

        if expected_count is None:
            expected_count = 0

        if count != expected_count:
            unexpected_missing[column] = {
                "actual": int(count),
                "expected": int(expected_count),
            }

    return missing_by_column, unexpected_missing


def validate_numeric_values(df):
    """Check for infinite and non-numeric values."""
    numeric_df = df.select_dtypes(
        include="number"
    )

    infinite_values = int(
        numeric_df.isin(
            [float("inf"), float("-inf")]
        )
        .sum()
        .sum()
    )

    non_numeric_columns = []

    for column in REQUIRED_COLUMNS:
        if column == "date":
            continue

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid_count = int(
            converted.isna().sum()
            - df[column].isna().sum()
        )

        if invalid_count > 0:
            non_numeric_columns.append(
                f"{column}: {invalid_count}"
            )

    return {
        "infinite_values": infinite_values,
        "non_numeric_columns": (
            non_numeric_columns
        ),
    }


def validate_rate_ranges(df):
    """Identify implausible values in percentage columns."""
    range_warnings = []

    for column in RATE_COLUMNS:
        values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if values.dropna().empty:
            continue

        minimum = values.min()
        maximum = values.max()

        if column == "Unemployment rate (%)":
            invalid_range = (
                minimum < 0
                or maximum > 100
            )
        else:
            invalid_range = (
                minimum < -100
                or maximum > 100
            )

        if invalid_range:
            range_warnings.append(
                f"{column}: "
                f"range {minimum} to {maximum}"
            )

    return range_warnings


def validate_staleness(df):
    """Report the latest observation and its age."""
    latest_date = df["date"].max()
    today = pd.Timestamp.now().normalize()

    if pd.isna(latest_date):
        return {
            "latest_date": "Unavailable",
            "days_since_latest": "Unavailable",
        }

    days_since_latest = (
        today - latest_date
    ).days

    return {
        "latest_date": str(
            latest_date.date()
        ),
        "days_since_latest": (
            days_since_latest
        ),
    }


def create_report(
    df,
    date_checks,
    expected_missing,
    missing_by_column,
    unexpected_missing,
    numeric_checks,
    range_warnings,
    staleness,
):
    """Create a plain-text validation report."""
    expected_lines = []

    for column, result in expected_missing.items():
        expected_lines.append(
            f"{column}: "
            f"expected={result['expected']}, "
            f"actual={result['actual']}, "
            f"matches={result['matches']}\n"
            f"  Reason: {result['reason']}"
        )

    unexpected_lines = []

    if unexpected_missing:
        for column, result in (
            unexpected_missing.items()
        ):
            unexpected_lines.append(
                f"{column}: "
                f"actual={result['actual']}, "
                f"expected={result['expected']}"
            )
    else:
        unexpected_lines.append("None")

    report_lines = [
        "Macroeconomic Data Validation Report",
        "====================================",
        "",
        "Validation time UTC: "
        f"{datetime.now(timezone.utc).isoformat()}",
        f"Input file: {INPUT_FILE}",
        f"Rows: {len(df)}",
        f"Columns: {len(df.columns)}",
        "",
        "Date checks",
        "-----------",
        "Missing dates: "
        f"{date_checks['missing_dates']}",
        "Duplicate dates: "
        f"{date_checks['duplicate_dates']}",
        "Dates sorted: "
        f"{date_checks['dates_sorted']}",
        "",
        "Expected missing values",
        "-----------------------",
        "\n".join(expected_lines),
        "",
        "Actual missing values by column",
        "--------------------------------",
        missing_by_column.to_string(),
        "",
        "Unexpected missing values",
        "-------------------------",
        "\n".join(unexpected_lines),
        "",
        "Numeric checks",
        "--------------",
        "Infinite values: "
        f"{numeric_checks['infinite_values']}",
        "Non-numeric values:",
        (
            "\n".join(
                numeric_checks[
                    "non_numeric_columns"
                ]
            )
            if numeric_checks[
                "non_numeric_columns"
            ]
            else "None"
        ),
        "",
        "Range checks",
        "------------",
        (
            "\n".join(range_warnings)
            if range_warnings
            else "No range warnings"
        ),
        "",
        "Staleness check",
        "---------------",
        "Latest observation: "
        f"{staleness['latest_date']}",
        "Days since latest observation: "
        f"{staleness['days_since_latest']}",
        "",
        "Descriptive statistics",
        "----------------------",
        df.describe(
            include="number"
        ).to_string(),
    ]

    REPORT_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


def main():
    df = load_data()

    date_checks = validate_dates(df)

    expected_missing = (
        calculate_expected_missing(df)
    )

    (
        missing_by_column,
        unexpected_missing,
    ) = validate_missing_values(
        df,
        expected_missing,
    )

    numeric_checks = (
        validate_numeric_values(df)
    )

    range_warnings = validate_rate_ranges(df)
    staleness = validate_staleness(df)

    create_report(
        df,
        date_checks,
        expected_missing,
        missing_by_column,
        unexpected_missing,
        numeric_checks,
        range_warnings,
        staleness,
    )

    print(f"Saved: {REPORT_FILE}")
    print(f"Rows checked: {len(df)}")
    print(
        "Unexpected missing values: "
        f"{len(unexpected_missing)}"
    )
    print(
        "Range warnings: "
        f"{len(range_warnings)}"
    )

    if unexpected_missing:
        print(
            "\nUnexpected missing values detected:"
        )

        for column, result in (
            unexpected_missing.items()
        ):
            print(
                f"- {column}: "
                f"{result['actual']} actual, "
                f"{result['expected']} expected"
            )
    else:
        print(
            "\nAll missing values match the "
            "expected calculation rules."
        )


if __name__ == "__main__":
    main()