import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, Flag, Heart, X } from 'lucide-react'
import { Badge, Button, Card, Modal, ScoreRing, Tag } from './ui'
import { api } from '../lib/api'
import type { Card as CardType } from '../lib/types'

export function ProfileCard({ card, onChange, onToast }: {
  card: CardType
  onChange: () => void
  onToast: (message: string, tone?: 'ok' | 'error') => void
}) {
  const [busy, setBusy] = useState<string | null>(null)
  const [reporting, setReporting] = useState(false)
  const [reason, setReason] = useState('harassment')
  const [details, setDetails] = useState('')

  async function act(kind: 'like' | 'pass' | 'save' | 'block') {
    setBusy(kind)
    try {
      if (kind === 'like') {
        const result: any = await api.like(card.account_id)
        onToast(result.mutual ? `Mutual match with ${card.display_name}.` : result.message)
      } else if (kind === 'pass') {
        await api.pass(card.account_id); onToast('Dismissed.')
      } else if (kind === 'save') {
        await api.save(card.account_id); onToast('Saved for later.')
      } else {
        await api.block(card.account_id); onToast(`${card.display_name} blocked and removed from discovery.`)
      }
      onChange()
    } catch (error: any) {
      onToast(error.message ?? 'That did not work.', 'error')
    } finally { setBusy(null) }
  }

  return (
    <Card className="card-hover stack" style={{ gap: '0.8rem' }}>
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="avatar lg">{card.initials}</div>
        <div className="stack" style={{ gap: '0.2rem', flex: 1, minWidth: 0 }}>
          <div className="row-between" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: '0.1rem' }}>
              <span style={{ fontWeight: 600, fontSize: '1.02rem' }}>
                {card.display_name}{card.age ? `, ${card.age}` : ''}
              </span>
              <span className="tiny muted">{card.city || 'Location hidden'}{card.connection_type ? ` · ${String(card.connection_type).replace('_', ' ')}` : ''}</span>
            </div>
            <ScoreRing value={card.overall} />
          </div>
          {card.is_demo ? <Badge tone="warn">Demo profile</Badge> : null}
        </div>
      </div>

      <p className="small" style={{ color: 'var(--muted)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {card.bio || 'No biography yet.'}
      </p>

      {card.shared_interests.length ? (
        <div className="row wrap" style={{ gap: '0.3rem' }}>
          {card.shared_interests.slice(0, 4).map((interest) => <Tag key={interest} shared>{interest}</Tag>)}
          {card.shared_interests.length > 4 ? <Tag>+{card.shared_interests.length - 4}</Tag> : null}
        </div>
      ) : (
        <span className="tiny muted">No overlapping interest tags — scored on written profile and answers.</span>
      )}

      <p className="tiny muted">
        <strong style={{ color: 'var(--plum)' }}>{card.top_dimension ? `${card.top_dimension.label} ${card.top_dimension.percent}%` : 'Limited data'}</strong>
        {' · '}information coverage {card.coverage_percent}% ({card.confidence} confidence)
      </p>

      <div className="row wrap" style={{ gap: '0.4rem' }}>
        <Link to={`/app/people/${card.account_id}`} className="btn btn-soft btn-sm" style={{ flex: 1 }}>View profile</Link>
        <Button size="sm" onClick={() => act('like')} loading={busy === 'like'}><Heart size={14} /> Like</Button>
        <Button size="sm" variant="ghost" onClick={() => act('pass')} loading={busy === 'pass'}><X size={14} /> Pass</Button>
        <Button size="sm" variant="ghost" onClick={() => act('save')} loading={busy === 'save'} aria-label="Save"><Bookmark size={14} /></Button>
        <Button size="sm" variant="ghost" onClick={() => setReporting(true)} aria-label="Report"><Flag size={14} /></Button>
      </div>

      {reporting ? (
        <Modal title={`Report ${card.display_name}`} onClose={() => setReporting(false)}>
          <div className="stack">
            <p className="small muted">Your identity is never shown to the person you report. Reports are stored with an honest status.</p>
            <label className="field">
              <span className="label">Reason</span>
              <select className="select" value={reason} onChange={(e) => setReason(e.target.value)}>
                <option value="harassment">Harassment</option>
                <option value="spam">Spam</option>
                <option value="fake_profile">Fake profile</option>
                <option value="inappropriate_content">Inappropriate content</option>
                <option value="safety_concern">Safety concern</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="field">
              <span className="label">Details (optional)</span>
              <textarea className="textarea" value={details} onChange={(e) => setDetails(e.target.value)} maxLength={1000} />
            </label>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <Button variant="ghost" size="sm" onClick={() => setReporting(false)}>Cancel</Button>
              <Button size="sm" onClick={async () => {
                try {
                  const result: any = await api.report({ account_id: card.account_id, reason, details })
                  onToast(result.message); setReporting(false)
                } catch (error: any) { onToast(error.message, 'error') }
              }}>Send report</Button>
            </div>
          </div>
        </Modal>
      ) : null}
    </Card>
  )
}
