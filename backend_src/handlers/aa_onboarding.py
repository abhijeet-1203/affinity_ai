#input_type_name: AaOnboardingInput
#output_type_name: AaOnboardingOutput
#function_name: aa_onboarding

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@
# @@INLINE:engine@@

class AaOnboardingInput(BaseModel):
    action: str = Field(description="status | save_profile | save_interests | save_answers | save_preferences | complete | preview")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaOnboardingOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _profile_row(pod, account_id):
    row = find_one(pod, "aa_profiles", [("account_id", "eq", account_id)])
    if not row:
        raise ApiError("profile_missing", "No profile found for this account.", 404)
    return row


def _status(pod, account):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    data = directory(pod)
    interests = data["interests_by_account"].get(account_id, [])
    answers = data["answers_by_account"].get(account_id, {})
    prefs = data["prefs_by_account"].get(account_id, {})
    steps = [
        {"step": 1, "key": "profile", "label": "Basic profile",
         "done": bool(profile.get("display_name")) and bool(profile.get("birth_date"))},
        {"step": 2, "key": "interests", "label": "Interests", "done": len(interests) >= 1},
        {"step": 3, "key": "questionnaire", "label": "Compatibility questions", "done": len(answers) >= 1},
        {"step": 4, "key": "preferences", "label": "Discovery preferences", "done": bool(prefs)},
        {"step": 5, "key": "visibility", "label": "Visibility and consent",
         "done": bool(profile.get("onboarding_completed"))},
    ]
    next_step = next((s["step"] for s in steps if not s["done"]), 5)
    return {
        "steps": steps,
        "next_step": next_step,
        "completed": bool(profile.get("onboarding_completed")),
        "percent": int(round(sum(1 for s in steps if s["done"]) / len(steps) * 100)),
        "questions": question_public_view(),
        "bundle": profile_bundle(pod, account, data),
    }


def _save_profile(pod, account, payload):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    update = {}
    if payload.get("display_name") is not None:
        update["display_name"] = clean_text(payload.get("display_name"), "Display name", 60, required=True, min_length=2)
    raw = payload.get("birth_date")
    if raw not in (None, ""):
        try:
            born = date.fromisoformat(str(raw)[:10])
        except ValueError:
            raise ApiError("invalid_input", "Birth date must be YYYY-MM-DD.", 422)
        age = age_from_birth_date(born)
        if age is None or age < 18:
            raise ApiError("age_restricted", "AffinityAI is only for adults aged 18 and over.", 422)
        if age > 120:
            raise ApiError("invalid_input", "Check the birth date you entered.", 422)
        update["birth_date"] = born.isoformat()
    if payload.get("bio") is not None:
        update["bio"] = clean_text(payload.get("bio"), "Bio", 1200)
    if payload.get("city") is not None:
        update["city"] = clean_text(payload.get("city"), "City", 80)
    if payload.get("connection_type") is not None:
        connection = str(payload.get("connection_type")).lower()
        if connection not in {"dating", "friendship", "activity_partner", "any"}:
            raise ApiError("invalid_input", "Unknown connection type.", 422)
        update["connection_type"] = connection
    if "discoverable" in payload:
        update["discoverable"] = bool(payload.get("discoverable"))
    for flag in ("show_age", "show_city"):
        if flag in payload:
            update[flag] = bool(payload.get(flag))
    update["onboarding_step"] = max(int(profile.get("onboarding_step") or 1), 2)
    pod.table("aa_profiles").update(str(profile["id"]), update)
    audit(pod, account_id, "onboarding_profile_saved")
    return _status(pod, account)


def _save_interests(pod, account, payload):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    raw_names = payload.get("interests") or []
    if not isinstance(raw_names, list):
        raise ApiError("invalid_input", "interests must be a list of names.", 422)
    normalized = []
    for name in raw_names:
        key = normalize_interest(name)
        if key and key not in normalized:
            normalized.append(key)
    if len(normalized) > MAX_INTERESTS:
        raise ApiError("too_many_interests", f"Choose at most {MAX_INTERESTS} interests.", 422)
    known = {str(r["normalized_name"]) for r in list_rows(pod, "aa_interests", limit=1000)}
    custom = [name for name in normalized if name not in known]
    if len(custom) > MAX_CUSTOM_INTERESTS:
        raise ApiError("too_many_custom", f"You can add at most {MAX_CUSTOM_INTERESTS} custom interests.", 422)

    rows = ensure_interest_rows(pod, normalized)
    for link in list_rows(pod, "aa_profile_interests", [("profile_id", "eq", str(profile["id"]))], limit=200):
        pod.table("aa_profile_interests").delete(str(link["id"]))
    if rows:
        pod.records.bulk_create("aa_profile_interests", [
            {"profile_id": str(profile["id"]), "interest_id": str(row["id"]),
             "source": "custom" if row["normalized_name"] not in known else "catalog"}
            for row in rows
        ])
    pod.table("aa_profiles").update(str(profile["id"]), {
        "onboarding_step": max(int(profile.get("onboarding_step") or 1), 3)})
    audit(pod, account_id, "onboarding_interests_saved", {"count": len(rows)})
    return _status(pod, account)


def _save_answers(pod, account, payload):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    answers = payload.get("answers") or {}
    if not isinstance(answers, dict):
        raise ApiError("invalid_input", "answers must be an object keyed by question.", 422)

    cleaned = {}
    for key, value in answers.items():
        question = next((q for q in QUESTIONS if q["key"] == key), None)
        if not question:
            raise ApiError("unknown_question", f"Unknown question '{key}'.", 422)
        if value in (None, "", []):
            continue
        if question["kind"] == "ordinal":
            try:
                number = int(float(value))
            except (TypeError, ValueError):
                raise ApiError("invalid_input", f"{question['prompt']} expects a number 1-5.", 422)
            if number < 1 or number > 5:
                raise ApiError("invalid_input", f"{question['prompt']} expects a number 1-5.", 422)
            cleaned[key] = number
        elif question["kind"] == "categorical":
            allowed = {str(o["value"]) for o in question["options"]}
            if str(value) not in allowed:
                raise ApiError("invalid_input", f"Unsupported answer for '{question['prompt']}'.", 422)
            cleaned[key] = str(value)
        else:  # multiselect
            values = value if isinstance(value, list) else [value]
            allowed = {str(o["value"]) for o in question["options"]}
            picked = [str(v) for v in values if str(v) in allowed]
            if not picked:
                raise ApiError("invalid_input", f"Pick at least one option for '{question['prompt']}'.", 422)
            maximum = question.get("max_selected") or len(allowed)
            cleaned[key] = picked[:maximum]

    existing = {str(r["question_key"]): r for r in list_rows(pod, "aa_questionnaire_responses", [("account_id", "eq", account_id)], limit=100)}
    for key, value in cleaned.items():
        if key in existing:
            pod.table("aa_questionnaire_responses").update(str(existing[key]["id"]), {"response_value": encode_json_value(value)})
        else:
            pod.table("aa_questionnaire_responses").create({
                "account_id": account_id, "question_key": key, "response_value": encode_json_value(value)})
    # Questions omitted from this payload are cleared, so the UI can un-answer.
    for key, row in existing.items():
        if key not in cleaned:
            pod.table("aa_questionnaire_responses").delete(str(row["id"]))
    pod.table("aa_profiles").update(str(profile["id"]), {
        "onboarding_step": max(int(profile.get("onboarding_step") or 1), 4)})
    audit(pod, account_id, "onboarding_answers_saved", {"count": len(cleaned)})
    return _status(pod, account)


def _save_preferences(pod, account, payload):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    prefs = find_one(pod, "aa_discovery_preferences", [("account_id", "eq", account_id)])
    existing = prefs or {}

    def _int(name, default, low, high):
        raw = payload.get(name, existing.get(name, default))
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ApiError("invalid_input", f"{name} must be a number.", 422)
        if value < low or value > high:
            raise ApiError("invalid_input", f"{name} must be between {low} and {high}.", 422)
        return value

    min_age = _int("min_age", 18, 18, 100)
    max_age = _int("max_age", 99, 18, 100)
    if max_age < min_age:
        raise ApiError("invalid_preferences", "Maximum age cannot be lower than the minimum age.", 422)

    connection = str(payload.get("connection_type", existing.get("connection_type", "dating"))).lower()
    if connection not in {"dating", "friendship", "activity_partner", "any"}:
        raise ApiError("invalid_input", "Unknown connection type.", 422)

    raw_weights = payload.get("weights") or {
        "shared_interests": existing.get("w_shared", DEFAULT_WEIGHTS["shared_interests"]),
        "semantic": existing.get("w_semantic", DEFAULT_WEIGHTS["semantic"]),
        "communication": existing.get("w_communication", DEFAULT_WEIGHTS["communication"]),
        "lifestyle": existing.get("w_lifestyle", DEFAULT_WEIGHTS["lifestyle"]),
    }
    normalized = normalize_weights({k: raw_weights.get(k, 0) for k in DIMENSIONS})

    update = {
        "connection_type": connection,
        "min_age": min_age,
        "max_age": max_age,
        "w_shared": normalized["shared_interests"],
        "w_semantic": normalized["semantic"],
        "w_communication": normalized["communication"],
        "w_lifestyle": normalized["lifestyle"],
        "include_demo": bool(payload.get("include_demo", existing.get("include_demo", True))),
    }
    if prefs:
        pod.table("aa_discovery_preferences").update(str(prefs["id"]), update)
    else:
        update["account_id"] = account_id
        pod.table("aa_discovery_preferences").create(update)
    pod.table("aa_profiles").update(str(profile["id"]), {
        "onboarding_step": max(int(profile.get("onboarding_step") or 1), 5)})
    audit(pod, account_id, "preferences_saved", {"weights": normalized})
    return _status(pod, account)


def _complete(pod, account, payload):
    account_id = str(account["id"])
    profile = _profile_row(pod, account_id)
    data = directory(pod)
    interests = data["interests_by_account"].get(account_id, [])
    missing = []
    if not profile.get("display_name"):
        missing.append("display name")
    if not profile.get("birth_date"):
        missing.append("birth date")
    if not interests:
        missing.append("at least one interest")
    if missing:
        raise ApiError("onboarding_incomplete", "Still needed: " + ", ".join(missing) + ".", 422)
    discoverable = bool(payload.get("discoverable", True))
    pod.table("aa_profiles").update(str(profile["id"]), {
        "onboarding_completed": True,
        "onboarding_step": 5,
        "discoverable": discoverable,
    })
    audit(pod, account_id, "onboarding_completed", {"discoverable": discoverable})
    return _status(pod, account)


def _preview(pod, account):
    bundle = profile_bundle(pod, account)
    profile = bundle["profile"]
    return {
        "card": {
            "display_name": profile["display_name"],
            "age": profile["age"] if profile["show_age"] else None,
            "city": profile["city"] if profile["show_city"] else None,
            "bio": profile["bio"],
            "interests": bundle["interests"],
            "initials": "".join(part[0] for part in (profile["display_name"] or "?").split()[:2]).upper(),
        },
        "visibility": {
            "discoverable": profile["discoverable"],
            "show_age": profile["show_age"],
            "show_city": profile["show_city"],
        },
        "visible_to_others": ["display name", "age (if enabled)", "city (if enabled)", "bio", "interests"],
        "never_visible": ["email address", "exact location", "individual questionnaire answers",
                          "who you liked or passed on", "your reports"],
    }


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    account = resolve_session(pod, data.token)
    if action == "status":
        return _status(pod, account)
    if action == "save_profile":
        return _save_profile(pod, account, payload)
    if action == "save_interests":
        return _save_interests(pod, account, payload)
    if action == "save_answers":
        return _save_answers(pod, account, payload)
    if action == "save_preferences":
        return _save_preferences(pod, account, payload)
    if action == "complete":
        return _complete(pod, account, payload)
    if action == "preview":
        return _preview(pod, account)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_onboarding(ctx: FunctionContext, data: AaOnboardingInput) -> AaOnboardingOutput:
    try:
        return AaOnboardingOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaOnboardingOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaOnboardingOutput(**fail(error))
