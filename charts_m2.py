"""MEMBER 2 - transportation-focused research questions."""
import plotly.express as px
import plotly.graph_objects as go


def _empty(message):
    return go.Figure().add_annotation(text=message, showarrow=False)


# ---------------------------------------------------------------- RQ3
def rq3(df):
    """Share of crashes with a pedestrian / cyclist casualty, by borough and year."""
    d = (df.groupby(["borough", "year"], as_index=False)
           [["crashes_total", "crashes_pedestrian", "crashes_cyclist"]].sum())
    d = d[d["crashes_total"] > 0]
    if d.empty:
        return _empty("No crashes for this filter")
    last_month = df.groupby("year")["month"].max()
    d["period"] = [str(y) if last_month[y] == 12 else f"{y} (to month {last_month[y]})" for y in d["year"]]
    d["Pedestrian"] = d["crashes_pedestrian"] / d["crashes_total"] * 100
    d["Cyclist"] = d["crashes_cyclist"] / d["crashes_total"] * 100
    long = d.melt(id_vars=["borough", "period", "crashes_total"], value_vars=["Pedestrian", "Cyclist"],
                  var_name="Casualty", value_name="share")
    fig = px.line(long, x="period", y="share", color="borough", facet_col="Casualty", markers=True,
                  hover_data={"crashes_total": True, "share": ":.1f"},
                  labels={"share": "% of crashes", "period": "Year", "borough": "Borough"})
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_xaxes(categoryorder="category ascending")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1] + " casualty"))
    return fig


# ---------------------------------------------------------------- RQ4
def rq4(df, top=15):
    """ZIPs with the most injuries per 100 crashes (the quarter of ZIPs with the fewest crashes is left out)."""
    d = df.groupby(["zip", "borough"], as_index=False)[["crashes_total", "injuries", "fatalities"]].sum()
    d = d[d["crashes_total"] > 0]
    if d.empty:
        return _empty("No crashes for this filter")
    d = d[d["crashes_total"] >= d["crashes_total"].quantile(0.25)]
    d["injuries_per_100"] = (d["injuries"] / d["crashes_total"] * 100).round(1)
    best = d.nlargest(top, "injuries_per_100").sort_values("injuries_per_100")
    fig = px.bar(best, x="injuries_per_100", y="zip", color="borough", orientation="h",
                 hover_data={"crashes_total": True, "injuries": True, "fatalities": True, "borough": False},
                 labels={"injuries_per_100": "Injuries per 100 crashes", "zip": "ZIP code", "borough": "Borough"})
    fig.update_yaxes(type="category", categoryorder="total ascending")
    return fig


CHARTS = [
    ("M2-RQ3: Which boroughs have the highest share of crashes with pedestrian or cyclist casualties, and has it changed since 2022?", rq3),
    ("M2-RQ4: Which ZIPs have the most injuries per crash?", rq4),
]