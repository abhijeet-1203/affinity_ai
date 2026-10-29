# API

Every endpoint is a call to one pod function with an envelope:

```json
{ "action": "<endpoint>", "token": "<session token or null>", "payload": { ... } }
```

Response: `{ "ok": true, "data": {...}, "error": null }` or
`{ "ok": false, "data": null, "error": { "code", "message", "status" } }`.

| Method & path (REST name) | Function action | Auth |
| --- | --- | --- |
| POST /api/v1/auth/register | `aa_auth:register` | – |
| POST /api/v1/auth/login | `aa_auth:login` | – |
| POST /api/v1/auth/logout | `aa_auth:logout` | token |
| GET /api/v1/auth/me | `aa_auth:me` | token |
| POST /api/v1/auth/password | `aa_auth:change_password` | token |
| DELETE /api/v1/auth/account | `aa_auth:delete_account` | token + password |
| GET /api/v1/profile/me | `aa_profile:get` | token |
| PUT /api/v1/profile/me | `aa_profile:update` | token |
| GET /api/v1/profiles/{id} | `aa_profile:public` | token |
| GET /api/v1/interests | `aa_profile:catalog` | token |
| POST /api/v1/personalisation/reset | `aa_profile:reset_personalization` | token |
| GET /api/v1/onboarding/status | `aa_onboarding:status` | token |
| PUT /api/v1/onboarding/profile | `aa_onboarding:save_profile` | token |
| PUT /api/v1/onboarding/interests | `aa_onboarding:save_interests` | token |
| PUT /api/v1/onboarding/responses | `aa_onboarding:save_answers` | token |
| PUT /api/v1/onboarding/preferences | `aa_onboarding:save_preferences` | token |
| POST /api/v1/onboarding/complete | `aa_onboarding:complete` | token |
| GET /api/v1/onboarding/preview | `aa_onboarding:preview` | token |
| GET /api/v1/discovery/recommendations | `aa_discovery:recommendations` | token |
| GET /api/v1/discovery/recommendations/{id} | `aa_discovery:detail` | token |
| POST /api/v1/discovery/feedback | `aa_discovery:feedback` | token |
| GET /api/v1/discovery/starters/{id} | `aa_discovery:starters` | token |
| POST /api/v1/interactions/like | `aa_interactions:like` | token |
| POST /api/v1/interactions/pass | `aa_interactions:pass` | token |
| POST /api/v1/interactions/save | `aa_interactions:save` | token |
| DELETE /api/v1/interactions/save/{id} | `aa_interactions:unsave` | token |
| POST /api/v1/interactions/block | `aa_interactions:block` | token |
| DELETE /api/v1/interactions/block/{id} | `aa_interactions:unblock` | token |
| POST /api/v1/interactions/report | `aa_interactions:report` | token |
| POST /api/v1/interactions/withdraw | `aa_interactions:withdraw` | token |
| GET /api/v1/interactions/summary | `aa_interactions:summary` | token |
| GET /api/v1/matches | `aa_matches:list` | token |
| GET /api/v1/matches/{id} | `aa_matches:get` | token |
| POST /api/v1/matches/{id}/withdraw | `aa_matches:withdraw` | token |
| GET /api/v1/insights | `aa_insights:summary` | token |
| GET /api/v1/evaluation | `aa_eval:latest` | – |
| POST /api/v1/evaluation/run | `aa_eval:run` | token |
| GET /api/v1/demo/status | `aa_seed:status` | – |
| POST /api/v1/demo/seed | `aa_seed:run` | token (or empty workspace) |

Errors use stable codes: `unauthenticated`, `invalid_session`, `session_expired`, `invalid_credentials`,
`account_locked`, `email_taken`, `weak_password`, `age_restricted`, `invalid_input`, `not_found`,
`invalid_target`, `onboarding_incomplete`, `nothing_to_update`, `unknown_action`.
