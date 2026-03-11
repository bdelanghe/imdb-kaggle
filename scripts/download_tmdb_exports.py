#!/usr/bin/env python3
"""
Download TMDB daily exports to data/.

Usage:
    .venv/bin/python scripts/download_tmdb_exports.py
"""
import datetime
import gzip
import json
import urllib.request
from pathlib import Path

import pandas as pd

DATA = Path("data")
DATA.mkdir(exist_ok=True)

today = datetime.date.today()
m, d, y = today.month, today.day, today.year


def fetch(name: str) -> pd.DataFrame:
    url = f"http://files.tmdb.org/p/exports/{name}_{m:02d}_{d:02d}_{y}.json.gz"
    print(f"Downloading {name} ...", end=" ", flush=True)
    with urllib.request.urlopen(url, timeout=60) as r:
        raw = gzip.decompress(r.read()).decode()
    records = [json.loads(line) for line in raw.strip().split("\n")]
    df = pd.DataFrame(records)
    out = DATA / f"tmdb_{name}.csv"
    df.to_csv(out, index=False)
    print(f"{len(df):,} rows → {out}")
    return df


movie_df = fetch("movie_ids")
company_df = fetch("production_company_ids")
collection_df = fetch("collection_ids")

print("\n--- Schemas ---")
print("movie_ids:               ", list(movie_df.columns))
print("production_company_ids:  ", list(company_df.columns))
print("collection_ids:          ", list(collection_df.columns))

print("\n--- Samples ---")
print(movie_df.sort_values("popularity", ascending=False).head(5).to_string(index=False))
print()
print(company_df.head(5).to_string(index=False))
print()
print(collection_df.head(5).to_string(index=False))
