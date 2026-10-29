import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, EmptyState, Skeleton, Stat } from '../components/ui'
import { api } from '../lib/api'

export default function Insights() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try { setData(await api.insights()) } catch (err: any) { setError(err.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (loading) return <div className="grid grid-4"><Skeleton height={90} /><Skeleton height={90} /><Skeleton height={90} /><Skeleton height={90} /></div>
  if (error) return <EmptyState title="Insights could not load" action={<Button size="sm" onClick={load}>Try again</Button>}>{error}</EmptyState>

  const counts = data?.counts ?? {}
  const maxShared = Math.max(1, ...(data?.top_shared_interests ?? []).map((row: any) => row.count))

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Your activity</span>
          <h2>Insights</h2>
          <p className="muted small">{data?.note}</p>
        </div>
      </div>

      <div className="grid grid-4">
        <Stat label="Recommendations viewed" value={counts.recommendations_viewed ?? 0} hint={`${counts.distinct_profiles_seen ?? 0} distinct profiles`} />
        <Stat label="Outgoing likes" value={counts.outgoing_likes ?? 0} />
        <Stat label="Mutual matches" value={counts.mutual_matches ?? 0} hint={`${counts.ended_matches ?? 0} ended`} />
        <Stat label="Saved" value={counts.saved_profiles ?? 0} />
      </div>

      {!data?.has_activity ? (
        <EmptyState title="No activity recorded yet" action={<Link to="/app/discover" className="btn btn-soft btn-sm">Start discovering</Link>}>
          Every metric here is counted from rows you create. Nothing is seeded to look busier than it is.
        </EmptyState>
      ) : null}

      <div className="grid grid-2" style={{ alignItems: 'start' }}>
        <Card className="stack" style={{ gap: '0.7rem' }}>
          <h3>Most shared interests in your recommendations</h3>
          {data?.top_shared_interests?.length ? data.top_shared_interests.map((row: any) => (
            <div key={row.interest} className="stack" style={{ gap: '0.2rem' }}>
              <div className="row-between small"><span>{row.interest}</span><span style={{ fontWeight: 600 }}>{row.count}</span></div>
              <div className="bar"><i style={{ width: `${(row.count / maxShared) * 100}%` }} /></div>
            </div>
          )) : <p className="small muted">No recommendations served yet.</p>}
        </Card>

        <div className="stack">
          <Card className="stack" style={{ gap: '0.6rem' }}>
            <h3>Recommendation quality signals</h3>
            <div className="row-between small"><span className="muted">Average alignment served</span><span style={{ fontWeight: 600 }}>{data?.average_alignment ?? '—'}{data?.average_alignment ? '%' : ''}</span></div>
            <div className="row-between small"><span className="muted">Average information coverage</span><span style={{ fontWeight: 600 }}>{data?.average_coverage ?? '—'}{data?.average_coverage ? '%' : ''}</span></div>
            <hr className="divider" />
            <h3 style={{ fontSize: '1rem' }}>Feedback distribution</h3>
            {data?.feedback_distribution?.length ? data.feedback_distribution.map((row: any) => (
              <div key={row.type} className="row-between small"><span className="muted">{row.type.replace(/_/g, ' ')}</span><span style={{ fontWeight: 600 }}>{row.count}</span></div>
            )) : <p className="small muted">No feedback given yet.</p>}
            <p className="tiny muted">Feedback changes ranking by a bounded, documented amount — never blocks or eligibility.</p>
          </Card>
          <Card className="card-flat stack" style={{ gap: '0.4rem' }}>
            <h3 style={{ fontSize: '1rem' }}>Not shown here</h3>
            <p className="tiny muted">Engagement rates, success rates and other members' activity are deliberately absent — we only show what your own rows can prove.</p>
          </Card>
        </div>
      </div>
    </div>
  )
}
