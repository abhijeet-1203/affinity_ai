import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { SlidersHorizontal } from 'lucide-react'
import { Button, Card, EmptyState, Skeleton } from '../components/ui'
import { ProfileCard } from '../components/ProfileCard'
import { api } from '../lib/api'
import { useSession, useToast } from '../lib/session'
import type { Card as CardType } from '../lib/types'

const PAGE = 6

export default function Discover() {
  const { bundle } = useSession()
  const toast = useToast()
  const [sessionId] = useState(() => `s-${Math.random().toString(36).slice(2, 10)}`)
  const [cards, setCards] = useState<CardType[]>([])
  const [meta, setMeta] = useState<any>(null)
  const [empty, setEmpty] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [more, setMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load(offset = 0) {
    offset === 0 ? setLoading(true) : setMore(true)
    setError(null)
    try {
      const data: any = await api.recommendations({ limit: PAGE, offset, session_id: sessionId })
      setCards((current) => offset === 0 ? data.recommendations : [...current, ...data.recommendations])
      setMeta(data.meta)
      setEmpty(data.empty_reason)
    } catch (err: any) { setError(err.message) } finally { setLoading(false); setMore(false) }
  }

  useEffect(() => { load(0) }, [])

  if (!bundle) return null

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Discovery</span>
          <h2>People who might actually fit</h2>
          <p className="muted small">
            Ranked by preference alignment estimate — never by popularity, age or profile completeness.
          </p>
        </div>
        <Link to="/app/settings" className="btn btn-ghost btn-sm"><SlidersHorizontal size={14} /> Weights & preferences</Link>
      </div>

      {meta ? (
        <Card className="card-flat stack" style={{ gap: '0.4rem' }}>
          <div className="row wrap" style={{ gap: '1rem' }}>
            <span className="small"><strong>{meta.total_eligible}</strong> eligible profiles scored</span>
            <span className="small muted">{meta.candidates_considered} considered</span>
            <span className="small muted">{meta.excluded?.length ?? 0} excluded with a reason</span>
            <span className="small muted">Diversity cap: max 2 profiles per top shared interest</span>
          </div>
          {meta.excluded?.length ? (
            <details>
              <summary className="small" style={{ cursor: 'pointer', color: 'var(--violet)' }}>Why some profiles were excluded</summary>
              <ul className="small muted" style={{ marginTop: '0.4rem', paddingLeft: '1.1rem' }}>
                {meta.excluded.slice(0, 8).map((row: any, index: number) => (
                  <li key={index}>{row.reason}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </Card>
      ) : null}

      {loading ? <div className="grid grid-2"><Skeleton height={260} /><Skeleton height={260} /><Skeleton height={260} /><Skeleton height={260} /></div> : null}
      {error ? <EmptyState title="Discovery could not load" action={<Button size="sm" onClick={() => load(0)}>Try again</Button>}>{error}</EmptyState> : null}

      {!loading && !error ? (
        cards.length ? (
          <div className="grid grid-2" style={{ gap: '1.1rem' }}>
            {cards.map((card) => <ProfileCard key={card.account_id} card={card} onChange={() => load(0)} onToast={toast.show} />)}
          </div>
        ) : (
          <EmptyState title="Nothing left to show right now" action={<Link to="/app/settings" className="btn btn-soft btn-sm">Adjust preferences</Link>}>
            {empty ?? 'Everyone eligible has been scored, acted on or filtered already.'}
          </EmptyState>
        )
      ) : null}

      {meta?.has_more ? (
        <div className="center">
          <Button variant="ghost" loading={more} onClick={() => load(cards.length)}>Load more</Button>
        </div>
      ) : null}
      {toast.node}
    </div>
  )
}
