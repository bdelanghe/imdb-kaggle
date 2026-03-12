# TMDB Keyword SCL Pipeline

A pipeline that scores TMDB movie keywords using the [SCL (Sentiment Composition Lexicon)](https://www.saifmohammad.com/WebPages/SCL.html) hierarchy and aggregates the results to per-movie valence profiles. The pipeline runs monthly via GitHub Actions and publishes datasets to Kaggle.

---

## Final Artifacts

| Dataset | Kaggle | Description |
|---------|--------|-------------|
| **Movie × Keyword pairs (enriched)** | [tmdb-movie-keyword-pairs-scl-enriched](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-keyword-pairs-scl-enriched) | 928K (movie, keyword) pairs with SCL valence, polarity, keyword type — 84.7% have a valence score |
| **Movies enriched with sentiment** | [tmdb-movie-enriched-scl-aggregate](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-enriched-scl-aggregate) | 212K movies (with keywords only) — full metadata + keyword sentiment aggregate (weighted mean, polarity fractions, dominant polarity) |

---

## All Kaggle Datasets

| Dataset | Description |
|---------|-------------|
| [tmdb-movies-clean](https://www.kaggle.com/datasets/bdelanghe/tmdb-movies-clean) | ~280K TMDB movies, deduplicated and keyword-filtered against the canonical keyword list |
| [tmdb-keyword-enriched](https://www.kaggle.com/datasets/bdelanghe/tmdb-keyword-enriched) | 84K keywords with SCL valence, keyword type, `is_narrative`, `movie_count`, unigram-avg fallback coverage |
| [tmdb-scl-joined](https://www.kaggle.com/datasets/bdelanghe/tmdb-scl-joined) | NRC VAD v2.1 + SCL-OPP + SCL-NMA joined on term, with composition shift analysis and generated valence |
| [tmdb-movie-keyword-pairs-scl-enriched](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-keyword-pairs-scl-enriched) | 928K (movie, keyword) pairs — **primary edge list** with valence and polarity per pair |
| [tmdb-movie-sentiment-scores](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-sentiment-scores) | Per-movie keyword sentiment aggregate (weighted mean, polarity fractions) |
| [tmdb-movie-enriched-scl-aggregate](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-enriched-scl-aggregate) | **Primary final table** — 212K movies with full metadata + sentiment aggregate |

---

## Pipeline Overview

```
TMDB API
  -> tmdb_movies_clean.csv          (scripts/fetch_new_movies.py)
  -> tmdb_keywords_canonical.csv    (scripts/build_tmdb_canonical.py)

NRC VAD v2.1 + SCL-OPP + SCL-NMA
  -> 06_scl_join.ipynb              SCL joined lexicon (OPP > NMA > VAD hierarchy)

TMDB keywords x SCL joined lexicon
  -> 04_keyword_lexicon.ipynb       NRC emotion + VAD scores per keyword (67K)
  -> 07_keyword_valence.ipynb       SCL valence + keyword_type + exclude_from_scl (84K)
  -> 08_movie_keyword_join.ipynb    Explode + join + aggregate per movie (246K movies)
```

---

## Notebooks

### `04_keyword_lexicon.ipynb` -- NRC scores per keyword

Scores each unique TMDB keyword phrase against three NRC lexicons:
- **EmoLex** -- binary 0/1 per emotion + positive/negative (union across tokens)
- **Emotion Intensity** -- continuous 0-1 per emotion (mean across tokens)
- **VAD v2.1** -- valence/arousal/dominance bipolar -1 to +1 (MWE-first, then token mean)

Output: `output/keyword-lexicon/tmdb_keyword_lexicon.csv`

### `06_scl_join.ipynb` -- SCL joined lexicon

Full outer join of NRC VAD v2.1, SCL-OPP (opposing polarity phrases), and SCL-NMA
(negator/modal/adverb constructions) on `term`. Valence hierarchy: OPP > NMA > VAD.
Adds composition shift analysis -- how much a phrase's empirical score deviates from
naive token averaging.

Output: `output/scl-joined/scl_joined_lexicon.csv`

### `07_keyword_valence.ipynb` -- SCL valence + keyword type classification

Scores all 84K canonical TMDB keywords against the SCL joined lexicon using phrase-first
lookup with token-mean fallback. Adds two classification columns:

**`keyword_type`** -- enum classifying each keyword's role:

| type | description | exclude_from_scl |
|------|-------------|:---:|
| `structural` | TMDB-approved trivia: stingers, sequel, remake, flashback, woman director | yes |
| `source_material` | Adaptation origin: "based on novel", "based on true story" | yes |
| `adult` | Primary adult/pornographic content keyword | yes |
| `time_period` | Temporal setting: 1970s, 19th century, world war ii | yes |
| `setting_place` | Geographic setting: france, new york city, california | yes |
| `film_form` | Technical/format descriptor: short film, found footage, mockumentary | yes |
| `identity_social` | Social/identity topic: lgbt, racism, feminism, coming of age | yes |
| `genre_label` | Genre-adjacent label: film noir, satire, anime, horror | yes |
| `character` | Narrative archetype: vampire, detective, serial killer | |
| `theme` | Core narrative emotion: love, revenge, grief, betrayal | |
| `other` | Unclassified long-tail keywords | |

**`is_adult`** -- broad explicit content flag (superset of `adult` type).

**`exclude_from_scl`** -- True for types where SCL valence reflects word connotation
rather than narrative emotional content. See notebook for per-type rationale.

Output: `output/keyword-lexicon/tmdb_keyword_lexicon.csv`

### `08_movie_keyword_join.ipynb` -- Movie x keyword join and aggregate

Explodes each movie's keyword list to one row per (movie, keyword), joins the keyword
lexicon, then aggregates back to one row per movie. Valence stats are computed **only
over `exclude_from_scl = False` keywords** -- the full keyword set is always retained
in the exploded output for downstream use.

| column | description |
|--------|-------------|
| `total_keywords` | All keywords for this movie |
| `excluded_keyword_count` | Keywords removed by `exclude_from_scl` filter |
| `matched_keyword_count` | SCL-eligible keywords with a valence score |
| `avg_keyword_valence` | Mean valence -- the movie's narrative sentiment signal |
| `min/max_keyword_valence` | Sentiment range |
| `valence_std` | Spread -- high = tonally mixed |
| `shift_strong_count` | Keywords with strong compositional surprise |
| `composition_type_dominant` | Dominant linguistic mechanism (direct/opposing_polarity/idiomatic) |

Output: `output/movie-keyword-scores/movie_keyword_scores.csv`

---

## Why exclude metadata keywords from SCL aggregation

SCL valence is designed to score **narrative emotional content**. Many TMDB keywords
are metadata tags that describe production origin, era, geography, or format rather than
story emotion. Applying SCL to these produces spurious signals:

- `spain` = +0.67 (word sounds pleasant -- nothing to do with what happens in films set there)
- `horror` = -0.91 (genre label, not a plot emotion -- many horror films are enjoyed positively)
- `based on novel` = +0.28 (token-averaging "based"+"on"+"novel" produces noise)
- `disability` = -0.85 (word connotation pathologizes the subject, not the film's tone)

The `character` and `theme` types (`serial killer`, `revenge`, `grief`) have genuine
narrative emotional weight and are retained.

---

## Lexicons

| Lexicon | Entries | Scale | Source |
|---------|---------|-------|--------|
| NRC EmoLex | 14,182 words | binary 0/1, 8 emotions + pos/neg | [link](https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm) |
| NRC Emotion Intensity | 5,891 words | continuous 0-1, 8 emotions | [link](https://saifmohammad.com/WebPages/AffectIntensity.htm) |
| NRC VAD v2.1 | 54,801 (unigrams + MWEs) | bipolar -1 to +1 | [link](https://saifmohammad.com/WebPages/nrc-vad.html) |
| SCL-OPP | 1,178 phrases | bipolar -1 to +1 | [link](https://www.saifmohammad.com/WebPages/SCL.html) |
| SCL-NMA | 3,207 constructions | bipolar -1 to +1 | [link](https://www.saifmohammad.com/WebPages/SCL.html) |

All lexicons by Saif M. Mohammad, National Research Council Canada.

---

## Quickstart

```bash
cp .env.example .env        # set KAGGLE_API_TOKEN and TMDB_TOKEN
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Build SCL joined lexicon (one-time or on lexicon update)
jupyter nbconvert --to notebook --execute --inplace 06_scl_join.ipynb

# Build keyword lexicon with NRC scores
jupyter nbconvert --to notebook --execute --inplace 04_keyword_lexicon.ipynb

# Score keyword valence + classify types
jupyter nbconvert --to notebook --execute --inplace 07_keyword_valence.ipynb

# Join with movies and aggregate
jupyter nbconvert --to notebook --execute --inplace 08_movie_keyword_join.ipynb
```

The GitHub Actions workflow (`.github/workflows/pipeline.yml`) runs the full pipeline
monthly and pushes all four datasets to Kaggle. Requires `KAGGLE_API_TOKEN` and
`TMDB_TOKEN` as repository secrets.

---

## Data Provenance

```
TMDb API (themoviedb.org)
  -> ~280K movie records via /3/movie/{id}
  -> scripts/fetch_new_movies.py
  -> data/tmdb_movies_clean.csv

TMDB keyword exports (daily export files)
  -> scripts/download_tmdb_exports.py + build_tmdb_canonical.py
  -> data/tmdb_keywords_canonical.csv (84K canonical keywords with TMDB IDs)
```

TMDb data sourced from [The Movie Database](https://www.themoviedb.org/) per [TMDb API terms](https://www.themoviedb.org/api-terms-of-use).

---

## License

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) -- matching the upstream NRC lexicon license. Free for non-commercial use with attribution.
