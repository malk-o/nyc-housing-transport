"""MEMBER 2 - transportation-focused research questions."""
import plotly.express as px

def rq1(df):
    d = df.groupby(["year", "month"], as_index=False)["transport_metric"].sum()
    d["month"] = d["month"].astype(str)
    return px.line(d, x="month", y="transport_metric", color=d["year"].astype(str),
                   labels={"transport_metric": "Crashes", "color": "Year"})

def rq2(df):
    d = df.groupby(["borough", "month"], as_index=False)["transport_metric"].sum()
    p = d.pivot(index="borough", columns="month", values="transport_metric").fillna(0)
    return px.imshow(p, aspect="auto", labels=dict(x="Month", y="Borough", color="Crashes"))

CHARTS = [
    ("M2-RQ1: [replace] Is there a seasonal pattern in crashes, and has it shifted by year?", rq1),
    ("M2-RQ2: [replace] Which borough-months are the crash hotspots?", rq2),
]
