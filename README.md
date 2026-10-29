# AffinityAI — AI-powered compatibility, meaningful matching & social discovery

**Live app:** https://affinityai.apps.lemma.work
**Problem statement:** PS 1 — *Beyond the Swipe: smarter compatibility and meaningful matches.*

AffinityAI recommends people from **meaningful profile information** — shared interests,
written descriptions of what they enjoy, communication style and lifestyle rhythm — then shows
its working. Compatibility is a **preference alignment estimate** computed by deterministic
arithmetic over stored profiles, never a random number and never an LLM's opinion.

> Less swiping. More understanding.

---

## 1. What is actually running

| Layer | Implementation |
| --- | --- |
| Frontend | React 19 + TypeScript + Vite + React Router + TanStack Query + Lucide icons, hand-built design system (`frontend/src/styles.css`) |
| Backend | 9 Python service functions on the Lemma pod runtime (Pydantic request/response models): `aa_auth`, `aa_profile`, `aa_onboarding`, `aa_discovery`, `aa_interactions`, `aa_matches`, `aa_insights`, `aa_seed`, `aa_eval` |
| Database | PostgreSQL (pod datastore), 16 `aa_*` tables with FKs, enums, timestamps, unique keys |
| ML engine | `ml/affinity/` — pure standard-library Python: Jaccard, lexicon-expanded TF-IDF cosine, structured alignment, weighted scoring with missing-data renormalisation, ranking, explanations, evaluation |
| Auth | Email + password, **scrypt** hashing (n=2¹⁴, r=8, p=1, 32-byte digest, per-user salt), server-issued opaque session tokens stored only as SHA-256 hashes, 7-day expiry, revocation, lockout after 5 failed attempts |
| Deployment | Live on the Lemma app platform (`*.apps.lemma.work`) |

**Documented stack deviations** (chosen because the runtime does not host them):
* The backend is the pod function runtime rather than a standalone FastAPI process. The
  request/response contract is identical (Pydantic-validated JSON, versioned action endpoints);
  `docs/api.md` maps every endpoint to a function + action.
* Sentence-Transformers cannot be installed in the function sandbox (no wheels for the runtime,
  no `numpy`/`torch`), so semantic similarity uses the documented TF-IDF fallback with an explicit
  concept lexicon. `ml/affinity/text.py` is the single place that would swap for an embedding model.
* Alembic migrations are replaced by declarative table bundles (`pod/tables/*/*.json`) applied with
  `lemma pods import`; schema changes are versioned in git like any migration.

## 2. Features (all working end to end)

* Public landing page: hero, how it works, why compatibility matters, engine explanation, example
  explanations, privacy & safety, FAQ, CTAs, footer.
* Registration, sign-in, sign-out, persistent sessions, protected routes on the client **and**
  authorisation on the server for every call.
* Five-step onboarding wizard that persists each step and resumes where you left off: basics,
  interests (catalogue + up to 5 custom, normalised), seven-question compatibility questionnaire,
  discovery preferences with weight sliders, visibility/consent with a live profile preview.
* Discovery feed: eligible candidates scored and ranked server-side, with pagination, session
  de-duplication, per-candidate exclusion reasons and a diversity cap.
* Compatibility explorer: overall estimate, four dimension bars (only where data exists), shared
  interests, matched questions, respectful differences, missing-information list, conversation
  starters, and the exact arithmetic (`Σ wᵢsᵢ / Σ wᵢ`) behind the number.
* Interactions: like, pass, save, unsave, withdraw, block, unblock, report — all persisted, all
  idempotent, all reflected in the UI.
* **Mutual matches** created only when both members independently like each other; concurrency-safe
  (insert-then-reconcile); a block ends the match immediately.
* Feedback loop: four explicit signals, bounded to ±6 ranking points, shown in the explanation,
  resettable from Settings.
* Personal insights computed only from the caller's own rows (no fabricated analytics).
* Engine evidence page: **measured** Precision@5, Recall@5, NDCG@5, coverage, diversity and a
  semantic sanity check, stored per run — with the synthetic dataset clearly labelled.
* Profile & settings: edit profile, interests, answers, weights, visibility, blocked list, reset
  personalisation, change password, delete account.

## 3. Demo accounts (fictional, deterministic)

Seven members are seeded; every one is flagged `is_demo = true` and labelled "Demo profile" in the UI.
No real person's data is used.

| Email | Password | Notes |
| --- | --- | --- |
| `demo@demo.affinityai.invalid` | `DemoPass123!` | the intended demo member (full profile, weights) |
| `aarav@demo.affinityai.invalid` | `DemoPass123!` | has **already liked the demo member** — like him back to see a real mutual match |
| `ira@`, `dev@`, `mira@`, `sana@`, `kabir@demo.affinityai.invalid` | `DemoPass123!` | other fictional members |

Seeding is idempotent (`aa_seed` → `run`) and existing accounts are never overwritten.

## 4. How to use it (judge walkthrough, 2 minutes)

1. Open https://affinityai.apps.lemma.work and click **Sign In** → **Use demo member**
   (or register a fresh account and complete onboarding).
2. **Overview** — profile completion, eligible count, matches, saved, suggested connections.
3. **Discover** — six ranked profiles. Each card shows the estimate, its strongest dimension and
   the information coverage. Open **Why some profiles were excluded** to see eligibility reasons.
4. Click **View profile** on Aarav → see the dimension bars, shared interests, starters, the
   differences and the calculation table.
5. Go back, press **Like** on Aarav → an immediate **mutual match** (he had already liked you).
   Check **Matches**.
6. **Settings → weights**: drag *Shared interests* to 80 and *Lifestyle* to 0, save, return to
   **Discover** — the order and the scores change accordingly (weights are renormalised server-side).
7. **Settings → privacy**: block someone, then confirm they disappear from Discover.
8. **Engine evidence** → **Run evaluation now** to recompute the metrics live and store a new run.
9. **How it works** documents the methodology, including what the score is *not*.

## 5. Architecture

```
Browser (React/TS)
   │  lemma SDK → pod function runtime (authenticated as the pod member)
   ▼
aa_auth / aa_profile / aa_onboarding ─┐
aa_discovery (ML engine) ─────────────┤→ PostgreSQL (aa_* tables, shared, RLS off by design
aa_interactions / aa_matches ─────────┤   so two members' profiles can be compared)
aa_insights / aa_eval / aa_seed ──────┘
   ▲
ml/affinity/*.py  ── inlined at build time into each function (scripts/build_functions.py)
```

* `backend_src/common.py` — sessions, scrypt hashing, rate limiting, validation, paging, privacy
  projection, directory loading.
* `ml/affinity/` — `text.py`, `questionnaire.py`, `weights.py`, `similarity.py`, `compatibility.py`,
  `ranking.py`, `explain.py`, `starters.py`, `evaluation.py`.
* `pod/functions/*/code.py` are **generated** by `scripts/build_functions.py` from the modules above
  (the sandbox allows one file per function), so there is one source of truth.
* See `docs/architecture.md`, `api.md`, `ml-methodology.md`.

## 6. Database design (16 tables)

`aa_accounts` (email unique, scrypt hash + salt, status, is_demo, lockout counters) ·
`aa_sessions` (sha-256 token hash, expiry, revocation) · `aa_profiles` (1:1 with account,
birth_date — age is always calculated, never stored) · `aa_interests` (unique normalised name) ·
`aa_profile_interests` (join, unique per profile+interest) · `aa_questionnaire_responses`
(account + question key, JSON value) · `aa_discovery_preferences` (age range, connection type,
four weights) · `aa_interactions` (like/pass, active flag) · `aa_matches` (unordered pair, status) ·
`aa_saved_profiles` · `aa_blocks` · `aa_reports` (reason, details, status) · `aa_feedback` ·
`aa_recommendation_events` (score, coverage, dimensions, session) · `aa_audit_logs` · `aa_eval_runs`.

## 7. Compatibility score

```
overall = Σ(wᵢ · sᵢ) / Σ(wᵢ)      over dimensions i that have data on both sides
coverage = Σ(wᵢ for available i) / Σ(wᵢ for all i)
```

| Dimension | Method | Default weight |
| --- | --- | --- |
| Shared interests | Jaccard `|A∩B| / |A∪B|` | 35% |
| Interest & bio similarity | cosine over lexicon-expanded TF-IDF vectors | 25% |
| Communication style | mean of explicit answer similarity maps | 20% |
| Lifestyle rhythm | ordinal distance `1 − |a−b|/4` + categorical maps | 20% |

Missing data is **excluded from both numerator and denominator**, then the remaining weights are
renormalised; coverage is reported as the confidence signal (`high ≥ 85%`, `moderate ≥ 60%`,
`limited ≥ 35%`, else `low`). Opposite answers are never treated as incompatible: categorical pairs
carry explicit 1.0 / 0.8 / 0.5 / 0.3 values, and strong differences are surfaced as topics.

## 8. Tests and evidence (run, not claimed)

```bash
cd ml && python -m pytest -q          # 42 passed — Jaccard, semantic, ordinal/categorical,
                                      # missing-data, weights, scoring, eligibility, ranking,
                                      # diversity, feedback bounds, explanations, evaluation
python scripts/build_functions.py     # regenerate pod functions from modules
```

Measured on the synthetic, hand-labelled set (12 fictional profiles, 132 pairs, hand-written
relevance labels, k=5): **Precision@5 0.433**, Recall@5 0.806, NDCG@5 0.762, coverage 1.0,
random baseline Precision@5 0.200. Semantic sanity check: paraphrase pairs 0.224 mean cosine vs
unrelated 0.027. These are offline results on synthetic data — not real-user outcomes.

## 9. Security & privacy

scrypt password hashing · opaque session tokens hashed at rest · login rate limiting and lockout ·
server-side authorization with a session token on every call · 18+ enforcement on birth date ·
no precise location, city only and hidden on request · questionnaire answers never serialised to
other members · blocks enforce exclusion in both directions · reports keep the reporter private and
honest statuses · account deletion removes profile content, interests, answers, sessions, likes,
saves, feedback (block rows retained without personal data and disclosed) · no secrets in the
frontend · safe input validation and quoted SQL literals throughout · audit log for security events.

**Known limitation:** the pod datastore tables are shared (RLS off) so the engine can compare two
members; per-account isolation is enforced in the service layer, not by row-level security. In a
production deployment each tenant would get its own schema with RLS, and session tokens would move
to `HttpOnly` cookies behind a same-origin BFF (this app stores a revocable 7-day token in
`localStorage` because the app is served from a static host).

## 10. Running it locally

```bash
# 1. Engine tests
cd ml && python -m pytest -q

# 2. Frontend
cd frontend
cp .env.example .env.local        # fill VITE_LEMMA_POD_ID / API / AUTH URLs
npm install
npm run dev                       # http://127.0.0.1:5173
npm run build

# 3. Pod resources
lemma pods import ./pod           # tables + functions (idempotent upsert)
lemma functions run aa_seed --data '{"action":"run","token":"<session token>"}'

# 4. End-to-end smoke test against the live functions
python scripts/smoke_api.py
```

## 11. Current limitations (honest list)

* Semantic similarity is lexicon + TF-IDF, not a sentence-transformer embedding; the lexicon is
  hand-curated and finite (documented in `text.py`).
* Evaluation labels are hand-written on synthetic profiles; no real-user evaluation exists, so no
  claim of validated accuracy is made anywhere in the product.
* Question weights inside a dimension are unweighted means — a defensible but simple choice.
* No chat/messaging, no photo upload pipeline (initials avatars with an optional URL field), no
  email delivery, so no password-reset-by-email flow is offered rather than faked.
* Reports are stored; there is no reviewer console yet, and the UI says so.
* Distance/location-based discovery is not implemented (city is display-only).

## 12. Future work

Sentence-transformer embeddings with cached vectors · learned weights from explicit feedback with
honest offline evaluation · reviewer console for reports · messaging with consent gates · photo
moderation · per-tenant schemas with RLS · A/B evaluation of ranking variants.
