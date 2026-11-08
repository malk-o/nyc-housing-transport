"""MEMBER 4 - cross-domain questions: seasonality and the map overlay.

RQ7  Do construction filings and crashes follow the same rhythm through the year?
     (borough x calendar-month heatmaps of a seasonal index; 100 = an average month)
RQ8  Where do heavy construction activity and a high share of pedestrian-casualty crashes overlap?
     (ZIP-centroid map: bubble size = filings, colour = pedestrian-casualty crashes as % of all crashes)

Every chart is a function f(df) -> plotly Figure. `df` already has the `housing_metric` and
`transport_metric` columns added by data_layer.apply_filters. The summarize_* helpers return
the exact numbers behind each chart so the notebook text can quote them.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BORO_ORDER = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]
MIN_CRASHES = 100          # RQ8: a share built on fewer crashes is mostly noise
# diverging scale shared with M3's palette: below average = teal, above average = red
DIVERGING = [[0, "#1f6f8b"], [0.5, "#f7f7f7"], [1, "#c8442f"]]


def _empty(message):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ---------------------------------------------------------------- RQ7
def seasonal_index(df, col):
    """Borough x calendar-month table. Each cell = the average monthly total for that calendar month
    (averaged over the years in the data), divided by the borough's average across all 12 months, x100.
    100 = a typical month; 130 = 30% busier than a typical month for that borough."""
    monthly = df.groupby(["borough", "year", "month"], as_index=False)[col].sum()
    avg = monthly.groupby(["borough", "month"])[col].mean().unstack("month").reindex(columns=range(1, 13))
    index = avg.div(avg.mean(axis=1).replace(0, np.nan), axis=0) * 100
    order = [b for b in BORO_ORDER if b in index.index]
    return index.loc[order]


def rq7(df):
    if df.empty:
        return _empty("No data for this filter")
    housing, transport = seasonal_index(df, "housing_metric"), seasonal_index(df, "transport_metric")
    if housing.empty or transport.empty:
        return _empty("No data for this filter")
    span = float(np.nanmax(np.abs(np.concatenate([housing.to_numpy().ravel(), transport.to_numpy().ravel()]) - 100)))
    span = max(span, 10.0)

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.03,
                        subplot_titles=("Construction filings", "Crashes"))
    for col, (name, table) in enumerate([("Filings", housing), ("Crashes", transport)], start=1):
        fig.add_trace(go.Heatmap(
            z=table.to_numpy(), x=MONTHS, y=table.index.tolist(), coloraxis="coloraxis",
            texttemplate="%{z:.0f}", textfont=dict(size=10),
            hovertemplate=f"{name}<br>%{{y}}, %{{x}}<br>Seasonal index %{{z:.0f}} (100 = average month)<extra></extra>"),
            row=1, col=col)
    fig.update_layout(
        coloraxis=dict(colorscale=DIVERGING, cmid=100, cmin=100 - span, cmax=100 + span,
                       colorbar=dict(title="Index<br>(100 = avg month)", thickness=12)),
        margin=dict(l=10, r=10, t=40, b=10))
    fig.update_yaxes(autorange="reversed")
    return fig


def summarize_rq7(df):
    """Numbers for the notebook: how alike are the two seasonal profiles, and when does each peak?"""
    housing, transport = seasonal_index(df, "housing_metric"), seasonal_index(df, "transport_metric")
    rows = []
    for b in housing.index:
        h, t = housing.loc[b], transport.loc[b]
        r = h.corr(t) if h.notna().sum() >= 6 else np.nan
        rows.append(dict(borough=b, profile_correlation=round(r, 2),
                         filings_peak=MONTHS[int(h.idxmax()) - 1], filings_peak_index=round(h.max()),
                         filings_low=MONTHS[int(h.idxmin()) - 1], filings_low_index=round(h.min()),
                         crashes_peak=MONTHS[int(t.idxmax()) - 1], crashes_peak_index=round(t.max()),
                         crashes_low=MONTHS[int(t.idxmin()) - 1], crashes_low_index=round(t.min())))
    table = pd.DataFrame(rows)
    city = df.groupby(["year", "month"], as_index=False)[["housing_metric", "transport_metric"]].sum()
    city = city.groupby("month")[["housing_metric", "transport_metric"]].mean().reindex(range(1, 13))
    city_r = city["housing_metric"].corr(city["transport_metric"])
    print(table.to_string(index=False))
    print(f"\nCitywide: correlation between the 12-month filings profile and the 12-month crash profile = {city_r:.2f}")
    print("Citywide seasonal index (100 = average month):")
    idx = (city / city.mean() * 100).round(0)
    idx.index = MONTHS
    print(idx.T.to_string())
    return table


# ---------------------------------------------------------------- RQ8
def zip_map_table(df, min_crashes=MIN_CRASHES):
    """One row per ZIP: filings, crashes, pedestrian-casualty share. ZIPs with fewer than min_crashes
    crashes are excluded from the colour scale because their share is mostly noise."""
    d = df.groupby(["zip", "borough"], as_index=False).agg(
        lat=("lat", "mean"), lon=("lon", "mean"),
        housing_metric=("housing_metric", "sum"), crashes_total=("crashes_total", "sum"),
        crashes_pedestrian=("crashes_pedestrian", "sum"))
    d = d[d["crashes_total"] > 0].copy()
    d["ped_share"] = d["crashes_pedestrian"] / d["crashes_total"] * 100
    n_excluded = int((d["crashes_total"] < min_crashes).sum())
    kept = d[d["crashes_total"] >= min_crashes]
    if len(kept) < 5:                       # a very narrow filter: show everything rather than an empty map
        kept, n_excluded = d, 0
    return kept.copy(), n_excluded


def rq8(df):
    if df.empty:
        return _empty("No data for this filter")
    d, n_excluded = zip_map_table(df)
    if d.empty:
        return _empty("No crashes for this filter")
    d["bubble"] = d["housing_metric"].clip(lower=0.5)         # zero would make the bubble vanish
    fig = px.scatter_map(
        d, lat="lat", lon="lon", size="bubble", size_max=28, color="ped_share",
        color_continuous_scale="YlOrRd", hover_name="zip",
        hover_data={"borough": True, "housing_metric": True, "crashes_total": True,
                    "ped_share": ":.1f", "bubble": False, "lat": False, "lon": False},
        labels={"ped_share": "Pedestrian-casualty<br>crashes (% of all)", "housing_metric": "Filings",
                "crashes_total": "Crashes", "borough": "Borough"},
        center=dict(lat=40.71, lon=-73.95), zoom=9.2, map_style="carto-positron")
    fig.update_traces(marker=dict(opacity=0.75))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_colorbar=dict(thickness=12))
    if n_excluded:
        fig.add_annotation(xref="paper", yref="paper", x=0, y=0, xanchor="left", yanchor="bottom",
                           showarrow=False, bgcolor="rgba(255,255,255,0.8)", font=dict(size=11),
                           text=f"{n_excluded} ZIPs with fewer than {MIN_CRASHES} crashes are not shown")
    return fig


def summarize_rq8(df):
    """Numbers for the notebook: which ZIPs combine heavy filings with a high pedestrian share?"""
    d, n_excluded = zip_map_table(df)
    d["housing_pct"] = d["housing_metric"].rank(pct=True)
    d["ped_pct"] = d["ped_share"].rank(pct=True)
    both = d[(d["housing_pct"] >= 0.75) & (d["ped_pct"] >= 0.75)].sort_values("ped_share", ascending=False)
    print(f"ZIPs shown: {len(d)} (excluded for fewer than {MIN_CRASHES} crashes: {n_excluded})")
    print(f"Citywide pedestrian-casualty share among shown ZIPs: "
          f"{d['crashes_pedestrian'].sum() / d['crashes_total'].sum() * 100:.1f}%")
    print(f"Rank correlation, filings vs pedestrian share across ZIPs: {d['housing_pct'].corr(d['ped_pct']):.2f}")
    print(f"ZIPs in the top quarter on BOTH filings and pedestrian share: {len(both)} of {len(d)} "
          f"(about {0.25 * 0.25 * 100:.0f}% = {0.0625 * len(d):.0f} expected if unrelated)")
    print("\nBoroughs of those ZIPs:"); print(both["borough"].value_counts().to_string())
    print("\nTop ZIPs:")
    print(both[["zip", "borough", "housing_metric", "crashes_total", "ped_share"]].round(1).head(8).to_string(index=False))
    print("\nPedestrian share by borough (all shown ZIPs):")
    g = d.groupby("borough")[["crashes_pedestrian", "crashes_total"]].sum()
    print((g["crashes_pedestrian"] / g["crashes_total"] * 100).round(1).to_string())
    return d


CHARTS = [
    ("M4-RQ7: Do construction filings and crashes follow the same rhythm through the year?", rq7),
    ("M4-RQ8: Where do heavy construction activity and a high pedestrian-casualty share overlap?", rq8),
]