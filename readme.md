# tmdb-nrc-emotional-intensity-movie-keywords

A dataset pipeline combining the [TMDB movies dataset](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies) (~930K movies) with the [NRC Emotional Intensity Lexicon](https://www.saifmohammad.com/WebPages/AffectIntensity.htm) to produce emotion-scored keyword features per movie.

The output is a Kaggle dataset annotating movie keywords with real-valued intensity scores (0–1) across eight emotions: anger, fear, joy, sadness, disgust, surprise, anticipation, trust.

## Quickstart

```bash
cp .env.example .env   # add KAGGLE_API_TOKEN
devbox run install-requirements
devbox run notebook
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for environment setup, task tracking, and editor configuration.
