#input_type_name: AaDiscoveryInput
#output_type_name: AaDiscoveryOutput
#function_name: aa_discovery

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@
# @@INLINE:engine@@

class AaDiscoveryInput(BaseModel):
    action: str = Field(description="recommendations | detail | feedback | starters")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaDiscoveryOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _blocked_ids(pod, account_id):
    ids = set()
    for row in list_rows(pod, "aa_blocks", [("blocker_id", "eq", account_id)], limit=500):
        ids.add(str(row["blocked_id"]))
    for row in list_rows(pod, "aa_blocks", [("blocked_id", "eq", account_id)], limit=500):
        ids.add(str(row["blocker_id"]))
    return ids


def _interacted_ids(pod, account_id):
    ids = set()
    for row in list_rows(pod, "aa_interactions", [("actor_id", "eq", account_id), ("active", "eq", True)], limit=1000):
        ids.add(str(row["target_id"]))
    return ids


def _feedback_rows(pod, account_id):
    return list_rows(pod, "aa_feedback", [("account_id", "eq", account_id)], limit=200)


def _relation_state(pod, account_id, target_id):
    state = {"liked": False, "passed": False, "saved": False, "matched": False, "liked_you": False}
    for row in list_rows(pod, "aa_interactions", [("actor_id", "eq", account_id), ("target_id", "eq", target_id), ("active", "eq", True)], limit=10):
        if row.get("action_type") == "like":
            state["liked"] = True
        if row.get("action_type") == "pass":
            state["passed"] = True
    for row in list_rows(pod, "aa_interactions", [("actor_id", "eq", target_id), ("target_id", "eq", account_id), ("action_type", "eq", "like"), ("active", "eq", True)], limit=5):
        state["liked_you"] = True
    if find_one(pod, "aa_saved_profiles", [("account_id", "eq", account_id), ("saved_account_id", "eq", target_id)]):
        state["saved"] = True
    pair = _find_match(pod, account_id, target_id)
    if pair and pair.get("status") == "active":
        state["matched"] = True
    return state


def _find_match(pod, a, b):
    low, high = sorted([str(a), str(b)])
    rows = pod.query(
        "select * from aa_matches where "
        f"((user_a_id = {sqlq(low)} and user_b_id = {sqlq(high)}) or "
        f"(user_a_id = {sqlq(high)} and user_b_id = {sqlq(low)})) order by created_at asc"
    ).to_dict().get("items") or []
    return rows[0] if rows else None


def _card(pod, dir_data, account_id, my_id, result, rank=None, my_weights=None):
    row = dir_data["profiles"].get(account_id) or {}
    account = dir_data["accounts"].get(account_id) or {}
    if not row:
        return None
    payload = result.to_dict()
    top = max((d for d in result.dimensions if d.available and d.score is not None),
              key=lambda d: d.score, default=None)
    return {
        "account_id": account_id,
        "rank": rank,
        "display_name": row.get("display_name"),
        "age": age_from_birth_date(row.get("birth_date")) if row.get("show_age", True) else None,
        "city": row.get("city") if row.get("show_city", True) else None,
        "bio": row.get("bio") or "",
        "avatar_url": row.get("avatar_url"),
        "initials": "".join(p[:1] for p in (row.get("display_name") or "?").split()[:2]).upper(),
        "is_demo": bool(account.get("is_demo")),
        "connection_type": row.get("connection_type"),
        "interests": sorted(dir_data["interests_by_account"].get(account_id, [])),
        "overall": payload["overall"],
        "ranked_score": payload["ranked_score"],
        "label": payload["label"],
        "coverage_percent": payload["coverage_percent"],
        "confidence": payload["confidence"],
        "dimensions": [d for d in payload["dimensions"]],
        "top_dimension": {"key": top.key, "label": DIMENSION_META[top.key]["label"], "percent": int(round(top.score * 100))} if top else None,
        "shared_interests": payload["shared_interests"],
        "interest_overlap_count": payload["interest_overlap_count"],
        "highlights": payload["highlights"],
        "summary": result.explanation,
        "feedback_adjustment": payload["feedback_adjustment"],
        "missing": payload["missing"],
    }


def _recommendations(pod, account, payload):
    account_id = str(account["id"])
    try:
        limit = max(1, min(24, int(payload.get("limit") or 9)))
        offset = max(0, int(payload.get("offset") or 0))
    except (TypeError, ValueError):
        raise ApiError("invalid_input", "limit and offset must be numbers.", 422)
    session_id = str(payload.get("session_id") or "")[:80] or None

    dir_data = directory(pod)
    me = features_for(dir_data, account_id)
    if me is None:
        raise ApiError("profile_missing", "Complete your profile before discovering people.", 404)
    prefs_row = dir_data["prefs_by_account"].get(account_id) or {}
    prefs = {
        "connection_type": prefs_row.get("connection_type") or "dating",
        "min_age": prefs_row.get("min_age") or 18,
        "max_age": prefs_row.get("max_age") or 99,
    }
    weights_raw = weights_of(prefs_row)

    blocked = _blocked_ids(pod, account_id)
    interacted = _interacted_ids(pod, account_id)
    candidate_ids = [
        cid for cid in dir_data["profiles"].keys()
        if cid != account_id and cid not in blocked
    ]
    candidates = [features_for(dir_data, cid) for cid in candidate_ids]
    candidates = [c for c in candidates if c is not None]
    corpus = [features_for(dir_data, cid).free_text for cid in candidate_ids if features_for(dir_data, cid)]
    corpus.append(me.free_text)

    excluded = set()
    if session_id:
        for row in list_rows(pod, "aa_recommendation_events", [("account_id", "eq", account_id), ("session_id", "eq", session_id)], limit=500):
            excluded.add(str(row["target_account_id"]))

    items, meta = rank_candidates(
        me, candidates, prefs=prefs, weights=weights_raw, blocked_ids=blocked,
        interacted_ids=interacted, feedback_rows=_feedback_rows(pod, account_id),
        corpus_texts=corpus, limit=limit, offset=offset, excluded=excluded,
    )

    cards = []
    events = []
    for item in items:
        card = _card(pod, dir_data, str(item["candidate"].account_id), account_id, item["result"], rank=item["rank"])
        if card:
            cards.append(card)
            events.append({
                "account_id": account_id,
                "target_account_id": str(item["candidate"].account_id),
                "score": round(item["result"].overall, 2),
                "coverage": round(item["result"].coverage, 4),
                "rank": item["rank"],
                "session_id": session_id,
                "dimensions": [d.to_dict() for d in item["result"].dimensions],
            })
    if events:
        pod.records.bulk_create("aa_recommendation_events", events)

    audit(pod, account_id, "recommendations_served", {"returned": len(cards), "considered": len(candidates)})
    return {
        "recommendations": cards,
        "meta": meta,
        "weights": weights_percent(weights_raw),
        "weights_note": "Weighted only over dimensions with enough information on both sides.",
        "empty_reason": None if cards else _empty_reason(pod, dir_data, account_id, len(candidates), meta),
        "fake_scores": False,
    }


def _empty_reason(pod, dir_data, account_id, candidates_considered, meta):
    if candidates_considered == 0:
        return ("No other members have a visible profile yet. Invite someone, or run the demo "
                "seeder to explore with clearly labelled fictional profiles.")
    if meta.get("total_eligible", 0) == 0:
        reasons = {}
        for row in meta.get("excluded", []):
            reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
        top = sorted(reasons.items(), key=lambda item: -item[1])[:2]
        detail = "; ".join(f"{count} \u00d7 {reason}" for reason, count in top)
        return ("Every eligible profile has been seen, filtered out or already acted on. " + detail)
    return "No profile had enough shared information to score honestly yet."


def weights_percent(weights_raw):
    normalized = normalize_weights(weights_raw)
    return {key: int(round(value * 100)) for key, value in normalized.items()}


def _detail(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    if target_id == account_id:
        raise ApiError("invalid_target", "That is your own profile.", 422)
    blocked = _blocked_ids(pod, account_id)
    if target_id in blocked:
        raise ApiError("not_found", "This profile is not available.", 404)

    dir_data = directory(pod)
    me = features_for(dir_data, account_id)
    them = features_for(dir_data, target_id)
    if me is None or them is None:
        raise ApiError("not_found", "This profile is not available.", 404)
    if not them.onboarding_completed:
        raise ApiError("not_found", "This profile is not discoverable.", 404)

    prefs_row = dir_data["prefs_by_account"].get(account_id) or {}
    corpus = [f.free_text for f in (features_for(dir_data, cid) for cid in dir_data["profiles"]) if f]
    result = score_pair(me, them, weights_of(prefs_row), corpus,
                        feedback_adjustment(me, them, _feedback_rows(pod, account_id),
                                            dir_data["interests_by_account"]))
    card = _card(pod, dir_data, target_id, account_id, result)
    explanation = explain_result(result)
    return {
        "profile": card,
        "compatibility": result.to_dict(),
        "explanation": explanation,
        "starters": conversation_starters(result.shared_interests),
        "relation": _relation_state(pod, account_id, target_id),
        "weights": weights_percent(weights_of(prefs_row)),
        "dimension_meta": DIMENSION_META,
    }


def _feedback(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    kind = str(payload.get("feedback_type") or "").strip().lower()
    if kind not in {"matches_interests", "not_relevant", "more_like_this", "does_not_align"}:
        raise ApiError("invalid_input", "Unknown feedback type.", 422)
    existing = find_one(pod, "aa_feedback", [("account_id", "eq", account_id), ("target_account_id", "eq", target_id)])
    if existing:
        pod.table("aa_feedback").update(str(existing["id"]), {"feedback_type": kind,
                                                              "note": clean_text(payload.get("note"), "Note", 300)})
    else:
        pod.table("aa_feedback").create({
            "account_id": account_id, "target_account_id": target_id,
            "feedback_type": kind, "note": clean_text(payload.get("note"), "Note", 300),
        })
    rows = _feedback_rows(pod, account_id)
    audit(pod, account_id, "feedback_recorded", {"type": kind})
    return {
        "recorded": True,
        "feedback_type": kind,
        "total_feedback": len(rows),
        "effect": ("Future ranking nudges up to \u00b16 points for profiles that share an interest "
                   "with profiles you gave feedback on. Eligibility and blocks always win first."),
    }


def _starters(pod, account, payload):
    target_id = require_uuid(payload.get("account_id"), "account_id")
    dir_data = directory(pod)
    mine = set(dir_data["interests_by_account"].get(str(account["id"]), []))
    theirs = set(dir_data["interests_by_account"].get(target_id, []))
    shared = sorted(mine & theirs)
    return {"shared_interests": shared, "starters": conversation_starters(shared),
            "note": "Templates built from shared interests only - nothing is invented about either person."}


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    if action == "catalog_questions":
        return {"questions": question_public_view()}
    account = resolve_session(pod, data.token)
    if action == "recommendations":
        return _recommendations(pod, account, payload)
    if action == "detail":
        return _detail(pod, account, payload)
    if action == "feedback":
        return _feedback(pod, account, payload)
    if action == "starters":
        return _starters(pod, account, payload)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_discovery(ctx: FunctionContext, data: AaDiscoveryInput) -> AaDiscoveryOutput:
    try:
        return AaDiscoveryOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaDiscoveryOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaDiscoveryOutput(**fail(error))
