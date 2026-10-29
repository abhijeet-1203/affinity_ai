# ML methodology

## Inputs
Per profile: interest tag set, free text (bio + interest labels), structured questionnaire answers,
and the member's four dimension weights.

## Dimensions
1. **Shared interests (Jaccard).** `|A∩B|/|A∪B|` over normalised tags. Both empty → unavailable.
2. **Semantic similarity.** Tokenise → stopwords removed → light suffix stemming → concept expansion
   (`hiking|trekking|trail → outdoor_hiking`) → IDF over the profiles in play →
   `cosine(v_A, v_B)` clipped to [0,1]. Empty text on either side → unavailable.
3. **Communication.** Questions `conversation_depth` (categorical map), `conversation_topics`
   (multi-select Jaccard), `shared_hobbies_importance` (ordinal), `valued_qualities` (multi-select).
4. **Lifestyle.** `free_time` (categorical map), `planning_style`, `social_frequency` (ordinal).

Ordinal similarity: `1 − |a−b|/(max−min)`. Categorical: explicit pair map, default 0.3 for
unlisted pairs. Multi-select / sets: Jaccard.

## Aggregation
`overall = Σ wᵢsᵢ / Σ wᵢ` over available dimensions; `coverage = Σ wᵢ(available) / Σ wᵢ`.
Confidence bands: high ≥ 0.85, moderate ≥ 0.60, limited ≥ 0.35, else low. Missing dimensions are
reported by name with the reason, never scored as zero.

## Ranking
Eligibility filters → minimum one available dimension → score = overall + bounded feedback
adjustment (≤ ±6 pts, ±1.5 per matching-interest feedback row, only positive/negative explicit
signals) → sort by (score, coverage, stable hash of the pair) → diversity pass (≤ 2 with the same
top interest consecutively) → paginate. Popularity, age, gender and profile length never enter the
score or the tie-break.

## Explanations
Deterministic templates populated from the computed `CompatResult` (shared interests, semantic
score, strongest/weakest dimension, matched questions, missing dimensions). Starters come from a
template catalogue keyed by shared interest; unknown interests use a neutral template naming the
interest. No generative model writes evidence.

## Evaluation
Synthetic dataset: 12 hand-written fictional profiles, 27 hand-labelled relevant pairs. Metrics:
Precision@k, Recall@k, NDCG@k, catalogue coverage, interest diversity, average information coverage,
score distribution, and a semantic separation check (paraphrase vs unrelated pairs). A random
baseline is computed over the same labels. Results are stored in `aa_eval_runs` and displayed only
after a run has actually happened.
