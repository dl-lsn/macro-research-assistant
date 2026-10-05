import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

fred_api_key = os.getenv("FRED_API_KEY")

if not fred_api_key:
    raise RuntimeError("FRED_API_KEY was not found in .env")


url = "https://api.stlouisfed.org/fred/series/observations"

parameters = {
    "series_id": "DGS10",
    "api_key": fred_api_key,
    "file_type": "json",
}

response = requests.get(url, params=parameters)

print("HTTP status code:", response.status_code)

response.raise_for_status()


data = response.json()
observations = data["observations"]

df = pd.DataFrame(observations)

df["date"] = pd.to_datetime(df["date"])
df["yield_10y"] = pd.to_numeric(
    df["value"],
    errors="coerce",
)

df = df[["date", "yield_10y"]].dropna()
df = df.sort_values("date").reset_index(drop=True)


# Calculate daily changes in percentage points.
df["daily_change"] = df["yield_10y"].diff()


# Calculate the change from one year earlier.
df["change_12_months"] = (
    df["yield_10y"] - df["yield_10y"].shift(252)
)


print("\nLatest daily observations:")
print(df.tail(10).to_string(index=False))


# Create monthly average yields.
monthly_df = (
    df.set_index("date")
    .resample("MS")
    .agg(
        {
            "yield_10y": "mean",
            "daily_change": "mean",
        }
    )
    .reset_index()
)

monthly_df["monthly_change"] = (
    monthly_df["yield_10y"].diff()
)

monthly_df["change_12_months"] = (
    monthly_df["yield_10y"]
    - monthly_df["yield_10y"].shift(12)
)


print("\nLatest monthly observations:")
print(monthly_df.tail(10).to_string(index=False))


# Save the cleaned daily data.
df.to_csv(
    "treasury_clean.csv",
    index=False,
)

print("\nSaved data: treasury_clean.csv")


# Save the monthly summary.
monthly_df.to_csv(
    "treasury_monthly.csv",
    index=False,
)

print("Saved monthly data: treasury_monthly.csv")


# Create the chart.
plt.figure(figsize=(12, 6))

plt.plot(
    df["date"],
    df["yield_10y"],
    color="purple",
    label="10-year Treasury yield",
)

plt.title("U.S. 10-Year Treasury Yield")
plt.xlabel("Date")
plt.ylabel("Yield (%)")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    "treasury_chart.png",
    dpi=150,
    bbox_inches="tight",
)

print("Saved chart: treasury_chart.png")