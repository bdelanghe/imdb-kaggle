# Development

## Environment

This project uses [Devbox](https://www.jetpack.io/devbox/) (Python 3.11) with [direnv](https://direnv.net/) for automatic environment loading.

```bash
# First-time setup
cp .env.example .env          # set KAGGLE_API_TOKEN (KGAT_... token from Kaggle)
devbox run install-requirements

# Start notebook
devbox run notebook

# Interactive shell
devbox shell
```

Direnv automatically loads the devbox environment and sets `BEADS_DIR` when you `cd` into the repo. Run `direnv allow` once after cloning.

### Without Devbox

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## VS Code / Cursor

`.vscode/settings.json` is committed and configures:

- **Python interpreter** — `.venv/bin/python`
- **Terminal** — devbox shell (auto-loads Python + env)
- **Jupyter output** — `output/` directory

To use the devbox Python as the notebook kernel, open any `.ipynb` and select the devbox kernel from the kernel picker, or run `devbox run which python` to find the interpreter path.

## Task Tracking (Beads)

Issues are tracked with [beads](https://github.com/steveyegge/beads) using the `imdb-` prefix. `BEADS_DIR` is set automatically via `.envrc`.

```bash
bd ready              # show unblocked tasks
bd show imdb-<id>     # view task details
bd update imdb-<id> --status=in_progress
bd close imdb-<id>
```

Current issues:

| ID | Title |
|---|---|
| `imdb-s4v` | Epic: Build dataset pipeline |
| `imdb-et4` | Restructure project layout |
| `imdb-pkc` | Fix NRC Intensity download (HTTP 406) |
| `imdb-bt9` | Build keyword→emotion intensity pipeline |
| `imdb-1b8` | Upload notebook + dataset to Kaggle |

## NRC Lexicons

**NRC Word-Emotion Lexicon** (binary, 8 emotions + 2 sentiments):

```bash
mkdir -p data
curl -L https://nyc3.digitaloceanspaces.com/ml-files-distro/v1/upshot-trump-emolex/data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt \
  -o data/NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt
```

**NRC Emotion Intensity Lexicon** (real-valued 0–1, 8 emotions): download from [saifmohammad.com](https://www.saifmohammad.com/WebPages/AffectIntensity.htm) — direct HTTP download returns 406, manual download required.

## Kaggle

Credentials are resolved in order: `KAGGLE_API_TOKEN` env var → `KAGGLE_USERNAME` + `KAGGLE_KEY` → `~/.kaggle/kaggle.json`.

Linking accounts in a Kaggle notebook:
- **Google Cloud** — Add-ons > Google Cloud Services
- **GitHub** — File > Open & Upload Notebook > GitHub (check Include Private Repositories)
