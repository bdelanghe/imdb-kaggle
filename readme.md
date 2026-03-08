# tmdb-nrc-emotional-intensity-movie-keywords

A pipeline that combines the [TMDB movies dataset](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies) (~1.38M movies) with three NRC affective lexicons to produce per-movie emotion and sentiment scores derived from plot keywords.

**Output dataset:** [kaggle.com/datasets/bdelanghe/tmdb-movie-vad-emotion-scores](https://www.kaggle.com/datasets/bdelanghe/tmdb-movie-vad-emotion-scores)

**Analysis notebook:** [kaggle.com/code/bdelanghe/exploring-emotional-profiles-in-1-38m-tmdb-movies](https://www.kaggle.com/code/bdelanghe/exploring-emotional-profiles-in-1-38m-tmdb-movies)

---

## What it produces

36 columns per movie — all 24 original TMDB columns plus 12 scored columns:

| Column | Source | Description |
|--------|--------|-------------|
| `sentiment` | derived | positive / negative / neutral / unknown |
| `valence` | NRC VAD | positivity of keyword associations (0–1) |
| `arousal` | NRC VAD | energy/activation level (0–1) |
| `dominance` | NRC VAD | sense of control/power (0–1) |
| `anger` | NRC Intensity | mean anger intensity across keywords (0–1) |
| `anticipation` | NRC Intensity | mean anticipation intensity (0–1) |
| `disgust` | NRC Intensity | mean disgust intensity (0–1) |
| `fear` | NRC Intensity | mean fear intensity (0–1) |
| `joy` | NRC Intensity | mean joy intensity (0–1) |
| `sadness` | NRC Intensity | mean sadness intensity (0–1) |
| `surprise` | NRC Intensity | mean surprise intensity (0–1) |
| `trust` | NRC Intensity | mean trust intensity (0–1) |

Column order in CSV: `id, title, keywords, sentiment, valence, arousal, dominance, anger … trust`, then remaining TMDB metadata.

**Coverage:** 1,382,594 movies — 320,895 (23.2%) have keyword coverage and receive emotion scores. The remaining 76.8% are scored `unknown` (no TMDB keywords).

---

## Lexicons used

| Lexicon | Words | Dimensions | Link |
|---------|-------|------------|------|
| NRC Emotion Lexicon (EmoLex) | 14,182 | binary (8 emotions + pos/neg) | [link](https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm) |
| NRC Emotion Intensity Lexicon | 5,891 | continuous 0–1 (8 emotions) | [link](https://saifmohammad.com/WebPages/AffectIntensity.htm) |
| NRC VAD Lexicon | 19,971 | continuous 0–1 (valence, arousal, dominance) | [link](https://saifmohammad.com/WebPages/nrc-vad.html) |

All lexicons by Saif M. Mohammad, National Research Council Canada. Full index: [saifmohammad.com/WebPages/lexicons.html](https://saifmohammad.com/WebPages/lexicons.html)

---

## Pipeline

```
TMDB keywords (comma-separated phrases)
  → tokenize on whitespace / hyphens
  → lemmatize (NLTK WordNetLemmatizer, noun / verb / adj POS)
  → look up each lemma in NRC intensity + VAD dicts
  → average matched token scores per keyword
  → average keyword scores per movie
```

**Notebooks:**
- `01_lexicons.ipynb` — load NRC files, build lookup dicts, save `data/lexicons/nrc_lookups.pkl` (run once)
- `02_score_and_export.ipynb` — load TMDB + pickle, score all movies, write CSV, upload to Kaggle
- `kaggle_notebook.ipynb` — analysis notebook published to Kaggle; genre VAD profiles, top films by emotion, visualizations

**Performance:** ~408K movies/sec on 1.38M rows (~3.5s total), 828 MB peak RAM.

**Automation:** `.github/workflows/pipeline.yml` runs the full pipeline on a monthly schedule and on manual dispatch. Requires `KAGGLE_API_TOKEN` set as a repository secret.

---

## Methodological notes

Scores represent **perceived emotional word associations** — not ground-truth movie sentiment. See: Mohammad (2020), [Practical and Ethical Considerations in the Effective use of Emotion and Sentiment Lexicons](https://www.saifmohammad.com/WebDocs/EmoLex-Ethics-Data-Statement.pdf).

- Scores are **relative, not absolute** — valence 0.7 means "more positive than 0.6", not "70% positive"
- **Association ≠ denotation** — "party" associates with joy but does not mean joy
- ~77% of rows have no TMDB keywords and are scored as `unknown`

Correct interpretation: *"Movies with these keywords contain more joy-associated language"* — not *"this movie is joyful."*

---

## Quickstart

```bash
cp .env.example .env        # add KAGGLE_API_TOKEN
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Step 1 — build lexicon pickle (once)
jupyter nbconvert --to notebook --execute 01_lexicons.ipynb

# Step 2 — score all movies + export CSV
jupyter nbconvert --to notebook --execute 02_score_and_export.ipynb

# Step 3 — upload to Kaggle
kaggle datasets version -p output -m "your message"

# Step 4 — push analysis notebook
kaggle kernels push -p .
```

Output CSV is **not tracked in git** — Kaggle is the source of truth.

---

## License

This dataset is released under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — the same non-commercial share-alike restriction as the upstream NRC lexicons by Saif M. Mohammad (National Research Council Canada). You may use and share it freely for non-commercial purposes with attribution.

Source data: [TMDB Movies Dataset](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies) — check upstream license for TMDB data terms.

---

## Future work / related lexicons

- [Warriner VAD](https://link.springer.com/article/10.3758/s13428-012-0314-x) — 13,915 human-rated lemmas, strong validation source for NRC VAD
- [ANEW](https://pdodds.w3.uvm.edu/teaching/courses/2009-08UVM-300/docs/others/everything/bradley1999a.pdf) — classic VAD norms
- [LIWC](https://www.liwc.app) — category-based psycholinguistic features
- [SenticNet](https://sentic.net) — concept-level sentiment for multi-word phrases
- [MovieLens Tag Genome](https://grouplens.org/datasets/movielens/tag-genome-2021/) — semantic movie tags with relevance scores
