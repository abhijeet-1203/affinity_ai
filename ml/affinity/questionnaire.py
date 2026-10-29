"""The compatibility questionnaire: what is asked, and how answers compare.

Every question is optional. Each one belongs to exactly one scoring dimension and
declares how two answers relate, so "different" is never silently treated as
"incompatible" and a skipped question is never treated as a disagreement.
"""

# Answer kinds:
#   ordinal    - ordered 1..5 scale, compared by normalised distance
#   categorical- explicit pair map; unlisted pairs fall back to `default`
#   multiselect- Jaccard over chosen options

ORDINAL_LABELS = {
    1: "Not at all",
    2: "Slightly",
    3: "Moderately",
    4: "Very",
    5: "Extremely",
}

QUESTIONS = [
    {
        "key": "free_time",
        "dimension": "lifestyle",
        "prompt": "How do you most like to spend a free day?",
        "kind": "categorical",
        "options": [
            {"value": "outdoors", "label": "Outside, moving around"},
            {"value": "home", "label": "At home, recharging"},
            {"value": "social", "label": "With people, out and about"},
            {"value": "creative", "label": "Making or learning something"},
        ],
        # 1.0 aligned / 0.5 partially aligned / 0.2 different but workable
        "pairs": {
            ("outdoors", "outdoors"): 1.0, ("outdoors", "creative"): 0.5,
            ("outdoors", "social"): 0.5, ("outdoors", "home"): 0.2,
            ("home", "home"): 1.0, ("home", "creative"): 0.5,
            ("home", "social"): 0.2, ("home", "outdoors"): 0.2,
            ("social", "social"): 1.0, ("social", "outdoors"): 0.5,
            ("social", "creative"): 0.2, ("social", "home"): 0.2,
            ("creative", "creative"): 1.0, ("creative", "outdoors"): 0.5,
            ("creative", "home"): 0.5, ("creative", "social"): 0.2,
        },
        "default": 0.3,
    },
    {
        "key": "conversation_depth",
        "dimension": "communication",
        "prompt": "Which conversations do you get the most out of?",
        "kind": "categorical",
        "options": [
            {"value": "deep", "label": "Deep and reflective"},
            {"value": "light", "label": "Playful and light"},
            {"value": "mix", "label": "A mix of both"},
        ],
        "pairs": {
            ("deep", "deep"): 1.0, ("deep", "mix"): 0.8, ("deep", "light"): 0.3,
            ("light", "light"): 1.0, ("light", "mix"): 0.8, ("light", "deep"): 0.3,
            ("mix", "mix"): 1.0, ("mix", "deep"): 0.8, ("mix", "light"): 0.8,
        },
        "default": 0.4,
    },
    {
        "key": "conversation_topics",
        "dimension": "communication",
        "prompt": "What do you like talking about most?",
        "kind": "multiselect",
        "options": [
            {"value": "ideas", "label": "Ideas and how things work"},
            {"value": "everyday", "label": "Everyday life and people"},
            {"value": "humour", "label": "Jokes and banter"},
            {"value": "culture", "label": "Culture, books, film, music"},
        ],
        "min_selected": 1,
        "max_selected": 3,
    },
    {
        "key": "planning_style",
        "dimension": "lifestyle",
        "prompt": "Plans or spontaneity?",
        "kind": "ordinal",
        "options": [{"value": str(i), "label": ORDINAL_LABELS[i]} for i in range(1, 6)],
        "scale_labels": {1: "Always plan ahead", 5: "Fully spontaneous"},
    },
    {
        "key": "social_frequency",
        "dimension": "lifestyle",
        "prompt": "How often do you enjoy social activities?",
        "kind": "ordinal",
        "options": [{"value": str(i), "label": ORDINAL_LABELS[i]} for i in range(1, 6)],
        "scale_labels": {1: "Rarely", 5: "Almost every day"},
    },
    {
        "key": "shared_hobbies_importance",
        "dimension": "communication",
        "prompt": "How important are shared hobbies to you?",
        "kind": "ordinal",
        "options": [{"value": str(i), "label": ORDINAL_LABELS[i]} for i in range(1, 6)],
        "scale_labels": {1: "Not important", 5: "Essential"},
    },
    {
        "key": "valued_qualities",
        "dimension": "communication",
        "prompt": "Which qualities do you appreciate in a connection?",
        "kind": "multiselect",
        "options": [
            {"value": "curiosity", "label": "Curiosity"},
            {"value": "kindness", "label": "Kindness"},
            {"value": "ambition", "label": "Ambition"},
            {"value": "humour", "label": "Humour"},
            {"value": "calm", "label": "Calm"},
        ],
        "min_selected": 1,
        "max_selected": 3,
    },
]

QUESTIONS_BY_KEY = {q["key"]: q for q in QUESTIONS}
DIMENSIONS_OF_QUESTIONS = {q["key"]: q["dimension"] for q in QUESTIONS}


def question_public_view():
    """Question definitions safe to send to the browser (no scoring internals)."""
    out = []
    for q in QUESTIONS:
        out.append({
            "key": q["key"],
            "dimension": q["dimension"],
            "prompt": q["prompt"],
            "kind": q["kind"],
            "options": q["options"],
            "scale_labels": q.get("scale_labels"),
            "min_selected": q.get("min_selected"),
            "max_selected": q.get("max_selected"),
            "required": False,
        })
    return out


def _as_set(value):
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(v).strip().lower() for v in value if str(v).strip()}
    text = str(value).strip()
    if not text:
        return set()
    if "," in text:
        return {part.strip().lower() for part in text.split(",") if part.strip()}
    return {text.lower()}


def ordinal_similarity(a, b):
    """1.0 for the same answer, 0.0 for opposite ends of a 5-point scale."""
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):
        return None
    return max(0.0, 1.0 - abs(x - y) / 4.0)


def categorical_similarity(question, a, b):
    av, bv = str(a).strip().lower(), str(b).strip().lower()
    if not av or not bv:
        return None
    if av == bv:
        return 1.0
    pairs = question.get("pairs") or {}
    if (av, bv) in pairs:
        return pairs[(av, bv)]
    if (bv, av) in pairs:
        return pairs[(bv, av)]
    return question.get("default", 0.3)


def multiselect_similarity(a, b):
    sa, sb = _as_set(a), _as_set(b)
    if not sa or not sb:
        return None
    return len(sa & sb) / len(sa | sb)


def answer_similarity(question, a, b):
    """Similarity for one question, or None when it cannot be compared."""
    if a is None or b is None:
        return None
    kind = question["kind"]
    if kind == "ordinal":
        return ordinal_similarity(a, b)
    if kind == "categorical":
        return categorical_similarity(question, a, b)
    if kind == "multiselect":
        return multiselect_similarity(a, b)
    return None


def answer_label(question, value):
    """Human-readable answer, used in explanations (never the raw questionnaire dump)."""
    if value is None:
        return None
    if question["kind"] == "multiselect":
        labels = [o["label"] for o in question["options"] if str(o["value"]).lower() in _as_set(value)]
        return ", ".join(labels) if labels else None
    if question["kind"] == "ordinal":
        try:
            num = int(float(value))
        except (TypeError, ValueError):
            return str(value)
        return (question.get("scale_labels") or {}).get(num) or ORDINAL_LABELS.get(num, str(value))
    for option in question["options"]:
        if str(option["value"]).lower() == str(value).strip().lower():
            return option["label"]
    return str(value)


def describe_difference(question, a, b):
    """A neutral sentence about two different answers - a topic, not a defect."""
    la, lb = answer_label(question, a), answer_label(question, b)
    if not la or not lb:
        return None
    return f"You picked \u201c{la}\u201d and they picked \u201c{lb}\u201d on \u201c{question['prompt']}\u201d."
