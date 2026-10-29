#input_type_name: AaEvalInput
#output_type_name: AaEvalOutput
#function_name: aa_eval

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@
# @@INLINE:engine@@

class AaEvalInput(BaseModel):
    action: str = Field(description="run | latest")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaEvalOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


def _run(pod, account, payload):
    try:
        k = max(1, min(10, int(payload.get("k") or 5)))
    except (TypeError, ValueError):
        raise ApiError("invalid_input", "k must be a number.", 422)
    metrics = evaluate(k=k)
    baseline = baseline_random(k=k)
    metrics["baseline"] = baseline
    metrics["engine"] = {
        "semantic": "lexicon-expanded TF-IDF cosine over profile text",
        "shared_interests": "Jaccard over normalised interest tags",
        "structured": "explicit alignment maps + normalised ordinal distance",
        "ranking": "weighted sum with missing-data renormalisation, bounded feedback nudge, diversity cap",
        "llm_used_for_scores": False,
    }
    record = pod.table("aa_eval_runs").create({
        "dataset": metrics["dataset"],
        "k": k,
        "metrics": metrics,
        "notes": ("Measured in this environment on the synthetic labelled set. "
                  "Not real-user outcomes."),
    })
    audit(pod, str(account["id"]) if account else None, "evaluation_run", {"k": k})
    return {"run_id": str(record["id"]), "metrics": metrics}


def _latest(pod, account):
    rows = pod.query("select * from aa_eval_runs order by created_at desc limit 5").to_dict().get("items") or []
    if not rows:
        return {"runs": [], "latest": None,
                "note": "No evaluation has been run in this workspace yet. Run it to see measured numbers."}
    latest = rows[0]
    return {
        "latest": {
            "run_id": str(latest["id"]),
            "run_at": iso(parse_dt(latest.get("created_at")) or now()),
            "dataset": latest.get("dataset"),
            "k": latest.get("k"),
            "metrics": latest.get("metrics"),
            "notes": latest.get("notes"),
        },
        "runs": [{"run_id": str(r["id"]), "run_at": iso(parse_dt(r.get("created_at")) or now()),
                  "k": r.get("k"), "precision_at_k": (r.get("metrics") or {}).get("precision_at_k")}
                 for r in rows],
    }


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    payload = data.payload or {}
    if action == "latest":
        return _latest(pod, None)
    account = resolve_session(pod, data.token)
    if action == "run":
        return _run(pod, account, payload)
    if action == "latest_authed":
        return _latest(pod, account)
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_eval(ctx: FunctionContext, data: AaEvalInput) -> AaEvalOutput:
    try:
        return AaEvalOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaEvalOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaEvalOutput(**fail(error))
