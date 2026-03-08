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

> **License**: NRC lexicons are free for research/non-commercial use. Commercial use requires permission from the author.
> See the [NRC EmoLex Ethics & Data Statement](https://www.saifmohammad.com/WebDocs/EmoLex-Ethics-Data-Statement.pdf) for full terms.

**NRC Word-Emotion Lexicon / EmoLex** (binary, 8 emotions + positive/negative sentiment):
- Homepage: https://www.saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm
- Download zip (includes wordlevel + senselevel + multilingual files):

```bash
mkdir -p data
curl -L https://www.saifmohammad.com/WebDocs/Lexicons/NRC-Emotion-Lexicon.zip \
  -o data/NRC-Emotion-Lexicon.zip && unzip data/NRC-Emotion-Lexicon.zip -d data/NRC-Emotion-Lexicon
```

**NRC Emotion Intensity Lexicon / EIL** (real-valued 0–1, 8 emotions):
- Homepage: https://www.saifmohammad.com/WebPages/AffectIntensity.htm

```bash
curl -L https://www.saifmohammad.com/WebDocs/Lexicons/NRC-Emotion-Intensity-Lexicon.zip \
  -o data/NRC-Emotion-Intensity-Lexicon.zip && unzip data/NRC-Emotion-Intensity-Lexicon.zip -d data/NRC-Emotion-Intensity-Lexicon
```

### Emotion–sentiment correlation (empirical, computed from EmoLex)

Words in EmoLex with a given emotion label are also labelled positive/negative at these rates:

| emotion      | pos%  | neg%  | signal            |
|--------------|-------|-------|-------------------|
| joy          | 98.4% | 5.4%  | strongly positive |
| trust        | 69.3% | 5.8%  | positive          |
| anticipation | 57.5% | 21.1% | positive          |
| surprise     | 41.4% | 40.8% | mixed             |
| anger        | 4.7%  | 92.0% | strongly negative |
| disgust      | 2.8%  | 91.8% | strongly negative |
| sadness      | 4.8%  | 89.7% | strongly negative |
| fear         | 6.8%  | 83.4% | negative          |

This mapping drives the `{emotion}_positive_intensity` / `{emotion}_negative_intensity` features in `nrc_scored`.

## Kaggle

Credentials are resolved in order: `KAGGLE_API_TOKEN` env var → `KAGGLE_USERNAME` + `KAGGLE_KEY` → `~/.kaggle/kaggle.json`.

Linking accounts in a Kaggle notebook:
- **Google Cloud** — Add-ons > Google Cloud Services
- **GitHub** — File > Open & Upload Notebook > GitHub (check Include Private Repositories)
