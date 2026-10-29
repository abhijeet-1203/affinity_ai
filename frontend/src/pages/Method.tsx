import { Card, DimensionBar } from '../components/ui'

export default function Method() {
  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Methodology</span>
          <h2>How AffinityAI computes compatibility</h2>
          <p className="muted small">Deterministic arithmetic over stored profile data. No LLM is used for any score.</p>
        </div>
      </div>

      <Card className="stack">
        <h3>1. Feature extraction</h3>
        <p className="small muted">
          Each profile becomes a normalised representation: a set of interest tags (lowercased,
          whitespace-collapsed, de-duplicated), a text field (biography + interest labels), and a
          dictionary of structured answers keyed by question. Unanswered questions are simply absent —
          never coerced to a default.
        </p>
      </Card>

      <Card className="stack">
        <h3>2. Shared interests — Jaccard</h3>
        <code className="small">J(A, B) = |A ∩ B| / |A ∪ B|</code>
        <p className="small muted">
          If either member has no interests, the dimension is reported as unavailable — the engine
          does not divide by zero or silently score a zero.
        </p>
      </Card>

      <Card className="stack">
        <h3>3. Semantic similarity — lexicon-expanded TF-IDF cosine</h3>
        <p className="small muted">
          Profile text is tokenised, stopword-filtered and lightly stemmed. Tokens are also mapped to
          concept ids through an explicit lexicon (hiking / trekking / mountain trails → outdoor_hiking;
          capturing landscapes / photography → photography), so paraphrases overlap on meaning. IDF is
          computed over the profiles actually in play, then cosine similarity is taken between the two
          sparse vectors, clipped to [0, 1].
        </p>
        <p className="tiny muted">
          This is the documented fallback for sentence-transformer embeddings, which cannot run in this
          function runtime. No similarity is displayed unless it was actually computed.
        </p>
      </Card>

      <Card className="stack">
        <h3>4. Structured alignment</h3>
        <p className="small muted">
          Categorical answers use explicit pair maps (aligned / partially aligned / different / unknown),
          so “deep conversations” and “a mix of both” score 0.8 rather than 0. Ordinal answers use
          normalised distance: 1 − |a − b| / 4. Multi-select answers use Jaccard over selections. A
          dimension's score is the mean across questions both people answered.
        </p>
        <p className="tiny muted">Opposites are not penalised by construction; a difference is neutral-to-partial, and surfaced to you as a topic.</p>
      </Card>

      <Card className="stack">
        <h3>5. Personalised weights and missing data</h3>
        <code className="small">overall = Σ(wᵢ · sᵢ) / Σ(wᵢ) over dimensions with data</code>
        <p className="small muted">
          Your weights are normalised to sum to 1. A dimension with insufficient information is dropped
          from both the numerator and the denominator, and the remaining weights are renormalised. The
          coverage figure tells you how much of what you care about could actually be checked.
        </p>
        <div className="stack" style={{ gap: '0.5rem', marginTop: '0.4rem' }}>
          <DimensionBar label="High confidence" percent={100} note="≥ 85% of your weight had data on both sides" />
          <DimensionBar label="Moderate" percent={70} note="60–85%" />
          <DimensionBar label="Limited" percent={45} note="35–60%" />
          <DimensionBar label="Low" percent={20} note="below 35% — the number is barely supported" />
        </div>
      </Card>

      <Card className="stack">
        <h3>6. Eligibility and ranking</h3>
        <ul className="small muted" style={{ paddingLeft: '1.1rem' }}>
          <li>Excluded: yourself, undiscoverable profiles, incomplete onboarding, outside your age range, blocked in either direction, already liked or passed.</li>
          <li>Excluded: pairs with no comparable dimension at all — no score is invented.</li>
          <li>Ranked by scored total (alignment + bounded feedback nudge), then information coverage, then a stable hash tie-break — never age, popularity or profile length.</li>
          <li>Diversity cap: at most two consecutive results may share the same top interest.</li>
          <li>Pagination and per-session de-duplication are applied server-side.</li>
        </ul>
      </Card>

      <Card className="stack">
        <h3>7. Explanations and starters</h3>
        <p className="small muted">
          Explanations are deterministic templates filled with computed facts: shared interests,
          the semantic score, the strongest and weakest dimensions, matched questions, and named
          missing dimensions. Starters come from a fixed template catalogue keyed by shared interest.
          Nothing about either person is invented, and an LLM is never used to write evidence.
        </p>
      </Card>

      <Card className="card-plum stack">
        <h3 style={{ color: '#fff' }}>What this is not</h3>
        <p className="small">The score is a preference alignment estimate. It has not been validated against real relationship outcomes, it is not a probability of success, and it does not use protected characteristics or infer anything from photographs. We make no scientific claim beyond the arithmetic shown here.</p>
      </Card>
    </div>
  )
}
