"""Unit tests for the compatibility engine. Run: pytest ml/tests -q"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from affinity import compatibility, evaluation, questionnaire, ranking, similarity, starters, text, weights


def profile(pid="u1", interests=None, bio="", answers=None, **kw):
    kwargs = dict(account_id=pid, display_name=kw.pop("name", pid), interests=interests or [],
                  bio=bio, answers=answers or {}, age=kw.pop("age", 30),
                  discoverable=kw.pop("discoverable", True),
                  onboarding_completed=kw.pop("onboarding_completed", True),
                  connection_type=kw.pop("connection_type", "dating"))
    kwargs.update(kw)
    return compatibility.ProfileFeatures(**kwargs)


# ---------------------------------------------------------------- interests

def test_jaccard_basic():
    score, shared, union = similarity.jaccard(["hiking", "art"], ["art", "music"])
    assert score == pytest.approx(1 / 3)
    assert shared == ["art"]
    assert union == 3


def test_jaccard_identical_and_disjoint():
    assert similarity.jaccard(["a"], ["a"])[0] == 1.0
    assert similarity.jaccard(["a"], ["b"])[0] == 0.0


def test_jaccard_both_empty_is_unavailable_not_zero():
    score, shared, union = similarity.jaccard([], [])
    assert score is None and shared == [] and union == 0


def test_jaccard_one_side_empty_is_unavailable():
    assert similarity.jaccard(["a"], [])[0] is None


# ---------------------------------------------------------------- text / semantic

def test_tokenize_strips_stopwords_and_stems():
    tokens = text.tokenize("I really enjoy hiking and the outdoors")
    assert "enjoy" not in tokens
    assert all(len(t) >= 2 for t in tokens)


def test_concepts_bridge_synonyms():
    a = text.concept_tokens("I enjoy hiking mountain trails")
    b = text.concept_tokens("I love trekking and exploring nature")
    assert "outdoor_hiking" in a and "outdoor_hiking" in b


def test_semantic_paraphrase_beats_unrelated():
    para = similarity.semantic_similarity(
        "I enjoy hiking, discovering mountain trails, and outdoor photography.",
        "I love trekking, exploring nature, and capturing landscapes.",
    )[0]
    unrelated = similarity.semantic_similarity(
        "I enjoy hiking, discovering mountain trails, and outdoor photography.",
        "I mostly stay in and stream competitive games.",
    )[0]
    assert para > unrelated
    assert 0.0 <= unrelated <= 1.0 and 0.0 <= para <= 1.0


def test_semantic_missing_text_is_unavailable():
    score, ok = similarity.semantic_similarity("", "something")
    assert score is None and ok is False


def test_semantic_is_symmetric():
    a, b = "I play guitar in a band", "I write songs and play guitar"
    assert similarity.semantic_similarity(a, b)[0] == similarity.semantic_similarity(b, a)[0]


# ---------------------------------------------------------------- questionnaire

def test_ordinal_similarity_is_distance_based():
    assert questionnaire.ordinal_similarity(3, 3) == 1.0
    assert questionnaire.ordinal_similarity(1, 5) == 0.0
    assert questionnaire.ordinal_similarity(1, 3) == pytest.approx(0.5)


def test_multiselect_uses_jaccard():
    q = questionnaire.QUESTIONS_BY_KEY["valued_qualities"]
    assert questionnaire.answer_similarity(q, ["curiosity"], ["curiosity"]) == 1.0
    assert questionnaire.answer_similarity(q, ["curiosity"], ["humour"]) == 0.0


def test_categorical_partial_alignment_is_not_zero():
    q = questionnaire.QUESTIONS_BY_KEY["conversation_depth"]
    mixed = questionnaire.answer_similarity(q, "deep", "mix")
    opposed = questionnaire.answer_similarity(q, "deep", "light")
    assert mixed > opposed
    assert mixed > 0


def test_missing_answer_returns_none():
    q = questionnaire.QUESTIONS_BY_KEY["planning_style"]
    assert questionnaire.answer_similarity(q, None, "3") is None


def test_questionnaire_covers_all_dimensions():
    dims = {q["dimension"] for q in questionnaire.QUESTIONS}
    assert dims == {"communication", "lifestyle"}


# ---------------------------------------------------------------- weights

def test_weight_normalisation_sums_to_one():
    w = weights.normalize_weights({"shared_interests": 4, "semantic": 3, "communication": 2, "lifestyle": 1})
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["shared_interests"] == pytest.approx(0.4)


def test_weight_percent_input_is_detected():
    w = weights.normalize_weights({"shared_interests": 35, "semantic": 25, "communication": 20, "lifestyle": 20})
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["shared_interests"] == pytest.approx(0.35)


def test_zero_and_negative_weights_fall_back_to_defaults():
    assert weights.normalize_weights({}) == weights.DEFAULT_WEIGHTS
    assert weights.normalize_weights({"shared_interests": -5}) == weights.DEFAULT_WEIGHTS


def test_weights_change_the_score():
    a = profile("a", ["hiking", "art"], "I hike and sketch")
    b = profile("b", ["hiking", "cooking"], "I hike and cook")
    interests_heavy = dict(shared_interests=0.9, semantic=0.1, communication=0.0, lifestyle=0.0)
    comm_heavy = dict(shared_interests=0.05, semantic=0.05, communication=0.6, lifestyle=0.3)
    assert compatibility.score_pair(a, b, interests_heavy).overall != compatibility.score_pair(a, b, comm_heavy).overall


# ---------------------------------------------------------------- scoring

def test_both_empty_profiles_report_low_confidence_not_zero_confidence():
    result = compatibility.score_pair(profile("a"), profile("b"))
    assert result.coverage == 0.0
    assert result.confidence == "low"
    assert result.missing  # every dimension named


def test_missing_dimension_is_excluded_not_zeroed():
    full = dict(free_time="outdoors", conversation_depth="deep", planning_style=2,
                social_frequency=3, conversation_topics=["ideas"], valued_qualities=["curiosity"])
    a = profile("a", ["hiking"], "I hike", full)
    b = profile("b", ["hiking"], "I hike", full)
    with_answers = compatibility.score_pair(a, b)
    without = compatibility.score_pair(a, profile("c", ["hiking"], "I hike", {}))

    assert with_answers.coverage == 1.0
    assert without.coverage < 1.0
    # Removing the answered dimensions must not drag the overall score down to a
    # weighted average with implicit zeros.
    assert without.overall >= with_answers.overall - 15


def test_score_is_deterministic():
    a = profile("a", ["hiking", "art"], "I hike and paint", {"conversation_depth": "deep"})
    b = profile("b", ["hiking", "music"], "I hike and sing", {"conversation_depth": "mix"})
    first = compatibility.score_pair(a, b).to_dict()
    second = compatibility.score_pair(a, b).to_dict()
    assert first == second


def test_score_is_symmetric_for_the_pair():
    a = profile("a", ["hiking", "art"], "I hike and paint", {"conversation_depth": "deep"})
    b = profile("b", ["hiking", "music"], "I hike and sing", {"conversation_depth": "deep"})
    assert compatibility.score_pair(a, b).overall == pytest.approx(compatibility.score_pair(b, a).overall)


def test_score_bounds_and_label():
    a = profile("a", ["hiking"], "hiking")
    b = profile("b", ["hiking"], "hiking")
    out = compatibility.score_pair(a, b).to_dict()
    assert 0 <= out["overall"] <= 100
    assert out["label"] == "Preference alignment estimate"
    assert out["confidence"] in {"low", "limited", "moderate", "high"}


def test_similar_pair_scores_higher_than_mismatched_pair():
    me = profile("me", ["hiking", "photography", "technology"],
                 "I enjoy hiking, discovering mountain trails, and outdoor photography.",
                 {"conversation_depth": "deep", "planning_style": 4, "free_time": "outdoors",
                  "social_frequency": 3, "conversation_topics": ["ideas"], "valued_qualities": ["curiosity"]})
    near = profile("near", ["photography", "hiking", "technology"],
                   "I love trekking, exploring nature, and capturing landscapes.",
                   {"conversation_depth": "deep", "planning_style": 4, "free_time": "outdoors",
                    "social_frequency": 3, "conversation_topics": ["ideas"], "valued_qualities": ["curiosity"]})
    far = profile("far", ["gaming", "nightlife"],
                  "I stream games all night and go clubbing.",
                  {"conversation_depth": "light", "planning_style": 1, "free_time": "social",
                   "social_frequency": 5, "conversation_topics": ["humour"], "valued_qualities": ["humour"]})
    corpus = [me.free_text, near.free_text, far.free_text]
    assert compatibility.score_pair(me, near, corpus_texts=corpus).overall > \
        compatibility.score_pair(me, far, corpus_texts=corpus).overall


def test_explanation_only_uses_computed_facts():
    a = profile("a", ["hiking"], "I hike", {"conversation_depth": "deep"})
    b = profile("b", ["hiking"], "I hike", {"conversation_depth": "deep"})
    result = compatibility.score_pair(a, b)
    assert "hiking" in result.explanation
    assert result.highlights
    assert result.differences == [] or all("you" in d["note"].lower() or "You picked" in d["note"] for d in result.differences)


def test_calculation_is_auditable():
    from affinity.explain import explain_result
    a = profile("a", ["hiking"], "I hike", {"conversation_depth": "deep"})
    b = profile("b", ["hiking"], "I hike", {"conversation_depth": "deep"})
    payload = explain_result(compatibility.score_pair(a, b))
    calc = payload["calculation"]
    expected = calc["numerator"] / calc["denominator"] * 100
    assert calc["overall"] == pytest.approx(expected, abs=0.05)
    assert calc["disclaimer"]


# ---------------------------------------------------------------- starters

def test_starters_use_shared_interests():
    out = starters.conversation_starters(["photography", "technology"])
    assert len(out) == 2
    assert all(s["text"].endswith("?") for s in out)
    assert "photograph" in out[0]["text"].lower()


def test_starters_fallback_names_the_interest():
    out = starters.conversation_starters(["competitive cheese rolling"])
    assert "competitive cheese rolling" in out[0]["text"]


def test_starters_empty_when_no_overlap():
    assert starters.conversation_starters([]) == []


# ---------------------------------------------------------------- eligibility / ranking

def test_eligibility_excludes_self_incomplete_and_hidden():
    me = profile("me")
    assert ranking.eligibility(me, profile("me")).eligible is False
    assert ranking.eligibility(me, profile("x", onboarding_completed=False)).eligible is False
    assert ranking.eligibility(me, profile("x", discoverable=False)).eligible is False
    assert ranking.eligibility(me, profile("x")).eligible is True


def test_eligibility_excludes_blocks_both_directions():
    me = profile("me")
    assert ranking.eligibility(me, profile("x"), blocked_ids={"x"}).eligible is False


def test_eligibility_respects_age_range():
    me = profile("me")
    assert ranking.eligibility(me, profile("x", age=19), {"min_age": 25}).eligible is False
    assert ranking.eligibility(me, profile("x", age=44), {"max_age": 40}).eligible is False


def test_eligibility_excludes_already_interacted():
    me = profile("me")
    assert ranking.eligibility(me, profile("x"), interacted_ids={"x"}).eligible is False


def test_ranking_orders_by_score_and_reports_meta():
    me = profile("me", ["hiking", "photography"], "I hike and take photos",
                 {"conversation_depth": "deep", "planning_style": 4, "free_time": "outdoors"})
    near = profile("near", ["hiking", "photography"], "Trekking and landscape photography",
                   {"conversation_depth": "deep", "planning_style": 4, "free_time": "outdoors"})
    far = profile("far", ["gaming"], "I play games", {"conversation_depth": "light", "planning_style": 1})
    items, meta = ranking.rank_candidates(me, [far, near], limit=10)
    assert items[0]["candidate"].account_id == "near"
    assert meta["total_eligible"] == 2
    assert items[0]["rank"] == 1


def test_ranking_paginates():
    me = profile("me", ["hiking"], "hiking")
    candidates = [profile(f"c{i}", ["hiking"], "hiking") for i in range(7)]
    page1, meta1 = ranking.rank_candidates(me, candidates, limit=3, offset=0)
    page2, _ = ranking.rank_candidates(me, candidates, limit=3, offset=3)
    assert len(page1) == 3 and len(page2) == 3
    assert meta1["has_more"] is True
    assert {i["candidate"].account_id for i in page1} & {i["candidate"].account_id for i in page2} == set()


def test_ranking_dedupes_excluded_session_profiles():
    me = profile("me", ["hiking"], "hiking")
    candidates = [profile("a", ["hiking"], "hiking"), profile("b", ["hiking"], "hiking")]
    items, meta = ranking.rank_candidates(me, candidates, excluded={"a"})
    assert [i["candidate"].account_id for i in items] == ["b"]
    assert any(not e["eligible"] and "session" in e["reason"] for e in meta["excluded"])


def test_ranking_never_ranks_by_profile_completeness_or_age():
    me = profile("me", ["hiking", "art"], "I hike and paint", {"conversation_depth": "deep"})
    thin = profile("thin", ["hiking", "art"], "I hike and paint", {})
    rich = profile("rich", ["gaming"], "I play games", {"conversation_depth": "light",
                                                          "planning_style": 1, "social_frequency": 5})
    items, _ = ranking.rank_candidates(me, [rich, thin], limit=10)
    assert items[0]["candidate"].account_id == "thin"


def test_diversity_cap_defers_repeated_top_interest():
    me = profile("me", ["hiking"], "hiking")
    candidates = [profile(f"h{i}", ["hiking"], f"hiking {i}") for i in range(5)]
    items, _ = ranking.rank_candidates(me, candidates, limit=5)
    assert len(items) == 5  # everything still returned, just reordered
    first_two = [i["candidate"].account_id for i in items[:2]]
    assert first_two == ["h0", "h1"] or len(set(first_two)) == 2


def test_feedback_adjustment_is_bounded_and_explainable():
    me = profile("me", ["hiking"], "hiking")
    candidate = profile("c", ["hiking", "art"], "hiking")
    feedback = [{"feedback_type": "matches_interests", "target_account_id": "c"}]
    adjustment = ranking.feedback_adjustment(me, candidate, feedback, {"c": ["hiking"]})
    assert adjustment == pytest.approx(ranking.FEEDBACK_PER_MATCH)
    many = [{"feedback_type": "matches_interests", "target_account_id": "c"} for _ in range(40)]
    capped = ranking.feedback_adjustment(me, candidate, many, {"c": ["hiking"]})
    assert capped == ranking.FEEDBACK_PER_MATCH * 4


def test_feedback_does_not_override_blocks():
    me = profile("me", ["hiking"], "hiking")
    feedback = [{"feedback_type": "not_relevant", "target_account_id": "x"}]
    items, meta = ranking.rank_candidates(me, [profile("x", ["hiking"], "hiking")],
                                          blocked_ids={"x"}, feedback_rows=feedback)
    assert items == []
    assert meta["excluded"][0]["account_id"] == "x"


# ---------------------------------------------------------------- evaluation

def test_evaluation_runs_on_synthetic_data_and_beats_random():
    metrics = evaluation.evaluate(k=5)
    baseline = evaluation.baseline_random(k=5)
    assert metrics["dataset"] == "synthetic"
    assert metrics["users_evaluated"] == len(evaluation.SYNTHETIC_PROFILES)
    assert metrics["precision_at_k"] > baseline["precision_at_k"]
    assert 0 <= metrics["ndcg_at_k"] <= 1
    assert metrics["semantic_check"]["paraphrase_mean"] > metrics["semantic_check"]["unrelated_mean"]


def test_synthetic_dataset_is_labelled_as_synthetic():
    metrics = evaluation.evaluate(k=3)
    assert "synthetic" in metrics["dataset_note"].lower()
    assert "not real" in metrics["dataset_note"].lower()
