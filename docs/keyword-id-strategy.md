# Keyword ID Strategy

> **Scope:** This is a TMDB project. We initially considered IMDB but scoped to TMDB only.
> Goal: assign `tmdb_keyword_id` to every keyword in `output/tmdb_keyword_lexicon.csv`.

---

## Data sources

| Source | Keywords | API cost | Freshness |
|--------|----------|----------|-----------|
| **TMDB daily export** | 84,761 | 0 requests | Updated daily at `files.tmdb.org` |
| **TMDB search/keyword** | any | 1 req/name, ~20 concurrent | Live |
| **TMDB movie/{id}/keywords** | per-movie | 1 req/movie | Live |

---

## Phase 1 — TMDB daily export (zero API cost) ✅

**Script:** `scripts/build_tmdb_canonical.py`

TMDB publishes a compressed JSONL export daily:
```
http://files.tmdb.org/p/exports/keyword_ids_MM_DD_YYYY.json.gz
```

One JSON object per line: `{"id": 9826, "name": "murder"}`.

Download once → 84,761 keyword IDs with no rate limiting.

**Results:**
- Kaggle keywords: 67,916
- Matched by exact lowercase name: 61,465 (90.5%)
- Unmatched: 6,451 (9.5%)
- Runtime: ~10 seconds

Unmatched examples: `london`, `usa`, `mixed martial arts`, `preserved film` — keywords
renamed, merged, or deleted in TMDB since the Kaggle snapshot was taken.

---

## Phase 2 — Search API fallback ✅

**Script:** `scripts/crawl_tmdb_keywords.py`

For the 6,451 keywords not in the daily export, called `/3/search/keyword?query={name}`
with exact name match, 20 concurrent via `asyncio.Semaphore(20)`.

**Results:** Found 4 more matches. Remaining 6,447 keywords are genuinely absent from
TMDB — they were deleted or renamed before the current export date.

**Final coverage: 61,469 / 67,916 (90.5%)** — this is the ceiling.

---

## Phase 3 — Movie-level enrichment (optional)

For keywords still unmatched, call:
```
GET /3/movie/{tmdb_movie_id}/keywords
```

This returns keywords with IDs attached. Calling for the ~1K movies most associated
with rare keywords (by `n_movies` count) could recover some IDs for keywords that exist
in TMDB under a different normalization than the Kaggle snapshot used.

**Cost:** ~1K requests, negligible time. Low expected yield given Phase 2 found almost
nothing — the unmatched keywords are likely truly gone from TMDB.

---

## Rate limiting policy

TMDB documented limit: **40 req / 10s** (older), practical: **~50 req/s** per IP.

Safe crawler design:
```
concurrency: asyncio.Semaphore(20)   # conservative for long-running jobs
on 429: sleep Retry-After + exponential backoff (max 60s)
on timeout: retry up to 3x with 2^n seconds wait
```

Never use the documented 40/10s limit as a target — treat it as a ceiling.

---

## Output schema

`data/tmdb_keywords_canonical.csv` (gitignored, generated):
```
tmdb_keyword_id, name
```

`output/tmdb_keyword_lexicon.csv` (gitignored, published to Kaggle):
```
keyword, tmdb_keyword_id, n_movies, emolex_found, ...
```

---

## True enum vs observed enum

The Kaggle CSV gives us an **observed enum**: keywords seen on movies in that snapshot.
The TMDB daily export gives us the **true enum**: every keyword TMDB has ever created.

The true enum (84,761) is larger than observed (67,916) because:
- Some TMDB keywords appear on movies not in the Kaggle dataset
- Some keywords exist in TMDB but are attached to no movies yet

The 9.5% gap in the other direction (Kaggle keywords with no TMDB ID) reflects keywords
that existed when the Kaggle snapshot was taken but have since been removed from TMDB.
