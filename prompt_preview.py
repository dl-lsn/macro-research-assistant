import pandas as pd

from prompt_builder import build_macro_prompt


def main():
    df = pd.read_csv("macro_derived.csv")

    df["date"] = pd.to_datetime(
        df["date"]
    )

    latest_row = df.sort_values(
        "date"
    ).tail(1).iloc[0]

    prompt = build_macro_prompt(
        latest_row
    )

    print(prompt)


if __name__ == "__main__":
    main()