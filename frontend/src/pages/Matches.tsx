import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, EmptyState, Skeleton, Tag } from '../components/ui'
import { api } from '../lib/api'
import { useToast } from '../lib/session'

export default function Matches() {
  const toast = useToast()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try { setData(await api.matches()) } catch (err: any) { setError(err.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (loading) return <div className="grid grid-2"><Skeleton height={180} /><Skeleton height={180} /></div>
  if (error) return <EmptyState title="Matches could not load" action={<Button size="sm" onClick={load}>Try again</Button>}>{error}</EmptyState>

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Mutual matches</span>
          <h2>Where you both said yes</h2>
          <p className="muted small">{data?.note}</p>
        </div>
      </div>

      {data?.matches?.length ? (
        <div className="grid grid-2">
          {data.matches.map((match: any) => (
            <Card key={match.match_id} className="stack card-hover" style={{ gap: '0.7rem' }}>
              <div className="row" style={{ alignItems: 'flex-start' }}>
                <div className="avatar lg">{match.profile.initials}</div>
                <div className="stack" style={{ gap: '0.2rem', flex: 1 }}>
                  <span style={{ fontWeight: 600 }}>{match.profile.display_name}{match.profile.age ? `, ${match.profile.age}` : ''}</span>
                  <span className="tiny muted">{match.profile.city || 'Location hidden'} · matched {new Date(match.created_at).toLocaleDateString()}</span>
                  {match.profile.is_demo ? <span className="badge badge-warn tiny">Demo profile</span> : null}
                </div>
              </div>
              {match.profile.shared_interests?.length ? (
                <div className="row wrap" style={{ gap: '0.3rem' }}>
                  {match.profile.shared_interests.slice(0, 4).map((interest: string) => <Tag key={interest} shared>{interest}</Tag>)}
                </div>
              ) : null}
              <div className="row wrap" style={{ gap: '0.4rem' }}>
                <Link to={`/app/people/${match.profile.account_id}`} className="btn btn-soft btn-sm">View compatibility</Link>
                <Button size="sm" variant="ghost" onClick={async () => {
                  try { const result: any = await api.withdrawMatch(match.match_id); toast.show(result.policy); await load() }
                  catch (err: any) { toast.show(err.message, 'error') }
                }}>Withdraw</Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState title="No mutual matches yet" action={<Link to="/app/discover" className="btn btn-soft btn-sm">Go to discovery</Link>}>
          A match is created only when two members independently express interest. A high compatibility
          score on its own never creates one.
        </EmptyState>
      )}

      {data?.ended?.length ? (
        <div className="stack">
          <h3>Ended</h3>
          <div className="grid grid-3">
            {data.ended.map((match: any) => (
              <Card key={match.match_id} className="card-flat stack" style={{ gap: '0.3rem' }}>
                <span className="small" style={{ fontWeight: 550 }}>{match.profile.display_name}</span>
                <span className="tiny muted">{match.status}</span>
              </Card>
            ))}
          </div>
        </div>
      ) : null}
      {toast.node}
    </div>
  )
}
