"""Convert the fitted term structures (data/<cc>/FittedTermStructure.xlsx)
into small JSON files used by the static site in docs/.

Run from the repo root after re-estimating the model:
    python scripts/build_site_data.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = {"ez": "Euro Area", "de": "Germany", "fr": "France",
             "it": "Italy", "es": "Spain", "nl": "Netherlands"}
OUT = ROOT / "docs" / "data"
OUT.mkdir(parents=True, exist_ok=True)

for code, name in COUNTRIES.items():
    df = pd.read_excel(ROOT / "data" / code / "FittedTermStructure.xlsx")
    df.columns = [c.replace(" ", "") for c in df.columns]
    df["Time"] = pd.to_datetime(df["Time"])
    hcols = [c for c in df.columns if c.startswith("pi_")]
    df = df.dropna(subset=hcols, how="all")
    dups = df["Time"].duplicated(keep="first")
    if dups.any():
        print(f"WARNING {code}: {dups.sum()} duplicate dates dropped (kept first occurrence): "
              f"{df.loc[dups, 'Time'].dt.strftime('%Y-%m').tolist()}")
        df = df[~dups]
    df = df.sort_values("Time")
    horizons = [int(c[3:-1]) for c in hcols]
    vals = df[hcols].round(3).astype(object).where(df[hcols].notna(), None)
    payload = {
        "country": name,
        "dates": df["Time"].dt.strftime("%Y-%m-%d").tolist(),
        "quarters": [f"{d.year}Q{(d.month - 1) // 3 + 1}" for d in df["Time"]],
        "horizons": horizons,
        "values": vals.values.tolist(),
    }
    (OUT / f"{code}.json").write_text(json.dumps(payload, separators=(",", ":")))
    print(f"{code}: {len(df)} quarters, {payload['quarters'][0]}-{payload['quarters'][-1]}")
