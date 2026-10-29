"""Personalised dimension weights, normalised to sum to 1.0."""

DIMENSIONS = ("shared_interests", "semantic", "communication", "lifestyle")

DIMENSION_META = {
    "shared_interests": {
        "label": "Shared interests",
        "description": "Jaccard overlap of the interest tags you both chose.",
    },
    "semantic": {
        "label": "Interest & bio similarity",
        "description": "TF-IDF cosine over your written descriptions, expanded through a concept lexicon.",
    },
    "communication": {
        "label": "Communication style",
        "description": "Agreement on conversation depth, topics, shared-hobby importance and valued qualities.",
    },
    "lifestyle": {
        "label": "Lifestyle rhythm",
        "description": "Agreement on how you spend free time, planning style and social frequency.",
    },
}

# Illustrative starting point, not empirically validated. Users can change it.
DEFAULT_WEIGHTS = {
    "shared_interests": 0.35,
    "semantic": 0.25,
    "communication": 0.20,
    "lifestyle": 0.20,
}

MIN_WEIGHT_SUM = 1e-6


def normalize_weights(raw):
    """Return weights that sum to 1.0.

    Negative and missing values are treated as 0. Inputs written as percentages
    (summing near 100) are detected and divided by their own total. If nothing
    usable is supplied, the documented defaults are returned.
    """
    values = {}
    for key in DIMENSIONS:
        try:
            value = float((raw or {}).get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        values[key] = max(0.0, value)
    total = sum(values.values())
    if total <= MIN_WEIGHT_SUM:
        return dict(DEFAULT_WEIGHTS)
    return {key: round(values[key] / total, 6) for key in DIMENSIONS}


def weights_to_percent(weights):
    normalised = normalize_weights(weights)
    return {key: int(round(value * 100)) for key, value in normalised.items()}
