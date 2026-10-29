"""MEMBER 3 - spatial / temporal relationships (integration lead)."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def rq1(df):
    d = df.groupby(["zip", "borough"], as_index=False)[["housing_metric", "transport_metric"]].sum()
    return px.scatter(d, x="housing_metric", y="transport_metric", color="borough",
                      hover_name="zip", trendline="ols",
                      labels={"housing_metric": "Housing filings (total)",
                              "transport_metric": "Crashes (total)"})

def rq2(df):
    """Lag correlation: do filings this month relate to crashes N months later?"""
    m = df.groupby("year_month")[["housing_metric", "transport_metric"]].sum().sort_index()
    lags = list(range(0, 7))
    corr = [m["housing_metric"].corr(m["transport_metric"].shift(-k)) for k in lags]
    return go.Figure(go.Bar(x=lags, y=corr)).update_layout(
        xaxis_title="Lag (months): crashes N months after filings",
        yaxis_title="Correlation")

CHARTS = [
    ("M3-RQ1: [replace] Do ZIPs with more filings also have more crashes?", rq1),
    ("M3-RQ2: [replace] Do crashes follow construction filings with a time lag?", rq2),
]
