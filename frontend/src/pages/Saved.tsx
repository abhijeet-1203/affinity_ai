import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, EmptyState, Skeleton, Tag } from '../components/ui'
import { api } from '../lib/api'
import { useToast } from '../lib/session'

export default function Saved() {
  const toast = useToast()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try { setData(await api.collections()) } catch (err: any) { toast.show(err.message, 'error') } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (loading) return <div className="grid grid-2"><Skeleton height={150} /><Skeleton height={150} /></div>

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Your shortlist</span>
          <h2>Saved profiles</h2>
          <p className="muted small">Saved profiles stay out of the pass pile and can be revisited any time.</p>
        </div>
      </div>

      {data?.saved?.length ? (
        <div className="grid grid-2">
          {data.saved.map((person: any) => (
            <Card key={person.account_id} className="stack card-hover" style={{ gap: '0.6rem' }}>
              <div className="row">
                <div className="avatar">{person.initials}</div>
                <div className="stack" style={{ gap: '0.1rem', flex: 1 }}>
                  <span style={{ fontWeight: 600 }}>{person.display_name}{person.age ? `, ${person.age}` : ''}</span>
                  <span className="tiny muted">{person.city || 'Location hidden'}</span>
                </div>
                {person.is_demo ? <span className="badge badge-warn tiny">Demo</span> : null}
              </div>
              {person.interests?.length ? (
                <div className="row wrap" style={{ gap: '0.3rem' }}>
                  {person.interests.slice(0, 5).map((interest: string) => <Tag key={interest}>{interest}</Tag>)}
                </div>
              ) : null}
              <div className="row" style={{ gap: '0.4rem' }}>
                <Link to={`/app/people/${person.account_id}`} className="btn btn-soft btn-sm">View</Link>
                <Button size="sm" variant="ghost" onClick={async () => { await api.unsave(person.account_id); toast.show('Removed from saved.'); load() }}>Unsave</Button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState title="Nothing saved yet" action={<Link to="/app/discover" className="btn btn-soft btn-sm">Browse discovery</Link>}>
          Save a recommendation to look at it again later. Saving does not express interest.
        </EmptyState>
      )}

      <div className="grid grid-3">
        <Card className="card-flat"><span className="tiny muted">Outgoing likes</span><p style={{ fontSize: '1.4rem', fontWeight: 650 }}>{data?.counts?.liked ?? 0}</p></Card>
        <Card className="card-flat"><span className="tiny muted">Passes</span><p style={{ fontSize: '1.4rem', fontWeight: 650 }}>{data?.counts?.passed ?? 0}</p></Card>
        <Card className="card-flat"><span className="tiny muted">Blocked</span><p style={{ fontSize: '1.4rem', fontWeight: 650 }}>{data?.counts?.blocked ?? 0}</p></Card>
      </div>
      {toast.node}
    </div>
  )
}
