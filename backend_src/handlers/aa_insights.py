#input_type_name: AaInsightsInput
#output_type_name: AaInsightsOutput
#function_name: aa_insights

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@

class AaInsightsInput(BaseModel):
    action: str = Field(description="summary")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaInsightsOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _summary(pod, account):
    account_id = str(account["id"])
    dir_data = directory(pod)

    def _count(sql_text):
        rows = pod.query(sql_text).to_dict().get("items") or []
        try:
            return int(rows[0].get("n") or 0) if rows else 0
        except Exception:
            return 0

    viewed = _count(f"select count(*) as n from aa_recommendation_events where account_id = {sqlq(account_id)}")
    distinct_viewed = _count(
        f"select count(distinct target_account_id) as n from aa_recommendation_events where account_id = {sqlq(account_id)}")
    likes = _count(f"select count(*) as n from aa_interactions where actor_id = {sqlq(account_id)} and action_type = 'like' and active = true")
    passes = _count(f"select count(*) as n from aa_interactions where actor_id = {sqlq(account_id)} and action_type = 'pass' and active = true")
    saved = _count(f"select count(*) as n from aa_saved_profiles where account_id = {sqlq(account_id)}")
    matches = _count(
        "select count(*) as n from aa_matches where status = 'active' and "
        f"(user_a_id = {sqlq(account_id)} or user_b_id = {sqlq(account_id)})")
    ended = _count(
        "select count(*) as n from aa_matches where status <> 'active' and "
        f"(user_a_id = {sqlq(account_id)} or user_b_id = {sqlq(account_id)})")
    reports = _count(f"select count(*) as n from aa_reports where reporter_id = {sqlq(account_id)}")
    blocks = _count(f"select count(*) as n from aa_blocks where blocker_id = {sqlq(account_id)}")

    # Most frequently shared interests across the recommendations actually served.
    shared_counter = {}
    for row in list_rows(pod, "aa_recommendation_events", [("account_id", "eq", account_id)], limit=1000):
        target_id = str(row.get("target_account_id"))
        shared = set(dir_data["interests_by_account"].get(account_id, [])) & set(
            dir_data["interests_by_account"].get(target_id, []))
        for interest in shared:
            shared_counter[interest] = shared_counter.get(interest, 0) + 1
    top_shared = sorted(shared_counter.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

    feedback_counter = {}
    for row in list_rows(pod, "aa_feedback", [("account_id", "eq", account_id)], limit=500):
        feedback_counter[str(row["feedback_type"])] = feedback_counter.get(str(row["feedback_type"]), 0) + 1

    # Average alignment and coverage of the recommendations served, from stored events.
    scores = [float(r.get("score") or 0) for r in list_rows(pod, "aa_recommendation_events", [("account_id", "eq", account_id)], limit=1000)]
    coverages = [float(r.get("coverage") or 0) for r in list_rows(pod, "aa_recommendation_events", [("account_id", "eq", account_id)], limit=1000)]

    return {
        "counts": {
            "recommendations_viewed": viewed,
            "distinct_profiles_seen": distinct_viewed,
            "outgoing_likes": likes,
            "passes": passes,
            "saved_profiles": saved,
            "mutual_matches": matches,
            "ended_matches": ended,
            "reports_filed": reports,
            "profiles_blocked": blocks,
        },
        "top_shared_interests": [{"interest": name, "count": count} for name, count in top_shared],
        "feedback_distribution": [
            {"type": name, "count": count} for name, count in sorted(feedback_counter.items(), key=lambda kv: -kv[1])],
        "average_alignment": round(sum(scores) / len(scores), 1) if scores else None,
        "average_coverage": (int(round(sum(coverages) / len(coverages) * 100)) if coverages else None),
        "note": ("Every number here is counted from rows you created. Nothing is simulated, and no "
                 "other member's private activity is included."),
        "has_activity": any([viewed, likes, passes, saved, matches, ended]),
    }


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    account = resolve_session(pod, data.token)
    if action == "summary":
        return _summary(pod, account)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_insights(ctx: FunctionContext, data: AaInsightsInput) -> AaInsightsOutput:
    try:
        return AaInsightsOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaInsightsOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaInsightsOutput(**fail(error))
