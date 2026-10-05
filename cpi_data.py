import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv


# Load the FRED API key from the local .env file.
load_dotenv()

fred_api_key = os.getenv("FRED_API_KEY")

if not fred_api_key:
    raise RuntimeError("FRED_API_KEY was not found in .env")


# Request the seasonally adjusted CPI series from FRED.
url = "https://api.stlouisfed.org/fred/series/observations"

parameters = {
    "series_id": "CPIAUCSL",
    "api_key": fred_api_key,
    "file_type": "json",
}

response = requests.get(url, params=parameters)

print("HTTP status code:", response.status_code)

response.raise_for_status()


# Convert the observations into a pandas DataFrame.
data = response.json()
observations = data["observations"]

df = pd.DataFrame(observations)

df["date"] = pd.to_datetime(df["date"])
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df[["date", "value"]].dropna()
df = df.sort_values("date").reset_index(drop=True)


# Calculate inflation rates.
df["monthly_inflation"] = df["value"].pct_change() * 100
df["annual_inflation"] = df["value"].pct_change(periods=12) * 100


print("\nLatest CPI observations:")
print(df.tail(10))

print("\nLatest inflation measures:")
print(
    df.tail(1)[
        ["date", "value", "monthly_inflation", "annual_inflation"]
    ]
)


# Save the cleaned data.
df.to_csv("cpi_clean.csv", index=False)

print("\nSaved data: cpi_clean.csv")


# Create a chart of the CPI index.
plt.figure(figsize=(12, 6))

plt.plot(
    df["date"],
    df["value"],
    label="CPI index",
)

plt.title("Consumer Price Index for All Urban Consumers")
plt.xlabel("Date")
plt.ylabel("Index level")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("cpi_chart.png", dpi=150)

print("Saved chart: cpi_chart.png")