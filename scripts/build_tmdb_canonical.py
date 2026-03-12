#!/usr/bin/env python3
"""
Build TMDB canonical keyword list from daily export.

Downloads https://files.tmdb.org/p/exports/keyword_ids_MM_DD_YYYY.json.gz
(no API key required, ~84K keywords) and optionally joins to
output/tmdb_keyword_lexicon.csv.

Outputs:
  data/tmdb_keywords_canonical.csv  — full TMDB export (tmdb_keyword_id, name)
  output/tmdb_keyword_lexicon.csv   — updated with tmdb_keyword_id column (if present)

Usage:
    python scripts/build_tmdb_canonical.py
"""
from __future__ import annotations

import gzip
import io
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

import pandas as pd

CANONICAL_FILE = Path("data/tmdb_keywords_canonical.csv")
LEXICON_FILE = Path("output/tmdb_keyword_lexicon.csv")
UNMATCHED_FILE = Path("data/tmdb_keywords_unmatched.txt")

BASE_URL = "https://files.tmdb.org/p/exports"
LOOKBACK_DAYS = 3
TIMEOUT = 60


def candidate_urls() -> Iterator[tuple[date, str]]:
    for delta in range(LOOKBACK_DAYS):
        d = date.today() - timedelta(days=delta)
        url = f"{BASE_URL}/keyword_ids_{d.month:02d}_{d.day:02d}_{d.year}.json.gz"
        yield d, url


def fetch_export() -> tuple[date, bytes]:
    errors: list[str] = []
    for d, url in candidate_urls():
        print(f"Trying {url} ...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
                data = resp.read()
            print(f"{len(data):,} bytes")
            return d, data
        except urllib.error.HTTPError as exc:
            msg = f"HTTP {exc.code}"
            print(msg)
            errors.append(f"{d}: {msg}")
        except urllib.error.URLError as exc:
            msg = str(exc.reason)
            print(msg)
            errors.append(f"{d}: {msg}")
    raise RuntimeError(
        f"Failed to fetch keyword export for last {LOOKBACK_DAYS} days:\n"
        + "\n".join(errors)
    )


def parse_export(raw_gz: bytes) -> pd.DataFrame:
    with gzip.open(io.BytesIO(raw_gz), "rt", encoding="utf-8") as fh:
        records = [
            {"tmdb_keyword_id": obj["id"], "name": obj["name"]}
            for line in fh
            if (line := line.strip())
            for obj in [json.loads(line)]
        ]
    return (
        pd.DataFrame(records)
        .drop_duplicates("tmdb_keyword_id")
        .sort_values("tmdb_keyword_id")
        .reset_index(drop=True)
        .astype({"tmdb_keyword_id": "int64", "name": "string"})
    )


def save_canonical(df: pd.DataFrame) -> None:
    CANONICAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CANONICAL_FILE, index=False)
    print(f"Saved {len(df):,} keywords → {CANONICAL_FILE}")


def join_to_lexicon(canonical: pd.DataFrame) -> None:
    if not LEXICON_FILE.exists():
        print(f"Skipping join: {LEXICON_FILE} not found")
        return

    lexicon = pd.read_csv(LEXICON_FILE)
    if "tmdb_keyword_id" in lexicon.columns:
        lexicon = lexicon.drop(columns=["tmdb_keyword_id"])

    norm = canonical.assign(name_norm=canonical["name"].str.lower().str.strip())
    lexicon["name_norm"] = lexicon["keyword"].str.lower().str.strip()

    lexicon = (
        lexicon
        .merge(norm[["tmdb_keyword_id", "name_norm"]], on="name_norm", how="left")
        .drop(columns="name_norm")
    )

    other_cols = [c for c in lexicon.columns if c not in ("keyword", "tmdb_keyword_id")]
    lexicon = lexicon[["keyword", "tmdb_keyword_id", *other_cols]]

    total = lexicon["keyword"].notna().sum()
    matched = lexicon["tmdb_keyword_id"].notna().sum()
    print(f"Matched   : {matched:,} / {total:,} ({matched / total * 100:.1f}%)")
    print(f"Unmatched : {total - matched:,} — see {UNMATCHED_FILE}")

    lexicon.to_csv(LEXICON_FILE, index=False)
    print(f"Updated   : {LEXICON_FILE}")

    unmatched = lexicon.loc[lexicon["tmdb_keyword_id"].isna(), "keyword"].dropna().tolist()
    UNMATCHED_FILE.write_text("\n".join(unmatched))


if __name__ == "__main__":
    export_date, raw_gz = fetch_export()
    canonical = parse_export(raw_gz)
    print(f"Export date : {export_date}  |  keywords : {len(canonical):,}")
    save_canonical(canonical)
    join_to_lexicon(canonical)
