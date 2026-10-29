import { Link } from 'react-router-dom'
import { ArrowRight, Camera, Compass, HeartHandshake, Lock, MessageCircle, Sparkles } from 'lucide-react'
import { Badge, Button, Card, DimensionBar, ScoreRing, Wordmark } from '../components/ui'
import { useSession } from '../lib/session'

const NAV = [
  ['/discover', 'Discover'], ['/how-it-works', 'How It Works'],
  ['/approach', 'Our Approach to Compatibility'], ['/safety', 'Safety'],
]

export default function Landing() {
  const { signedIn } = useSession()
  return (
    <div>
      <header className="public-nav">
        <div className="container inner">
          <Wordmark />
          <nav className="nav-links">
            {NAV.map(([to, label]) => <Link key={to} to={to}>{label}</Link>)}
          </nav>
          <div className="row">
            <Link to="/signin" className="btn btn-ghost btn-sm">Sign In</Link>
            <Link to="/register" className="btn btn-primary btn-sm">Get Started</Link>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="container hero-grid">
          <div className="stack-lg">
            <div className="stack" style={{ gap: '1rem' }}>
              <span className="eyebrow">Less swiping. More understanding.</span>
              <h1>Meet Beyond the Surface.</h1>
              <p className="lede">
                Discover meaningful connections through shared interests, aligned preferences, and
                compatibility insights designed to help you understand people better.
              </p>
            </div>
            <div className="row wrap">
              <Link to={signedIn ? '/app/discover' : '/register'} className="btn btn-primary">
                Discover Your Compatibility <ArrowRight size={16} />
              </Link>
              <Link to="/how-it-works" className="btn btn-ghost">See How It Works</Link>
            </div>
            <div className="row wrap" style={{ gap: '0.5rem' }}>
              <Badge tone="success" dot>Scores computed from stored profiles</Badge>
              <Badge tone="outline">No LLM required for matching</Badge>
              <Badge tone="outline">18+ only</Badge>
            </div>
          </div>

          <div className="stack" style={{ gap: '1rem' }}>
            <Card className="card-hover">
              <div className="row" style={{ alignItems: 'flex-start' }}>
                <div className="avatar lg">IR</div>
                <div className="stack" style={{ gap: '0.35rem', flex: 1 }}>
                  <div className="row-between">
                    <span style={{ fontWeight: 600 }}>Ira, 27</span>
                    <span className="badge">Demo profile</span>
                  </div>
                  <span className="small muted">Illustrator. Trekking, capturing landscapes, cooking something new.</span>
                  <div className="row wrap" style={{ gap: '0.3rem' }}>
                    <span className="tag shared">photography</span>
                    <span className="tag shared">hiking</span>
                    <span className="tag shared">cooking</span>
                  </div>
                </div>
              </div>
              <hr className="divider" style={{ margin: '1rem 0' }} />
              <div className="row-between">
                <div className="stack" style={{ gap: '0.1rem' }}>
                  <span className="tiny muted">Preference alignment estimate</span>
                  <span style={{ fontSize: '1.9rem', fontWeight: 650, color: 'var(--plum)' }}>62%</span>
                </div>
                <ScoreRing value={62} />
              </div>
              <p className="small muted" style={{ marginTop: '0.75rem' }}>
                “You both listed photography, hiking and cooking. Your written descriptions also
                overlap in meaning, and your communication answers were close.”
              </p>
            </Card>
            <Card className="card-flat">
              <div className="stack" style={{ gap: '0.8rem' }}>
                <span className="tiny muted" style={{ fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                  Dimension breakdown — computed, not guessed
                </span>
                <DimensionBar label="Shared interests" percent={50} />
                <DimensionBar label="Interest & bio similarity" percent={37} />
                <DimensionBar label="Communication style" percent={80} />
                <DimensionBar label="Lifestyle rhythm" percent={45} />
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="section section-alt">
        <div className="container stack-lg">
          <div className="stack" style={{ gap: '0.5rem', maxWidth: '60ch' }}>
            <span className="eyebrow">How AffinityAI works</span>
            <h2>Five steps, and you can see every one of them</h2>
          </div>
          <div className="grid grid-3">
            {[
              ['Tell us what matters', 'Interests, a short bio, and seven optional questions about communication and lifestyle. Skip anything you like.'],
              ['We read it properly', 'Your interests are compared as sets, your words are compared by meaning, your answers by explicit alignment rules.'],
              ['You set the weights', 'Decide how much shared interests, written similarity, communication and lifestyle each count.'],
              ['We rank and explain', 'Eligible profiles are scored, ranked, and explained in plain language with the arithmetic shown.'],
              ['You decide', 'Like, pass, save or block. A match only exists when both people independently say yes.'],
            ].map(([title, body], index) => (
              <Card key={title} className="card-hover">
                <span className="badge" style={{ marginBottom: '0.6rem' }}>Step {index + 1}</span>
                <h3 style={{ marginBottom: '0.35rem' }}>{title}</h3>
                <p className="small muted">{body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container grid grid-2">
          <div className="stack" style={{ gap: '1rem' }}>
            <span className="eyebrow">Why compatibility matters</span>
            <h2>Photos say very little about a Tuesday evening</h2>
            <p className="lede">
              Most discovery surfaces reward fast judgements on appearance and a two-line bio. What
              actually shapes whether two people enjoy each other is narrower and more specific:
              how you like to spend a free day, how deeply you like to talk, whether you plan or
              drift, and what you would both happily do again next weekend.
            </p>
            <p className="lede">
              AffinityAI makes those things the input, then shows its working — including the parts
              where it simply does not know enough yet.
            </p>
          </div>
          <div className="grid" style={{ gap: '0.9rem' }}>
            {[
              [Compass, 'Shared interests, measured', 'Jaccard overlap over normalised tags, with the actual overlapping interests listed.'],
              [Sparkles, 'Meaning, not just words', 'Lexicon-expanded TF-IDF cosine finds “trekking” in “hiking” without inventing similarity.'],
              [MessageCircle, 'Communication alignment', 'Explicit answer-to-answer rules, including partial alignment — never “opposites fail”.'],
              [Lock, 'Privacy by default', 'Questionnaire answers stay private. Only aggregated alignment is shared.'],
            ].map(([Icon, title, body]: any) => (
              <Card key={title} className="card-flat">
                <div className="row" style={{ alignItems: 'flex-start' }}>
                  <span className="avatar"><Icon size={18} /></span>
                  <div>
                    <h3 style={{ fontSize: '1rem', marginBottom: '0.2rem' }}>{title}</h3>
                    <p className="small muted">{body}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container stack-lg">
          <div className="stack" style={{ gap: '0.5rem', maxWidth: '62ch' }}>
            <span className="eyebrow">How the matching engine works</span>
            <h2>Deterministic, inspectable, and honest about missing data</h2>
            <p className="lede">
              Four dimensions are scored between 0 and 1. Your weights are normalised, then applied
              only across dimensions where both profiles have real information — with the remaining
              weights renormalised. Missing answers are never counted as disagreement.
            </p>
          </div>
          <div className="grid grid-4">
            {[
              ['Shared interests', 'J(A,B) = |A∩B| / |A∪B|', '35% default'],
              ['Semantic similarity', 'cosine(TF-IDF(A), TF-IDF(B)) with concept expansion', '25% default'],
              ['Communication', 'mean of explicit answer similarity (1.0 / 0.8 / 0.5 / 0.3)', '20% default'],
              ['Lifestyle', 'ordinal distance + categorical alignment', '20% default'],
            ].map(([title, formula, weight]) => (
              <Card key={title} className="card-flat">
                <h3 style={{ fontSize: '0.98rem', marginBottom: '0.35rem' }}>{title}</h3>
                <code className="tiny muted" style={{ display: 'block', marginBottom: '0.5rem' }}>{formula}</code>
                <Badge tone="outline">{weight}</Badge>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container grid grid-2">
          <div className="stack" style={{ gap: '0.9rem' }}>
            <span className="eyebrow">Example explanations</span>
            <h2>What a recommendation actually says</h2>
            <Card className="card-flat">
              <p className="small">
                “You and Ira both listed photography, hiking and cooking. Your written descriptions
                also overlap in meaning (37%), which is measured from the text you both wrote, not
                from shared tags. The strongest alignment is in communication style. On ‘Which
                conversations do you get the most out of?’ your answers were close. Lifestyle rhythm
                differs more than the rest — a useful thing to talk about early.”
              </p>
            </Card>
            <Card className="card-flat">
              <p className="small">
                “You and Dev share technology. There is not enough information to compare lifestyle
                rhythm, so it is excluded rather than scored as zero. Confidence: moderate —
                2 of 4 dimensions had data on both sides.”
              </p>
            </Card>
          </div>
          <div className="stack" style={{ gap: '0.9rem' }}>
            <span className="eyebrow">Conversation starters</span>
            <h2>Start with something meaningful</h2>
            <p className="lede">
              Starters are generated from shared interests using fixed templates. Nothing is
              invented about the other person, and you edit anything before you send it.
            </p>
            <Card className="card-flat">
              <div className="stack" style={{ gap: '0.6rem' }}>
                <div className="row"><Camera size={16} /><span className="small">Shared interest: photography</span></div>
                <p className="small">“What kind of places do you most enjoy photographing?”</p>
                <hr className="divider" />
                <div className="row"><HeartHandshake size={16} /><span className="small">Shared interest: cooking</span></div>
                <p className="small">“If you could learn one dish from any country, which would it be?”</p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section id="safety" className="section section-alt">
        <div className="container grid grid-2">
          <div className="stack" style={{ gap: '0.9rem' }}>
            <span className="eyebrow">Privacy & safety principles</span>
            <h2>Your answers are not a public profile</h2>
            <ul className="stack small muted" style={{ paddingLeft: '1.1rem' }}>
              <li>Questionnaire answers are used for scoring and never displayed to other members.</li>
              <li>Location is a city you type, never GPS, and you can hide it entirely.</li>
              <li>Blocks take effect immediately and remove both directions from discovery.</li>
              <li>Reports are recorded with an honest status — nobody claims a review that did not happen.</li>
              <li>You can delete your account and its personal content from Settings at any time.</li>
            </ul>
          </div>
          <Card className="card-plum">
            <h3 style={{ marginBottom: '0.5rem' }}>What the score is not</h3>
            <p className="small">
              A preference alignment estimate is not a probability that a relationship will succeed.
              It is arithmetic over the fields you chose to fill in. We have not validated it against
              real relationship outcomes, and we do not claim to have.
            </p>
            <hr className="divider" style={{ margin: '1rem 0', background: 'rgba(255,255,255,0.2)' }} />
            <p className="small">
              Evaluated offline on a synthetic, hand-labelled set only. Those numbers are published in
              the app, with their limitations, exactly as measured.
            </p>
          </Card>
        </div>
      </section>

      <section className="section">
        <div className="container grid grid-2">
          <div className="stack" style={{ gap: '0.9rem' }}>
            <span className="eyebrow">Frequently asked</span>
            <h2>Straight answers</h2>
          </div>
          <div className="faq">
            {[
              ['Is this a dating app?', 'It is a compatibility-first discovery app. You choose whether you are looking for dating, friendship or an activity partner during onboarding, and that preference filters candidates.'],
              ['Does an AI model decide my matches?', 'No. Scores are deterministic arithmetic over your stored profile. An LLM is optional and never used for scoring in this build.'],
              ['What if I skip the questionnaire?', 'Then those dimensions are reported as having no data and are excluded — not scored as zero. Your confidence indicator will say so.'],
              ['How are demo accounts handled?', 'They are fictional, deterministic, flagged is_demo in the database, and labelled in the interface. No real personal data is used.'],
              ['Can I see why a profile was recommended?', 'Every recommendation has a compatibility page showing the dimension scores, the shared interests, the arithmetic and the missing data.'],
            ].map(([question, answer]) => (
              <details key={question}>
                <summary>{question}<span aria-hidden>+</span></summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container center stack" style={{ alignItems: 'center', gap: '1rem' }}>
          <h2>Understand people before you meet them</h2>
          <p className="lede" style={{ margin: '0 auto' }}>
            Create an account, answer what you feel like answering, and see your recommendations
            explained — including where the engine admits it does not know enough.
          </p>
          <div className="row">
            <Link to="/register" className="btn btn-primary">Get Started <ArrowRight size={16} /></Link>
            <Link to="/signin" className="btn btn-ghost">Sign In</Link>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container grid grid-3">
          <div className="stack" style={{ gap: '0.6rem' }}>
            <span style={{ color: '#fff', fontWeight: 650 }}>AffinityAI</span>
            <p className="small">Less swiping. More understanding.</p>
          </div>
          <div className="stack" style={{ gap: '0.4rem' }}>
            <span className="tiny" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Product</span>
            <Link to="/discover">Discover</Link>
            <Link to="/how-it-works">How It Works</Link>
            <Link to="/approach">Our Approach</Link>
            <Link to="/safety">Safety</Link>
          </div>
          <div className="stack" style={{ gap: '0.4rem' }}>
            <span className="tiny" style={{ letterSpacing: '0.08em', textTransform: 'uppercase' }}>Account</span>
            <Link to="/signin">Sign In</Link>
            <Link to="/register">Create account</Link>
            <Link to="/app/method">ML methodology</Link>
            <Link to="/app/evaluation">Engine evidence</Link>
          </div>
        </div>
        <div className="container small" style={{ marginTop: '2rem', opacity: 0.7 }}>
          AffinityAI is an 18+ demonstration product built for a hackathon. Compatibility scores are
          preference alignment estimates, not predictions of relationship success.
        </div>
      </footer>
    </div>
  )
}
