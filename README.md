# Where NYC builds and where it crashes

**Data Engineering and Visualization, Winter 2026, Milestone 1** (German International University)

We ask whether the parts of New York with the most new construction also have more street-safety problems. We join two NYC Open Data tables at ZIP code x month and explore them in an interactive website.

- **Live site:** `https://malk0.pythonanywhere.com/`
- **Notebook:** `notebook/` (EDA, cleaning, integration, research questions, prompt log)

## Datasets

| Domain | Dataset | Catalog ID | Link |
|---|---|---|---|
| Housing and development | DOB NOW: Build, Job Application Filings | H5 (`w9ak-ipjd`) | https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd |
| Transportation | Motor Vehicle Collisions, Crashes | T4 (`h9gi-nx95`) | https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95 |

Integration: both tables are aggregated to **ZIP code x month** and joined on `zip` + `year_month`. The notebook explains why (alternatives were borough x month, a row-level spatial join, and census tract).

## Repository layout

```
app.py              Dash website: story, filters, search, Generate report (Member 4)
assets/style.css    Site styling (Member 4)
data_layer.py       Schema contract, data loading, filters, search parser (Member 3)
charts_m1.py        Charts for research questions 1-2 (Member 1)
charts_m2.py        Charts for research questions 3-4 (Member 2)
charts_m3.py        Charts for research questions 5-6 (Member 3)
charts_m4.py        Charts for research questions 7-8 (Member 4)
data/merged_data.csv  Integrated ZIP x month table the site reads
notebook/           Colab notebook
requirements.txt    Python dependencies
render.yaml         Render deployment settings
```

`data/merged_data.csv` has one row per ZIP x month. The column list is in the docstring at the top of `data_layer.py`.

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # opens on http://localhost:8050
```

If `data/merged_data.csv` is missing, the site falls back to made-up placeholder data and shows a red warning banner at the top. Never submit with that banner showing.

## How the website works

1. **Filters:** borough, year, housing job type and crash type dropdowns.
2. **Search mode:** switch to Search and type a request such as `Brooklyn 2023 new buildings pedestrian`. The text is turned into the same filters by `parse_search` in `data_layer.py`. If nothing is recognised, the page says so and shows all data.
3. **Generate report:** one button redraws every chart, the summary numbers and the filter description. Pressing Enter in the search box does the same.
4. **Charts:** lines, bars, heatmaps, a percentile scatter and a ZIP map. The last row combines both domains (hotspot scatter, lag correlation, seasonality heatmaps, map).
5. **Story:** the numbers in the story section are computed from the loaded data, so they always match the charts.

## Deploy on Render

1. Push this repository to GitHub (include `data/merged_data.csv`).
2. On https://render.com choose **New > Web Service** and connect the repository.
3. Settings (also stored in `render.yaml`): runtime Python, build command `pip install -r requirements.txt`, start command `gunicorn app:server --workers 1 --timeout 120`, plan Free.
4. Deploy, open the URL, and test the dropdowns, search mode and **Generate report**.

The free plan sleeps after about 15 minutes without visits, and the first request afterwards takes up to a minute. Open the site shortly before anyone grades it.

## Team contributions

| Member | Work |
|---|---|
| Member 1 (housing data) | EDA and pre-integration cleaning of the DOB NOW filings; found that the published ZIP column does not match the building location and derived ZIP from coordinates; research questions 1-2, charts in `charts_m1.py` |
| Member 2 (transport data) | EDA and pre-integration cleaning of the crash data, including ZIP recovery from coordinates and borough checks; research questions 3-4, charts in `charts_m2.py` |
| Member 3 (integration) | Downloader, shared cleaning helpers, ZIP x month integration, post-integration cleaning and validation, `data_layer.py` (filters and search parser), `data/merged_data.csv`; research questions 5-6, charts in `charts_m3.py` |
| Member 4 (website and story) | Website (`app.py`, `assets/style.css`): layout, filters, search mode, Generate report, story section; research questions 7-8 (`charts_m4.py`); Render deployment, this README, the GitHub repository and the submission email |

## AI use

Every prompt used in the project is listed in section 9 of the notebook.