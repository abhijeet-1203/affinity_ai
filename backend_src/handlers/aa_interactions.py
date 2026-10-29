#input_type_name: AaInteractionsInput
#output_type_name: AaInteractionsOutput
#function_name: aa_interactions

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@

class AaInteractionsInput(BaseModel):
    action: str = Field(description="like | pass | save | unsave | block | unblock | report | withdraw | summary")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaInteractionsOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _ensure_visible(pod, account_id, target_id):
    if target_id == account_id:
        raise ApiError("invalid_target", "You cannot do that to your own profile.", 422)
    target = pod.table("aa_accounts").get(target_id)
    if not target or target.get("account_status") != "active":
        raise ApiError("not_found", "This member is not available.", 404)
    for row in list_rows(pod, "aa_blocks", [("blocker_id", "eq", target_id), ("blocked_id", "eq", account_id)], limit=1):
        raise ApiError("not_found", "This member is not available.", 404)
    return target


def _matches(pod, a, b):
    low, high = sorted([str(a), str(b)])
    return pod.query(
        "select * from aa_matches where "
        f"((user_a_id = {sqlq(low)} and user_b_id = {sqlq(high)}) or "
        f"(user_a_id = {sqlq(high)} and user_b_id = {sqlq(low)})) order by created_at asc"
    ).to_dict().get("items") or []


def _create_mutual_match(pod, a, b):
    """Create the match for a reciprocal like, safely under concurrent requests.

    There is no composite unique constraint available on the pair, so the
    compensating control is: insert, then re-read every row for the pair and
    keep the oldest one. Two simultaneous likes therefore converge on a single
    match instead of producing duplicates.
    """
    low, high = sorted([str(a), str(b)])
    pod.table("aa_matches").create({"user_a_id": low, "user_b_id": high, "status": "active"})
    rows = _matches(pod, low, high)
    if len(rows) > 1:
        keeper = rows[0]
        for extra in rows[1:]:
            if str(extra["status"]) == "active":
                try:
                    pod.table("aa_matches").delete(str(extra["id"]))
                except Exception:
                    pod.table("aa_matches").update(str(extra["id"]), {"status": "withdrawn"})
        return keeper
    return rows[0] if rows else None


def _upsert_interaction(pod, account_id, target_id, action_type):
    existing = find_one(pod, "aa_interactions", [
        ("actor_id", "eq", account_id), ("target_id", "eq", target_id), ("action_type", "eq", action_type)])
    if existing:
        if not existing.get("active"):
            pod.table("aa_interactions").update(str(existing["id"]), {"active": True})
        return existing, False
    # A member has one active stance per target: liking clears an earlier pass.
    other = "pass" if action_type == "like" else "like"
    for row in list_rows(pod, "aa_interactions", [
            ("actor_id", "eq", account_id), ("target_id", "eq", target_id),
            ("action_type", "eq", other), ("active", "eq", True)], limit=5):
        pod.table("aa_interactions").update(str(row["id"]), {"active": False})
    created = pod.table("aa_interactions").create({
        "actor_id": account_id, "target_id": target_id, "action_type": action_type, "active": True})
    return created, True


def _like(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    _ensure_visible(pod, account_id, target_id)
    row, created = _upsert_interaction(pod, account_id, target_id, "like")

    reciprocal = None
    for candidate in list_rows(pod, "aa_interactions", [
            ("actor_id", "eq", target_id), ("target_id", "eq", account_id),
            ("action_type", "eq", "like"), ("active", "eq", True)], limit=5):
        reciprocal = candidate
    match = None
    mutual = False
    if reciprocal:
        existing = _matches(pod, account_id, target_id)
        active = [m for m in existing if str(m.get("status")) == "active"]
        if active:
            match = active[0]
        else:
            match = _create_mutual_match(pod, account_id, target_id)
        mutual = True
        audit(pod, account_id, "mutual_match_created", {"match_id": str(match["id"]) if match else None})
    audit(pod, account_id, "like", {"target": target_id, "mutual": mutual})
    return {
        "liked": True,
        "duplicate": not created,
        "mutual": mutual,
        "match_id": str(match["id"]) if match else None,
        "message": ("You matched. Both of you expressed interest independently."
                    if mutual else "Interest expressed. A match appears only if they express interest too."),
    }


def _pass(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    _ensure_visible(pod, account_id, target_id)
    row, created = _upsert_interaction(pod, account_id, target_id, "pass")
    audit(pod, account_id, "pass", {"target": target_id})
    return {"passed": True, "duplicate": not created,
            "message": "Dismissed. A pass is not a judgement of the other person; it only hides them from your feed."}


def _save(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    _ensure_visible(pod, account_id, target_id)
    if not find_one(pod, "aa_saved_profiles", [("account_id", "eq", account_id), ("saved_account_id", "eq", target_id)]):
        pod.table("aa_saved_profiles").create({"account_id": account_id, "saved_account_id": target_id})
    audit(pod, account_id, "profile_saved", {"target": target_id})
    return {"saved": True}


def _unsave(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    for row in list_rows(pod, "aa_saved_profiles", [("account_id", "eq", account_id), ("saved_account_id", "eq", target_id)], limit=5):
        pod.table("aa_saved_profiles").delete(str(row["id"]))
    return {"saved": False}


def _block(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    if target_id == account_id:
        raise ApiError("invalid_target", "You cannot block yourself.", 422)
    if not find_one(pod, "aa_blocks", [("blocker_id", "eq", account_id), ("blocked_id", "eq", target_id)]):
        pod.table("aa_blocks").create({"blocker_id": account_id, "blocked_id": target_id})
    # A block immediately removes the pair from each other's discovery and ends
    # any match between them.
    for match in _matches(pod, account_id, target_id):
        pod.table("aa_matches").update(str(match["id"]), {"status": "blocked"})
    for row in list_rows(pod, "aa_interactions", [("actor_id", "eq", account_id), ("target_id", "eq", target_id)], limit=10):
        pod.table("aa_interactions").update(str(row["id"]), {"active": False})
    audit(pod, account_id, "block", {"target": target_id})
    return {"blocked": True, "message": "Blocked. They are excluded from your discovery and cannot appear again."}


def _unblock(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    for row in list_rows(pod, "aa_blocks", [("blocker_id", "eq", account_id), ("blocked_id", "eq", target_id)], limit=5):
        pod.table("aa_blocks").delete(str(row["id"]))
    audit(pod, account_id, "unblock", {"target": target_id})
    return {"blocked": False}


def _report(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    reason = str(payload.get("reason") or "").strip().lower()
    allowed = {"harassment", "spam", "fake_profile", "inappropriate_content", "safety_concern", "other"}
    if reason not in allowed:
        raise ApiError("invalid_input", "Choose a report reason.", 422)
    if target_id == account_id:
        raise ApiError("invalid_target", "You cannot report yourself.", 422)
    pod.table("aa_reports").create({
        "reporter_id": account_id, "reported_id": target_id, "reason": reason,
        "details": clean_text(payload.get("details"), "Details", 1000),
        "status": "open",
    })
    audit(pod, account_id, "report_filed", {"target": target_id, "reason": reason})
    return {
        "reported": True,
        "status": "open",
        "message": ("Report recorded for review. Your identity is never shown to the reported member. "
                    "No review has taken place yet - the status is honest: open."),
    }


def _withdraw(pod, account, payload):
    account_id = str(account["id"])
    target_id = require_uuid(payload.get("account_id"), "account_id")
    changed = 0
    for row in list_rows(pod, "aa_interactions", [("actor_id", "eq", account_id), ("target_id", "eq", target_id), ("action_type", "eq", "like"), ("active", "eq", True)], limit=5):
        pod.table("aa_interactions").update(str(row["id"]), {"active": False})
        changed += 1
    ended = 0
    for match in _matches(pod, account_id, target_id):
        if str(match.get("status")) == "active":
            pod.table("aa_matches").update(str(match["id"]), {"status": "withdrawn", "withdrawn_by": account_id})
            ended += 1
    audit(pod, account_id, "like_withdrawn", {"target": target_id, "matches_withdrawn": ended})
    return {"withdrawn": changed > 0, "matches_withdrawn": ended,
            "policy": "Withdrawing your interest deactivates your like and ends any active match with that member."}


def _summary(pod, account):
    account_id = str(account["id"])
    dir_data = directory(pod)

    def _cards(ids, with_relation=True):
        out = []
        for target_id in ids:
            row = dir_data["profiles"].get(target_id)
            if not row:
                continue
            account_row = dir_data["accounts"].get(target_id) or {}
            out.append({
                "account_id": target_id,
                "display_name": row.get("display_name"),
                "age": age_from_birth_date(row.get("birth_date")) if row.get("show_age", True) else None,
                "city": row.get("city") if row.get("show_city", True) else None,
                "bio": row.get("bio") or "",
                "initials": "".join(p[:1] for p in (row.get("display_name") or "?").split()[:2]).upper(),
                "interests": sorted(dir_data["interests_by_account"].get(target_id, [])),
                "is_demo": bool(account_row.get("is_demo")),
                "discoverable": bool(row.get("discoverable", True)),
            })
        return out

    likes = [str(r["target_id"]) for r in list_rows(pod, "aa_interactions", [
        ("actor_id", "eq", account_id), ("action_type", "eq", "like"), ("active", "eq", True)], limit=500)]
    passes = [str(r["target_id"]) for r in list_rows(pod, "aa_interactions", [
        ("actor_id", "eq", account_id), ("action_type", "eq", "pass"), ("active", "eq", True)], limit=500)]
    saved = [str(r["saved_account_id"]) for r in list_rows(pod, "aa_saved_profiles", [("account_id", "eq", account_id)], limit=500)]
    blocked = [str(r["blocked_id"]) for r in list_rows(pod, "aa_blocks", [("blocker_id", "eq", account_id)], limit=500)]
    return {
        "liked": _cards(likes),
        "passed": len(passes),
        "saved": _cards(saved),
        "blocked": _cards(blocked),
        "counts": {"liked": len(likes), "passed": len(passes), "saved": len(saved), "blocked": len(blocked)},
    }


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    account = resolve_session(pod, data.token)
    handlers = {
        "like": _like, "pass": _pass, "save": _save, "unsave": _unsave,
        "block": _block, "unblock": _unblock, "report": _report, "withdraw": _withdraw,
    }
    if action == "summary":
        return _summary(pod, account)
    if action in handlers:
        return handlers[action](pod, account, payload)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_interactions(ctx: FunctionContext, data: AaInteractionsInput) -> AaInteractionsOutput:
    try:
        return AaInteractionsOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaInteractionsOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaInteractionsOutput(**fail(error))
