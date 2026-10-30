"""MEMBER 3 - spatial / temporal relationships (integration lead).

RQ1  Which ZIP codes are hotspots in BOTH domains?  (percentile quadrant)
RQ2  Within the same ZIP, do months with unusually many filings come before months with unusually many crashes?
     (lag correlation on ZIP- and month-adjusted data, so ZIP size and seasonality do not drive the result)
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

HOT_Q = 0.75      # "high" = top quarter of ZIP codes
MAX_LAG = 6       # months


# ---------------------------------------------------------------- RQ1
def zip_summary(df):
    """One row per ZIP: totals, percentile rank in each domain, and a both-high flag."""
    d = df.groupby(["zip", "borough"], as_index=False)[["housing_metric", "transport_metric"]].sum()
    d["housing_pct"] = d["housing_metric"].rank(pct=True)
    d["transport_pct"] = d["transport_metric"].rank(pct=True)
    d["hotspot"] = (d["housing_pct"] >= HOT_Q) & (d["transport_pct"] >= HOT_Q)
    return d


def rq1(df):
    d = zip_summary(df)
    if d.empty:
        return go.Figure()
    d["marker_size"] = np.where(d["hotspot"], 15, 8)
    fig = px.scatter(d, x="housing_pct", y="transport_pct", color="borough", size="marker_size",
                     size_max=15, hover_name="zip",
                     hover_data={"housing_metric": True, "transport_metric": True,
                                 "housing_pct": ":.0%", "transport_pct": ":.0%", "marker_size": False},
                     labels={"housing_pct": "Construction activity (percentile among ZIPs)",
                             "transport_pct": "Crashes (percentile among ZIPs)",
                             "housing_metric": "Filings", "transport_metric": "Crashes"})
    # shade the "high on both" corner
    fig.add_shape(type="rect", x0=HOT_Q, x1=1.02, y0=HOT_Q, y1=1.02, fillcolor="rgba(200,68,47,0.10)",
                  line=dict(width=0), layer="below")
    n_hot, n = int(d["hotspot"].sum()), len(d)
    # label sits just ABOVE the plot area so it never covers data points
    fig.add_annotation(xref="paper", yref="paper", x=1, y=1.02, xanchor="right", yanchor="bottom",
                       showarrow=False, text=f"{n_hot} of {n} ZIPs are high on both",
                       font=dict(size=12, color="#c8442f"))
    fig.update_xaxes(tickformat=".0%", range=[0, 1.05])
    fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
    return fig


# ---------------------------------------------------------------- RQ2
def _adjusted_panel(df, col):
    """ZIP x month matrix with each ZIP's own average and each month's citywide average removed.
    What is left = 'more or less than usual for this ZIP, in this month'."""
    wide = df.pivot_table(index="zip", columns="year_month", values=col, aggfunc="sum")
    months = pd.period_range(wide.columns.min(), wide.columns.max(), freq="M").astype(str)
    wide = wide.reindex(columns=months)               # missing months stay NaN, so lags never skip a gap
    w = wide.sub(wide.mean(axis=1), axis=0)
    w = w.sub(w.mean(axis=0), axis=1)
    return w.to_numpy()


def lag_correlations(df, max_lag=MAX_LAG):
    """Correlation between filings in month t and crashes in month t+lag, pooled over ZIPs."""
    if df.empty:
        return pd.DataFrame(columns=["lag", "r", "n"])
    h, t = _adjusted_panel(df, "housing_metric"), _adjusted_panel(df, "transport_metric")
    n_months, rows = h.shape[1], []
    for k in range(max_lag + 1):
        if n_months - k < 3:
            break
        a, b = h[:, : n_months - k], t[:, k:]
        ok = np.isfinite(a) & np.isfinite(b)
        r = np.nan
        if ok.sum() > 10:
            with np.errstate(invalid="ignore"):
                r = np.corrcoef(a[ok], b[ok])[0, 1]
        rows.append({"lag": k, "r": r, "n": int(ok.sum())})
    return pd.DataFrame(rows)


def rq2(df):
    lc = lag_correlations(df)
    if lc.empty or lc["r"].isna().all():
        return go.Figure().add_annotation(text="Not enough months for this filter", showarrow=False)
    fig = go.Figure(go.Bar(
        x=lc["lag"], y=lc["r"], text=lc["r"].round(3), textposition="outside",
        marker_color=np.where(lc["r"] >= 0, "#1f6f8b", "#c8442f"),
        customdata=lc["n"], hovertemplate="Lag %{x} months<br>r = %{y:.3f}<br>%{customdata:,} ZIP-month pairs<extra></extra>"))
    fig.update_layout(xaxis_title="Months between filings and crashes (0 = same month)",
                      yaxis_title="Correlation (ZIP- and month-adjusted)", xaxis=dict(dtick=1))
    fig.add_hline(y=0, line_width=1, line_color="#17212b")
    return fig


CHARTS = [
    ("M3-RQ1: Which ZIP codes rank in the top quarter for BOTH construction filings and crashes?", rq1),
    ("M3-RQ2: Within a ZIP, do months with unusually many filings come before months with unusually many crashes?", rq2),
]

