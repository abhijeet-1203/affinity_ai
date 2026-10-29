"""Profile feature extraction and the explainable compatibility score.

Scoring contract
----------------
* Four dimensions, each scored in [0, 1] or marked unavailable.
* A dimension is unavailable when either side lacks the information for it.
  Unavailable dimensions are *excluded from the weighted average and the
  remaining weights are renormalised* - missing data is never scored as zero.
* overall = sum(w_i * s_i for available i) / sum(w_i for available i)
* coverage = sum(w_i for available i) / sum(w_i for all i), reported alongside
  the score as "how much of what matters to you could actually be checked".
* The result is labelled a *preference alignment estimate*, never a probability
  of relationship success.
"""

from .similarity import dimension_from_answers, jaccard, semantic_similarity
from .weights import DIMENSIONS, DIMENSION_META, normalize_weights

DIMENSION_ORDER = DIMENSIONS

CONFIDENCE_BANDS = (
    (0.85, "high"),
    (0.60, "moderate"),
    (0.35, "limited"),
    (0.0, "low"),
)


class DimensionScore:
    __slots__ = ("key", "score", "available", "reason", "weight")

    def __init__(self, key, score=None, available=False, reason="", weight=0.0):
        self.key = key
        self.score = score
        self.available = available
        self.reason = reason
        self.weight = weight

    def to_dict(self):
        return {
            "key": self.key,
            "label": DIMENSION_META[self.key]["label"],
            "description": DIMENSION_META[self.key]["description"],
            "score": None if self.score is None else round(self.score, 4),
            "percent": None if self.score is None else int(round(self.score * 100)),
            "available": self.available,
            "reason": self.reason,
            "weight": round(self.weight, 4),
            "weight_percent": int(round(self.weight * 100)),
        }

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"DimensionScore({self.key!r}, score={self.score!r}, available={self.available!r})"


class CompatResult:
    """Everything the UI needs to explain one pair, and nothing it does not."""

    def __init__(self, overall, dimensions, coverage, confidence, shared_interests,
                 interest_overlap_count, union_count, differences, aligned_questions,
                 missing, explanation, semantic_corpus_size=0, feedback_adjustment=0.0,
                 ranked_score=None, highlights=None):
        self.overall = overall
        self.dimensions = dimensions
        self.coverage = coverage
        self.confidence = confidence
        self.shared_interests = shared_interests
        self.interest_overlap_count = interest_overlap_count
        self.union_count = union_count
        self.differences = differences
        self.aligned_questions = aligned_questions
        self.missing = missing
        self.explanation = explanation
        self.semantic_corpus_size = semantic_corpus_size
        self.feedback_adjustment = feedback_adjustment
        self.ranked_score = overall if ranked_score is None else ranked_score
        self.highlights = highlights or []

    def dimension(self, key):
        for dim in self.dimensions:
            if dim.key == key:
                return dim
        return None

    def to_dict(self):
        return {
            "overall": round(self.overall, 2),
            "ranked_score": round(self.ranked_score, 2),
            "label": "Preference alignment estimate",
            "coverage": round(self.coverage, 4),
            "coverage_percent": int(round(self.coverage * 100)),
            "confidence": self.confidence,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "shared_interests": self.shared_interests,
            "interest_overlap_count": self.interest_overlap_count,
            "interest_union_count": self.union_count,
            "differences": self.differences,
            "aligned_questions": self.aligned_questions,
            "missing": self.missing,
            "explanation": self.explanation,
            "highlights": self.highlights,
            "feedback_adjustment": round(self.feedback_adjustment, 2),
            "semantic_corpus_size": self.semantic_corpus_size,
        }


class ProfileFeatures:
    """Normalised profile representation handed to the scorer."""

    __slots__ = ("account_id", "display_name", "interests", "bio", "answers",
                 "age", "city", "discoverable", "onboarding_completed", "connection_type",
                 "demographics")

    def __init__(self, account_id, display_name="", interests=None, bio="",
                 answers=None, age=None, city=None, discoverable=True,
                 onboarding_completed=False, connection_type=None, demographics=None):
        self.account_id = str(account_id)
        self.display_name = display_name or ""
        self.interests = [str(i).strip() for i in (interests or []) if str(i).strip()]
        self.bio = bio or ""
        self.answers = dict(answers or {})
        self.age = age
        self.city = city
        self.discoverable = discoverable
        self.onboarding_completed = onboarding_completed
        self.connection_type = connection_type
        # Explicitly *not* used for scoring: kept only to document that no
        # protected attribute enters the model. Always empty in practice.
        self.demographics = demographics or {}

    @property
    def free_text(self):
        """The text the semantic dimension reads: the bio plus interest labels."""
        parts = [self.bio] + list(self.interests)
        return " ".join(part for part in parts if part)

    def answered_keys(self):
        return {k for k, v in self.answers.items() if v not in (None, "", [])}

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "display_name": self.display_name,
            "interests": self.interests,
            "bio": self.bio,
            "answers": self.answers,
            "age": self.age,
            "city": self.city,
            "discoverable": self.discoverable,
            "onboarding_completed": self.onboarding_completed,
            "connection_type": self.connection_type,
        }


def extract_features(row, interests=None, answers=None):
    """Build ProfileFeatures from a stored profile row plus its interests/answers."""
    if row is None:
        raise ValueError("a profile row is required")
    return ProfileFeatures(
        account_id=row.get("account_id") or row.get("id"),
        display_name=row.get("display_name") or "",
        interests=interests if interests is not None else row.get("interests") or [],
        bio=row.get("bio") or "",
        answers=answers if answers is not None else row.get("answers") or {},
        age=row.get("age"),
        city=row.get("city"),
        discoverable=bool(row.get("discoverable", True)),
        onboarding_completed=bool(row.get("onboarding_completed", False)),
        connection_type=row.get("connection_type"),
    )


def _confidence_for(coverage):
    for threshold, label in CONFIDENCE_BANDS:
        if coverage >= threshold:
            return label
    return "low"


def score_pair(a, b, weights=None, corpus_texts=None, feedback_adjustment=0.0):
    """Score two ProfileFeatures and explain the result.

    Deterministic: identical inputs always produce identical output. No network
    call, no randomness, no LLM.
    """
    w = normalize_weights(weights)

    dims = []
    # 1. Shared interests (Jaccard)
    jac, shared, union_size = jaccard(a.interests, b.interests)
    dims.append(DimensionScore(
        "shared_interests", jac, jac is not None, weight=w["shared_interests"],
        reason="" if jac is not None else "One of you has no interests listed, so overlap cannot be measured.",
    ))

    # 2. Semantic similarity (lexicon-expanded TF-IDF cosine)
    corpus = corpus_texts if corpus_texts is not None else [a.free_text, b.free_text]
    sem, sem_ok = semantic_similarity(a.free_text, b.free_text, corpus)
    dims.append(DimensionScore(
        "semantic", sem, sem_ok, weight=w["semantic"],
        reason="" if sem_ok else "Neither profile has written text to compare.",
    ))

    # 3 & 4. Structured questionnaire dimensions
    aligned, differences = [], []
    for key in ("communication", "lifestyle"):
        score, detail, dim_aligned, dim_diff = dimension_from_answers(a.answers, b.answers, key)
        aligned.extend(dim_aligned)
        differences.extend(dim_diff)
        answered = sum(1 for d in detail if d.get("similarity") is not None or d.get("prompt") and d.get("status") != "missing")
        dims.append(DimensionScore(
            key, score, score is not None, weight=w[key],
            reason="" if score is not None else "Not enough answered questions on both sides to compare this dimension.",
        ))

    available = [d for d in dims if d.available and d.score is not None]
    total_weight = sum(d.weight for d in dims) or 1.0
    available_weight = sum(d.weight for d in available)
    if available:
        overall = sum(d.weight * d.score for d in available) / available_weight
    else:
        overall = 0.0
    coverage = available_weight / total_weight

    missing = [
        {"key": d.key, "label": DIMENSION_META[d.key]["label"], "reason": d.reason}
        for d in dims if not d.available
    ]

    base_score = round(overall * 100.0, 2)
    ranked = max(0.0, min(100.0, base_score + float(feedback_adjustment or 0.0)))

    result = CompatResult(
        overall=base_score,
        dimensions=dims,
        coverage=coverage,
        confidence=_confidence_for(coverage),
        shared_interests=shared,
        interest_overlap_count=len(shared),
        union_count=union_size,
        differences=differences,
        aligned_questions=aligned,
        missing=missing,
        explanation="",
        semantic_corpus_size=len(corpus or []),
        feedback_adjustment=float(feedback_adjustment or 0.0),
        ranked_score=ranked,
    )
    result.explanation = _template_explanation(a, b, result)
    result.highlights = _highlights(result)
    return result


def _top_dimension(result):
    scored = [d for d in result.dimensions if d.available and d.score is not None]
    if not scored:
        return None
    return max(scored, key=lambda d: d.score * (0.5 + d.weight))


def _highlights(result):
    """Two or three short lines: the strongest evidence for this recommendation."""
    out = []
    if result.shared_interests:
        names = ", ".join(result.shared_interests[:3])
        out.append(f"{len(result.shared_interests)} shared interest"
                   f"{'s' if len(result.shared_interests) != 1 else ''}: {names}")
    top = _top_dimension(result)
    if top is not None and top.score >= 0.55:
        out.append(f"{DIMENSION_META[top.key]['label']} aligns at {int(round(top.score * 100))}%")
    if result.aligned_questions:
        out.append(f"{len(result.aligned_questions)} questionnaire answer"
                   f"{'s' if len(result.aligned_questions) != 1 else ''} matched closely")
    if result.missing:
        out.append(f"{len(result.missing)} dimension"
                   f"{'s' if len(result.missing) != 1 else ''} had too little information")
    return out[:3]


def _template_explanation(a, b, result):
    """Deterministic explanation written only from computed facts.

    No generative model is involved, so nothing here can be invented. An LLM may
    later be layered on for tone *after* this text exists, but the evidence lines
    below are the source of truth.
    """
    name = b.display_name or "This person"
    sentences = []

    strong = [d for d in result.dimensions if d.available and d.score is not None and d.score >= 0.6]
    weak = [d for d in result.dimensions if d.available and d.score is not None and d.score < 0.4]

    if result.shared_interests:
        listed = ", ".join(result.shared_interests[:4])
        sentences.append(f"You and {name} both listed {listed}.")
    elif result.dimension("shared_interests").available:
        sentences.append(f"You and {name} do not share any listed interests, so the comparison rests on your written profiles and answers.")

    semantic = result.dimension("semantic")
    if semantic.available and semantic.score and semantic.score >= 0.25:
        sentences.append(
            f"Your written descriptions also overlap in meaning (semantic similarity "
            f"{int(round(semantic.score * 100))}%), which is measured from the text you both wrote, not from shared tags."
        )
    elif semantic.available and semantic.score is not None:
        sentences.append(
            f"Your written descriptions overlap little (semantic similarity {int(round(semantic.score * 100))}%)."
        )

    if strong:
        labels = ", ".join(DIMENSION_META[d.key]["label"].lower() for d in strong[:2])
        sentences.append(f"The strongest alignment is in {labels}.")
    if result.aligned_questions:
        q = result.aligned_questions[0]
        sentences.append(f"On \u201c{q['prompt']}\u201d your answers were close.")
    if weak:
        labels = ", ".join(DIMENSION_META[d.key]["label"].lower() for d in weak[:2])
        sentences.append(f"{labels.capitalize()} differ more than the rest \u2014 a useful thing to talk about early.")
    if result.missing:
        labels = ", ".join(m["label"].lower() for m in result.missing[:2])
        sentences.append(f"There is not enough information to compare {labels}.")
    if not sentences:
        sentences.append("Both profiles are too thin to compare meaningfully yet.")
    return " ".join(sentences)
