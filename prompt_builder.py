import pandas as pd


def format_number(value, decimals=2):
    """Format a number for inclusion in a prompt."""
    if pd.isna(value):
        return "missing"

    return f"{value:.{decimals}f}"


def build_macro_prompt(latest_row):
    """Build a structured prompt from one macro observation."""
    date = latest_row["date"]

    context = {
        "Federal funds rate (%)": format_number(
            latest_row["Federal funds rate (%)"]
        ),
        "CPI index": format_number(
            latest_row["CPI index"]
        ),
        "Monthly inflation (%)": format_number(
            latest_row["Monthly inflation (%)"]
        ),
        "Annual inflation (%)": format_number(
            latest_row["Annual inflation (%)"]
        ),
        "Payrolls (thousands)": format_number(
            latest_row["Payrolls (thousands)"],
            decimals=0,
        ),
        "Unemployment rate (%)": format_number(
            latest_row["Unemployment rate (%)"]
        ),
        "Monthly payroll change (thousands)": format_number(
            latest_row[
                "Monthly payroll change (thousands)"
            ],
            decimals=0,
        ),
        "Payroll growth YoY (%)": format_number(
            latest_row["Payroll growth YoY (%)"]
        ),
        "10-year Treasury average (%)": format_number(
            latest_row[
                "10-year Treasury average (%)"
            ]
        ),
        "10-year Treasury month-end (%)": format_number(
            latest_row[
                "10-year Treasury month-end (%)"
            ]
        ),
    }

    return f"""
<role>
You are a careful macroeconomic research assistant.
</role>

<task>
Analyze the latest complete monthly U.S. macroeconomic
observation and explain what it indicates.
</task>

<context>
Observation date: {date}

Federal funds rate: {context["Federal funds rate (%)"]}%
CPI index: {context["CPI index"]}
Monthly inflation: {context["Monthly inflation (%)"]}%
Annual inflation: {context["Annual inflation (%)"]}%
Payrolls: {context["Payrolls (thousands)"]} thousand
Unemployment rate: {context["Unemployment rate (%)"]}%
Monthly payroll change: {
    context["Monthly payroll change (thousands)"]
} thousand
Payroll growth year-over-year: {
    context["Payroll growth YoY (%)"]
}%
10-year Treasury monthly average: {
    context["10-year Treasury average (%)"]
}%
10-year Treasury month-end: {
    context["10-year Treasury month-end (%)"]
}%
</context>

<definitions>
- Inflation percentages are calculated from CPI data.
- Payrolls are measured in thousands of people.
- Interest rates and yields are expressed in percent.
- The 10-year Treasury average is the monthly average yield.
- The 10-year Treasury month-end value is the final available
  observation in the month.
</definitions>

<instructions>
Separate your response into these sections:

1. Facts
   Report only what the supplied data shows.

2. Calculations
   Explain the changes and relationships visible in the data.

3. Interpretation
   Offer cautious economic interpretations.

4. Uncertainty and limitations
   Identify what cannot be concluded from one observation.

5. Missing information
   State which additional data would improve the analysis.

Do not invent data.
Do not introduce GDP or indicators not supplied here.
Do not claim causation from correlation.
Do not present interpretation as fact.
Do not give investment advice.
</instructions>

<output_format>
Use Markdown headings.
Use concise paragraphs and bullet points.
Keep the response below 500 words.
End with a two-sentence caveat explaining that one monthly
observation is insufficient to establish a trend.
</output_format>

Based on the supplied data, provide the analysis now.
""".strip()