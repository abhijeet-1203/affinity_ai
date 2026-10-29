"""Explanation helpers exposed to the API layer."""

from .compatibility import score_pair  # noqa: F401  (re-exported for convenience)
from .weights import DIMENSION_META
from .starters import conversation_starters  # noqa: F401


def explain_result(result):
    """Return the explanation payload for one computed pair.

    Everything is derived from the CompatResult: no extra inference, no LLM.
    """
    return {
        "summary": result.explanation,
        "highlights": result.highlights,
        "why_recommended": _why(result),
        "aligned": [
            {"key": d.key, "label": DIMENSION_META[d.key]["label"], "percent": d.to_dict()["percent"]}
            for d in result.dimensions if d.available and d.score is not None and d.score >= 0.6
        ],
        "differences": result.differences,
        "missing": result.missing,
        "starters": conversation_starters(result.shared_interests),
        "calculation": _calculation(result),
    }


def _why(result):
    """One line naming the concrete reason this profile surfaced."""
    if result.shared_interests:
        return (f"Ranked on a preference alignment estimate of {int(round(result.overall))}% "
                f"with {len(result.shared_interests)} shared interest"
                f"{'s' if len(result.shared_interests) != 1 else ''}.")
    strongest = max(
        (d for d in result.dimensions if d.available and d.score is not None),
        key=lambda d: d.score,
        default=None,
    )
    if strongest is None:
        return "Both profiles are too incomplete to rank meaningfully."
    return (f"Ranked on a preference alignment estimate of {int(round(result.overall))}% "
            f"led by {DIMENSION_META[strongest.key]['label'].lower()} "
            f"({strongest.to_dict()['percent']}%).")


def _calculation(result):
    """The exact arithmetic behind the number, so it is auditable in the UI."""
    parts = []
    numerator = 0.0
    denominator = 0.0
    for d in result.dimensions:
        if d.available and d.score is not None:
            numerator += d.weight * d.score
            denominator += d.weight
            parts.append({
                "dimension": DIMENSION_META[d.key]["label"],
                "weight": round(d.weight, 4),
                "score": round(d.score, 4),
                "contribution": round(d.weight * d.score, 4),
            })
    return {
        "formula": "overall = sum(weight_i * score_i) / sum(weight_i) over dimensions with data",
        "components": parts,
        "numerator": round(numerator, 4),
        "denominator": round(denominator, 4),
        "overall": round(result.overall, 2),
        "coverage_percent": int(round(result.coverage * 100)),
        "missing_handling": ("Dimensions without enough information are dropped from both the "
                             "numerator and the denominator, then the remaining weights are "
                             "renormalised. They are never counted as zero."),
        "feedback_adjustment": round(result.feedback_adjustment, 2),
        "ranked_score": round(result.ranked_score, 2),
        "disclaimer": ("This is a preference alignment estimate computed from the profile fields "
                       "you both filled in. It is not a prediction of relationship success and "
                       "has not been validated as one."),
    }
