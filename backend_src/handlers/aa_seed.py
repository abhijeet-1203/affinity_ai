#input_type_name: AaSeedInput
#output_type_name: AaSeedOutput
#function_name: aa_seed

from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext

# @@INLINE:common@@

class AaSeedInput(BaseModel):
    action: str = Field(description="run | status")
    token: str | None = None
    payload: dict = Field(default_factory=dict)


class AaSeedOutput(BaseModel):
    ok: bool
    data: dict | None = None
    error: dict | None = None


DEMO_PASSWORD = "DemoPass123!"
DEMO_DOMAIN = "demo.affinityai.invalid"

# Deterministic, clearly fictional demonstration members. Written for this
# project; no real person's data is used, and every account is flagged is_demo.
DEMO_PEOPLE = [
    {
        "email": "demo@" + DEMO_DOMAIN, "name": "Demo Member", "birth_date": "1997-04-12",
        "city": "Pune", "connection": "dating",
        "bio": ("Product designer who spends weekends on a trail with a camera. I like long "
                "conversations about ideas, cooking for friends, and planning the next trip."),
        "interests": ["photography", "hiking", "cooking", "technology", "travel"],
        "answers": {"free_time": "outdoors", "conversation_depth": "deep", "planning_style": 4,
                    "social_frequency": 3, "conversation_topics": ["ideas", "culture"],
                    "valued_qualities": ["curiosity", "kindness"], "shared_hobbies_importance": 4},
        "weights": (0.35, 0.25, 0.20, 0.20),
    },
    {
        "email": "aarav@" + DEMO_DOMAIN, "name": "Aarav (demo)", "birth_date": "1995-09-02",
        "city": "Pune", "connection": "dating",
        "bio": ("I enjoy hiking, discovering mountain trails, and outdoor photography. Most "
                "weekends I am above the treeline with a flask of coffee."),
        "interests": ["hiking", "photography", "outdoors", "cooking", "travel"],
        "answers": {"free_time": "outdoors", "conversation_depth": "deep", "planning_style": 4,
                    "social_frequency": 3, "conversation_topics": ["ideas", "everyday"],
                    "valued_qualities": ["curiosity", "calm"], "shared_hobbies_importance": 4},
        "weights": (0.35, 0.25, 0.20, 0.20),
    },
    {
        "email": "ira@" + DEMO_DOMAIN, "name": "Ira (demo)", "birth_date": "1998-01-27",
        "city": "Mumbai", "connection": "dating",
        "bio": ("Illustrator. I love trekking, exploring nature, and capturing landscapes, then "
                "coming home to cook something new from a recipe I found travelling."),
        "interests": ["photography", "art", "travel", "cooking", "hiking"],
        "answers": {"free_time": "creative", "conversation_depth": "mix", "planning_style": 3,
                    "social_frequency": 3, "conversation_topics": ["culture", "ideas"],
                    "valued_qualities": ["curiosity", "humour"], "shared_hobbies_importance": 3},
        "weights": (0.30, 0.30, 0.20, 0.20),
    },
    {
        "email": "dev@" + DEMO_DOMAIN, "name": "Dev (demo)", "birth_date": "1994-11-15",
        "city": "Bengaluru", "connection": "dating",
        "bio": ("Backend engineer. I read science fiction, build small side projects at night, "
                "and I am slowly learning to cook more than pasta."),
        "interests": ["technology", "books", "gaming", "learning", "coffee"],
        "answers": {"free_time": "home", "conversation_depth": "deep", "planning_style": 2,
                    "social_frequency": 2, "conversation_topics": ["ideas"],
                    "valued_qualities": ["curiosity", "ambition"], "shared_hobbies_importance": 2},
        "weights": (0.25, 0.30, 0.25, 0.20),
    },
    {
        "email": "mira@" + DEMO_DOMAIN, "name": "Mira (demo)", "birth_date": "1996-06-08",
        "city": "Pune", "connection": "activity_partner",
        "bio": ("Marathon training most mornings, cooking for friends most evenings, and always "
                "planning the next trip somewhere with a coastline."),
        "interests": ["fitness", "cooking", "travel", "food", "cycling"],
        "answers": {"free_time": "social", "conversation_depth": "light", "planning_style": 2,
                    "social_frequency": 5, "conversation_topics": ["everyday", "humour"],
                    "valued_qualities": ["humour", "kindness"], "shared_hobbies_importance": 3},
        "weights": (0.40, 0.20, 0.20, 0.20),
    },
    {
        "email": "sana@" + DEMO_DOMAIN, "name": "Sana (demo)", "birth_date": "1999-03-19",
        "city": "Hyderabad", "connection": "friendship",
        "bio": ("I sketch people on trains and photograph old buildings. Volunteering at a "
                "community art room keeps my week honest."),
        "interests": ["art", "photography", "volunteering", "books", "music"],
        "answers": {"free_time": "creative", "conversation_depth": "deep", "planning_style": 3,
                    "social_frequency": 3, "conversation_topics": ["culture", "ideas"],
                    "valued_qualities": ["kindness", "curiosity"], "shared_hobbies_importance": 4},
        "weights": (0.30, 0.25, 0.25, 0.20),
    },
    {
        "email": "kabir@" + DEMO_DOMAIN, "name": "Kabir (demo)", "birth_date": "1993-07-30",
        "city": "Pune", "connection": "dating",
        "bio": ("Weekend hiker and cyclist, happiest on a long ridge with a daypack and no "
                "signal. I cook badly but enthusiastically."),
        "interests": ["outdoors", "cycling", "hiking", "fitness", "cooking"],
        "answers": {"free_time": "outdoors", "conversation_depth": "mix", "planning_style": 5,
                    "social_frequency": 3, "conversation_topics": ["everyday", "humour"],
                    "valued_qualities": ["humour", "calm"], "shared_hobbies_importance": 5},
        "weights": (0.35, 0.20, 0.20, 0.25),
    },
]


def _ensure_catalog(pod):
    existing = {str(r["normalized_name"]) for r in list_rows(pod, "aa_interests", limit=1000)}
    missing = [
        {"normalized_name": key, "label": label, "category": category, "is_custom": False}
        for key, label, category in SEED_CATALOG if key not in existing
    ]
    if missing:
        pod.records.bulk_create("aa_interests", missing)


def _ensure_account(pod, person):
    existing = find_one(pod, "aa_accounts", [("email", "eq", person["email"])])
    if existing:
        return existing, False
    password_hash, salt = hash_password(DEMO_PASSWORD)
    return pod.table("aa_accounts").create({
        "email": person["email"], "password_hash": password_hash, "password_salt": salt,
        "password_algo": "scrypt", "account_status": "active", "is_demo": True,
        "failed_login_count": 0,
    }), True


def _status(pod):
    accounts = [r for r in list_rows(pod, "aa_accounts", limit=500) if r.get("is_demo")]
    profiles = list_rows(pod, "aa_profiles", limit=500)
    return {
        "demo_accounts": len(accounts),
        "total_accounts": len(list_rows(pod, "aa_accounts", limit=500)),
        "profiles": len(profiles),
        "seeded": len(accounts) > 0,
        "credentials": {"email": DEMO_PEOPLE[0]["email"], "password": DEMO_PASSWORD},
        "label": "All demo accounts are fictional and flagged is_demo in the database.",
    }


def _run(pod, account, payload):
    _ensure_catalog(pod)
    created = 0
    accounts_by_email = {}
    for person in DEMO_PEOPLE:
        row, is_new = _ensure_account(pod, person)
        accounts_by_email[person["email"]] = row
        if is_new:
            created += 1
        account_id = str(row["id"])
        profile = find_one(pod, "aa_profiles", [("account_id", "eq", account_id)])
        if not profile:
            profile = pod.table("aa_profiles").create({
                "account_id": account_id, "display_name": person["name"],
                "birth_date": person["birth_date"], "bio": person["bio"], "city": person["city"],
                "discoverable": True, "show_age": True, "show_city": True,
                "onboarding_step": 5, "onboarding_completed": True,
                "connection_type": person["connection"],
            })
        linked = {str(r["interest_id"]) for r in list_rows(
            pod, "aa_profile_interests", [("profile_id", "eq", str(profile["id"]))], limit=100)}
        interests = ensure_interest_rows(pod, person["interests"])
        new_links = [
            {"profile_id": str(profile["id"]), "interest_id": str(interest["id"]), "source": "catalog"}
            for interest in interests if str(interest["id"]) not in linked
        ]
        if new_links:
            pod.records.bulk_create("aa_profile_interests", new_links)
        answered = {str(r["question_key"]) for r in list_rows(
            pod, "aa_questionnaire_responses", [("account_id", "eq", account_id)], limit=100)}
        missing_answers = [
            {"account_id": account_id, "question_key": key,
             "response_value": encode_json_value(value)}
            for key, value in person["answers"].items() if key not in answered
        ]
        if missing_answers:
            pod.records.bulk_create("aa_questionnaire_responses", missing_answers)
        if not find_one(pod, "aa_discovery_preferences", [("account_id", "eq", account_id)]):
            w = person["weights"]
            pod.table("aa_discovery_preferences").create({
                "account_id": account_id, "connection_type": person["connection"],
                "min_age": 21, "max_age": 45,
                "w_shared": w[0], "w_semantic": w[1], "w_communication": w[2], "w_lifestyle": w[3],
                "include_demo": True,
            })

    # Demonstration interactions, clearly seeded rather than pretending real
    # activity: Aarav has already expressed interest in the demo member, so
    # liking him back demonstrates a genuine reciprocal match.
    demo_id = str(accounts_by_email[DEMO_PEOPLE[0]["email"]]["id"])
    aarav_id = str(accounts_by_email[DEMO_PEOPLE[1]["email"]]["id"])
    ira_id = str(accounts_by_email[DEMO_PEOPLE[2]["email"]]["id"])
    seeded_interactions = 0
    for actor, target in ((aarav_id, demo_id), (ira_id, aarav_id)):
        if not find_one(pod, "aa_interactions", [("actor_id", "eq", actor), ("target_id", "eq", target),
                                                 ("action_type", "eq", "like")]):
            pod.table("aa_interactions").create({
                "actor_id": actor, "target_id": target, "action_type": "like", "active": True})
            seeded_interactions += 1
    if not find_one(pod, "aa_saved_profiles", [("account_id", "eq", demo_id), ("saved_account_id", "eq", ira_id)]):
        pod.table("aa_saved_profiles").create({"account_id": demo_id, "saved_account_id": ira_id})

    audit(pod, str(account["id"]) if account else None, "demo_seeded",
          {"accounts_created": created, "interactions": seeded_interactions})
    status = _status(pod)
    status["accounts_created"] = created
    status["interactions_seeded"] = seeded_interactions
    status["note"] = ("Demo members are deterministic and fictional. Their passwords are printed in "
                      "the README; they are not real people and hold no real personal data.")
    return status


def _dispatch(pod, data):
    action = str(data.action or "").strip().lower()
    if action == "status":
        return _status(pod)
    account = None
    if data.token:
        account = resolve_session(pod, data.token)
    elif list_rows(pod, "aa_accounts", limit=1):
        # Seeding over an existing workspace is a workspace-level action.
        raise ApiError("unauthenticated", "Sign in to seed the workspace.", 401)
    if action == "run":
        return _run(pod, account, data.payload or {})
    raise ApiError("unknown_action", f"Unknown action '{action}'.", 404)


async def aa_seed(ctx: FunctionContext, data: AaSeedInput) -> AaSeedOutput:
    try:
        return AaSeedOutput(**ok(_dispatch(ctx.pod, data)))
    except ApiError as error:
        return AaSeedOutput(**fail(error))
    except Exception as error:  # noqa: BLE001
        return AaSeedOutput(**fail(error))
