"""Offline evaluation of the ranking engine.

The dataset here is SYNTHETIC and explicitly labelled as such: profiles written
by hand for this project, with a hand-written relevance label per (user, candidate)
pair ("would this person plausibly want this recommendation?"). Results are
therefore a check that the engine ranks the way its rules say it should - not a
measure of real-world dating success, and not a claim about real users.
"""

import random

from .compatibility import ProfileFeatures, score_pair
from .ranking import rank_candidates
from .similarity import semantic_similarity

SYNTHETIC_PROFILES = [
    # (id, name, interests, bio, answers)
    ("syn_01", "Aarav", ["hiking", "photography", "technology"],
     "I enjoy hiking, discovering mountain trails, and outdoor photography.",
     {"free_time": "outdoors", "conversation_depth": "deep", "planning_style": 4,
      "social_frequency": 3, "conversation_topics": ["ideas", "culture"],
      "valued_qualities": ["curiosity", "kindness"], "shared_hobbies_importance": 4}),
    ("syn_02", "Ira", ["travel", "photography", "cooking"],
     "I love trekking, exploring nature, and capturing landscapes, then cooking something new.",
     {"free_time": "creative", "conversation_depth": "mix", "planning_style": 4,
      "social_frequency": 3, "conversation_topics": ["culture", "everyday"],
      "valued_qualities": ["curiosity", "humour"], "shared_hobbies_importance": 3}),
    ("syn_03", "Dev", ["technology", "gaming", "books"],
     "Software engineer. I read science fiction and build side projects at night.",
     {"free_time": "home", "conversation_depth": "deep", "planning_style": 2,
      "social_frequency": 2, "conversation_topics": ["ideas"],
      "valued_qualities": ["curiosity", "ambition"], "shared_hobbies_importance": 2}),
    ("syn_04", "Mira", ["fitness", "food", "travel"],
     "Marathon training, cooking for friends, and planning the next trip.",
     {"free_time": "social", "conversation_depth": "light", "planning_style": 1,
      "social_frequency": 5, "conversation_topics": ["everyday", "humour"],
      "valued_qualities": ["humour", "kindness"], "shared_hobbies_importance": 3}),
    ("syn_05", "Rohan", ["music", "art", "film"],
     "I play guitar badly, collect vinyl, and go to every film festival I can.",
     {"free_time": "creative", "conversation_depth": "deep", "planning_style": 3,
      "social_frequency": 4, "conversation_topics": ["culture", "ideas"],
      "valued_qualities": ["curiosity", "humour"], "shared_hobbies_importance": 4}),
    ("syn_06", "Anya", ["books", "learning", "volunteering"],
     "Teacher. I read history, study languages, and volunteer at the library.",
     {"free_time": "home", "conversation_depth": "deep", "planning_style": 2,
      "social_frequency": 2, "conversation_topics": ["ideas", "culture"],
      "valued_qualities": ["kindness", "curiosity"], "shared_hobbies_importance": 3}),
    ("syn_07", "Kabir", ["outdoors", "fitness", "travel"],
     "Weekend hiker and cyclist. Happiest on a long trail with a daypack.",
     {"free_time": "outdoors", "conversation_depth": "mix", "planning_style": 5,
      "social_frequency": 3, "conversation_topics": ["everyday", "humour"],
      "valued_qualities": ["humour", "calm"], "shared_hobbies_importance": 5}),
    ("syn_08", "Sana", ["art", "photography", "volunteering"],
     "Illustrator. I sketch people on trains and photograph old buildings.",
     {"free_time": "creative", "conversation_depth": "deep", "planning_style": 3,
      "social_frequency": 3, "conversation_topics": ["culture", "ideas"],
      "valued_qualities": ["curiosity", "kindness"], "shared_hobbies_importance": 4}),
    ("syn_09", "Neel", ["entrepreneurship", "technology", "travel"],
     "Building a startup. I travel for work and read about markets for fun.",
     {"free_time": "social", "conversation_depth": "deep", "planning_style": 1,
      "social_frequency": 4, "conversation_topics": ["ideas", "everyday"],
      "valued_qualities": ["ambition", "curiosity"], "shared_hobbies_importance": 2}),
    ("syn_10", "Tara", ["gaming", "film", "music"],
     "I stream on weekends, watch too many films, and make playlists for everything.",
     {"free_time": "home", "conversation_depth": "light", "planning_style": 5,
      "social_frequency": 2, "conversation_topics": ["humour", "culture"],
      "valued_qualities": ["humour", "calm"], "shared_hobbies_importance": 3}),
    ("syn_11", "Vikram", ["hiking", "gardening", "learning"],
     "I grow vegetables, walk long distances, and listen to history podcasts.",
     {"free_time": "outdoors", "conversation_depth": "deep", "planning_style": 3,
      "social_frequency": 2, "conversation_topics": ["ideas", "everyday"],
      "valued_qualities": ["curiosity", "calm"], "shared_hobbies_importance": 4}),
    ("syn_12", "Lina", ["cooking", "nightlife", "music"],
     "I cook for crowds and dance until the kitchen closes.",
     {"free_time": "social", "conversation_depth": "light", "planning_style": 4,
      "social_frequency": 5, "conversation_topics": ["humour", "everyday"],
      "valued_qualities": ["humour", "kindness"], "shared_hobbies_importance": 2}),
]

# Hand-written relevance labels: (user, candidate) pairs a thoughtful human would
# call a plausible match. Used as ground truth for precision@k / recall@k.
RELEVANT_PAIRS = {
    ("syn_01", "syn_02"), ("syn_01", "syn_08"), ("syn_01", "syn_07"), ("syn_01", "syn_11"),
    ("syn_02", "syn_08"), ("syn_02", "syn_07"), ("syn_02", "syn_12"),
    ("syn_03", "syn_06"), ("syn_03", "syn_09"), ("syn_03", "syn_11"),
    ("syn_04", "syn_12"), ("syn_04", "syn_07"), ("syn_04", "syn_02"),
    ("syn_05", "syn_08"), ("syn_05", "syn_10"), ("syn_05", "syn_02"),
    ("syn_06", "syn_11"), ("syn_06", "syn_08"), ("syn_06", "syn_09"),
    ("syn_09", "syn_03"), ("syn_09", "syn_04"),
    ("syn_10", "syn_05"), ("syn_10", "syn_12"),
    ("syn_11", "syn_01"), ("syn_11", "syn_06"),
    ("syn_12", "syn_04"), ("syn_12", "syn_05"),
}


def synthetic_profiles():
    return [
        ProfileFeatures(
            account_id=pid, display_name=name, interests=interests, bio=bio, answers=answers,
            age=25 + (index % 9), city="Pune", discoverable=True, onboarding_completed=True,
            connection_type="dating",
        )
        for index, (pid, name, interests, bio, answers) in enumerate(SYNTHETIC_PROFILES)
    ]


def _dcg(gains):
    import math
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def _ndcg(relevances, k):
    gains = relevances[:k]
    ideal = sorted(relevances, reverse=True)[:k]
    dcg = _dcg(gains)
    idcg = _dcg(ideal)
    return 0.0 if idcg == 0 else dcg / idcg


def evaluate(k=5, weights=None):
    """Run the engine over the synthetic set and measure ranking quality."""
    profiles = synthetic_profiles()
    by_id = {p.account_id: p for p in profiles}
    corpus = [p.free_text for p in profiles]

    precisions, recalls, ndcgs, coverage_hits = [], [], [], []
    recommended = set()
    top_interest_counter = {}
    feature_rows = []

    for user in profiles:
        others = [p for p in profiles if p.account_id != user.account_id]
        items, meta = rank_candidates(
            user, others, prefs={}, weights=weights, corpus_texts=corpus, limit=k,
        )
        relevant = {b for (a, b) in RELEVANT_PAIRS if a == user.account_id}
        ranked_ids = [item["candidate"].account_id for item in items]
        recommended.update(ranked_ids)

        hits = [1 if cid in relevant else 0 for cid in ranked_ids]
        precisions.append(sum(hits) / k if k else 0.0)
        recalls.append(sum(hits) / len(relevant) if relevant else 0.0)
        ndcgs.append(_ndcg(hits, k))

        for item in items:
            result = item["result"]
            dic = result.to_dict()
            coverage_hits.append(dic["coverage"])
            for interest in dic["shared_interests"][:1]:
                top_interest_counter[interest] = top_interest_counter.get(interest, 0) + 1
            feature_rows.append({
                "user": user.account_id,
                "candidate": item["candidate"].account_id,
                "score": dic["overall"],
                "coverage": dic["coverage"],
                "shared": dic["shared_interests"],
                "available_dimensions": sum(1 for d in dic["dimensions"] if d["available"]),
            })

    total_candidates = len(profiles) * (len(profiles) - 1)
    distinct_interests = len({i for p in profiles for i in p.interests}) or 1
    distinct_recommended_interests = len(top_interest_counter) or 1

    metrics = {
        "dataset": "synthetic",
        "dataset_note": ("Synthetic dataset: hand-written fictional profiles with hand-labelled "
                         "relevance. Not real users and not real relationship outcomes."),
        "users_evaluated": len(profiles),
        "pairs_considered": total_candidates,
        "k": k,
        "precision_at_k": round(sum(precisions) / len(precisions), 4),
        "recall_at_k": round(sum(recalls) / len(recalls), 4),
        "ndcg_at_k": round(sum(ndcgs) / len(ndcgs), 4),
        "coverage": round(len(recommended) / len(profiles), 4),
        "interest_diversity": round(distinct_recommended_interests / distinct_interests, 4),
        "avg_information_coverage": round(sum(coverage_hits) / len(coverage_hits), 4),
        "avg_available_dimensions": round(
            sum(r["available_dimensions"] for r in feature_rows) / len(feature_rows), 2),
        "score_distribution": {
            "min": round(min(r["score"] for r in feature_rows), 2),
            "max": round(max(r["score"] for r in feature_rows), 2),
            "mean": round(sum(r["score"] for r in feature_rows) / len(feature_rows), 2),
        },
        "label_definition": ("A pair is relevant when a human reviewer judged the two profiles "
                             "plausibly compatible before the engine ran; labels were written "
                             "by hand, not derived from the engine's own scores."),
        "samples": feature_rows[:12],
    }

    # Semantic sanity check: do known paraphrase pairs score above unrelated pairs?
    paraphrase = [
        ("I enjoy hiking, discovering mountain trails, and outdoor photography.",
         "I love trekking, exploring nature, and capturing landscapes."),
        ("I cook for friends most weekends and collect recipes.", "Making dinner for people I love is my hobby; I hoard cookbooks."),
        ("I play guitar and go to as many gigs as I can.", "Live music and my old acoustic take up my evenings."),
    ]
    unrelated = [
        ("I enjoy hiking, discovering mountain trails, and outdoor photography.",
         "I mostly stay in and stream competitive games."),
        ("I cook for friends most weekends and collect recipes.", "My weekends are for marathon training and spreadsheets."),
        ("I play guitar and go to as many gigs as I can.", "I volunteer at the local library and study history."),
    ]
    p_scores = [semantic_similarity(a, b, corpus)[0] or 0.0 for a, b in paraphrase]
    u_scores = [semantic_similarity(a, b, corpus)[0] or 0.0 for a, b in unrelated]
    metrics["semantic_check"] = {
        "paraphrase_pairs": len(p_scores),
        "paraphrase_mean": round(sum(p_scores) / len(p_scores), 4),
        "unrelated_mean": round(sum(u_scores) / len(u_scores), 4),
        "separation": round(sum(p_scores) / len(p_scores) - sum(u_scores) / len(u_scores), 4),
        "note": "True paraphrase pairs should score higher than unrelated pairs; overlap in range is a limitation, not a success.",
    }
    return metrics


def baseline_random(k=5, seed=7):
    """Random-ranking baseline over the same synthetic labels, for comparison."""
    profiles = synthetic_profiles()
    rng = random.Random(seed)
    precisions = []
    for user in profiles:
        others = [p.account_id for p in profiles if p.account_id != user.account_id]
        rng.shuffle(others)
        relevant = {b for (a, b) in RELEVANT_PAIRS if a == user.account_id}
        hits = [1 if cid in relevant else 0 for cid in others[:k]]
        precisions.append(sum(hits) / k)
    return {
        "baseline": "random ordering",
        "seed": seed,
        "precision_at_k": round(sum(precisions) / len(precisions), 4),
        "k": k,
    }
