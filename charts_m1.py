"""MEMBER 1 - housing-focused research questions.
Each chart = a function f(df) -> plotly Figure. df already has
`housing_metric` and `transport_metric` columns (see data_layer.apply_filters).
Add your function to CHARTS as (research question, function)."""
import plotly.express as px

def rq1(df):
    d = df.groupby(["year_month", "borough"], as_index=False)["housing_metric"].sum()
    return px.line(d, x="year_month", y="housing_metric", color="borough",
                   labels={"housing_metric": "Job filings", "year_month": "Month"})

def rq2(df):
    d = df.groupby("borough", as_index=False)[["housing_metric", "transport_metric"]].sum()
    d["crashes_per_filing"] = d["transport_metric"] / d["housing_metric"].clip(lower=1)
    return px.bar(d, x="borough", y="crashes_per_filing",
                  labels={"crashes_per_filing": "Crashes per filing"})

CHARTS = [
    ("M1-RQ1: [replace] How has construction activity changed over time by borough?", rq1),
    ("M1-RQ2: [replace] Which boroughs have the most crashes per construction filing?", rq2),
]
