# VAD Research Landscape (2022–2025)

The VAD paradigm (valence, arousal, dominance) has evolved steadily from its 1999 origin through several increasingly large annotated datasets. This doc maps the current state for the movie keyword sentiment project.

---

## The canonical progression

| Dataset | Year | Size | Notes |
|---------|------|------|-------|
| ANEW | 1999 | ~1k words | Bradley & Lang; origin of the paradigm |
| Warriner VAD | 2013 | ~14k words | Large crowdsourced expansion |
| NRC VAD v1 | 2018 | ~20k words | Mohammad; MTurk, high reliability |
| **NRC VAD v2.1** | **2025** | **~55k words + 10k MWEs** | Direct successor; what this project uses |
| MWE VAD ("Breaking Bad") | 2025 | 10k phrases | Compositionality study; subset overlapping v2.1 MWEs |

**This project uses NRC VAD v2.1.** See [`docs/nrc-vad-lexicon.md`](nrc-vad-lexicon.md) for methodology.

---

## NRC VAD Lexicon v2.1 (2025)

> Mohammad, S.M. (2025). *NRC VAD Lexicon v2: Norms for Valence, Arousal, and Dominance for over 55k English Terms.* NRC Canada.
> Paper: `data/NRC-VAD-Lexicon-v2.1/Paper-VAD-v2-2025.pdf`

Key additions over v1:
- ~25k new unigrams
- ~10k multi-word expressions (MWEs) — phrases like *serial killer*, *fall in love*, *coming of age*
- MWEs matter for TMDB keywords: most keywords are multi-word phrases that single-token lexicons can't score directly

The MWE file is at `data/NRC-VAD-Lexicon-v2.1/MWE/mwe-NRC-VAD-Lexicon-v2.1.txt` (10,073 entries). The main file (`NRC-VAD-Lexicon-v2.1.txt`) contains both unigrams and MWEs together (54,801 entries total).

---

## MWE compositionality paper ("Breaking Bad", 2025)

> arXiv: [2511.19816](https://arxiv.org/abs/2511.19816)
> *Norms for Valence, Arousal, and Dominance for over 10k English Multiword Expressions*

Annotates ~10k phrases and studies **emotional compositionality** — whether phrase emotion can be predicted from its component words.

Key finding: phrase emotion is **not always compositional**.

Examples:
```
cold  → neutral
blood → neutral
cold blood → negative
cold-blooded → very negative
```

This is the core problem with token-mean fallback in the pipeline: averaging "not" + "happy" yields ~0 instead of negative. The NRC VAD v2.1 MWE list partially addresses this by providing direct phrase scores.

The remaining gap — phrases not in any MWE list — is what `imdb-414` (SCL-OPP integration) targets.

---

## WorryWords (2024)

> arXiv: [2409.07901](https://arxiv.org/abs/2409.07901) (adjacent; see also WorryWords paper)

A ~44k word lexicon measuring **anxiety association**, derived by projecting the VAD space onto a specific psychological axis. Demonstrates that VAD can serve as a coordinate system for generating domain-specific emotion signals, not just the three base dimensions.

Not currently integrated; would require a separate lookup layer.

---

## The geometric shift in emotion modeling

Older NLP work used **discrete labels**:
```
anger / joy / fear / sadness
```

Newer work increasingly uses **continuous coordinates**:
```
(valence, arousal, dominance)
```

Reason: emotions behave like points on a continuous manifold, not bins.

```
terror → panic → fear → unease → anxiety
```

That's a gradient, not five separate categories. VAD captures it; categorical labels don't.

Researchers are now treating emotion vectors similarly to word embeddings — with addition, interpolation, and distance metrics making sense geometrically.

---

## Relevance to this project

| Concept | Where it matters |
|---------|-----------------|
| MWE scores | TMDB keywords are mostly phrases — direct lookup beats token mean |
| Compositionality limits | Token-mean fallback for uncovered phrases is lossy; see SCL-OPP (`imdb-414`) |
| VAD as coordinates | `(valence, arousal, dominance)` per movie enables continuous clustering, not just pos/neg buckets |
| RoBERTa hybrid (`imdb-b9v`) | Treats model output as a VAD-space signal to fill gaps where lexicons have no coverage |
