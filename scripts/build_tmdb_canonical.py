#!/usr/bin/env python3
"""
Phase 1: Build TMDB canonical keyword list from daily export.

Downloads http://files.tmdb.org/p/exports/keyword_ids_MM_DD_YYYY.json.gz
(zero API cost, ~84K keywords) and joins to output/tmdb_keyword_lexicon.csv.

Coverage: ~90.5% of Kaggle keywords matched by exact lowercase name.

Outputs:
  data/tmdb_keywords_canonical.csv  — full TMDB export (tmdb_keyword_id, name)
  output/tmdb_keyword_lexicon.csv   — updated with tmdb_keyword_id column

Usage:
    .venv/bin/python scripts/build_tmdb_canonical.py
"""
import datetime
import gzip
import json
import urllib.request
from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("data")
CANONICAL_FILE = OUTPUT_DIR / "tmdb_keywords_canonical.csv"
LEXICON_FILE = Path("output/tmdb_keyword_lexicon.csv")


def download_export() -> pd.DataFrame:
    today = datetime.date.today()
    url = (
        f"http://files.tmdb.org/p/exports/"
        f"keyword_ids_{today.month:02d}_{today.day:02d}_{today.year}.json.gz"
    )
    print(f"Downloading {url} ...")
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = gzip.decompress(r.read()).decode()

    records = [json.loads(line) for line in raw.strip().split("\n")]
    df = pd.DataFrame(records).rename(columns={"id": "tmdb_keyword_id"})
    df = df[["tmdb_keyword_id", "name"]].sort_values("tmdb_keyword_id").reset_index(drop=True)
    print(f"Downloaded {len(df):,} keywords from TMDB export")
    return df


def save_canonical(df: pd.DataFrame):
    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(CANONICAL_FILE, index=False)
    print(f"Saved {len(df):,} keywords → {CANONICAL_FILE}")


def join_to_lexicon(canonical: pd.DataFrame):
    lexicon = pd.read_csv(LEXICON_FILE)

    # Drop any pre-existing tmdb_keyword_id column
    if "tmdb_keyword_id" in lexicon.columns:
        lexicon = lexicon.drop(columns=["tmdb_keyword_id"])

    canonical["name_norm"] = canonical["name"].str.lower().str.strip()
    lexicon["name_norm"] = lexicon["keyword"].str.lower().str.strip()

    lexicon = lexicon.merge(
        canonical[["tmdb_keyword_id", "name_norm"]],
        on="name_norm",
        how="left",
    ).drop(columns="name_norm")

    # Move tmdb_keyword_id to second column
    cols = ["keyword", "tmdb_keyword_id"] + [
        c for c in lexicon.columns if c not in ("keyword", "tmdb_keyword_id")
    ]
    lexicon = lexicon[cols]

    total = lexicon["keyword"].notna().sum()
    matched = lexicon["tmdb_keyword_id"].notna().sum()
    unmatched = total - matched
    print(f"Matched:   {matched:,} / {total:,} ({matched/total*100:.1f}%)")
    print(f"Unmatched: {unmatched:,} — run scripts/crawl_tmdb_keywords.py for Phase 2")

    lexicon.to_csv(LEXICON_FILE, index=False)
    print(f"Updated {LEXICON_FILE}")

    # Save unmatched list for Phase 2
    unmatched_kws = lexicon.loc[lexicon["tmdb_keyword_id"].isna(), "keyword"].dropna().tolist()
    unmatched_file = OUTPUT_DIR / "tmdb_keywords_unmatched.txt"
    unmatched_file.write_text("\n".join(unmatched_kws))
    print(f"Unmatched list → {unmatched_file} ({len(unmatched_kws):,} keywords)")


if __name__ == "__main__":
    canonical = download_export()
    save_canonical(canonical)
    join_to_lexicon(canonical)
