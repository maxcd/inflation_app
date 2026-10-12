# Term Structure of European Survey Inflation Expectations

An interactive dashboard for exploring the fitted term structure of professional inflation expectations across the Euro Area and major European economies.

## Live App

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://inflation-expectations-ea.streamlit.app/)

## Overview

This app visualizes the estimated term structure of inflation expectations derived from professional forecaster surveys. It covers six economies — the **Euro Area, Germany, France, Italy, Spain, and the Netherlands** — with quarterly data going back to 1989.

The dashboard has three views:

- **Overview** — time series of inflation expectations across all forecast horizons (1Q to 40Q ahead)
- **Term Structure Comparison** — compare the shape of the curve across multiple quarters side by side
- **Curve Evolution** — step through individual quarters to see how the term structure has shifted over time

## Data & Methodology

The underlying data is based on the ECBs Survey of Professional Forecasters and from of Consensus Economics. The term structure is estimated with a Bayesian version of the model by Aruoba (2020). The original data are not shared here, only the model output. 

## Static site (GitHub Pages)

A static version of the dashboard lives in `docs/` and runs entirely in the browser (Plotly.js), so it never needs to be woken up.

- `docs/index.html`: the page
- `docs/data/<cc>.json`: model output, generated from the Excel files

After re-estimating the model, regenerate the JSON and push:

```bash
python scripts/build_site_data.py
```

To publish, go to GitHub → Settings → Pages → *Deploy from a branch* → `main` / `/docs`.
To preview locally: `python -m http.server -d docs` and open http://localhost:8000.

## Local Development

To run the app locally:

```bash
git clone https://github.com/[your-username]/[your-repo].git
cd [your-repo]
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app expects country-level data files at the following paths:

```
data/
├── de/FittedTermStructure.xlsx   # Germany
├── es/FittedTermStructure.xlsx   # Spain
├── ez/FittedTermStructure.xlsx   # Euro Area
├── fr/FittedTermStructure.xlsx   # France
├── it/FittedTermStructure.xlsx   # Italy
└── nl/FittedTermStructure.xlsx   # Netherlands
```

## Literature

- Borağan Aruoba, S. (2020). *Term structures of inflation expectations and real interest rates*. Journal of Business & Economic Statistics 38(3): 542-553.