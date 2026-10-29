#input_type_name: AaAuthInput
#output_type_name: AaAuthOutput
#function_name: aa_auth

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@

class AaAuthInput(BaseModel):
    action: str = Field(description="register | login | logout | me | delete_account | change_password")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaAuthOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _recent_failures(pod, email):
    since = iso(now() - timedelta(minutes=LOCK_MINUTES))
    rows = pod.query(
        "select count(*) as n from aa_audit_logs "
        f"where action = 'login_failed' and created_at > {sqlq(since)} "
        f"and metadata->>'email' = {sqlq(email)}"
    ).to_dict().get("items") or []
    try:
        return int(rows[0].get("n") or 0) if rows else 0
    except Exception:
        return 0


def _register(pod, payload):
    email = clean_email(payload.get("email"))
    password = validate_password(payload.get("password"))
    display_name = clean_text(payload.get("display_name"), "Display name", 60, required=True, min_length=2)

    existing = find_one(pod, "aa_accounts", [("email", "eq", email)])
    if existing:
        raise ApiError("email_taken", "An account with that email already exists. Sign in instead.", 409)

    password_hash, salt = hash_password(password)
    account = pod.table("aa_accounts").create({
        "email": email,
        "password_hash": password_hash,
        "password_salt": salt,
        "password_algo": "scrypt",
        "account_status": "active",
        "is_demo": False,
        "failed_login_count": 0,
        "last_login_at": iso(),
    })
    account_id = str(account["id"])
    pod.table("aa_profiles").create({
        "account_id": account_id,
        "display_name": display_name,
        "discoverable": False,
        "show_age": True,
        "show_city": True,
        "onboarding_step": 1,
        "onboarding_completed": False,
        "connection_type": "dating",
    })
    pod.table("aa_discovery_preferences").create({
        "account_id": account_id, "connection_type": "dating", "min_age": 18, "max_age": 99,
        "w_shared": 0.35, "w_semantic": 0.25, "w_communication": 0.20, "w_lifestyle": 0.20,
        "include_demo": True,
    })
    token = issue_session(pod, account_id)
    audit(pod, account_id, "account_registered", {"email": email})
    bundle = profile_bundle(pod, account)
    bundle["token"] = token
    return bundle


def _login(pod, payload):
    email = clean_email(payload.get("email"))
    password = str(payload.get("password") or "")
    account = find_one(pod, "aa_accounts", [("email", "eq", email)])

    if account:
        locked = parse_dt(account.get("locked_until"))
        if locked and locked > now():
            raise ApiError("account_locked", "Too many attempts. Try again in a few minutes.", 429)
    else:
        if _recent_failures(pod, email) >= MAX_FAILED_LOGINS:
            raise ApiError("account_locked", "Too many attempts. Try again in a few minutes.", 429)
        audit(pod, None, "login_failed", {"email": email, "reason": "unknown_email"})
        raise ApiError("invalid_credentials", "Email or password is incorrect.", 401)

    if account.get("account_status") != "active":
        raise ApiError("account_unavailable", "This account is not active.", 403)

    if not verify_password(password, account.get("password_hash"), account.get("password_salt")):
        failures = int(account.get("failed_login_count") or 0) + 1
        update = {"failed_login_count": failures}
        if failures >= MAX_FAILED_LOGINS:
            update["locked_until"] = iso(now() + timedelta(minutes=LOCK_MINUTES))
        try:
            pod.table("aa_accounts").update(str(account["id"]), update)
        except Exception:
            pass
        audit(pod, str(account["id"]), "login_failed", {"email": email, "reason": "bad_password"})
        raise ApiError("invalid_credentials", "Email or password is incorrect.", 401)

    try:
        pod.table("aa_accounts").update(str(account["id"]), {
            "failed_login_count": 0, "locked_until": None, "last_login_at": iso(),
        })
    except Exception:
        pass
    token = issue_session(pod, str(account["id"]))
    audit(pod, str(account["id"]), "login_succeeded", {"email": email})
    bundle = profile_bundle(pod, pod.table("aa_accounts").get(str(account["id"])))
    bundle["token"] = token
    return bundle


def _logout(pod, account, payload, token):
    row = find_one(pod, "aa_sessions", [("token_hash", "eq", token_hash(token or ""))])
    if row:
        pod.table("aa_sessions").update(str(row["id"]), {"revoked": True, "revoked_reason": "member signed out"})
    audit(pod, str(account["id"]), "logout")
    return {"signed_out": True}


def _me(pod, account):
    bundle = profile_bundle(pod, account)
    account_id = str(account["id"])
    likes = list_rows(pod, "aa_interactions", [("actor_id", "eq", account_id), ("action_type", "eq", "like"), ("active", "eq", True)], limit=500)
    saves = list_rows(pod, "aa_saved_profiles", [("account_id", "eq", account_id)], limit=500)
    matches = pod.query(
        "select count(*) as n from aa_matches where status = 'active' and "
        f"(user_a_id = {sqlq(account_id)} or user_b_id = {sqlq(account_id)})"
    ).to_dict().get("items") or []
    bundle["counts"] = {
        "outgoing_likes": len(likes),
        "saved": len(saves),
        "mutual_matches": int(matches[0].get("n") or 0) if matches else 0,
    }
    return bundle


def _change_password(pod, account, payload):
    current = str(payload.get("current_password") or "")
    new_password = validate_password(payload.get("new_password"))
    if not verify_password(current, account.get("password_hash"), account.get("password_salt")):
        raise ApiError("invalid_credentials", "Your current password is incorrect.", 401)
    password_hash, salt = hash_password(new_password)
    pod.table("aa_accounts").update(str(account["id"]), {"password_hash": password_hash, "password_salt": salt})
    # Every other session is revoked on a password change.
    for row in list_rows(pod, "aa_sessions", [("account_id", "eq", str(account["id"])), ("revoked", "eq", False)], limit=50):
        pod.table("aa_sessions").update(str(row["id"]), {"revoked": True, "revoked_reason": "password changed"})
    audit(pod, str(account["id"]), "password_changed")
    return {"changed": True, "signed_out": True}


def _delete_account(pod, account, payload):
    password = str(payload.get("password") or "")
    if not verify_password(password, account.get("password_hash"), account.get("password_salt")):
        raise ApiError("invalid_credentials", "Confirm your password to delete the account.", 401)
    account_id = str(account["id"])

    # Personal content is removed. Block rows are retained (without any personal
    # data beyond the opaque ids) so a block keeps protecting the other member,
    # which is disclosed in the privacy page.
    profile = find_one(pod, "aa_profiles", [("account_id", "eq", account_id)])
    if profile:
        for link in list_rows(pod, "aa_profile_interests", [("profile_id", "eq", str(profile["id"]))], limit=100):
            pod.table("aa_profile_interests").delete(str(link["id"]))
        pod.table("aa_profiles").update(str(profile["id"]), {
            "display_name": "Deleted member",
            "bio": "",
            "city": "",
            "birth_date": None,
            "avatar_url": None,
            "discoverable": False,
            "onboarding_completed": False,
        })
    for row in list_rows(pod, "aa_questionnaire_responses", [("account_id", "eq", account_id)], limit=200):
        pod.table("aa_questionnaire_responses").delete(str(row["id"]))
    for table, column in (("aa_saved_profiles", "account_id"), ("aa_recommendation_events", "account_id"),
                          ("aa_feedback", "account_id"), ("aa_interactions", "actor_id"),
                          ("aa_sessions", "account_id")):
        for row in list_rows(pod, table, [(column, "eq", account_id)], limit=1000):
            pod.table(table).delete(str(row["id"]))
    for match in list_rows(pod, "aa_matches", [("user_a_id", "eq", account_id)], limit=200) + \
            list_rows(pod, "aa_matches", [("user_b_id", "eq", account_id)], limit=200):
        pod.table("aa_matches").update(str(match["id"]), {"status": "withdrawn"})
    pod.table("aa_accounts").update(account_id, {
        "email": f"deleted-{account_id}@deleted.affinityai.invalid",
        "password_hash": "",
        "password_salt": "",
        "account_status": "deleted",
    })
    audit(pod, account_id, "account_deleted")
    return {"deleted": True}


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    if action == "register":
        return _register(pod, payload)
    if action == "login":
        return _login(pod, payload)
    if action == "logout":
        account = resolve_session(pod, data.token)
        return _logout(pod, account, payload, data.token)
    if action == "me":
        account = resolve_session(pod, data.token)
        return _me(pod, account)
    if action == "change_password":
        account = resolve_session(pod, data.token)
        return _change_password(pod, account, payload)
    if action == "delete_account":
        account = resolve_session(pod, data.token)
        return _delete_account(pod, account, payload)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_auth(ctx: FunctionContext, data: AaAuthInput) -> AaAuthOutput:
    try:
        return AaAuthOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaAuthOutput(**fail(error))
    except Exception as error:  # noqa: BLE001 - returned to the client, never swallowed
        return AaAuthOutput(**fail(error))
