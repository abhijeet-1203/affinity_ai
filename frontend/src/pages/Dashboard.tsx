import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Button, Card, EmptyState, Skeleton, Stat } from '../components/ui'
import { ProfileCard } from '../components/ProfileCard'
import { api } from '../lib/api'
import { useSession, useToast } from '../lib/session'
import type { Card as CardType } from '../lib/types'

export default function Dashboard() {
  const { bundle, refresh } = useSession()
  const toast = useToast()
  const [feed, setFeed] = useState<any>(null)
  const [matches, setMatches] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const [recommendations, matchList] = await Promise.all([
        api.recommendations({ limit: 4, session_id: 'dashboard' }),
        api.matches(),
      ])
      setFeed(recommendations); setMatches(matchList)
    } catch (err: any) { setError(err.message) } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  if (!bundle) return null
  const completion = bundle.completion

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Your workspace</span>
          <h2>Hello, {bundle.profile.display_name.split(' ')[0]}</h2>
          <p className="muted small">Suggestions are ranked from your stored profile, weights and feedback.</p>
        </div>
        <div className="row">
          <Link to="/app/discover" className="btn btn-primary btn-sm">Discover <ArrowRight size={14} /></Link>
          <Link to="/app/settings" className="btn btn-ghost btn-sm">Edit profile</Link>
        </div>
      </div>

      {bundle.account.is_demo ? (
        <div className="demo-banner">
          <strong>Demo account.</strong> This member is fictional and flagged <code>is_demo</code> in the database.
          Recommendations, scores and matches are real calculations over the seeded profiles.
        </div>
      ) : null}

      {!bundle.profile.onboarding_completed ? (
        <Card className="stack" style={{ gap: '0.6rem' }}>
          <div className="row-between">
            <h3>Finish onboarding to unlock discovery</h3>
            <Link to="/join" className="btn btn-primary btn-sm">Resume</Link>
          </div>
          <p className="small muted">Discovery needs your birth date and at least one interest before it can score anything honestly.</p>
        </Card>
      ) : null}

      <div className="grid grid-4">
        <Stat label="Profile complete" value={`${completion.percent}%`} hint={`${completion.checks.filter((c) => c.done).length}/${completion.checks.length} checks`} />
        <Stat label="Eligible now" value={feed?.meta?.total_eligible ?? '—'} hint="So far this session" />
        <Stat label="Mutual matches" value={matches?.counts?.active ?? '—'} hint="Both said yes" />
        <Stat label="Saved" value={bundle.counts?.saved ?? '—'} hint="For later" />
      </div>

      <div className="grid" style={{ gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr)', alignItems: 'start', gap: '1.25rem' }}>
        <div className="stack">
          <div className="row-between">
            <h3>Suggested connections</h3>
            <Link to="/app/discover" className="small" style={{ color: 'var(--violet)' }}>See all</Link>
          </div>
          {loading ? <div className="grid grid-2" style={{ gap: '1rem' }}><Skeleton height={240} /><Skeleton height={240} /></div> : null}
          {error ? <EmptyState title="Could not load suggestions">{error}<div style={{ marginTop: '1rem' }}><Button size="sm" onClick={load}>Try again</Button></div></EmptyState> : null}
          {!loading && !error && feed?.recommendations?.length ? (
            <div className="grid grid-2" style={{ gap: '1rem' }}>
              {feed.recommendations.slice(0, 4).map((card: CardType) => (
                <ProfileCard key={card.account_id} card={card} onChange={load} onToast={toast.show} />
              ))}
            </div>
          ) : null}
          {!loading && !error && !feed?.recommendations?.length ? (
            <EmptyState title="No recommendations available yet" action={<Link to="/app/discover" className="btn btn-soft btn-sm">Open discovery</Link>}>
              {feed?.empty_reason ?? 'Complete more of your profile so the engine has something to compare.'}
            </EmptyState>
          ) : null}
        </div>

        <div className="stack">
          <Card className="stack" style={{ gap: '0.7rem' }}>
            <div className="row-between"><h3>Recent matches</h3><Link to="/app/matches" className="small" style={{ color: 'var(--violet)' }}>All</Link></div>
            {matches?.matches?.length ? matches.matches.slice(0, 3).map((match: any) => (
              <Link key={match.match_id} to="/app/matches" className="row" style={{ gap: '0.6rem' }}>
                <div className="avatar">{match.profile.initials}</div>
                <div className="stack" style={{ gap: '0.1rem' }}>
                  <span className="small" style={{ fontWeight: 550 }}>{match.profile.display_name}</span>
                  <span className="tiny muted">{match.profile.shared_interests?.length ?? 0} shared interests</span>
                </div>
              </Link>
            )) : <p className="small muted">No mutual matches yet. Both people have to express interest independently.</p>}
          </Card>

          <Card className="stack" style={{ gap: '0.6rem' }}>
            <div className="row-between"><h3>Your weights</h3><Link to="/app/settings" className="small" style={{ color: 'var(--violet)' }}>Adjust</Link></div>
            {Object.entries(bundle.preferences.weights).map(([key, value]) => (
              <div key={key} className="stack" style={{ gap: '0.2rem' }}>
                <div className="row-between small"><span style={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}</span><span style={{ fontWeight: 600 }}>{Math.round(Number(value) * 100)}%</span></div>
                <div className="bar"><i style={{ width: `${Number(value) * 100}%` }} /></div>
              </div>
            ))}
            <p className="tiny muted">Illustrative defaults, not empirically validated. Change them and the ranking changes with them.</p>
          </Card>

          <Card className="card-plum stack" style={{ gap: '0.5rem' }}>
            <Sparkles size={18} />
            <h3 style={{ color: '#fff' }}>Every score shows its working</h3>
            <p className="small">Open any profile to see dimension scores, the arithmetic, missing data and conversation starters.</p>
            <Link to="/app/method" className="btn btn-soft btn-sm" style={{ alignSelf: 'flex-start' }}>How the engine works</Link>
          </Card>
        </div>
      </div>
      {toast.node}
    </div>
  )
}
