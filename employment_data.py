import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

fred_api_key = os.getenv("FRED_API_KEY")

if not fred_api_key:
    raise RuntimeError("FRED_API_KEY was not found in .env")


def get_fred_series(series_id, column_name):
    """Download one monthly series from FRED."""
    url = "https://api.stlouisfed.org/fred/series/observations"

    parameters = {
        "series_id": series_id,
        "api_key": fred_api_key,
        "file_type": "json",
    }

    response = requests.get(url, params=parameters)
    response.raise_for_status()

    observations = response.json()["observations"]

    df = pd.DataFrame(observations)

    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df[["date", "value"]].dropna()
    df = df.rename(columns={"value": column_name})

    return df


# Retrieve payroll and unemployment data.
payrolls_df = get_fred_series(
    "PAYEMS",
    "payrolls_thousands",
)

unemployment_df = get_fred_series(
    "UNRATE",
    "unemployment_rate",
)


# Combine the two monthly datasets.
employment_df = pd.merge(
    payrolls_df,
    unemployment_df,
    on="date",
    how="inner",
)

employment_df = employment_df.sort_values("date")
employment_df = employment_df.reset_index(drop=True)


# Calculate monthly payroll changes.
employment_df["payroll_change"] = (
    employment_df["payrolls_thousands"].diff()
)


# Calculate year-over-year payroll growth.
employment_df["payroll_growth_yoy"] = (
    employment_df["payrolls_thousands"]
    .pct_change(periods=12)
    * 100
)


print("\nLatest employment observations:")
print(employment_df.tail(12).to_string(index=False))


print("\nLatest labor-market observation:")
print(
    employment_df.tail(1).to_string(index=False)
)


# Save the cleaned dataset.
employment_df.to_csv(
    "employment_clean.csv",
    index=False,
)

print("\nSaved data: employment_clean.csv")


# Create a two-panel chart.
fig, axes = plt.subplots(
    2,
    1,
    figsize=(12, 9),
    sharex=True,
)


axes[0].plot(
    employment_df["date"],
    employment_df["payrolls_thousands"],
    color="darkgreen",
    label="Total nonfarm payrolls",
)

axes[0].set_title("Total Nonfarm Payroll Employment")
axes[0].set_ylabel("Thousands of people")
axes[0].grid(True)
axes[0].legend()


axes[1].plot(
    employment_df["date"],
    employment_df["unemployment_rate"],
    color="darkorange",
    label="Unemployment rate",
)

axes[1].set_title("Unemployment Rate")
axes[1].set_xlabel("Date")
axes[1].set_ylabel("Percent")
axes[1].grid(True)
axes[1].legend()


fig.suptitle(
    "U.S. Labor Market: Payrolls and Unemployment",
    fontsize=16,
)

fig.tight_layout()

fig.savefig(
    "employment_chart.png",
    dpi=150,
    bbox_inches="tight",
)

print("Saved chart: employment_chart.png")