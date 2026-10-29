import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Heart, MessageCircle, ShieldAlert, X } from 'lucide-react'
import { Badge, Button, Card, DimensionBar, EmptyState, ScoreRing, Skeleton, Tag } from '../components/ui'
import { api } from '../lib/api'
import { useToast } from '../lib/session'

export default function Compatibility() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  async function load() {
    setLoading(true); setError(null)
    try { setData(await api.compatibility(id!)) } catch (err: any) { setError(err.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [id])

  if (loading) return <div className="stack"><Skeleton height={140} /><Skeleton height={260} /><Skeleton height={200} /></div>
  if (error) return <EmptyState title="This profile is not available" action={<Link to="/app/discover" className="btn btn-soft btn-sm">Back to discovery</Link>}>{error}</EmptyState>
  if (!data) return null

  const { profile, compatibility, explanation, relation, dimension_meta: dimensionMeta } = data

  async function act(kind: string) {
    try {
      if (kind === 'like') { const r: any = await api.like(profile.account_id); toast.show(r.mutual ? `Mutual match with ${profile.display_name}.` : r.message) }
      if (kind === 'pass') { await api.pass(profile.account_id); toast.show('Dismissed.'); navigate('/app/discover') }
      if (kind === 'save') { await api.save(profile.account_id); toast.show('Saved.') }
      if (kind === 'block') { await api.block(profile.account_id); toast.show('Blocked.'); navigate('/app/discover') }
      await load()
    } catch (err: any) { toast.show(err.message, 'error') }
  }

  async function sendFeedback(type: string) {
    try { await api.feedback({ account_id: profile.account_id, feedback_type: type }); setFeedback(type); toast.show('Feedback recorded.') }
    catch (err: any) { toast.show(err.message, 'error') }
  }

  return (
    <div className="stack-lg">
      <button className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start' }} onClick={() => navigate(-1)}><ArrowLeft size={14} /> Back</button>

      <div className="grid" style={{ gridTemplateColumns: 'minmax(0, 1.5fr) minmax(0, 1fr)', alignItems: 'start', gap: '1.25rem' }}>
        <div className="stack-lg">
          <Card className="stack" style={{ gap: '0.8rem' }}>
            <div className="row" style={{ alignItems: 'flex-start' }}>
              <div className="avatar lg">{profile.initials}</div>
              <div className="stack" style={{ gap: '0.2rem', flex: 1 }}>
                <h2 style={{ fontSize: '1.5rem' }}>{profile.display_name}{profile.age ? `, ${profile.age}` : ''}</h2>
                <span className="small muted">{profile.city || 'Location hidden'} · looking for {String(profile.connection_type || 'any').replace('_', ' ')}</span>
                {profile.is_demo ? <Badge tone="warn">Demo profile</Badge> : null}
              </div>
              <div className="stack" style={{ alignItems: 'center', gap: '0.2rem' }}>
                <ScoreRing value={compatibility.overall} size="lg" />
                <span className="tiny muted">alignment</span>
              </div>
            </div>
            <p className="small">{profile.bio || 'No biography yet.'}</p>
            <div className="row wrap" style={{ gap: '0.3rem' }}>
              {profile.interests.map((interest: string) => (
                <Tag key={interest} shared={compatibility.shared_interests.includes(interest)}>{interest}</Tag>
              ))}
            </div>
            <div className="row wrap" style={{ gap: '0.4rem', marginTop: '0.25rem' }}>
              <Button size="sm" onClick={() => act('like')} disabled={relation.liked}><Heart size={14} /> {relation.liked ? 'Interest expressed' : 'Like'}</Button>
              <Button size="sm" variant="ghost" onClick={() => act('pass')}><X size={14} /> Pass</Button>
              <Button size="sm" variant="ghost" onClick={() => act('save')} disabled={relation.saved}>{relation.saved ? 'Saved' : 'Save'}</Button>
              <Button size="sm" variant="ghost" onClick={() => act('block')}><ShieldAlert size={14} /> Block</Button>
            </div>
            {relation.liked_you && !relation.matched ? <p className="tiny" style={{ color: 'var(--success)' }}>They have already expressed interest in you. Liking back creates a mutual match.</p> : null}
            {relation.matched ? <p className="tiny" style={{ color: 'var(--success)' }}>You are a mutual match — both of you said yes.</p> : null}
          </Card>

          <Card className="stack" style={{ gap: '0.9rem' }}>
            <div className="row-between">
              <h3>Dimension breakdown</h3>
              <span className="tiny muted">{compatibility.coverage_percent}% information coverage · {compatibility.confidence} confidence</span>
            </div>
            {compatibility.dimensions.map((dimension: any) => (
              <DimensionBar key={dimension.key} label={`${dimension.label} (${dimension.weight_percent}% weight)`}
                percent={dimension.percent} missing={!dimension.available}
                note={dimension.available ? (dimension.score >= 0.6 ? 'Strong alignment' : dimension.score >= 0.4 ? 'Partial alignment' : 'A genuine difference worth discussing') : dimension.reason} />
            ))}
            <hr className="divider" />
            <h3>What this means</h3>
            <p className="small">{explanation.summary}</p>
            <p className="tiny muted">{compatibility.label}: arithmetic over the fields you both filled in — not a probability that a relationship will succeed.</p>
          </Card>

          <Card className="stack" style={{ gap: '0.7rem' }}>
            <h3>Conversation opportunities</h3>
            {explanation.starters.length ? explanation.starters.map((starter: any) => (
              <div key={starter.interest} className="panel stack" style={{ gap: '0.3rem' }}>
                <div className="row"><MessageCircle size={15} /><span className="tiny muted">Shared interest: {starter.interest}</span></div>
                <p className="small">{starter.text}</p>
                <Button size="sm" variant="ghost" style={{ alignSelf: 'flex-start' }} onClick={() => { navigator.clipboard?.writeText(starter.text); toast.show('Copied. Edit it before you send it.') }}>Copy</Button>
              </div>
            )) : <p className="small muted">No shared interests, so no interest-specific starters. The engine never invents personal facts.</p>}
          </Card>

          <Card className="stack" style={{ gap: '0.6rem' }}>
            <h3>Potential differences</h3>
            {compatibility.differences.length ? compatibility.differences.map((difference: any) => (
              <div key={difference.key} className="panel">
                <span className="small" style={{ fontWeight: 550 }}>{difference.prompt}</span>
                <p className="small muted" style={{ marginTop: '0.2rem' }}>
                  You: {difference.you} · Them: {difference.them}. {difference.note} This is a topic, not a defect.
                </p>
              </div>
            )) : <p className="small muted">No material differences on the questions you both answered.</p>}
            {compatibility.missing.length ? (
              <div className="panel">
                <span className="small" style={{ fontWeight: 550 }}>Where information is missing</span>
                <ul className="small muted" style={{ marginTop: '0.2rem', paddingLeft: '1.1rem' }}>
                  {compatibility.missing.map((item: any) => <li key={item.key}>{item.label}: {item.reason}</li>)}
                </ul>
              </div>
            ) : null}
          </Card>
        </div>

        <div className="stack">
          <Card className="stack" style={{ gap: '0.6rem' }}>
            <h3>How this score works</h3>
            <code className="tiny muted" style={{ display: 'block' }}>{explanation.calculation.formula}</code>
            <table className="table">
              <thead><tr><th>Dimension</th><th>Weight</th><th>Score</th></tr></thead>
              <tbody>
                {explanation.calculation.components.map((row: any) => (
                  <tr key={row.dimension}><td>{row.dimension}</td><td>{(row.weight * 100).toFixed(0)}%</td><td>{Math.round(row.score * 100)}%</td></tr>
                ))}
              </tbody>
            </table>
            <p className="tiny muted">
              {explanation.calculation.numerator.toFixed(3)} ÷ {explanation.calculation.denominator.toFixed(3)} = {(explanation.calculation.overall / 100).toFixed(3)}
            </p>
            <p className="tiny muted">{explanation.calculation.missing_handling}</p>
            {explanation.calculation.feedback_adjustment ? (
              <p className="tiny" style={{ color: 'var(--violet)' }}>Personalisation adjustment applied: {explanation.calculation.feedback_adjustment > 0 ? '+' : ''}{explanation.calculation.feedback_adjustment} points (ranked score {explanation.calculation.ranked_score}).</p>
            ) : null}
            <Link to="/app/settings" className="btn btn-ghost btn-sm">Adjust matching weights</Link>
          </Card>

          <Card className="stack" style={{ gap: '0.5rem' }}>
            <h3>Was this a good recommendation?</h3>
            <p className="tiny muted">Feedback nudges future ranking by at most ±6 points, for profiles sharing interests with this one. It never overrides blocks or eligibility.</p>
            <div className="row wrap" style={{ gap: '0.35rem' }}>
              {[['matches_interests', 'Matches my interests'], ['not_relevant', 'Not relevant'], ['more_like_this', 'More like this'], ['does_not_align', 'Does not align']].map(([value, label]) => (
                <button key={value} className="chip" data-selected={feedback === value} onClick={() => sendFeedback(value)}>{label}</button>
              ))}
            </div>
          </Card>

          <Card className="card-flat">
            <h3 style={{ fontSize: '1rem', marginBottom: '0.3rem' }}>Privacy</h3>
            <p className="tiny muted">Only aggregated alignment is shared. Their individual questionnaire answers stay private — you see the effect, never the raw response.</p>
          </Card>
        </div>
      </div>
      {toast.node}
    </div>
  )
}
