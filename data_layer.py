"""
DATA LAYER  (owner: Member 3)
-----------------------------------------------------------------
THE SCHEMA CONTRACT: everyone codes against these columns.
Final merged file = data/merged_data.csv, one row per ZIP x month.

zip                  str   5-digit ZIP, e.g. "11201"
borough              str   MANHATTAN | BROOKLYN | QUEENS | BRONX | STATEN ISLAND
year                 int
month                int   1-12
year_month           str   "2024-03"
lat, lon             float ZIP centroid (mean of lat/lon of records in the ZIP)
filings_new_building int   housing: new building job filings in that ZIP-month
filings_alteration   int   housing: alteration job filings
filings_other        int   housing: all other job types
crashes_total        int   transport: crashes in that ZIP-month
crashes_pedestrian   int   crashes with >=1 pedestrian injured/killed
crashes_cyclist      int   crashes with >=1 cyclist injured/killed
crashes_motorist     int   crashes with >=1 motorist injured/killed
injuries             int   persons injured
fatalities           int   persons killed

If data/merged_data.csv does not exist yet, synthetic placeholder data is
generated with the SAME schema so everybody can build charts right now.
-----------------------------------------------------------------
"""
import os
import numpy as np
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "merged_data.csv")

BOROUGHS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]

# Dropdown option -> column (or columns) to use as the metric
HOUSING_CATEGORIES = {
    "All job types": ["filings_new_building", "filings_alteration", "filings_other"],
    "New buildings": ["filings_new_building"],
    "Alterations": ["filings_alteration"],
    "Other jobs": ["filings_other"],
}
TRANSPORT_CATEGORIES = {
    "All crashes": ["crashes_total"],
    "Pedestrian crashes": ["crashes_pedestrian"],
    "Cyclist crashes": ["crashes_cyclist"],
    "Motorist crashes": ["crashes_motorist"],
}

_CENTERS = {  # rough borough centres, used only for synthetic data
    "BRONX": (40.85, -73.88), "BROOKLYN": (40.65, -73.95),
    "MANHATTAN": (40.78, -73.97), "QUEENS": (40.73, -73.80),
    "STATEN ISLAND": (40.58, -74.15),
}


def _synthetic(seed: int = 42) -> pd.DataFrame:
    """Fake data with a mild housing->crash relationship, for development only."""
    rng = np.random.default_rng(seed)
    rows = []
    zip_id = 10000
    for b in BOROUGHS:
        lat0, lon0 = _CENTERS[b]
        for _ in range(14):
            zip_id += int(rng.integers(3, 9))
            lat, lon = lat0 + rng.normal(0, .05), lon0 + rng.normal(0, .06)
            size = rng.uniform(0.5, 2.0)
            for y in range(2022, 2026):
                for m in range(1, 13):
                    new_b = rng.poisson(2 * size)
                    alt = rng.poisson(10 * size)
                    oth = rng.poisson(4 * size)
                    base = 25 * size + 1.2 * new_b + 4 * np.sin(m / 12 * 2 * np.pi)
                    c = max(int(rng.normal(base, 6)), 0)
                    rows.append(dict(
                        zip=str(zip_id), borough=b, year=y, month=m,
                        year_month=f"{y}-{m:02d}", lat=lat, lon=lon,
                        filings_new_building=new_b, filings_alteration=alt,
                        filings_other=oth, crashes_total=c,
                        crashes_pedestrian=int(c * .08), crashes_cyclist=int(c * .04),
                        crashes_motorist=int(c * .5), injuries=int(c * .3),
                        fatalities=int(rng.binomial(1, .03)),
                    ))
    return pd.DataFrame(rows)


def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH, dtype={"zip": str})
    else:
        print("[data_layer] data/merged_data.csv not found -> using SYNTHETIC data")
        df = _synthetic()
    return df


def apply_filters(df, boroughs=None, years=None, housing_cat="All job types",
                  transport_cat="All crashes"):
    """Filter rows and add the two metric columns every chart can rely on:
       housing_metric   = filings for the chosen housing category
       transport_metric = crashes for the chosen transport category"""
    out = df.copy()
    if boroughs:
        out = out[out["borough"].isin(boroughs)]
    if years:
        out = out[out["year"].isin(years)]
    out["housing_metric"] = out[HOUSING_CATEGORIES[housing_cat]].sum(axis=1)
    out["transport_metric"] = out[TRANSPORT_CATEGORIES[transport_cat]].sum(axis=1)
    return out


def parse_search(text: str, df: pd.DataFrame) -> dict:
    """Turn free text like 'Brooklyn 2022 new buildings pedestrian' into filters."""
    t = (text or "").lower()
    boroughs = [b for b in BOROUGHS if b.lower() in t]
    if "staten" in t and "STATEN ISLAND" not in boroughs:
        boroughs.append("STATEN ISLAND")
    years = [y for y in sorted(df["year"].unique()) if str(y) in t]

    housing = "All job types"
    if "new building" in t or "new construction" in t or "new build" in t:
        housing = "New buildings"
    elif "alteration" in t or "renovat" in t:
        housing = "Alterations"

    transport = "All crashes"
    if "pedestrian" in t:
        transport = "Pedestrian crashes"
    elif "cyclist" in t or "bike" in t or "bicycl" in t:
        transport = "Cyclist crashes"
    elif "motorist" in t or "driver" in t or "car" in t:
        transport = "Motorist crashes"
    return dict(boroughs=boroughs, years=years, housing=housing, transport=transport)
