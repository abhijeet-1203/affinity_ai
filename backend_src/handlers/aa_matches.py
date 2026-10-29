#input_type_name: AaMatchesInput
#output_type_name: AaMatchesOutput
#function_name: aa_matches

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@
# @@INLINE:engine@@

class AaMatchesInput(BaseModel):
    action: str = Field(description="list | get | withdraw")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaMatchesOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _pair_rows(pod, account_id):
    return pod.query(
        "select * from aa_matches where "
        f"user_a_id = {sqlq(account_id)} or user_b_id = {sqlq(account_id)} "
        "order by created_at desc"
    ).to_dict().get("items") or []


def _card(pod, dir_data, target_id, account_id):
    row = dir_data["profiles"].get(target_id) or {}
    account_row = dir_data["accounts"].get(target_id) or {}
    return {
        "account_id": target_id,
        "display_name": row.get("display_name") or "Deleted member",
        "age": age_from_birth_date(row.get("birth_date")) if row.get("show_age", True) else None,
        "city": row.get("city") if row.get("show_city", True) else None,
        "bio": row.get("bio") or "",
        "initials": "".join(p[:1] for p in (row.get("display_name") or "?").split()[:2]).upper(),
        "interests": sorted(dir_data["interests_by_account"].get(target_id, [])),
        "shared_interests": sorted(
            set(dir_data["interests_by_account"].get(target_id, []))
            & set(dir_data["interests_by_account"].get(account_id, []))),
        "is_demo": bool(account_row.get("is_demo")),
    }


def _list(pod, account):
    account_id = str(account["id"])
    dir_data = directory(pod)
    active, ended = [], []
    for row in _pair_rows(pod, account_id):
        target_id = str(row["user_b_id"]) if str(row["user_a_id"]) == account_id else str(row["user_a_id"])
        entry = {
            "match_id": str(row["id"]),
            "status": row.get("status"),
            "created_at": iso(parse_dt(row.get("created_at")) or now()),
            "profile": _card(pod, dir_data, target_id, account_id),
        }
        if entry["status"] == "active":
            active.append(entry)
        else:
            ended.append(entry)
    return {
        "matches": active,
        "ended": ended,
        "counts": {"active": len(active), "ended": len(ended)},
        "note": ("A mutual match exists only because both members expressed interest independently. "
                 "Compatibility scores alone never create one."),
    }


def _get(pod, account, payload):
    account_id = str(account["id"])
    match_id = require_uuid(payload.get("match_id"), "match_id")
    row = pod.table("aa_matches").get(match_id)
    if not row or account_id not in {str(row["user_a_id"]), str(row["user_b_id"])}:
        raise ApiError("not_found", "Match not found.", 404)
    target_id = str(row["user_b_id"]) if str(row["user_a_id"]) == account_id else str(row["user_a_id"])
    dir_data = directory(pod)
    profile = _card(pod, dir_data, target_id, account_id)
    me = features_for(dir_data, account_id)
    them = features_for(dir_data, target_id)
    compatibility = None
    if me and them:
        prefs = dir_data["prefs_by_account"].get(account_id) or {}
        corpus = [f.free_text for f in (features_for(dir_data, cid) for cid in dir_data["profiles"]) if f]
        compatibility = score_pair(me, them, weights_of(prefs), corpus).to_dict()
    return {
        "match_id": str(row["id"]),
        "status": row.get("status"),
        "created_at": iso(parse_dt(row.get("created_at")) or now()),
        "profile": profile,
        "compatibility": compatibility,
    }


def _withdraw(pod, account, payload):
    account_id = str(account["id"])
    match_id = require_uuid(payload.get("match_id"), "match_id")
    row = pod.table("aa_matches").get(match_id)
    if not row or account_id not in {str(row["user_a_id"]), str(row["user_b_id"])}:
        raise ApiError("not_found", "Match not found.", 404)
    if str(row.get("status")) != "active":
        return {"withdrawn": False, "status": row.get("status")}
    target_id = str(row["user_b_id"]) if str(row["user_a_id"]) == account_id else str(row["user_a_id"])
    pod.table("aa_matches").update(match_id, {"status": "withdrawn", "withdrawn_by": account_id})
    for interaction in list_rows(pod, "aa_interactions", [
            ("actor_id", "eq", account_id), ("target_id", "eq", target_id), ("action_type", "eq", "like")], limit=5):
        pod.table("aa_interactions").update(str(interaction["id"]), {"active": False})
    audit(pod, account_id, "match_withdrawn", {"match_id": match_id})
    return {"withdrawn": True, "status": "withdrawn",
            "policy": "Withdrawing ends the match for both members and deactivates your interest."}


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    account = resolve_session(pod, data.token)
    if action == "list":
        return _list(pod, account)
    if action == "get":
        return _get(pod, account, payload)
    if action == "withdraw":
        return _withdraw(pod, account, payload)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_matches(ctx: FunctionContext, data: AaMatchesInput) -> AaMatchesOutput:
    try:
        return AaMatchesOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaMatchesOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaMatchesOutput(**fail(error))
