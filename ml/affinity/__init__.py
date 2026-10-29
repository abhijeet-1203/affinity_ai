"""AffinityAI compatibility engine.

Pure-stdlib, deterministic recommendation engine: shared-interest Jaccard,
lexicon-expanded TF-IDF semantic similarity, structured questionnaire alignment,
personalised weights with missing-data renormalisation, explainable output and
feedback-aware ranking. No external API is required for any of it.
"""

from .compatibility import (  # noqa: F401
    DIMENSIONS,
    CompatResult,
    DimensionScore,
    ProfileFeatures,
    extract_features,
    score_pair,
)
from .ranking import (  # noqa: F401
    CandidateDecision,
    eligibility,
    rank_candidates,
)
from .explain import explain_result, conversation_starters  # noqa: F401
from .weights import DEFAULT_WEIGHTS, normalize_weights  # noqa: F401

__all__ = [
    "DIMENSIONS",
    "CompatResult",
    "DimensionScore",
    "ProfileFeatures",
    "extract_features",
    "score_pair",
    "eligibility",
    "rank_candidates",
    "explain_result",
    "conversation_starters",
    "DEFAULT_WEIGHTS",
    "normalize_weights",
]
