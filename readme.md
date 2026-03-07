# IMDb Kaggle Dataset

## Setup

1. Copy `.env.example` to `.env` and set your `KAGGLE_API_TOKEN` (e.g. a KGAT_… token from Kaggle).
2. Keep `.env` out of version control (it is in `.gitignore`).

## Devbox (recommended)

Use [Devbox](https://www.jetpack.io/devbox/) for a consistent environment (Python 3.11 and deps).

1. Install devbox, then from the repo root:
   ```bash
   devbox run install-requirements   # once: installs deps into devbox env
   ```
2. **Load TMDb dataset:**  
   `devbox run load-tmdb` (add flags like `-- --nrows 10`).
3. **Jupyter in the browser:**  
   `devbox run notebook`.
4. **Interactive shell with env:**  
   `devbox shell` then run `python3 scripts/load_tmdb.py`, `jupyter notebook`, or open `load_tmdb.ipynb` with a kernel that uses the devbox Python (see below).

The script and the notebook both load `.env` so `KAGGLE_API_TOKEN` is used when you run from the repo root.

## Running a Python notebook

### With Devbox

- **Browser:** Run `devbox run notebook`, create or open a notebook, and run cells. The kernel uses the devbox Python and deps.
- **Cursor / VS Code:** To use the devbox Python as the notebook kernel, run `devbox run which python` and set that path as the Jupyter kernel interpreter (e.g. add a kernel spec pointing at the devbox Python). Alternatively use the venv flow below.

### Without Devbox (e.g. Cursor with venv)

1. From the repo root:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
2. In Cursor, set the Python interpreter to `${workspaceFolder}/.venv/bin/python` (or reload the window so it picks up `.vscode/settings.json`).
3. Open `load_tmdb.ipynb` and run cells; the notebook loads `.env` for Kaggle.

## Loading the TMDb dataset (CLI)

- **With devbox:** `devbox run load-tmdb` (optional: `devbox run load-tmdb -- --nrows 5 --dataset owner/slug`).
- **Without devbox:** `python3 scripts/load_tmdb.py` (from repo root; script loads `.env`).

## NRC Emotion Lexicon

The NRC Emotion Lexicon file lives at `data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt`. To refresh:

```bash
mkdir -p data
curl -L https://nyc3.digitaloceanspaces.com/ml-files-distro/v1/upshot-trump-emolex/data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt -o data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt
```

## Linking accounts on Kaggle

**Google Cloud Services** – In a Kaggle notebook: **Add-ons > Google Cloud Services**, then follow the prompts.

**GitHub** – In a Kaggle notebook: **File > Open & Upload Notebook > GitHub**, then check **Include Private Repositories** if needed.
