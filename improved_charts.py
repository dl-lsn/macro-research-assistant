from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


INPUT_FILE = Path("macro_derived.csv")
OUTPUT_FILE = Path("macro_dashboard.png")


def load_data():
    """Load and prepare the derived macroeconomic data."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing required file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    if "date" not in df.columns:
        raise ValueError(
            "The dataset must contain a date column."
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = df.dropna(subset=["date"])
    df = df.sort_values("date")
    df = df.reset_index(drop=True)

    return df


def configure_date_axis(axis):
    """Apply consistent date formatting."""
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(
        locator
    )

    axis.xaxis.set_major_locator(locator)
    axis.xaxis.set_major_formatter(formatter)

    axis.grid(
        True,
        linestyle="--",
        alpha=0.35,
    )


def plot_dashboard(df):
    """Create and save the multi-panel dashboard."""
    fig, axes = plt.subplots(
        4,
        1,
        figsize=(14, 14),
        sharex=True,
    )

    fig.suptitle(
        "U.S. Macroeconomic Dashboard",
        fontsize=18,
        fontweight="bold",
    )

    # Panel 1: Inflation.
    axes[0].plot(
        df["date"],
        df["Annual inflation (%)"],
        color="firebrick",
        linewidth=2,
        label="Annual inflation",
    )

    axes[0].plot(
        df["date"],
        df["Annual inflation 3-month average (%)"],
        color="darkorange",
        linewidth=1.8,
        label="3-month average",
    )

    axes[0].axhline(
        y=2,
        color="black",
        linestyle=":",
        linewidth=1.5,
        label="2% reference",
    )

    axes[0].set_title("Inflation")
    axes[0].set_ylabel("Percent")
    axes[0].legend(loc="upper left")

    # Panel 2: Labor market.
    axes[1].plot(
        df["date"],
        df["Unemployment rate (%)"],
        color="navy",
        linewidth=2,
        label="Unemployment rate",
    )

    axes[1].set_title("Unemployment and Payroll Changes")
    axes[1].set_ylabel("Unemployment (%)")
    axes[1].legend(loc="upper left")

    payroll_axis = axes[1].twinx()

    payroll_axis.bar(
        df["date"],
        df["Monthly payroll change (thousands)"],
        width=20,
        alpha=0.25,
        color="seagreen",
        label="Monthly payroll change",
    )

    payroll_axis.set_ylabel(
        "Payroll change (thousands)"
    )

    # Combine legends from both axes.
    labor_lines, labor_labels = (
        axes[1].get_legend_handles_labels()
    )

    payroll_lines, payroll_labels = (
        payroll_axis.get_legend_handles_labels()
    )

    axes[1].legend(
        labor_lines + payroll_lines,
        labor_labels + payroll_labels,
        loc="upper left",
    )

    # Panel 3: Interest rates.
    axes[2].plot(
        df["date"],
        df["Federal funds rate (%)"],
        color="purple",
        linewidth=2,
        label="Federal funds rate",
    )

    axes[2].plot(
        df["date"],
        df["10-year Treasury average (%)"],
        color="teal",
        linewidth=2,
        label="10-year Treasury average",
    )

    axes[2].set_title("Short- and Long-Term Interest Rates")
    axes[2].set_ylabel("Percent")
    axes[2].legend(loc="upper left")

    # Panel 4: Term spread.
    axes[3].plot(
        df["date"],
        df["10-year minus federal funds spread (%)"],
        color="darkgreen",
        linewidth=2,
        label="10-year minus federal funds",
    )

    axes[3].axhline(
        y=0,
        color="black",
        linestyle=":",
        linewidth=1.5,
    )

    axes[3].set_title("10-Year Treasury Minus Federal Funds Rate")
    axes[3].set_ylabel("Percentage points")
    axes[3].set_xlabel("Date")
    axes[3].legend(loc="upper left")

    for axis in axes:
        configure_date_axis(axis)

    fig.text(
        0.01,
        0.01,
        (
            "Sources: FRED series used by the project. "
            "Values may be revised. "
            "The chart is descriptive and does not establish causation."
        ),
        fontsize=9,
    )

    fig.tight_layout(
        rect=[0, 0.03, 1, 0.96]
    )

    fig.savefig(
        OUTPUT_FILE,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def main():
    df = load_data()

    plot_dashboard(df)

    print(f"Saved: {OUTPUT_FILE}")
    print(f"Rows plotted: {len(df)}")
    print(
        f"Date range: {df['date'].min().date()} "
        f"to {df['date'].max().date()}"
    )


if __name__ == "__main__":
    main()