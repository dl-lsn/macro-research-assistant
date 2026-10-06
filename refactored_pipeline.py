from macro_functions import (
    load_context_data,
    load_derived_data,
    save_dataframe,
)


def main():
    context_df = load_context_data(
        "macro_context.csv"
    )

    derived_df = load_derived_data(
        "macro_derived.csv"
    )

    save_dataframe(
        context_df,
        "refactored_context.csv",
    )

    save_dataframe(
        derived_df,
        "refactored_derived.csv",
    )

    print(
        f"Context rows: {len(context_df)}"
    )

    print(
        f"Derived rows: {len(derived_df)}"
    )

    print(
        "Context date range: "
        f"{context_df['date'].min().date()} "
        f"to "
        f"{context_df['date'].max().date()}"
    )

    print(
        "Derived date range: "
        f"{derived_df['date'].min().date()} "
        f"to "
        f"{derived_df['date'].max().date()}"
    )


if __name__ == "__main__":
    main()