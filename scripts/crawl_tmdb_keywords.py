#!/usr/bin/env python3
"""
Phase 2: Search API fallback for keywords not in the TMDB daily export.

Reads data/tmdb_keywords_unmatched.txt (produced by scripts/build_tmdb_canonical.py)
and looks up each keyword via /3/search/keyword?query={name} (exact name match).

Run build_tmdb_canonical.py first (Phase 1) to get the unmatched list.

Rate limit: asyncio.Semaphore(20) — conservative, well under TMDB's ~50 req/s limit.
429 handling: sleep Retry-After + exponential backoff.
NaN-safe: skips empty or null keyword names.

Appends matched results to data/tmdb_keywords_canonical.csv and updates
output/tmdb_keyword_lexicon.csv with any newly resolved tmdb_keyword_ids.

Usage:
    .venv/bin/python scripts/crawl_tmdb_keywords.py
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
SEARCH_URL = "https://api.themoviedb.org/3/search/keyword"

CONCURRENCY = 20          # parallel requests — conservative, well under TMDB's ~50/s limit
CHECKPOINT_EVERY = 2_000  # keywords between checkpoint saves

CHECKPOINT_FILE = Path("data/tmdb_keywords_checkpoint.json")
OUTPUT_FILE = Path("data/tmdb_keywords_canonical.csv")
LEXICON_FILE = Path("output/tmdb_keyword_lexicon.csv")


def load_checkpoint(all_keywords: list[str]):
    if CHECKPOINT_FILE.exists():
        ckpt = json.loads(CHECKPOINT_FILE.read_text())
        done_names = set(ckpt["done"])
        remaining = [kw for kw in all_keywords if kw not in done_names]
        results = ckpt["results"]  # list of {tmdb_keyword_id, name}
        print(f"Resuming: {len(results):,} found so far, {len(remaining):,} remaining")
        return remaining, results
    print(f"Starting fresh: {len(all_keywords):,} keywords to look up")
    return all_keywords, []


async def search_keyword(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    name: str,
    retries: int = 4,
) -> dict | None:
    """Search for exact name match. Returns {tmdb_keyword_id, name} or None."""
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(
                    SEARCH_URL,
                    params={"query": name},
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("results", []):
                            if item["name"].lower() == name.lower():
                                return {"tmdb_keyword_id": item["id"], "name": item["name"]}
                        return None  # not found in first page (rare)
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        wait = retry_after + attempt * 5
                        print(f"\n429 rate limit — sleeping {wait}s (attempt {attempt+1})")
                        await asyncio.sleep(wait)
                        continue
                    return None  # other error
            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        return None


async def crawl(keywords: list[str], prior_results: list) -> tuple[list, list]:
    """Returns (all_results, done_names_list)."""
    found = list(prior_results)
    done_names = [r["name"] for r in found]
    t0 = time.monotonic()
    total = len(keywords)
    completed = 0
    next_checkpoint = CHECKPOINT_EVERY

    semaphore = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY * 2)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = {
            asyncio.create_task(search_keyword(session, semaphore, kw)): kw
            for kw in keywords
        }

        for coro in asyncio.as_completed(tasks.keys()):
            result = await coro
            completed += 1

            if result is not None:
                found.append(result)
                done_names.append(result["name"])

            if completed % 100 == 0 or completed == total:
                elapsed = time.monotonic() - t0
                rate = completed / elapsed if elapsed > 0 else 0
                print(
                    f"{completed:,}/{total:,}  found={len(found):,}  {rate:.1f} kw/s",
                    end="\r",
                    flush=True,
                )

            if completed >= next_checkpoint:
                ckpt_data = {"done": done_names, "results": found}
                CHECKPOINT_FILE.write_text(json.dumps(ckpt_data))
                elapsed = time.monotonic() - t0
                print(f"\nCheckpoint: {completed:,} done, {len(found):,} matched ({elapsed:.0f}s)")
                next_checkpoint = completed + CHECKPOINT_EVERY

    return found, done_names


def save_output(all_results: list):
    df = (
        pd.DataFrame(all_results)
        .drop_duplicates("tmdb_keyword_id")
        .sort_values("tmdb_keyword_id")
        .reset_index(drop=True)
    )
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved {len(df):,} keywords → {OUTPUT_FILE}")
    return df


def join_to_lexicon(canonical_df: pd.DataFrame):
    lexicon = pd.read_csv(LEXICON_FILE)
    canonical_df["name_norm"] = canonical_df["name"].str.lower().str.strip()
    lexicon["name_norm"] = lexicon["keyword"].str.lower().str.strip()

    lexicon = lexicon.merge(
        canonical_df[["tmdb_keyword_id", "name_norm"]],
        on="name_norm",
        how="left",
    ).drop(columns="name_norm")

    cols = ["keyword", "tmdb_keyword_id"] + [
        c for c in lexicon.columns if c not in ("keyword", "tmdb_keyword_id")
    ]
    lexicon = lexicon[cols]

    matched = lexicon["tmdb_keyword_id"].notna().sum()
    print(f"Matched {matched:,} / {len(lexicon):,} keywords ({matched/len(lexicon)*100:.1f}%)")
    lexicon.to_csv(LEXICON_FILE, index=False)
    print(f"Updated {LEXICON_FILE}")


def append_to_canonical(new_results: list) -> pd.DataFrame:
    """Append newly found keywords to canonical CSV (dedup by ID)."""
    existing = pd.read_csv(OUTPUT_FILE) if OUTPUT_FILE.exists() else pd.DataFrame(columns=["tmdb_keyword_id", "name"])
    combined = (
        pd.concat([existing, pd.DataFrame(new_results)], ignore_index=True)
        .drop_duplicates("tmdb_keyword_id")
        .sort_values("tmdb_keyword_id")
        .reset_index(drop=True)
    )
    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"\nCanonical file: {len(combined):,} total keywords → {OUTPUT_FILE}")
    return combined


def update_lexicon_ids(canonical: pd.DataFrame):
    """Fill in any still-missing tmdb_keyword_id values in the lexicon."""
    lexicon = pd.read_csv(LEXICON_FILE)

    # Build name→id map from full canonical (export + search results)
    id_map = dict(zip(canonical["name"].str.lower().str.strip(), canonical["tmdb_keyword_id"]))

    mask = lexicon["tmdb_keyword_id"].isna() & lexicon["keyword"].notna()
    lexicon.loc[mask, "tmdb_keyword_id"] = (
        lexicon.loc[mask, "keyword"].str.lower().str.strip().map(id_map)
    )

    matched = lexicon["tmdb_keyword_id"].notna().sum()
    total = lexicon["keyword"].notna().sum()
    print(f"Lexicon coverage: {matched:,} / {total:,} ({matched/total*100:.1f}%)")
    lexicon.to_csv(LEXICON_FILE, index=False)
    print(f"Updated {LEXICON_FILE}")


if __name__ == "__main__":
    unmatched_file = Path("data/tmdb_keywords_unmatched.txt")
    if not unmatched_file.exists():
        print("Run scripts/build_tmdb_canonical.py first (Phase 1)")
        raise SystemExit(1)

    # Load unmatched keyword names (NaN-safe)
    all_keywords = [
        kw.strip() for kw in unmatched_file.read_text().splitlines()
        if kw.strip()
    ]
    print(f"Phase 2: {len(all_keywords):,} unmatched keywords to search")

    remaining, prior_results = load_checkpoint(all_keywords)
    all_results, _ = asyncio.run(crawl(remaining, prior_results))
    print(f"\nSearch found: {len(all_results):,} / {len(all_keywords):,}")

    canonical = append_to_canonical(all_results)
    update_lexicon_ids(canonical)
