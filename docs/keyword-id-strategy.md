# Keyword ID Strategy

Goal: assign `tmdb_keyword_id` (and eventually `imdb_keyword_id`) to every keyword in `output/tmdb_keyword_lexicon.csv`.

---

## Data sources

| Source | Keywords | API cost | Freshness |
|--------|----------|----------|-----------|
| **TMDB daily export** | 84,761 | 0 requests | Updated daily at `files.tmdb.org` |
| **TMDB search/keyword** | any | 1 req/name, ~73 kw/s with 40 concurrency | Live |
| **TMDB movie/{id}/keywords** | per-movie | 1 req/movie | Live |
| **IMDB endpoint** | TBD | TBD | TBD |

---

## Phase 1 — TMDB daily export (zero API cost)

**Script:** `scripts/build_tmdb_canonical.py`

TMDB publishes a compressed JSONL export daily:
```
http://files.tmdb.org/p/exports/keyword_ids_MM_DD_YYYY.json.gz
```

One JSON object per line: `{"id": 9826, "name": "murder"}`.

Download once → 84,761 keyword IDs with no rate limiting.

**Match results against Kaggle keywords (90.5% coverage):**
- Kaggle keywords: 67,916
- Matched by exact lowercase name: 61,462 (90.5%)
- Unmatched: 6,453 (9.5%)

Unmatched examples: `london`, `usa`, `mixed martial arts`, `preserved film` — likely
renamed, merged, or differently normalized in TMDB vs the Kaggle snapshot.

---

## Phase 2 — Search API fallback for unmatched keywords

**Script:** `scripts/crawl_tmdb_keywords.py` (search mode, NaN-safe)

For the 6,453 keywords not in the daily export, call `/3/search/keyword?query={name}`
and look for exact name match in results.

**Rate limit strategy:**
- 40 concurrent requests via `asyncio.Semaphore(40)`
- 429 → sleep `Retry-After` header seconds + exponential backoff (2^attempt * 5s)
- Safe sustained rate: ~20 req/s (well under TMDB's ~50 req/s practical limit)
- Estimated time: 6,453 / 20 ≈ ~5 min

After this phase, gap drops from 9.5% → ~1–2% (keywords that no longer exist in TMDB).

---

## Phase 3 — IMDB integration

**Endpoint:** TBD (user has IMDB API access)

Add `imdb_keyword_id` column to the lexicon. IMDB also maintains a keyword vocabulary.
Cross-referencing TMDB ↔ IMDB keyword IDs creates a bridge useful for:
- Joining to IMDB datasets (title.keywords.tsv from IMDb Non-Commercial Datasets)
- Matching movies across both databases by shared keyword semantics
- Richer coverage (IMDB has its own distinct keyword set)

**Design:** add `imdb_keyword_id` as a separate column; don't try to merge the two
vocabularies since they're independently maintained with different semantics.

---

## Phase 4 — Movie-level keyword enrichment (optional)

For keywords still unmatched after phases 1–2, try:
```
GET /3/movie/{tmdb_movie_id}/keywords
```

This returns keywords with IDs attached. If we call this for the ~1K movies most likely
to use a rare keyword (based on `n_movies` count in the lexicon), we can recover IDs
for most remaining gaps.

**Cost:** ~1K requests ≈ negligible

---

## Rate limiting policy

TMDB documented limit: **40 req / 10s** (older), practical: **~50 req/s** per IP.

Safe crawler design:
```
concurrency: asyncio.Semaphore(20)   # conservative for long-running jobs
on 429: sleep Retry-After + exponential backoff (max 60s)
on timeout: retry up to 3x with 2^n seconds wait
```

Never use the documented 40/10s limit as a target — use it as a ceiling.

---

## Output schema

`data/tmdb_keywords_canonical.csv`:
```
tmdb_keyword_id, name
```

`output/tmdb_keyword_lexicon.csv` (updated):
```
keyword, tmdb_keyword_id, imdb_keyword_id, n_movies, emolex_found, ...
```

---

## What "true enum" vs "observed enum" means here

The Kaggle CSV gives us an **observed enum**: keywords we've seen on movies in that snapshot.
The TMDB daily export gives us the **true enum**: every keyword TMDB has ever created.

The true enum (84,761) is larger than observed (67,916) because:
- Some TMDB keywords appear on movies not in the Kaggle dataset
- Some keywords exist in TMDB but are attached to no movies yet

For our pipeline, we care about matching our observed keywords to IDs so we can use
`with_keywords=` in TMDB API queries and cross-reference with IMDB.
