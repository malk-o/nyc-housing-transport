"""MEMBER 4 - cross-domain visuals (map overlay, bubble/scatter)."""
import plotly.express as px

def rq1(df):
    """Map: ZIP centroids, size = filings, colour = crashes."""
    d = df.groupby(["zip", "borough"], as_index=False).agg(
        lat=("lat", "mean"), lon=("lon", "mean"),
        housing_metric=("housing_metric", "sum"), transport_metric=("transport_metric", "sum"))
    # plotly>=6 renamed scatter_mapbox -> scatter_map; support both versions
    map_fn = getattr(px, "scatter_map", None) or px.scatter_mapbox
    fig = map_fn(d, lat="lat", lon="lon", size="housing_metric",
                 color="transport_metric", hover_name="zip",
                 color_continuous_scale="YlOrRd", zoom=9.2, height=520,
                 labels={"housing_metric": "Filings", "transport_metric": "Crashes"})
    style_key = "map_style" if hasattr(px, "scatter_map") else "mapbox_style"
    fig.update_layout(**{style_key: "open-street-map"}, margin=dict(l=0, r=0, t=0, b=0))
    return fig

def rq2(df):
    d = df.groupby("year", as_index=False)[["housing_metric", "transport_metric"]].sum()
    return px.scatter(d, x="housing_metric", y="transport_metric", text="year",
                      labels={"housing_metric": "Filings", "transport_metric": "Crashes"})

CHARTS = [
    ("M4-RQ1: [replace] Where do heavy-construction ZIPs overlap with crash hotspots?", rq1),
    ("M4-RQ2: [replace] Did yearly construction and crash totals move together?", rq2),
]
