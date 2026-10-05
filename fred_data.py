import os

import requests
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

fred_api_key = os.getenv("FRED_API_KEY")

if not fred_api_key:
    raise RuntimeError("FRED_API_KEY was not found in .env")

url = "https://api.stlouisfed.org/fred/series/observations"

parameters = {
    "series_id": "FEDFUNDS",
    "api_key": fred_api_key,
    "file_type": "json",
}

response = requests.get(url, params=parameters)

print("HTTP status code:", response.status_code)
data = response.json()

observations = data["observations"]

df = pd.DataFrame(observations)
df["date"] = pd.to_datetime(df["date"])
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df.sort_values("date").reset_index(drop=True)

#print("\nLatest observations:")
#print(df.tail(10)[["date", "value"]])

#print("\nMissing values:")
#print(df[["date", "value"]].isna().sum())

clean_df = df[["date", "value"]].dropna()

clean_df["change"] = clean_df["value"].diff()

clean_df.to_csv("fedfunds_clean.csv", index=False)

#print("\nSaved rows:", len(clean_df))

#print("\nSummary statistics:")
#print(clean_df["value"].describe())

print("\nLatest change:")
print(clean_df.tail(10)[["date", "value", "change"]])

plt.figure(figsize=(12, 6))

plt.plot(
    clean_df["date"],
    clean_df["value"],
    label="Federal funds rate",
)

plt.title("Federal Funds Rate Over Time")
plt.xlabel("Date")
plt.ylabel("Rate (%)")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("fedfunds_chart.png", dpi=150)

print("\nSaved chart: fedfunds_chart.png")