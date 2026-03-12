#!/usr/bin/env python3
"""
Download TMDB daily exports (movie_ids, production_company_ids, collection_ids) to data/.

Usage:
    python scripts/download_tmdb_exports.py
"""
from __future__ import annotations

import gzip
import io
import json
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

import pandas as pd

DATA = Path("data")
DATA.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://files.tmdb.org/p/exports"
LOOKBACK_DAYS = 3
TIMEOUT = 60

EXPORTS = ["movie_ids", "production_company_ids", "collection_ids"]


def candidate_urls(name: str) -> Iterator[tuple[date, str]]:
    for delta in range(LOOKBACK_DAYS):
        d = date.today() - timedelta(days=delta)
        url = f"{BASE_URL}/{name}_{d.month:02d}_{d.day:02d}_{d.year}.json.gz"
        yield d, url


def fetch(name: str) -> pd.DataFrame:
    errors: list[str] = []
    for d, url in candidate_urls(name):
        print(f"Trying {url} ...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
                raw_gz = resp.read()
            print(f"{len(raw_gz):,} bytes  (export date: {d})")
            with gzip.open(io.BytesIO(raw_gz), "rt", encoding="utf-8") as fh:
                records = [json.loads(line) for line in fh if line.strip()]
            df = pd.DataFrame(records)
            out = DATA / f"tmdb_{name}.csv"
            df.to_csv(out, index=False)
            print(f"  → {len(df):,} rows saved to {out}")
            return df
        except urllib.error.HTTPError as exc:
            msg = f"HTTP {exc.code}"
            print(msg)
            errors.append(f"{d}: {msg}")
        except urllib.error.URLError as exc:
            msg = str(exc.reason)
            print(msg)
            errors.append(f"{d}: {msg}")
    raise RuntimeError(
        f"Failed to fetch '{name}' export for last {LOOKBACK_DAYS} days:\n"
        + "\n".join(errors)
    )


if __name__ == "__main__":
    frames: dict[str, pd.DataFrame] = {}
    for export in EXPORTS:
        frames[export] = fetch(export)

    print("\n--- Schemas ---")
    for name, df in frames.items():
        print(f"{name:<30} {list(df.columns)}")

    print("\n--- Samples ---")
    if "movie_ids" in frames:
        print(frames["movie_ids"].sort_values("popularity", ascending=False).head(5).to_string(index=False))
