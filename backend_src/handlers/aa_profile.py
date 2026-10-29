#input_type_name: AaProfileInput
#output_type_name: AaProfileOutput
#function_name: aa_profile

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@
# @@INLINE:engine@@

class AaProfileInput(BaseModel):
    action: str = Field(description="get | update | public | catalog | reset_personalization")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaProfileOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _update_profile(pod, account, payload):
    account_id = str(account["id"])
    profile = find_one(pod, "aa_profiles", [("account_id", "eq", account_id)])
    if not profile:
        raise ApiError("profile_missing", "No profile found for this account.", 404)

    update = {}
    if "display_name" in payload:
        update["display_name"] = clean_text(payload.get("display_name"), "Display name", 60, required=True, min_length=2)
    if "bio" in payload:
        update["bio"] = clean_text(payload.get("bio"), "Bio", 1200)
    if "city" in payload:
        update["city"] = clean_text(payload.get("city"), "City", 80)
    if "avatar_url" in payload:
        url = str(payload.get("avatar_url") or "").strip()
        if url and not (url.startswith("http://") or url.startswith("https://") or url.startswith("/")):
            raise ApiError("invalid_input", "Avatar must be an https URL or a pod file path.", 422)
        update["avatar_url"] = url or None
    if "birth_date" in payload:
        raw = payload.get("birth_date")
        if raw in (None, ""):
            update["birth_date"] = None
        else:
            try:
                born = date.fromisoformat(str(raw)[:10])
            except ValueError:
                raise ApiError("invalid_input", "Birth date must be YYYY-MM-DD.", 422)
            age = age_from_birth_date(born)
            if age is None or age < 18:
                raise ApiError("age_restricted", "AffinityAI is for adults aged 18 and over.", 422)
            if age > 120:
                raise ApiError("invalid_input", "Check the birth date you entered.", 422)
            update["birth_date"] = born.isoformat()
    for flag in ("discoverable", "show_age", "show_city"):
        if flag in payload:
            update[flag] = bool(payload.get(flag))
    if "connection_type" in payload:
        connection = str(payload.get("connection_type") or "dating").lower()
        if connection not in {"dating", "friendship", "activity_partner", "any"}:
            raise ApiError("invalid_input", "Unknown connection type.", 422)
        update["connection_type"] = connection
    if "onboarding_step" in payload:
        try:
            step = int(payload.get("onboarding_step"))
        except (TypeError, ValueError):
            raise ApiError("invalid_input", "Onboarding step must be a number.", 422)
        update["onboarding_step"] = max(1, min(5, step))

    if not update:
        raise ApiError("nothing_to_update", "No recognised fields were supplied.", 422)
    pod.table("aa_profiles").update(str(profile["id"]), update)
    audit(pod, account_id, "profile_updated", {"fields": sorted(update.keys())})
    return profile_bundle(pod, account)


def _public(pod, account, payload):
    account_id = require_uuid(payload.get("account_id"), "account_id")
    if account_id == str(account["id"]):
        return profile_bundle(pod, account)
    blocked = _blocked_ids(pod, str(account["id"]))
    if account_id in blocked:
        raise ApiError("not_found", "This profile is not available.", 404)
    target_account = pod.table("aa_accounts").get(account_id)
    if not target_account or target_account.get("account_status") != "active":
        raise ApiError("not_found", "This profile is not available.", 404)
    data = directory(pod)
    row = data["profiles"].get(account_id)
    if not row or not row.get("onboarding_completed") or not row.get("discoverable"):
        raise ApiError("not_found", "This profile is not discoverable.", 404)
    age = age_from_birth_date(row.get("birth_date")) if row.get("show_age", True) else None
    return {
        "account_id": account_id,
        "is_demo": bool(target_account.get("is_demo")),
        "display_name": row.get("display_name"),
        "age": age,
        "city": row.get("city") if row.get("show_city", True) else None,
        "bio": row.get("bio"),
        "avatar_url": row.get("avatar_url"),
        "connection_type": row.get("connection_type"),
        "interests": sorted(data["interests_by_account"].get(account_id, [])),
        "questionnaire_shared": False,
        "note": "Questionnaire answers stay private; only aggregated alignment is shared.",
    }


def _blocked_ids(pod, account_id):
    out = set()
    for row in list_rows(pod, "aa_blocks", [("blocker_id", "eq", account_id)], limit=500):
        out.add(str(row["blocked_id"]))
    for row in list_rows(pod, "aa_blocks", [("blocked_id", "eq", account_id)], limit=500):
        out.add(str(row["blocker_id"]))
    return out


def _reset_personalization(pod, account):
    account_id = str(account["id"])
    removed = 0
    for row in list_rows(pod, "aa_feedback", [("account_id", "eq", account_id)], limit=500):
        pod.table("aa_feedback").delete(str(row["id"]))
        removed += 1
    for row in list_rows(pod, "aa_recommendation_events", [("account_id", "eq", account_id)], limit=2000):
        pod.table("aa_recommendation_events").delete(str(row["id"]))
    preferences = find_one(pod, "aa_discovery_preferences", [("account_id", "eq", account_id)])
    if preferences:
        pod.table("aa_discovery_preferences").update(str(preferences["id"]), {
            "w_shared": 0.35, "w_semantic": 0.25, "w_communication": 0.20, "w_lifestyle": 0.20,
        })
    audit(pod, account_id, "personalisation_reset", {"feedback_removed": removed})
    return {"reset": True, "feedback_removed": removed, "weights": dict(DEFAULT_WEIGHTS)}


def _catalog(pod):
    rows = list_rows(pod, "aa_interests", limit=500)
    grouped = {}
    for row in rows:
        category = row.get("category") or "Other"
        grouped.setdefault(category, []).append({
            "name": row["normalized_name"],
            "label": row.get("label") or row["normalized_name"],
            "custom": bool(row.get("is_custom")),
        })
    return {
        "categories": [
            {"name": category, "interests": sorted(items, key=lambda item: item["label"])}
            for category, items in sorted(grouped.items())
        ],
        "max_interests": MAX_INTERESTS,
        "max_custom": MAX_CUSTOM_INTERESTS,
    }


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    if action == "catalog":
        return _catalog(pod)
    account = resolve_session(pod, data.token)
    if action == "get":
        return profile_bundle(pod, account)
    if action == "update":
        return _update_profile(pod, account, payload)
    if action == "public":
        return _public(pod, account, payload)
    if action == "reset_personalization":
        return _reset_personalization(pod, account)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_profile(ctx: FunctionContext, data: AaProfileInput) -> AaProfileOutput:
    try:
        return AaProfileOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaProfileOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaProfileOutput(**fail(error))
