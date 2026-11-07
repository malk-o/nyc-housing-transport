"""MEMBER 1 - housing-focused research questions.
Each chart = a function f(df) -> plotly Figure. df is the filtered ZIP x month table
(columns include zip, borough, year, month, filings_new_building, filings_alteration).
Counts are initial applications (one row per job application), see the notebook, section 3.
Add your function to CHARTS as (research question, function)."""
import plotly.express as px
import plotly.graph_objects as go

NEW, ALT = "filings_new_building", "filings_alteration"

BOROUGH_COLORS = {"BRONX": "#636EFA", "BROOKLYN": "#EF553B", "MANHATTAN": "#00CC96",
                  "QUEENS": "#AB63FA", "STATEN ISLAND": "#FFA15A"}


def _empty(message):
    """Blank figure with a message, so the site never crashes on an empty filter."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _usable_years(df):
    """Years to compare: complete years (12 distinct months) if there are any, otherwise every year present.
    This keeps the unfinished current year from looking like a drop."""
    months_per_year = df.groupby("year")["month"].nunique()
    full = [int(y) for y in months_per_year.index if months_per_year[y] == 12]
    return full if full else sorted(int(y) for y in months_per_year.index)


def _bar(best, x, labels, hover):
    fig = px.bar(best, x=x, y="zip", color="borough", orientation="h",
                 color_discrete_map=BOROUGH_COLORS, hover_data=hover, labels=labels)
    fig.update_yaxes(type="category", categoryorder="total ascending")
    fig.update_layout(legend_title_text="Borough")
    return fig


def rq1(df, top=15):
    """Which ZIPs gained the most new-building applications between the first and last full year?
    With fewer than two complete years selected, show where new-building applications were concentrated."""
    if df.empty or NEW not in df:
        return _empty("No data for the selected filters")
    d = df.assign(zip=lambda t: t["zip"].astype(str))
    years = _usable_years(d)

    if len(years) < 2:   # growth needs two complete years: show the selected period's top ZIPs instead
        best = d.groupby(["zip", "borough"], as_index=False)[NEW].sum().nlargest(top, NEW)
        return _bar(best, NEW,
                    {NEW: "New-building applications in the selected period (growth needs two complete years)",
                     "zip": "ZIP code"},
                    {"borough": False})

    y0, y1 = min(years), max(years)
    t = (d[d["year"].isin([y0, y1])].groupby(["zip", "borough", "year"])[NEW].sum()
         .unstack("year", fill_value=0).reindex(columns=[y0, y1], fill_value=0).reset_index())
    t.columns = ["zip", "borough", f"filings_{y0}", f"filings_{y1}"]
    t["change"] = t[f"filings_{y1}"] - t[f"filings_{y0}"]
    base = t[f"filings_{y0}"].where(t[f"filings_{y0}"] > 0)      # % change undefined when the base is 0
    t["pct_change"] = (t["change"] / base * 100).round(0)
    best = t.nlargest(top, "change")
    return _bar(best, "change",
                {"change": f"Increase in new-building applications, {y0} to {y1}", "zip": "ZIP code"},
                {f"filings_{y0}": True, f"filings_{y1}": True, "pct_change": True,
                 "change": True, "borough": False})


def rq2(df):
    """How does the share of new-building applications (vs alterations) differ by borough and year?"""
    if df.empty or NEW not in df or ALT not in df:
        return _empty("No data for the selected filters")
    years = _usable_years(df)
    d = (df[df["year"].isin(years)].groupby(["borough", "year"])[[NEW, ALT]].sum().reset_index())
    total = d[NEW] + d[ALT]
    d["new_share"] = (d[NEW] / total.where(total > 0) * 100).round(1)
    fig = px.line(d, x="year", y="new_share", color="borough", markers=True,
                  color_discrete_map=BOROUGH_COLORS,
                  hover_data={NEW: True, ALT: True},
                  labels={"new_share": "New buildings as % of new + alteration applications", "year": "Year"})
    fig.update_xaxes(dtick=1)
    fig.update_layout(legend_title_text="Borough")
    return fig


CHARTS = [
    ("M1-RQ1: Which ZIP codes had the largest growth in new-building applications between the first and last full year?", rq1),
    ("M1-RQ2: How does the share of new-building applications (versus alterations) differ across boroughs and over time?", rq2),
]
