# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

This project uses [Devbox](https://www.jetpack.io/devbox/) (Python 3.11) as the recommended environment.

```bash
# First-time setup
devbox run install-requirements

# Or without devbox (venv)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Credentials: copy `.env.example` to `.env` and set `KAGGLE_API_TOKEN` (a `KGAT_…` token from Kaggle). The devbox shell auto-sources `.env` via `init_hook`.

## Commands

```bash
# Load TMDb dataset (CLI)
devbox run load-tmdb                          # default: 5 rows
devbox run load-tmdb -- --nrows 100           # custom row count
devbox run load-tmdb -- --dataset owner/slug  # different dataset

# Without devbox
python3 scripts/load_tmdb.py --nrows 10

# Jupyter notebook
devbox run notebook
```

## Architecture

This is a data exploration project, not a web app. The two main entry points share the same logic:

- **`scripts/load_tmdb.py`** — CLI script with `--dataset`, `--nrows`, and `--pandas-kwargs` (JSON string) flags. Downloads via `kagglehub.dataset_download()`, resolves whether the result is a zip or extracted directory, and reads the first CSV found.
- **`load_tmdb.ipynb`** — Notebook that mirrors the script logic and adds further analysis: keyword extraction, NRC Emotion Lexicon scoring (word-level sentiment/emotion pivot), and NRC Emotion Intensity Lexicon scoring.

**Data flow:** Kaggle API → `kagglehub` cache (`~/.cache/kagglehub/`) → zip/CSV resolution → pandas DataFrame.

**Key dataset:** `asaniczka/tmdb-movies-dataset-2023-930k-movies` (~930K movies, 24 columns including genres, keywords, revenue, ratings).

**NRC Emotion Lexicon:** `data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt` — tab-separated (word, emotion, 0|1), 46-line header to skip. Refresh command in `readme.md`.

**Kaggle credentials resolution order** (in both script and notebook):
1. `KAGGLE_API_TOKEN` env var
2. `KAGGLE_USERNAME` + `KAGGLE_KEY` env vars
3. `~/.kaggle/kaggle.json` or `~/.kaggle/access_token`
