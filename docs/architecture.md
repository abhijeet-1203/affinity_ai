# Architecture

## Runtime shape
The app is a static React bundle served by the Lemma host. All state lives in PostgreSQL via the
pod function runtime. The browser holds exactly one thing: a revocable session token.

```
React (Vite) ──► lemma SDK ──► function runtime ──► aa_* tables
                                   │
                                   └─ ml/affinity (inlined at build time)
```

## Why functions, not REST routes in the browser
Authorization must not be a frontend concern. Every action re-resolves the caller from the session
token server-side, so a forged `account_id` in a payload cannot read another member's profile,
likes or answers. The browser never receives another member's questionnaire answers at all.

## Shared tables, service-level isolation
`aa_*` tables are created with `enable_rls: false` because compatibility scoring compares **two**
members' profiles, which per-user rows would make impossible. Isolation between app accounts is
enforced in `backend_src/common.py` (`resolve_session`, `account_public`, `profile_bundle`) and in
each handler. This is documented as a known limitation with the production path (per-tenant schema
+ RLS).

## Build pipeline
`scripts/build_functions.py` inlines `backend_src/common.py` and `ml/affinity/*.py` into each
function's single `code.py` (the sandbox allows one file). The modules remain the source of truth;
the generated files carry a banner. `lemma pods import ./pod` applies tables and functions
idempotently.

## Concurrency
A reciprocal like inserts a match then re-reads every row for the unordered pair and reconciles to
the oldest (deleting any extras). Two simultaneous likes converge on one match; a block sets that
match to `blocked` immediately.

## Failure behaviour
No silent mock fallbacks: a failing function returns a typed error, and the UI shows it with a retry
control. Empty states explain *why* they are empty using the server's `empty_reason` and the
per-candidate exclusion list.
