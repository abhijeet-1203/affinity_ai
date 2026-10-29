"""Candidate eligibility, feedback adjustment and recommendation ranking.

Ranking rules, in order:
1. Hard eligibility filters (self, undiscoverable, incomplete onboarding, age
   preference, blocks in either direction, already liked/passed).
2. Minimum information: at least one comparable dimension must exist, otherwise
   the pair is dropped with a reason instead of being shown at a fake score.
3. Score = preference alignment estimate + a small, bounded, explicit
   personalisation adjustment from the user's own feedback.
4. Tie-break on information coverage, then on a stable hash of the pair (never on
   popularity, age, gender or profile completeness).
5. Diversity pass: at most MAX_SAME_TOP_INTEREST profiles whose strongest shared
   interest is the same one, so the feed is not a monoculture.
"""

import hashlib

from .compatibility import score_pair

MIN_DIMENSIONS = 1
MAX_SAME_TOP_INTEREST = 2
FEEDBACK_PER_MATCH = 1.5
FEEDBACK_CAP = 6.0

POSITIVE_FEEDBACK = {"matches_interests", "more_like_this"}
NEGATIVE_FEEDBACK = {"not_relevant", "does_not_align"}


def _stable_tiebreak(a_id, b_id):
    raw = "|".join(sorted([str(a_id), str(b_id)]))
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


class CandidateDecision:
    """Why a candidate was included or excluded - surfaced in the UI, not logged away."""

    __slots__ = ("account_id", "eligible", "reason")

    def __init__(self, account_id, eligible, reason=""):
        self.account_id = account_id
        self.eligible = eligible
        self.reason = reason

    def to_dict(self):
        return {"account_id": self.account_id, "eligible": self.eligible, "reason": self.reason}


def eligibility(me, candidate, prefs=None, blocked_ids=None, interacted_ids=None):
    """Return (eligible, reason). Pure function, easy to test."""
    prefs = prefs or {}
    blocked = blocked_ids or set()
    interacted = interacted_ids or set()
    cid = str(candidate.account_id)

    if cid == str(me.account_id):
        return CandidateDecision(cid, False, "This is your own profile.")
    if cid in {str(b) for b in blocked}:
        return CandidateDecision(cid, False, "Blocked in one direction or the other.")
    if not candidate.onboarding_completed:
        return CandidateDecision(cid, False, "Their profile is not complete yet.")
    if not candidate.discoverable:
        return CandidateDecision(cid, False, "They have turned profile discovery off.")

    connection = prefs.get("connection_type")
    if connection and connection != "any" and candidate.connection_type and candidate.connection_type != connection:
        return CandidateDecision(cid, False, f"They are looking for {candidate.connection_type.replace('_', ' ')}.")

    min_age = prefs.get("min_age")
    max_age = prefs.get("max_age")
    if candidate.age is not None:
        if min_age and candidate.age < int(min_age):
            return CandidateDecision(cid, False, "Younger than your preferred age range.")
        if max_age and candidate.age > int(max_age):
            return CandidateDecision(cid, False, "Older than your preferred age range.")

    if cid in {str(i) for i in interacted}:
        return CandidateDecision(cid, False, "You have already liked or passed on this profile.")
    return CandidateDecision(cid, True, "")


def feedback_adjustment(me, candidate, feedback_rows, my_interests_by_target=None):
    """Bounded, explainable nudge from the user's own explicit feedback.

    For every earlier feedback item the user gave, if this candidate shares at
    least one interest with that earlier profile the adjustment moves by
    +/- FEEDBACK_PER_MATCH, capped at FEEDBACK_CAP points. It is shown in the
    explanation as "personalisation adjustment" and never overrides blocks or
    eligibility (eligibility runs first).
    """
    if not feedback_rows:
        return 0.0
    mine = {str(i).lower() for i in (candidate.interests or [])}
    total = 0.0
    for row in feedback_rows:
        kind = str(row.get("feedback_type") or "")
        target = str(row.get("target_account_id") or "")
        if not target or not mine:
            continue
        target_interests = {
            str(i).lower() for i in (my_interests_by_target or {}).get(target, [])
        }
        if not (mine & target_interests):
            continue
        if kind in POSITIVE_FEEDBACK:
            total += FEEDBACK_PER_MATCH
        elif kind in NEGATIVE_FEEDBACK:
            total -= FEEDBACK_PER_MATCH
    return max(-FEEDBACK_CAP, min(FEEDBACK_CAP, total))


def rank_candidates(me, candidates, prefs=None, weights=None, blocked_ids=None,
                    interacted_ids=None, feedback_rows=None, corpus_texts=None,
                    limit=12, offset=0, excluded=None):
    """Score, filter, rank and paginate. Returns (items, meta)."""
    prefs = prefs or {}
    excluded = excluded or set()
    decisions = []
    scored = []
    interests_by_target = {
        str(c.account_id): c.interests for c in candidates
    }

    for candidate in candidates:
        cid = str(candidate.account_id)
        if cid in {str(e) for e in excluded}:
            decisions.append(CandidateDecision(cid, False, "Already shown in this discovery session."))
            continue
        decision = eligibility(me, candidate, prefs, blocked_ids, interacted_ids)
        if not decision.eligible:
            decisions.append(decision)
            continue
        adjustment = feedback_adjustment(me, candidate, feedback_rows or [], interests_by_target)
        result = score_pair(me, candidate, weights, corpus_texts, adjustment)
        available = [d for d in result.dimensions if d.available and d.score is not None]
        if len(available) < MIN_DIMENSIONS:
            decisions.append(CandidateDecision(
                cid, False, "Not enough information on either profile to estimate alignment."))
            continue
        decisions.append(CandidateDecision(cid, True, ""))
        scored.append((result, candidate))

    scored.sort(key=lambda pair: (
        -round(pair[0].ranked_score, 2),
        -round(pair[0].coverage, 4),
        _stable_tiebreak(me.account_id, pair[1].account_id),
    ))

    # Diversity pass: defer a profile when its top shared interest is already
    # represented MAX_SAME_TOP_INTEREST times higher up the list.
    balanced = []
    deferred = []
    seen_top = {}
    for result, candidate in scored:
        top = result.shared_interests[0].lower() if result.shared_interests else "__none__"
        count = seen_top.get(top, 0)
        if count >= MAX_SAME_TOP_INTEREST:
            deferred.append((result, candidate))
            continue
        seen_top[top] = count + 1
        balanced.append((result, candidate))
    balanced.extend(deferred)

    total = len(balanced)
    page = balanced[offset:offset + limit]
    items = []
    for rank, (result, candidate) in enumerate(page, start=offset + 1):
        items.append({"rank": rank, "candidate": candidate, "result": result})

    meta = {
        "total_eligible": total,
        "returned": len(items),
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total,
        "candidates_considered": len(candidates),
        "excluded": [d.to_dict() for d in decisions if not d.eligible],
        "algorithm": "content-based scoring on structured + semantic features, personalised weights",
        "minimum_dimensions": MIN_DIMENSIONS,
    }
    return items, meta
