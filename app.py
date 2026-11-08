"""NYC housing x transportation data story: Dash website (owner: Member 4).

Run locally:   python app.py
On Render:     gunicorn app:server

Flow: the visitor picks filters (or types a search), then presses "Generate report".
The report callback filters the ZIP x month table with data_layer.apply_filters and redraws
every chart from charts_m1 ... charts_m4.
"""
import os
import re
import traceback

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

import charts_m1
import charts_m2
import charts_m3
import charts_m4
import data_layer as dl

# ---------------------------------------------------------------- data
DF = dl.load_data()
USING_REAL_DATA = os.path.exists(dl.DATA_PATH)

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
FIRST_MONTH = pd.Period(DF["year_month"].min(), freq="M")
LAST_MONTH = pd.Period(DF["year_month"].max(), freq="M")
WINDOW_TEXT = f"{MONTH_NAMES[FIRST_MONTH.month - 1]} {FIRST_MONTH.year} to {MONTH_NAMES[LAST_MONTH.month - 1]} {LAST_MONTH.year}"
N_ZIPS = DF["zip"].nunique()

DATASET_LINKS = {
    "DOB NOW: Build, Job Application Filings": "https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd",
    "Motor Vehicle Collisions, Crashes": "https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95",
}

# ---------------------------------------------------------------- look shared by every chart
INK = "#17212b"
FONT = "Archivo, Helvetica Neue, Arial, sans-serif"
# one colour per borough, kept identical in every chart (teal and red are reserved for the two domains)
BOROUGH_COLORS = {"BRONX": "#6a4c93", "BROOKLYN": "#e08a1e", "MANHATTAN": "#4b5d6b",
                  "QUEENS": "#4f9d5d", "STATEN ISLAND": "#b5527a"}
MAP_TRACES = ("scattermap", "scattermapbox")

HOUSING_LABELS = {"All job types": "Job filings", "New buildings": "New-building filings",
                  "Alterations": "Alteration filings", "Other jobs": "Other filings"}

# (heading, domain class for the panel rule, chart list)
GROUPS = [
    ("Construction", "housing", charts_m1.CHARTS),
    ("Crashes", "transport", charts_m2.CHARTS),
    ("Where the two meet", "both", charts_m3.CHARTS + charts_m4.CHARTS),
]
WIDE_CHARTS = {charts_m4.rq7, charts_m4.rq8}      # these need the full width to be readable


def style_figure(fig):
    """Same fonts, colours and sizes on every chart, whoever wrote it."""
    is_map = any(getattr(t, "type", "") in MAP_TRACES for t in fig.data)
    fig.update_layout(font=dict(family=FONT, color=INK, size=12), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=480 if is_map else 380,
                      hoverlabel=dict(font=dict(family=FONT, size=12)))
    if not is_map:
        fig.update_layout(margin=dict(l=55, r=20, t=44, b=50))
        fig.update_xaxes(gridcolor="#e3e8eb", zeroline=False)
        fig.update_yaxes(gridcolor="#e3e8eb", zeroline=False)

    def recolor(trace):
        color = BOROUGH_COLORS.get(getattr(trace, "name", None))
        if color is None:
            return
        trace.update(marker=dict(color=color))
        if trace.type == "scatter" and "lines" in (trace.mode or ""):
            trace.update(line=dict(color=color))
    fig.for_each_trace(recolor)
    return fig


def error_figure(message):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def clean_title(title):
    """'M3-RQ1: [replace] Which ZIP...' -> 'Which ZIP...' (the member tags live in the README)."""
    return re.sub(r"^M\d-RQ\d:\s*(\[replace\]\s*)?", "", title)


# ---------------------------------------------------------------- story (numbers come from the data)
def describe_r(r):
    """Plain-language label for a correlation coefficient."""
    if not np.isfinite(r):
        return "no measurable relationship"
    a = abs(r)
    sign = "positive" if r >= 0 else "negative"
    if a < 0.1:
        return "almost no relationship"
    return f"a {'weak' if a < 0.3 else 'moderate' if a < 0.5 else 'strong'} {sign} relationship"


def story_stats(df):
    """Headline numbers quoted in the story, computed from the same table the charts use.
    Any failure returns {} and the story falls back to text without numbers."""
    try:
        base = dl.apply_filters(df, housing_cat="New buildings", transport_cat="All crashes")
        z = charts_m3.zip_summary(base)
        lag = charts_m3.lag_correlations(base).dropna(subset=["r"])
        city = (base.groupby(["year", "month"])[["housing_metric", "transport_metric"]].sum()
                    .groupby("month").mean().reindex(range(1, 13)))
        map_table, _ = charts_m4.zip_map_table(base)
        return dict(
            n_zips=len(z), n_hot=int(z["hotspot"].sum()),
            rank_r=float(z["housing_pct"].corr(z["transport_pct"])),
            hot_boroughs=z[z["hotspot"]]["borough"].value_counts().to_dict(),
            lag_lo=float(lag["r"].min()), lag_hi=float(lag["r"].max()), lag_max_abs=float(lag["r"].abs().max()),
            lag_last=int(lag["lag"].max()),
            zero_share=float((df["filings_new_building"] == 0).mean()),
            season_r=float(city["housing_metric"].corr(city["transport_metric"])),
            crash_peak=MONTH_NAMES[int(city["transport_metric"].idxmax()) - 1],
            crash_low=MONTH_NAMES[int(city["transport_metric"].idxmin()) - 1],
            filing_peak=MONTH_NAMES[int(city["housing_metric"].idxmax()) - 1],
            ped_r=float(map_table["housing_metric"].rank(pct=True).corr(map_table["ped_share"].rank(pct=True))),
        )
    except Exception:
        traceback.print_exc()
        return {}


def borough_list(counts):
    parts = [f"{b.title()} ({n})" for b, n in counts.items() if n > 0]
    return ", ".join(parts[:-1]) + f" and {parts[-1]}" if len(parts) > 1 else "".join(parts)


def story_section(s):
    found = []
    if s:
        found.append(html.P([html.Strong("Across ZIP codes. "),
                             f"ZIP codes with more new-building filings also tend to have more crashes "
                             f"({describe_r(s['rank_r'])}, rank correlation {s['rank_r']:.2f}). "
                             f"{s['n_hot']} of {s['n_zips']} ZIP codes are in the top quarter on both, "
                             f"where about {0.0625 * s['n_zips']:.0f} would be expected if the two were unrelated"
                             + (f". They are in {borough_list(s['hot_boroughs'])}." if s["hot_boroughs"] else ".")]))
        lag_weak = s["lag_max_abs"] < 0.1
        found.append(html.P([html.Strong("Within one ZIP code. "),
                             f"After removing its usual level and each month's citywide pattern, "
                             f"filings and crashes up to {s['lag_last']} months later correlate between "
                             f"{s['lag_lo']:.3f} and {s['lag_hi']:.3f}. That is {describe_r(s['lag_max_abs'])}"
                             + (": unusually busy filing months were not followed by noticeably worse crash months."
                                if lag_weak else
                                ": busier filing months were followed by somewhat busier crash months, which on its own does not show cause.")]))
        found.append(html.P([html.Strong("Through the year. "),
                             f"Crashes are highest in {s['crash_peak']} and lowest in {s['crash_low']}, "
                             f"while new-building filings peak in {s['filing_peak']}. Across the year the two patterns have "
                             f"{describe_r(s['season_r'])} (r = {s['season_r']:.2f})."]))
        found.append(html.P([html.Strong("Pedestrians. "),
                             f"Across ZIP codes, the share of crashes that injure or kill a pedestrian has "
                             f"{describe_r(s['ped_r'])} to the number of new-building filings (rank correlation {s['ped_r']:.2f})."]))
        verdict = ("Taken together, the overlap looks like geography: dense, busy neighbourhoods have more of both. "
                   "It does not look like construction timing driving crashes." if s["rank_r"] >= 0.3 and s["lag_max_abs"] < 0.1
                   else "These are patterns of association only.")
        found.append(html.P(verdict))
    else:
        found.append(html.P("Use the explorer below to compare construction filings and crashes by ZIP code and month."))

    zero = f" About {s['zero_share']:.0%} of ZIP-months have no new-building filings at all, so small counts can swing results." if s else ""
    limits = [
        html.P("Correlation is not causation. Nothing here shows that construction causes crashes, or that crashes shape where people build."),
        html.P("A filing is an application, not a finished building or a household moving in, and its date can sit months away from the work."),
        html.P("The data has no traffic counts, so busy ZIP codes naturally have more crashes. Crash records also depend on police reporting."),
        html.P("Many filings and some crashes had no usable ZIP code, so we placed them using their coordinates. Records near a ZIP boundary can land in the neighbouring ZIP." + zero),
    ]
    return html.Section(id="story", className="story", children=html.Div(className="wrap", children=[
        html.Div(className="story-block", children=[
            html.H2("The question"),
            html.Div(className="story-text", children=[
                html.P(f"Do the parts of New York with the most new construction also have more street-safety problems? "
                       f"We lined up Department of Buildings job filings with police-recorded motor vehicle crashes, "
                       f"ZIP code by ZIP code and month by month, across {N_ZIPS} ZIP codes from {WINDOW_TEXT}."),
                html.P("It matters because the people who decide where housing goes and the people who decide where to fix streets "
                       "rarely work from the same map."),
            ])]),
        html.Div(className="story-block", children=[html.H2("What we found"), html.Div(className="story-text", children=found)]),
        html.Div(className="story-block", children=[html.H2("What the data cannot tell us"), html.Div(className="story-text", children=limits)]),
        html.Div(className="story-block", children=[
            html.H2("Why it matters for New York"),
            html.Div(className="story-text", children=[
                html.P("Planners can start safety reviews in the ZIP codes where heavy construction and frequent crashes already coincide, "
                       "instead of waiting for new housing to open."),
                html.P("Because busy filing months were not followed by worse crash months, a spike in filings is not an early warning. "
                       "Safety teams will get more from tracking persistent hotspots."
                       if not s or s["lag_max_abs"] < 0.1 else
                       "Busier filing months were followed by somewhat busier crash months, so safety teams could watch filing "
                       "spikes as one signal, alongside persistent hotspots."),
                html.P("Housing and street-safety advocates can use the map and filters below to check their own neighbourhood. "
                       "The next step is to add traffic and population counts so the comparison is per person, not per ZIP code."),
            ])]),
    ]))


STORY = story_stats(DF)

# ---------------------------------------------------------------- layout
YEAR_LAST_MONTH = DF.groupby("year")["month"].max()
YEAR_OPTIONS = [{"label": str(y) if YEAR_LAST_MONTH[y] == 12 else f"{y} (January to {MONTH_NAMES[YEAR_LAST_MONTH[y] - 1]})",
                 "value": int(y)} for y in sorted(DF["year"].unique())]

app = Dash(__name__, title="Where New York builds and where it crashes")
server = app.server      # gunicorn app:server


def controls():
    return html.Div(className="controls", children=html.Div(className="wrap controls-inner", children=[
        html.Div(className="field", children=[
            html.Label("How to choose", htmlFor="mode"),
            dcc.RadioItems(id="mode", className="mode", value="filters",
                           options=[{"label": "Filters", "value": "filters"}, {"label": "Search", "value": "search"}]),
        ]),
        html.Div(id="filter-fields", children=[
            html.Div(className="field field-borough", children=[
                html.Label("Borough"),
                dcc.Dropdown(id="boroughs", multi=True, placeholder="All boroughs",
                             options=[{"label": b.title(), "value": b} for b in dl.BOROUGHS])]),
            html.Div(className="field field-year", children=[
                html.Label("Year"),
                dcc.Dropdown(id="years", multi=True, placeholder="All years", options=YEAR_OPTIONS)]),
            html.Div(className="field field-housing", children=[
                html.Label("Housing job type"),
                dcc.Dropdown(id="housing", clearable=False, value="All job types",
                             options=[{"label": k, "value": k} for k in dl.HOUSING_CATEGORIES])]),
            html.Div(className="field field-transport", children=[
                html.Label("Crash type"),
                dcc.Dropdown(id="transport", clearable=False, value="All crashes",
                             options=[{"label": k, "value": k} for k in dl.TRANSPORT_CATEGORIES])]),
        ]),
        html.Div(id="search-field", style={"display": "none"}, children=[
            html.Div(className="field field-search", children=[
                html.Label("Describe what you want to see", htmlFor="search"),
                dcc.Input(id="search", type="text", className="search-input", n_submit=0, debounce=False,
                          placeholder="Try: Brooklyn 2023 new buildings pedestrian"),
            ])]),
        html.Button("Generate report", id="generate", className="go", n_clicks=0),
    ]))


def serve_layout():
    return html.Div([
        None if USING_REAL_DATA else html.Div(
            "Placeholder data: data/merged_data.csv was not found, so every number on this page is made up.",
            className="warning-banner"),
        html.Header(className="hero", children=[
            html.Div(className="wrap", children=[
                html.H1("Do the places New York builds in also have the most crashes?"),
                html.P(f"Construction filings and traffic crashes across {N_ZIPS} ZIP codes, {WINDOW_TEXT}.", className="hero-sub"),
                html.Div(className="hero-links", children=[
                    html.A("Read the story", href="#story"), html.A("Explore the data", href="#explorer")]),
            ]),
            html.Div(className="hero-rule", children=[html.Span(className="h"), html.Span(className="t")]),
        ]),
        story_section(STORY),
        html.Section(id="explorer", children=[
            html.Div(className="wrap explorer-head", children=[
                html.H2("Explore the data"),
                html.P("Choose filters, or switch to Search and type a request, then select Generate report. "
                       "Every chart below redraws from your choice."),
            ]),
            controls(),
            html.Div(className="wrap", children=dcc.Loading(type="circle", color=INK,
                                                            children=html.Div(id="report", className="report"))),
        ]),
        html.Footer(className="site-footer", children=html.Div(className="wrap", children=[
            html.P("Data from NYC Open Data:"),
            html.P([x for i, (name, url) in enumerate(DATASET_LINKS.items())
                    for x in ([html.A(name, href=url, target="_blank", rel="noopener")] + ([" and "] if i == 0 else []))]),
            html.P("Built for Data Engineering and Visualization, Winter 2026, German International University."),
        ])),
    ])


app.layout = serve_layout


# ---------------------------------------------------------------- callbacks
@app.callback(Output("filter-fields", "style"), Output("search-field", "style"), Input("mode", "value"))
def toggle_mode(mode):
    return ({"display": "none"}, {"display": "contents"}) if mode == "search" else ({"display": "contents"}, {"display": "none"})


def resolve_filters(mode, boroughs, years, housing, transport, text):
    """Return (filters, note). In search mode the free text is turned into filters by data_layer.parse_search."""
    if mode != "search":
        return dict(boroughs=boroughs or [], years=years or [], housing=housing, transport=transport), None
    parsed = dl.parse_search(text, DF)
    nothing = (not parsed["boroughs"] and not parsed["years"]
               and parsed["housing"] == "All job types" and parsed["transport"] == "All crashes")
    note = None
    if nothing:
        note = ("We did not find a borough, year, job type or crash type in "
                f"\"{(text or '').strip()}\", so the report shows all the data. Try \"Brooklyn 2023 new buildings pedestrian\".")
    return parsed, note


def describe_filters(f):
    places = ", ".join(b.title() for b in f["boroughs"]) if f["boroughs"] else "all five boroughs"
    years = ", ".join(str(y) for y in f["years"]) if f["years"] else "all years"
    return html.P(className="applied", children=[
        "Showing ", html.Strong(places), " in ", html.Strong(years), ": ",
        html.Strong(f["housing"].lower()), " filings against ", html.Strong(f["transport"].lower()), "."])


def kpi(value, label):
    return html.Div(children=[html.Span(f"{int(value):,}", className="kpi-value"), html.Span(label, className="kpi-label")])


def render_panel(title, fn, df, domain):
    try:
        fig = fn(df)
    except Exception:
        traceback.print_exc()
        fig = error_figure("This chart could not be drawn for this selection")
    style_figure(fig)
    wide = " wide" if fn in WIDE_CHARTS else ""
    return html.Div(className=f"panel {domain}{wide}", children=[
        html.H4(clean_title(title)),
        dcc.Graph(figure=fig, config={"displaylogo": False, "responsive": True},
                  style={"height": f"{fig.layout.height or 380}px", "width": "100%"}),
    ])


@app.callback(
    Output("report", "children"),
    Input("generate", "n_clicks"), Input("search", "n_submit"),
    State("mode", "value"), State("boroughs", "value"), State("years", "value"),
    State("housing", "value"), State("transport", "value"), State("search", "value"),
)
def build_report(_clicks, _submits, mode, boroughs, years, housing, transport, text):
    filters, note = resolve_filters(mode, boroughs, years, housing or "All job types", transport or "All crashes", text)
    d = dl.apply_filters(DF, boroughs=filters["boroughs"], years=filters["years"],
                         housing_cat=filters["housing"], transport_cat=filters["transport"])
    head = [html.P(note, className="search-note")] if note else []
    head.append(describe_filters(filters))
    if d.empty:
        return head + [html.Div(className="empty", children=[
            html.Strong("No data matches this selection."),
            "Clear a borough or year, or search for a different combination."])]

    kpis = html.Div(className="kpis", children=[
        kpi(d["housing_metric"].sum(), HOUSING_LABELS[filters["housing"]]),
        kpi(d["transport_metric"].sum(), filters["transport"]),
        kpi(d["injuries"].sum(), "People injured"),
        kpi(d["zip"].nunique(), "ZIP codes"),
    ])
    groups = [html.Div(className="group", children=[
        html.H3(heading),
        html.Div(className="grid", children=[render_panel(t, fn, d, domain) for t, fn in charts]),
    ]) for heading, domain, charts in GROUPS]
    foot = html.P("Pedestrian, cyclist and motorist crashes are crashes with at least one such person injured or killed, "
                  "so one crash can count in more than one group. The map on the last row always colours ZIP codes by "
                  "pedestrian-casualty crashes as a share of all crashes.", className="footnote")
    return head + [kpis] + groups + [foot]


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))