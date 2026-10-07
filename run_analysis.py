import argparse
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = "macro_derived.csv"
DEFAULT_OUTPUT = "cli_analysis.csv"


def parse_date(value):
    """Convert a YYYY-MM-DD string into a pandas timestamp."""
    try:
        return pd.Timestamp(value)
    except Exception as error:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. "
            "Use YYYY-MM-DD."
        ) from error


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Filter and inspect the macroeconomic "
            "derived dataset."
        )
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=(
            "Input CSV file. "
            f"Default: {DEFAULT_INPUT}"
        ),
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        help=(
            "Keep observations on or after "
            "this date. Format: YYYY-MM-DD."
        ),
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        help=(
            "Keep observations on or before "
            "this date. Format: YYYY-MM-DD."
        ),
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=(
            "Output CSV file. "
            f"Default: {DEFAULT_OUTPUT}"
        ),
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Keep only the latest observation.",
    )

    return parser


def load_data(input_file):
    """Load and prepare the input dataset."""
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    if "date" not in df.columns:
        raise ValueError(
            "The input file must contain a date column."
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    if df["date"].isna().any():
        raise ValueError(
            "The input file contains invalid dates."
        )

    return df.sort_values(
        "date"
    ).reset_index(drop=True)


def apply_filters(
    df,
    start_date=None,
    end_date=None,
    latest=False,
):
    """Apply date and latest-observation filters."""
    result = df.copy()

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise ValueError(
            "start-date cannot be later than end-date."
        )

    if start_date is not None:
        result = result[
            result["date"] >= start_date
        ]

    if end_date is not None:
        result = result[
            result["date"] <= end_date
        ]

    if latest:
        if result.empty:
            raise ValueError(
                "No observations remain after filtering."
            )

        result = result.tail(1)

    return result.reset_index(drop=True)


def main():
    parser = build_parser()
    args = parser.parse_args()

    df = load_data(args.input)

    filtered_df = apply_filters(
        df,
        start_date=args.start_date,
        end_date=args.end_date,
        latest=args.latest,
    )

    filtered_df.to_csv(
        args.output,
        index=False,
    )

    print(f"Saved: {args.output}")
    print(f"Rows returned: {len(filtered_df)}")

    if not filtered_df.empty:
        print(
            "Date range: "
            f"{filtered_df['date'].min().date()} "
            f"to "
            f"{filtered_df['date'].max().date()}"
        )

        print("\nLatest result:")
        print(
            filtered_df.tail(1).to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()