"""Similarity primitives: Jaccard, semantic cosine, structured alignment."""

from .questionnaire import QUESTIONS, answer_label, answer_similarity, describe_difference
from .text import build_idf, cosine, tfidf_vector, tokenize


def jaccard(a, b):
    """Jaccard similarity of two interest sets.

    Returns (score, shared, union_size). Both-empty returns (None, [], 0) - an
    explicitly unavailable dimension rather than a zero.
    """
    sa = {x for x in (a or []) if str(x).strip()}
    sb = {x for x in (b or []) if str(x).strip()}
    if not sa or not sb:
        return None, [], 0
    shared = sa & sb
    union = sa | sb
    return len(shared) / len(union), sorted(shared), len(union)


def semantic_similarity(text_a, text_b, corpus=None):
    """Cosine similarity of lexicon-expanded TF-IDF vectors.

    `corpus` should contain both texts plus every other profile in play so the
    IDF weights are meaningful; when it is omitted the pair itself is used.
    Returns (score, available) where score is None when both texts are empty.
    """
    a = (text_a or "").strip()
    b = (text_b or "").strip()
    if not a or not b:
        return None, False
    if not tokenize(a) or not tokenize(b):
        return None, False
    docs = list(corpus or []) + [a, b]
    idf = build_idf(docs)
    score = cosine(tfidf_vector(a, idf), tfidf_vector(b, idf))
    return round(score, 4), True


def dimension_from_answers(answers_a, answers_b, dimension):
    """Mean similarity across the answered questions of one dimension.

    Returns (score, per-question detail, shared_answers, differing_answers).
    Questions either side skipped are omitted, never scored as zero.
    """
    scores = []
    detail = []
    aligned = []
    differences = []
    for question in QUESTIONS:
        if question["dimension"] != dimension:
            continue
        raw_a = answers_a.get(question["key"])
        raw_b = answers_b.get(question["key"])
        similarity = answer_similarity(question, raw_a, raw_b)
        if similarity is None:
            detail.append({"key": question["key"], "prompt": question["prompt"], "status": "missing"})
            continue
        scores.append(similarity)
        label_a = answer_label(question, raw_a)
        label_b = answer_label(question, raw_b)
        entry = {
            "key": question["key"],
            "prompt": question["prompt"],
            "similarity": round(similarity, 3),
            "you": label_a,
            "them": label_b,
        }
        if similarity >= 0.75:
            aligned.append(entry)
        elif similarity <= 0.4:
            entry["note"] = describe_difference(question, raw_a, raw_b)
            differences.append(entry)
        detail.append(entry)
    if not scores:
        return None, detail, aligned, differences
    return round(sum(scores) / len(scores), 4), detail, aligned, differences
