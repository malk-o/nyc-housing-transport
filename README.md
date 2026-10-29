# NYC: Where we build vs. where streets get dangerous
GIU Data Engineering & Visualization, Milestone 1 (deadline 9 Nov 2026)

**Datasets:** DOB NOW Build Job Application Filings (housing) + Motor Vehicle Collisions Crashes (transportation), NYC Open Data. 
- Housing (`w9ak-ipjd`): https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd
- Crashes (`h9gi-nx95`): https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

**Note:** the crash feed was reported paused in 2026 (data through ~June). The pipeline uses the common date window of both datasets.
**Integration:** both aggregated to ZIP x year-month, joined on `zip` + `year_month`.

## Repo layout
| File | Purpose | Owner |
|---|---|---|
| `notebooks/NYC_Housing_Transport.ipynb` | EDA, cleaning, integration, RQs, prompt log | everyone (own sections) |
| `data_layer.py` | merged-data schema contract, filters, search parser | M3 |
| `charts_m1.py` ... `charts_m4.py` | each member's 2 research-question charts | M1 to M4 |
| `app.py`, `assets/style.css` | Dash layout, callbacks, story section | M4 (skeleton by M3) |
| `data/merged_data.csv` | final integrated dataset (app falls back to synthetic data if missing) | M3 |

## Run locally
```
pip install -r requirements.txt
python app.py        # http://127.0.0.1:8050
```

## Add your chart (members)
1. Open your `charts_mX.py`. 2. Write `def my_chart(df): ... return fig` (df has `housing_metric` and `transport_metric`).
3. Add `("Your research question", my_chart)` to `CHARTS`. It appears on the site automatically.

## Deploy on Render
New -> Web Service -> connect this repo. Build: `pip install -r requirements.txt`. Start: `gunicorn app:server`.

## Git rules
Pull before you work, commit small, only edit your own files. Never commit raw CSVs larger than 50 MB (the merged file is small).

## Team contributions
| Member | Contribution |
|---|---|
| M1 | TODO |
| M2 | TODO |
| M3 | TODO |
| M4 | TODO |

