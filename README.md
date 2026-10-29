# AffinityAI — AI-Powered Compatibility, Meaningful Matching & Social Discovery

**Live Application:** [https://affinityai.apps.lemma.work/](https://affinityai.apps.lemma.work/)
**Hackathon:** AFFECIO HACKS ’26
**Problem Statement:** PS 1 — Beyond the Swipe: Smarter Compatibility and Meaningful Matches

> **Less swiping. More understanding.**

AffinityAI is an AI-powered compatibility and social-discovery platform designed to help people discover meaningful connections beyond superficial profile browsing. It analyzes shared interests, profile descriptions, communication preferences, and lifestyle alignment to generate explainable compatibility estimates and personalized recommendations.

Unlike conventional swipe-based platforms, AffinityAI explains *why* two people may be compatible, identifies shared interests, highlights areas of alignment and difference, and gives users control over their matching preferences.

**Important:** Compatibility scores represent preference alignment based on available profile information. They are not probabilities of relationship success.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Our Solution](#our-solution)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Machine Learning and Compatibility Methodology](#machine-learning-and-compatibility-methodology)
- [Recommendation Ranking](#recommendation-ranking)
- [Database Design](#database-design)
- [Authentication and Security](#authentication-and-security)
- [Demo Accounts](#demo-accounts)
- [Judge Walkthrough](#judge-walkthrough)
- [Local Development and Testing](#local-development-and-testing)
- [Evaluation Results](#evaluation-results)
- [Backend API Overview](#backend-api-overview)
- [Project Structure](#project-structure)
- [Known Limitations](#known-limitations)
- [Future Enhancements](#future-enhancements)
- [Responsible AI and Privacy](#responsible-ai-and-privacy)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

Modern dating and social-discovery applications often encourage users to make quick decisions based on profile pictures, short biographies, or limited information. This can make it difficult to understand whether two people share interests, communication preferences, values, and lifestyle habits.

AffinityAI addresses this challenge by creating a transparent and explainable recommendation experience.

The platform evaluates available profile information, calculates compatibility across multiple dimensions, ranks eligible profiles, and explains the signals behind its recommendations.

### Our Core Principles

- **Meaningful connections:** Focus on shared interests and preference alignment rather than superficial browsing alone.
- **Explainable AI:** Show the factors contributing to compatibility estimates.
- **User control:** Allow users to adjust matching weights and discovery preferences.
- **Transparency:** Identify missing information instead of silently treating it as incompatibility.
- **Mutual consent:** Create matches only after both users independently express interest.
- **Privacy:** Keep private questionnaire responses and account information protected from other members.
- **Responsible recommendations:** Never claim that a numerical score guarantees relationship success.

---

## Problem Statement

### PS 1 — Beyond the Swipe: Smarter Compatibility and Meaningful Matches

Traditional dating and social-discovery experiences can prioritize quick profile decisions over deeper compatibility signals.

Users may encounter numerous profiles without understanding:

- Which interests they share with another person.
- Whether their communication preferences align.
- How their lifestyles and routines compare.
- Why a particular profile appears in their recommendations.
- Which areas of similarity or difference could support meaningful conversation.

The challenge is to develop a smarter discovery platform that promotes understanding, transparency, and more meaningful connections.

## Our Solution

AffinityAI combines profile-based similarity analysis, structured preference comparison, explainable scoring, and personalized ranking.

The platform:

1. Collects profile information, interests, questionnaire answers, and discovery preferences.
2. Compares eligible profiles using deterministic similarity methods.
3. Calculates weighted compatibility estimates using available information.
4. Ranks recommendations according to compatibility and user preferences.
5. Explains shared interests, aligned preferences, differences, and missing information.
6. Provides conversation starters based on shared interests.
7. Incorporates bounded user feedback into recommendation ranking.
8. Creates a mutual match only when both users independently like each other.

The system is designed to support human decisions rather than make relationship decisions on users' behalf.

---

## Key Features

### 1. Modern Landing Page

- Clear product introduction and value proposition.
- Explanation of the compatibility methodology.
- Overview of key platform features.
- Privacy and safety information.
- Frequently asked questions.
- Registration and sign-in navigation.

### 2. Authentication and Session Management

- User registration and login.
- Secure password hashing.
- Server-side authorization.
- Persistent sessions with expiration.
- Session revocation during logout.
- Failed-login protection.

### 3. Five-Step Onboarding

The onboarding workflow collects the information required to personalize recommendations.

**Step 1 — Basic Profile**

- Profile details.
- Personal description.
- Optional broad location information.

**Step 2 — Interests**

- Selection from a predefined interest catalogue.
- Support for normalized custom interests.
- Profile-based interest comparison.

**Step 3 — Compatibility Questionnaire**

- Seven compatibility-related questions.
- Structured responses used for preference alignment.

**Step 4 — Discovery Preferences**

- Connection and discovery preferences.
- Customizable matching weights.
- Personalized recommendation settings.

**Step 5 — Visibility and Consent**

- Profile visibility settings.
- Profile preview.
- User-controlled discovery participation.

Onboarding progress is persisted so users can resume the process.

### 4. Intelligent Discovery Feed

The discovery feed ranks eligible profiles using compatibility estimates and configured preferences.

Features include:

- Server-side candidate eligibility.
- Compatibility-based recommendation ranking.
- Paginated discovery results.
- Session-level recommendation de-duplication.
- Exclusion explanations.
- Diversity controls to reduce repetitive recommendations.

### 5. Explainable Compatibility Explorer

Each recommended profile can include a detailed compatibility breakdown.

Users can explore:

- Overall compatibility estimate.
- Dimension-level similarity scores.
- Shared interests.
- Aligned questionnaire responses.
- Areas of difference.
- Missing-information indicators.
- Conversation starters.
- A calculation table explaining the final estimate.

The purpose is not merely to display a number but to explain the evidence behind it.

### 6. Profile Interactions

AffinityAI supports persistent user interactions:

- Like a profile.
- Pass on a profile.
- Save a profile.
- Unsave a profile.
- Withdraw interest.
- Block a profile.
- Unblock a profile.
- Report a profile.

The interaction layer supports idempotent actions to reduce unintended duplicate state changes.

### 7. Mutual Matching

AffinityAI follows a consent-based matching model.

- A single like does not create a mutual match.
- A match is created only after reciprocal interest.
- Concurrent reciprocal actions are reconciled to avoid duplicate matches.
- Blocking ends the relevant match immediately.

### 8. Feedback-Driven Ranking

Users can provide explicit feedback about recommendations.

- Feedback can influence recommendation ranking.
- Adjustments are bounded to **±6 ranking points**.
- The system can explain the feedback adjustment.
- Users can reset personalization through Settings.

Feedback is used as a bounded ranking adjustment rather than as an unvalidated claim of relationship prediction.

### 9. Personal Insights

The platform provides personal analytics based on persisted user records.

These insights are intended to help users understand their own discovery activity without fabricating activity counts.

### 10. Engine Evidence and Evaluation

The evaluation interface provides visibility into the recommendation engine's measured offline performance.

Metrics include:

- Precision\@5.
- Recall\@5.
- NDCG\@5.
- Recommendation coverage.
- Diversity.
- Semantic-similarity sanity checks.

Evaluation uses a synthetic, hand-labelled dataset. Results must not be interpreted as evidence of real-world dating accuracy.

### 11. Profile and Settings Management

Users can manage:

- Profile information.
- Interests.
- Questionnaire responses.
- Matching weights.
- Discovery preferences.
- Profile visibility.
- Blocked profiles.
- Personalization settings.
- Password changes.
- Account deletion.

---

## Technology Stack

| Layer                           | Technologies                                        |
| ------------------------------- | --------------------------------------------------- |
| Frontend                        | React 19, TypeScript, Vite                          |
| Routing                         | React Router                                        |
| Server-state management         | TanStack Query                                      |
| Icons                           | Lucide                                              |
| UI styling                      | Custom design system and CSS                        |
| Backend runtime                 | Lemma pod function runtime                          |
| Request and response validation | Pydantic                                            |
| Database                        | PostgreSQL pod datastore                            |
| Compatibility engine            | Python standard library                             |
| Text similarity                 | Lexicon-expanded TF-IDF and cosine similarity       |
| Structured similarity           | Jaccard similarity and explicit preference mappings |
| Password security               | Scrypt                                              |
| Session management              | Opaque session tokens with hashed token storage     |
| Deployment                      | Lemma application platform                          |

### Runtime Implementation Notes

The deployed implementation uses the Lemma pod function runtime rather than a standalone FastAPI server.

The compatibility engine is implemented using Python's standard library because the deployed function environment does not provide the full dependency stack required for heavier embedding models.

Database schema resources are managed through declarative pod table definitions rather than a conventional Alembic migration workflow.

These choices reflect the application's actual deployment environment.

---

## System Architecture

AffinityAI follows a frontend, backend-functions, database, and compatibility-engine architecture.

```text
                  ┌──────────────────────────┐
                  │       User Browser       │
                  │                          │
                  │     React + TypeScript   │
                  │      Vite Frontend       │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │     Lemma SDK / API      │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │    Backend Functions     │
                  │                          │
                  │ aa_auth                  │
                  │ aa_profile               │
                  │ aa_onboarding            │
                  │ aa_discovery             │
                  │ aa_interactions          │
                  │ aa_matches               │
                  │ aa_insights              │
                  │ aa_seed                  │
                  │ aa_eval                  │
                  └────────────┬─────────────┘
                               │
                  ┌────────────┴─────────────┐
                  ▼                          ▼
       ┌────────────────────┐    ┌────────────────────┐
       │ PostgreSQL         │    │ Compatibility       │
       │ Pod Datastore      │    │ Engine              │
       │                    │    │                    │
       │ Profiles           │    │ Similarity          │
       │ Interests          │    │ Weighted scoring    │
       │ Interactions       │    │ Ranking             │
       │ Matches            │    │ Explanations        │
       │ Feedback           │    │ Evaluation          │
       └────────────────────┘    └────────────────────┘
```

### Architecture Highlights

- The frontend handles the user interface and navigation.
- Backend functions validate requests and apply application rules.
- PostgreSQL stores persistent profiles, preferences, interactions, and evaluation records.
- The compatibility engine calculates similarity and recommendation explanations.
- Recommendation eligibility and ranking are handled server-side.
- Shared compatibility modules are incorporated into deployable functions through the function-build script.

---

## Machine Learning and Compatibility Methodology

AffinityAI uses a transparent, multi-dimensional compatibility engine.

Rather than producing an unexplained score, the engine calculates similarity across available profile information and exposes the factors contributing to the result.

### 1. Shared Interest Similarity

Jaccard similarity measures the overlap between two users' interest sets.

[
J(A,B)=\frac{|A\cap B|}{|A\cup B|}
]

Where:

- (A) represents the first user's interests.
- (B) represents the second user's interests.
- (A\cap B) represents shared interests.
- (A\cup B) represents all unique interests across both users.

A higher value indicates a greater proportion of shared interests.

### 2. Text Similarity

The text similarity component compares profile descriptions using lexicon-expanded TF-IDF vectors and cosine similarity.

The process includes:

1. Text normalization.
2. Expansion of recognized related concepts using a curated lexicon.
3. TF-IDF vector construction.
4. Cosine similarity calculation.
5. Use of similarity evidence in the compatibility calculation.

Cosine similarity is calculated as:

[
\operatorname{cosine}(A,B)=
\frac{A\cdot B}{|A||B|}
]

This approach provides a lightweight alternative when larger language-model embedding dependencies are unavailable in the runtime.

It is important to distinguish this implementation from a transformer-based semantic embedding model: AffinityAI currently uses a curated lexicon and TF-IDF rather than Sentence Transformers.

### 3. Structured Preference Alignment

Questionnaire responses are compared using explicit similarity mappings.

The engine supports categorical mappings and ordinal-distance comparisons where appropriate.

Documented categorical alignment values include:

| Alignment         | Score |
| ----------------- | ----: |
| Strong alignment  |   1.0 |
| High alignment    |   0.8 |
| Partial alignment |   0.5 |
| Lower alignment   |   0.3 |

These values are predefined mappings, not probabilities of a successful relationship.

### 4. Lifestyle Alignment

Lifestyle preferences are compared as a separate compatibility dimension.

Users can adjust the importance of lifestyle alignment through matching settings.

### 5. Weighted Compatibility Score

The default compatibility dimensions and weights are:

| Dimension                         | Default Weight |
| --------------------------------- | -------------: |
| Shared interests                  |            35% |
| Interest and biography similarity |            25% |
| Communication preferences         |            20% |
| Lifestyle preferences             |            20% |
| **Total**                         |       **100%** |

The weighted score is calculated using dimensions for which both profiles contain usable data:

[
S=\frac{\sum\_{i\in A}w_i s_i}{\sum\_{i\in A}w_i}
]

Where:

- (S) is the final compatibility estimate.
- (w_i) is the configured weight of dimension (i).
- (s_i) is the similarity score for dimension (i).
- (A) is the set of dimensions with usable data for both profiles.

The engine renormalizes weights over available dimensions rather than automatically treating missing information as incompatibility.

### 6. Data Coverage

The engine also calculates data coverage:

[
C=\frac{\sum\_{i\in A}w_i}{\sum\_{i\in D}w_i}
]

Where (D) represents all configured dimensions.

Coverage communicates how much of the configured compatibility information was available for the comparison.

The documented coverage labels are:

| Coverage | Threshold |
| -------- | --------: |
| High     |     ≥ 85% |
| Moderate |     ≥ 60% |
| Limited  |     ≥ 35% |
| Low      |     < 35% |

This helps users distinguish a score supported by substantial profile information from one calculated using limited data.

### 7. Explainable Results

The engine produces explanations based on available comparison evidence.

Examples of explanation categories include:

- Shared interests.
- Similar communication preferences.
- Lifestyle alignment.
- Differences worth discussing.
- Missing information.
- The contribution of individual compatibility dimensions.

The engine is designed to explain preference alignment, not to infer personal worth or guarantee relationship outcomes.

---

## Recommendation Ranking

Compatibility scoring and recommendation ranking serve different purposes.

- **Compatibility scoring** estimates alignment between two profiles.
- **Eligibility filtering** determines whether a profile can be recommended.
- **Ranking** orders eligible profiles using the configured preferences and permitted feedback adjustments.

The discovery system includes:

- Server-side eligibility checks.
- Compatibility-based ordering.
- Pagination.
- Session-level de-duplication.
- Diversity controls.
- Bounded feedback adjustments.
- Explanations for recommendations and exclusions.

The ranking system does not treat a recommendation as consent or reciprocal interest.

---

## Database Design

AffinityAI uses a PostgreSQL pod datastore with 16 documented `aa_*` tables.

| Table                        | Purpose                                    |
| ---------------------------- | ------------------------------------------ |
| `aa_accounts`                | Account and authentication information     |
| `aa_sessions`                | Session records and expiry                 |
| `aa_profiles`                | User profile information                   |
| `aa_interests`               | Interest catalogue                         |
| `aa_profile_interests`       | Profile-to-interest relationships          |
| `aa_questionnaire_responses` | Structured questionnaire answers           |
| `aa_discovery_preferences`   | Discovery preferences and matching weights |
| `aa_interactions`            | Like, pass, and related interactions       |
| `aa_matches`                 | Reciprocal matches                         |
| `aa_saved_profiles`          | Saved profile records                      |
| `aa_blocks`                  | Blocking relationships                     |
| `aa_reports`                 | Profile reports                            |
| `aa_feedback`                | Recommendation feedback                    |
| `aa_recommendation_events`   | Recommendation-related events              |
| `aa_audit_logs`              | Auditable application actions              |
| `aa_eval_runs`               | Stored engine evaluation results           |

The schema uses relational constraints, timestamps, foreign keys, and uniqueness rules to maintain consistent application state.

---

## Authentication and Security

AffinityAI implements password-based authentication and revocable sessions.

### Password Security

Passwords are hashed using Scrypt with the documented configuration:

- `n = 2^14`
- `r = 8`
- `p = 1`
- 32-byte digest
- Per-user salt

Plaintext passwords are not intended to be stored in the database.

### Session Security

- The application issues opaque session tokens.
- Session tokens are stored as SHA-256 hashes on the server.
- Sessions expire after seven days.
- Sessions can be revoked.
- Failed login attempts trigger lockout protection after five failures.

### Privacy Controls

- Private questionnaire responses are not exposed to other members.
- Blocking affects discovery and the relevant match.
- Users can manage profile visibility.
- Users can change their matching preferences.
- Account deletion is supported in the application.

### Production Security Considerations

The current static-host implementation stores the session token in browser `localStorage`. A production deployment should consider a same-origin backend-for-frontend architecture using secure, `HttpOnly` cookies.

The documented shared pod datastore uses service-layer authorization rather than database row-level security. Stronger tenant isolation and database-level access policies would be appropriate future improvements.

---

## Demo Accounts

The application includes fictional demo data for evaluation and demonstrations.

**Documented demo account**

- Email: `demo@demo.affinityai.invalid`
- Password: `DemoPass123!`

The demo dataset also includes fictional profiles such as Aarav and other seeded users.

The Aarav demo profile has already liked the demo member, allowing the reciprocal-like workflow to be demonstrated.

Use only the configured fictional demo environment. Do not use demo credentials for real accounts or production systems.

---

## Judge Walkthrough

The following sequence demonstrates the core project features.

### Step 1 — Open the Application

Visit:

[https://affinityai.apps.lemma.work/](https://affinityai.apps.lemma.work/)

Review the landing page and the explanation of the platform's purpose.

### Step 2 — Sign In

Use the documented demo account:

```text
Email: demo@demo.affinityai.invalid
Password: DemoPass123!
```

### Step 3 — Explore the Dashboard

Review the member overview and available navigation.

### Step 4 — Open Discover

Inspect recommended profiles and their compatibility estimates.

### Step 5 — Open a Compatibility Breakdown

Select a profile and inspect:

- Shared interests.
- Compatibility dimensions.
- Areas of alignment.
- Differences.
- Missing-information indicators.
- The score calculation.

### Step 6 — Demonstrate Mutual Matching

Open the seeded Aarav profile and like it.

Because Aarav has already liked the demo member, this action demonstrates the reciprocal-interest workflow.

### Step 7 — Adjust Matching Weights

Open Settings and change the relative importance of compatibility dimensions.

For example, reduce the Lifestyle weight, save the settings, and revisit Discover to observe the effect on scoring and ranking.

### Step 8 — Demonstrate Blocking

Open the privacy settings, block a profile, and verify that the blocked profile is excluded from discovery.

### Step 9 — Run Engine Evaluation

Open Engine Evidence and choose **Run evaluation now**.

Review the recorded offline evaluation metrics.

### Step 10 — Review the Methodology

Visit the methodology or “How it works” page to understand the scoring approach and its limitations.

---

## Local Development and Testing

Local execution requires the repository source and the appropriate frontend and Lemma runtime configuration.

### Prerequisites

- Python.
- `pytest`.
- Node.js and npm.
- Lemma CLI access for pod operations.
- Appropriate environment values for the configured Lemma application.

### 1. Run the Compatibility Engine Tests

From the repository root:

```bash
cd ml
python -m pytest -q
```

The documented test run reports **42 passed**.

The suite covers similarity calculations, text similarity, structured alignment, missing-data handling, configurable weights, compatibility scoring, eligibility, ranking, diversity, feedback bounds, explanations, and evaluation.

### 2. Build the Deployable Functions

From the repository root:

```bash
python scripts/build_functions.py
```

This regenerates the deployable function bundles from the shared source modules.

### 3. Configure the Frontend

Navigate to the frontend directory:

```bash
cd frontend
```

Copy the example environment file:

```bash
cp .env.example .env.local
```

Configure the required environment values, including `VITE_LEMMA_POD_ID` and any API or authentication URLs required by the project.

Install the dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The development server is expected to run at:

```text
http://127.0.0.1:5173
```

Create a production build:

```bash
npm run build
```

### 4. Import Pod Resources

From the repository root, with the Lemma CLI configured:

```bash
lemma pods import ./pod
```

The table and function import is designed as an idempotent upsert.

### 5. Seed Demo Data

The documented seed command is:

```bash
lemma functions run aa_seed --data '{"action":"run","token":"<session token>"}'
```

Replace the placeholder with a valid session token for the configured environment. Never commit session tokens or credentials to source control.

### 6. Run the API Smoke Test

From the repository root:

```bash
python scripts/smoke_api.py
```

Ensure that the target environment and credentials are configured correctly before running the smoke test.

---

## Evaluation Results

AffinityAI includes an offline evaluation against a synthetic, hand-labelled dataset.

### Evaluation Dataset

| Property           |                         Value |
| ------------------ | ----------------------------: |
| Fictional profiles |                            12 |
| Profile pairs      |                           132 |
| Evaluation method  | Hand-written relevance labels |
| Ranking cutoff     |                             5 |

### Measured Offline Results

| Metric                       | Result |
| ---------------------------- | -----: |
| Precision\@5                 |  0.433 |
| Recall\@5                    |  0.806 |
| NDCG\@5                      |  0.762 |
| Coverage                     |  1.000 |
| Random-baseline Precision\@5 |  0.200 |

### Semantic Similarity Sanity Check

| Pair Type        | Mean Cosine Similarity |
| ---------------- | ---------------------: |
| Paraphrase pairs |                  0.224 |
| Unrelated pairs  |                  0.027 |

### Interpretation

These results demonstrate the engine's behavior on the documented synthetic dataset.

They do **not** establish:

- Real-world dating accuracy.
- Relationship success prediction.
- Validated outcomes for real users.
- Generalization to all user populations.

The evaluation interface can run the evaluation again and store a new result.

---

## Backend API Overview

AffinityAI exposes backend actions through the Lemma pod function runtime. It is not deployed as a standalone FastAPI service.

| Function          | Responsibility                                                          |
| ----------------- | ----------------------------------------------------------------------- |
| `aa_auth`         | Registration, login, sessions, and authentication                       |
| `aa_profile`      | Profile retrieval and updates                                           |
| `aa_onboarding`   | Onboarding progress, interests, answers, and preferences                |
| `aa_discovery`    | Candidate eligibility, compatibility scoring, ranking, and explanations |
| `aa_interactions` | Likes, passes, saves, blocking, reports, and related actions            |
| `aa_matches`      | Mutual-match retrieval and lifecycle                                    |
| `aa_insights`     | Personal insights and analytics                                         |
| `aa_seed`         | Fictional demonstration data                                            |
| `aa_eval`         | Offline engine evaluation and stored evaluation runs                    |

For exact action names, request and response structures, and authentication requirements, consult `docs/api.md` in the repository.

---

## Project Structure

The following is a representative structure based on the documented implementation. Refer to the repository for the exact current file list.

```text
affinityai/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── styles.css
│   ├── package.json
│   └── .env.example
├── backend_src/
│   └── common.py
├── ml/
│   └── affinity/
│       ├── text.py
│       ├── questionnaire.py
│       ├── weights.py
│       ├── similarity.py
│       ├── compatibility.py
│       ├── ranking.py
│       ├── explain.py
│       ├── starters.py
│       └── evaluation.py
├── pod/
│   ├── functions/
│   └── tables/
├── scripts/
│   ├── build_functions.py
│   └── smoke_api.py
└── docs/
    ├── architecture.md
    ├── api.md
    └── ml-methodology.md
```

---

## Known Limitations

The following limitations are documented in the current implementation.

1. **Text similarity:** The engine uses a curated concept lexicon with TF-IDF rather than Sentence Transformer embeddings. Its vocabulary is finite.
2. **Evaluation data:** Evaluation uses synthetic profiles and hand-written relevance labels, not real-user outcomes.
3. **Questionnaire weighting:** Answers within a dimension use an unweighted mean.
4. **Messaging:** In-app chat and messaging are not implemented.
5. **Photo upload:** A complete photo-upload pipeline is not implemented. Profiles can use initials-based avatars and an optional avatar URL field.
6. **Email delivery:** Email delivery is not configured, so email-based password reset is not offered.
7. **Report review:** Reports are stored, but a reviewer console is not implemented.
8. **Distance discovery:** City information is display-only; GPS-based or distance-based discovery is not implemented.
9. **Database isolation:** The shared pod datastore uses service-layer authorization rather than row-level security.
10. **Session storage:** The static-host implementation stores a revocable seven-day session token in `localStorage`. Secure `HttpOnly` cookies are recommended for production.

These limitations are stated explicitly so that judges and users can distinguish implemented functionality from future work.

---

## Future Enhancements

Potential improvements include:

- Integrating Sentence Transformer embeddings when the runtime supports the required dependencies.
- Improving personalized ranking using explicit feedback and rigorous offline evaluation.
- Developing a reviewer console for reports and moderation workflows.
- Introducing consent-gated messaging after mutual matches.
- Implementing a secure photo-upload and moderation pipeline.
- Adding per-tenant database schemas and row-level security.
- Moving session handling to secure `HttpOnly` cookies.
- Evaluating ranking alternatives with privacy-conscious experiments.
- Expanding evaluation datasets using representative, consent-based data.
- Improving accessibility and automated testing coverage.

These are proposed enhancements, not claims about existing features.

---

## Responsible AI and Privacy

AffinityAI is designed to help users explore preference alignment. It does not attempt to judge a person's worth or guarantee a successful relationship.

The project follows these principles:

- Compatibility scores are not relationship-success probabilities.
- Missing information is not automatically treated as incompatibility.
- Differences can provide useful conversation topics rather than being treated as defects.
- Recommendations do not imply reciprocal interest.
- Mutual matches require independent interest from both users.
- Private questionnaire responses are not exposed to other members.
- Users can adjust preferences, control visibility, and block profiles.
- Synthetic evaluation results must not be presented as real-world dating outcomes.
- Users retain control over whether to interact with a recommendation.

The system is intended to support user judgment, not replace it.

---

## Contributing

Contributions can focus on improving compatibility explanations, test coverage, accessibility, privacy controls, and recommendation evaluation.

Before contributing:

1. Review the project structure and implementation notes.
2. Run the compatibility engine tests.
3. Avoid committing credentials, session tokens, or private user data.
4. Clearly document any new scoring assumptions.
5. Add tests for changes to ranking or compatibility behavior.
6. Distinguish measured results from assumptions or proposed improvements.

A formal contribution workflow and issue-reporting process can be added as the project evolves.

---

## License

This project is licensed under the [MIT License](https://opensource.org/license/mit/).

You are free to use, copy, modify, distribute, and sublicense this software, subject to the terms and conditions of the MIT License.



##

---

## Acknowledgements

Built for **AFFECIO HACKS ’26**, addressing:

**PS 1 — Beyond the Swipe: Smarter Compatibility and Meaningful Matches.**

---

\<div align="center">

**AffinityAI**

*Less swiping. More understanding.*

[Live Application](https://affinityai.apps.lemma.work/)

\</div>
