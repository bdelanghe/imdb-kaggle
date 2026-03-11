#!/usr/bin/env python3
"""
1. Filter Kaggle snapshot to movies in both Kaggle + TMDB daily export.
2. Fetch full metadata + keywords for the 1,429 new TMDB movies via API.
3. Append new movies to filtered dataset.

Output: data/tmdb_movies_clean.csv  (valid movies only, with keywords)

Usage:
    .venv/bin/python scripts/fetch_new_movies.py
"""
import asyncio
import json
import os
import time
from pathlib import Path

import aiohttp
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TMDB_TOKEN = os.environ["TMDB_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TMDB_TOKEN}", "accept": "application/json"}
DETAIL_URL = "https://api.themoviedb.org/3/movie/{}?append_to_response=keywords"

KAGGLE_FILE = Path("/Users/bobby/.cache/kagglehub/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies/versions/868/TMDB_movie_dataset_v11.csv")
TMDB_EXPORT = Path("data/tmdb_movie_ids.csv")
OUT_FILE    = Path("data/tmdb_movies_clean.csv")
CONCURRENCY = 20


async def fetch_movie(session, semaphore, movie_id):
    async with semaphore:
        for attempt in range(4):
            try:
                async with session.get(
                    DETAIL_URL.format(movie_id),
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    if resp.status == 429:
                        wait = int(resp.headers.get("Retry-After", 10)) + attempt * 5
                        print(f"\n429 — sleeping {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    return None
            except asyncio.TimeoutError:
                await asyncio.sleep(2 ** attempt)
        return None


def parse_movie(data: dict) -> dict:
    keywords = ", ".join(kw["name"] for kw in data.get("keywords", {}).get("keywords", []))
    genres   = ", ".join(g["name"] for g in data.get("genres", []))
    return {
        "id":               data.get("id"),
        "title":            data.get("title"),
        "original_title":   data.get("original_title"),
        "release_date":     data.get("release_date"),
        "popularity":       data.get("popularity"),
        "vote_average":     data.get("vote_average"),
        "vote_count":       data.get("vote_count"),
        "genres":           genres,
        "keywords":         keywords or None,
        "overview":         data.get("overview"),
        "revenue":          data.get("revenue"),
        "budget":           data.get("budget"),
        "runtime":          data.get("runtime"),
        "original_language":data.get("original_language"),
        "status":           data.get("status"),
    }


async def fetch_all(ids: list[int]) -> list[dict]:
    semaphore = asyncio.Semaphore(CONCURRENCY)
    results = []
    t0 = time.monotonic()
    connector = aiohttp.TCPConnector(limit=CONCURRENCY * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_movie(session, semaphore, mid) for mid in ids]
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            data = await coro
            if data:
                results.append(parse_movie(data))
            if i % 50 == 0 or i == len(ids):
                rate = i / (time.monotonic() - t0)
                print(f"{i}/{len(ids)}  fetched={len(results)}  {rate:.1f} req/s", end="\r", flush=True)
    return results


if __name__ == "__main__":
    print("Loading Kaggle snapshot...")
    kaggle = pd.read_csv(KAGGLE_FILE, low_memory=False)
    tmdb   = pd.read_csv(TMDB_EXPORT)

    kaggle_ids = set(kaggle["id"].dropna().astype(int))
    tmdb_ids   = set(tmdb["id"].dropna().astype(int))
    valid_ids  = kaggle_ids & tmdb_ids
    new_ids    = sorted(tmdb_ids - kaggle_ids)

    # Step 1: filter Kaggle to valid movies only
    print(f"Filtering Kaggle: {len(kaggle):,} → {len(valid_ids):,} valid movies")
    clean = kaggle[kaggle["id"].isin(valid_ids)].copy()

    # Step 2: fetch new movies from API
    print(f"\nFetching {len(new_ids):,} new movies from TMDB API...")
    new_records = asyncio.run(fetch_all(new_ids))
    print(f"\nFetched {len(new_records):,} / {len(new_ids):,}")

    # Step 3: append
    new_df = pd.DataFrame(new_records)
    clean  = pd.concat([clean, new_df], ignore_index=True)
    clean  = clean.sort_values("popularity", ascending=False).reset_index(drop=True)

    OUT_FILE.parent.mkdir(exist_ok=True)
    clean.to_csv(OUT_FILE, index=False)
    print(f"\nSaved {len(clean):,} movies → {OUT_FILE}")
    print(f"  with keywords: {clean['keywords'].notna().sum():,}")
    print(f"  no keywords:   {clean['keywords'].isna().sum():,}")
