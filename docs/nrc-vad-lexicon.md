# NRC VAD Lexicon v2

> Mohammad, S.M. (2025). *NRC VAD Lexicon v2: Norms for Valence, Arousal, and Dominance for over 55k English Terms.* National Research Council Canada.
> Paper: `data/NRC-VAD-Lexicon-v2.1/Paper-VAD-v2-2025.pdf` | Project page: saifmohammad.com/WebPages/nrc-vad.html

---

## What it is

A human-annotated lexicon mapping English words and phrases to three continuous scores, each on a **-1 to +1** scale:

| Dimension | Low end (-1) | High end (+1) | Example contrast |
|-----------|-------------|--------------|-----------------|
| **Valence (V)** | negative / displeasure | positive / pleasure | *funeral* vs *banquet* |
| **Arousal (A)** | calm / passive / sluggish | active / excited / alert | *lazy* vs *nervous* |
| **Dominance (D)** | submissive / weak / out-of-control | powerful / competent / in-control | *delicate* vs *fight* |

v2.1 (released March 2025) covers **55,001 entries**: ~44,928 unigrams + ~10,073 multi-word expressions (MWEs) such as common phrases and light verb constructions — roughly 3× the coverage of v1.

---

## Why VAD?

Factor analysis studies (Osgood et al. 1957; Russell 1980) have consistently shown that V, A, and D are the three most important and largely independent dimensions of word meaning. They map to:

- **Valence** — the pleasure/displeasure axis; primary driver of approach vs. avoid responses
- **Arousal** — the activation axis; correlates with physiological engagement
- **Dominance** — the power/control axis; corresponds to "competence" in social psychology (Fiske et al. 2002)

Individual emotions (joy, anger, fear…) are positions in this 3D VAD space rather than independent categories. The lexicon bridges categorical emotion models (like the NRC Emotion Lexicon's 8 Plutchik emotions) and dimensional affect models.

---

## How the scores were created

1. **Term selection** — sourced from NRC Emotion Lexicon, ANEW, Warriner et al., General Inquirer, and the Prevalence dataset (Brysbaert et al. 2019, ~62k lemmas known to ≥70% of English speakers). MWEs from Muraki et al. 2023.

2. **Annotation** — crowdsourced via Amazon Mechanical Turk. Annotators rated each term on a 7-point scale (-3 to +3) for each of V, A, D. ~9 annotators per term. ~95% US-based, average age 34.

   The questionnaire defined each dimension carefully to prevent conflation. For example, the **valence** instructions explicitly broadened the concept beyond just "happy/sad":

   > *Consider positive feelings to be a broad category that includes: positiveness / pleasure / goodness / happiness / greatness / brilliance / superiority / health etc.*
   > *Consider negative feelings to be a category that includes: negativeness / displeasure / badness / unhappiness / insignificance / terribleness / inferiority / sickness etc.*

   Annotators were instructed to select **what most English speakers will agree with** (not their personal feeling), and they could look up unfamiliar words in a dictionary. The actual question presented was:

   > **Q: `<term>` is often associated with:**
   > - `+3` very positive feelings
   > - `+2` moderately positive feelings
   > - `+1` slightly positive feelings
   > - ` 0` not associated with positive or negative feelings
   > - `-1` slightly negative feelings
   > - `-2` moderately negative feelings
   > - `-3` very negative feelings

   **Arousal** instructions defined the dimension as:

   > *Consider activeness or arousal to be a broad category that includes: active, aroused, stimulated, excited, jittery, alert, etc.*
   > *Consider inactiveness or calmness to be a broad category that includes: inactive, calm, unaroused, passive, relaxed, sluggish, etc.*
   > *This task is not about sentiment. (For example, something can be positive and inactive (such as flower), positive and active (such as exercise and party), negative and active (such as murderer), and negative and inactive (such as negligent).)*

   **Dominance** instructions defined the dimension as:

   > *Consider dominance, competence, control of situation, or powerfulness to be a broad category that includes: dominant, competent, in control of the situation, powerful, influential, important, autonomous, etc.*
   > *Consider submissiveness, incompetence, controlled by outside factors, or weakness to be a broad category that includes: submissive, incompetent, not in control of the situation, weak, influenced, cared-for, guided, etc.*
   > *This task is not about sentiment. (For example, something can be positive and weak (such as a flower petal) and something can be negative and strong (such as tyrant).)*

   The repeated "not about sentiment" framing is deliberate: without it, annotators tend to conflate arousal and dominance with positivity, collapsing the three independent dimensions into one.

3. **Quality control** — ~2% of items were gold questions with known correct answers. Half showed a pop-up if answered incorrectly (immediate feedback); the other half were silent but tracked. Annotators falling below 80% accuracy on either gold set were filtered and their responses discarded.

4. **Aggregation** — raw -3 to +3 integer responses averaged, then linearly rescaled to -1 to +1.

**Reliability** (split-half reliability over 1,000 trials):

| Dimension | Spearman ρ | Pearson r |
|-----------|-----------|----------|
| Valence   | 0.98      | 0.99     |
| Arousal   | 0.97      | 0.98     |
| Dominance | 0.96      | 0.96     |

Scores above 0.95 indicate high reproducibility — independent halves of the annotator pool produce nearly identical results.

---

## How this project uses it

The pipeline in this repo uses NRC VAD v2.1 to score TMDB movie keywords:

1. Each TMDB keyword phrase is looked up directly in the MWE list; if not found, it's tokenized + lemmatized and token scores are averaged.
2. Keyword-level VAD scores are averaged per movie to produce per-movie `valence`, `arousal`, and `dominance` columns.
3. `sentiment` is derived from the sign of `valence` (positive / negative / neutral / unknown).

The MWE coverage is significant: phrases like "serial killer" or "coming of age" can be looked up as units rather than averaged from their component words, avoiding compositional errors.

**Caveat:** averaging scores across mixed-polarity tokens on a bipolar scale can wash out signal. E.g., "not happy" tokenizes to "not" + "happy", which may average to near 0 rather than a negative value. Phrases not in the MWE list are subject to this limitation. See: Mohammad et al., [Sentiment Composition of Words with Opposing Polarities](https://www.saifmohammad.com/WebPages/SCL.html).

---

## Relationship to other NRC lexicons

| Lexicon | Entries | What it provides |
|---------|---------|-----------------|
| NRC Emotion Lexicon (EmoLex) | 14,182 words | Binary membership in 8 emotion categories + pos/neg |
| NRC Emotion Intensity Lexicon | 5,891 words | Continuous 0–1 intensity for the same 8 emotions |
| **NRC VAD Lexicon v2.1** | 55,001 words + MWEs | Continuous -1 to +1 for valence, arousal, dominance |

EmoLex tells you *which* emotions a word associates with. Intensity tells you *how strongly*. VAD tells you *where* in affect-space the word sits, independent of discrete emotion labels.

---

## Limitations and ethical notes

- Coverage skews toward Standard American English; annotators are not representative of all English speakers.
- Scores reflect the **predominant word sense** — context-specific or domain-specific senses may differ.
- Scores are **perceptions at the time of annotation**, not immutable properties. Associations can shift culturally over time.
- Crowd annotators on MTurk skew male, white, and younger relative to the US population.
- **Don't over-claim from small samples.** VAD scores are reliable indicators of word-level associations in aggregate — not sentence-level emotion detectors. `'the use of high-valence words grew by 20%'` is meaningful when measured across thousands of instances; the same statistic from a single sentence or paragraph is noise. Do not draw inferences about a single utterance from the VAD scores of its constituent words.
- Use comparatively and at scale. Single-sentence inferences from VAD scores are unreliable.
- Claims should be about *word usage patterns*, not speaker emotional states (avoid essentialism).

Full ethics discussion: Mohammad (2023), [Best Practices in the Creation and Use of Emotion Lexicons](https://aclanthology.org/2023.eacl-main.236/).
