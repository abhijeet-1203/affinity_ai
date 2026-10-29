import { useEffect, useState } from 'react'
import { Button, Card, Field, Modal, Tag } from '../components/ui'
import { api } from '../lib/api'
import { useSession, useToast } from '../lib/session'
import type { Question } from '../lib/types'

const TABS = ['profile', 'interests', 'questions', 'weights', 'privacy'] as const

export default function Settings() {
  const { bundle, refresh, setBundle, signOut } = useSession()
  const toast = useToast()
  const [tab, setTab] = useState<(typeof TABS)[number]>('profile')
  const [catalog, setCatalog] = useState<any>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [password, setPassword] = useState('')
  const [form, setForm] = useState<any>(null)
  const [interests, setInterests] = useState<string[]>([])
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [weights, setWeights] = useState({ shared_interests: 35, semantic: 25, communication: 20, lifestyle: 20 })
  const [prefs, setPrefs] = useState({ min_age: 21, max_age: 45, connection_type: 'dating' })
  const [blocked, setBlocked] = useState<any[]>([])

  useEffect(() => {
    (async () => {
      try {
        const [catalogue, onboarding, collections] = await Promise.all([api.catalog(), api.onboarding(), api.collections()])
        setCatalog(catalogue)
        setQuestions(onboarding.questions)
        setBlocked(collections.blocked ?? [])
      } catch (error: any) { toast.show(error.message, 'error') }
    })()
  }, [])

  useEffect(() => {
    if (!bundle) return
    setForm({
      display_name: bundle.profile.display_name,
      birth_date: bundle.profile.birth_date ?? '',
      city: bundle.profile.city,
      bio: bundle.profile.bio,
      connection_type: bundle.profile.connection_type,
      discoverable: bundle.profile.discoverable,
      show_age: bundle.profile.show_age,
      show_city: bundle.profile.show_city,
    })
    setInterests(bundle.interests)
    setAnswers(bundle.answers)
    setWeights({
      shared_interests: Math.round(Number(bundle.preferences.weights.shared_interests) * 100),
      semantic: Math.round(Number(bundle.preferences.weights.semantic) * 100),
      communication: Math.round(Number(bundle.preferences.weights.communication) * 100),
      lifestyle: Math.round(Number(bundle.preferences.weights.lifestyle) * 100),
    })
    setPrefs({ min_age: bundle.preferences.min_age, max_age: bundle.preferences.max_age, connection_type: bundle.preferences.connection_type })
  }, [bundle])

  if (!bundle || !form) return null

  async function saveProfile() {
    setBusy(true)
    try { const next: any = await api.updateProfile(form); setBundle(next); toast.show('Profile saved.') }
    catch (error: any) { toast.show(error.message, 'error') } finally { setBusy(false) }
  }
  async function saveInterests() {
    setBusy(true)
    try { await api.saveInterests(interests); await refresh(); toast.show('Interests saved.') }
    catch (error: any) { toast.show(error.message, 'error') } finally { setBusy(false) }
  }
  async function saveAnswers() {
    setBusy(true)
    try { await api.saveAnswers(answers); await refresh(); toast.show('Answers saved.') }
    catch (error: any) { toast.show(error.message, 'error') } finally { setBusy(false) }
  }
  async function saveWeights() {
    setBusy(true)
    try {
      await api.savePreferences({ ...prefs, weights })
      await refresh(); toast.show('Weights normalised and saved. Recommendations will re-rank.')
    } catch (error: any) { toast.show(error.message, 'error') } finally { setBusy(false) }
  }

  const total = Object.values(weights).reduce((a, b) => a + Number(b), 0) || 1

  return (
    <div className="stack-lg">
      <div className="page-head">
        <div className="stack" style={{ gap: '0.3rem' }}>
          <span className="eyebrow">Settings</span>
          <h2>Your profile and preferences</h2>
          <p className="muted small">Every change is validated on the server and persists across sessions.</p>
        </div>
      </div>

      <div className="row wrap" style={{ gap: '0.4rem' }}>
        {TABS.map((item) => (
          <button key={item} className="chip" data-selected={tab === item} onClick={() => setTab(item)} style={{ textTransform: 'capitalize' }}>{item}</button>
        ))}
      </div>

      {tab === 'profile' ? (
        <Card className="stack">
          <div className="grid grid-2" style={{ gap: '0.75rem' }}>
            <Field label="Display name"><input className="input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} /></Field>
            <Field label="Birth date" hint="18+ only; age is calculated, never stored as a number."><input className="input" type="date" value={form.birth_date ?? ''} onChange={(e) => setForm({ ...form, birth_date: e.target.value })} /></Field>
            <Field label="City"><input className="input" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} /></Field>
            <Field label="Looking for">
              <select className="select" value={form.connection_type} onChange={(e) => setForm({ ...form, connection_type: e.target.value })}>
                <option value="dating">Dating</option><option value="friendship">Friendship</option>
                <option value="activity_partner">Activity partner</option><option value="any">Open to any</option>
              </select>
            </Field>
          </div>
          <Field label="Biography" hint="Read by the semantic similarity dimension.">
            <textarea className="textarea" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} maxLength={1200} />
          </Field>
          <Button onClick={saveProfile} loading={busy} style={{ alignSelf: 'flex-start' }}>Save profile</Button>
        </Card>
      ) : null}

      {tab === 'interests' ? (
        <Card className="stack">
          <div className="row-between"><h3>Interests</h3><span className="tiny muted">{interests.length} / 20</span></div>
          {(catalog?.categories ?? []).map((category: any) => (
            <div key={category.name} className="stack" style={{ gap: '0.35rem' }}>
              <span className="tiny muted" style={{ textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600 }}>{category.name}</span>
              <div className="row wrap" style={{ gap: '0.35rem' }}>
                {category.interests.map((interest: any) => (
                  <button key={interest.name} className="chip" data-selected={interests.includes(interest.name)}
                    onClick={() => setInterests(interests.includes(interest.name) ? interests.filter((i) => i !== interest.name) : interests.length < 20 ? [...interests, interest.name] : interests)}>
                    {interest.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <Button onClick={saveInterests} loading={busy} style={{ alignSelf: 'flex-start' }}>Save interests</Button>
        </Card>
      ) : null}

      {tab === 'questions' ? (
        <Card className="stack-lg">
          <p className="small muted">Answers stay private. Changing them changes your compatibility scores immediately.</p>
          {questions.map((question) => (
            <div key={question.key} className="stack" style={{ gap: '0.4rem' }}>
              <span className="label">{question.prompt}</span>
              {question.kind === 'ordinal' ? (
                <div className="stack" style={{ gap: '0.2rem' }}>
                  <input className="range" type="range" min={1} max={5} value={Number(answers[question.key] ?? 3)} onChange={(e) => setAnswers({ ...answers, [question.key]: Number(e.target.value) })} />
                  <span className="tiny muted">{question.options.find((o) => Number(o.value) === Number(answers[question.key] ?? 3))?.label}</span>
                </div>
              ) : (
                <div className="row wrap" style={{ gap: '0.35rem' }}>
                  {question.options.map((option) => {
                    const picked = question.kind === 'multiselect' ? (answers[question.key] ?? []) : answers[question.key]
                    const selected = question.kind === 'multiselect' ? (picked as string[]).includes(option.value) : picked === option.value
                    return (
                      <button key={option.value} className="chip" data-selected={selected}
                        onClick={() => {
                          if (question.kind === 'multiselect') {
                            const list: string[] = answers[question.key] ?? []
                            setAnswers({ ...answers, [question.key]: selected ? list.filter((v) => v !== option.value) : [...list, option.value] })
                          } else {
                            setAnswers({ ...answers, [question.key]: selected ? undefined : option.value })
                          }
                        }}>{option.label}</button>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
          <Button onClick={saveAnswers} loading={busy} style={{ alignSelf: 'flex-start' }}>Save answers</Button>
        </Card>
      ) : null}

      {tab === 'weights' ? (
        <Card className="stack-lg">
          <div className="grid grid-2" style={{ gap: '0.75rem' }}>
            <Field label="Minimum age"><input className="input" type="number" min={18} value={prefs.min_age} onChange={(e) => setPrefs({ ...prefs, min_age: Number(e.target.value) })} /></Field>
            <Field label="Maximum age"><input className="input" type="number" min={18} value={prefs.max_age} onChange={(e) => setPrefs({ ...prefs, max_age: Number(e.target.value) })} /></Field>
          </div>
          <Field label="Looking for">
            <select className="select" value={prefs.connection_type} onChange={(e) => setPrefs({ ...prefs, connection_type: e.target.value })}>
              <option value="dating">Dating</option><option value="friendship">Friendship</option>
              <option value="activity_partner">Activity partner</option><option value="any">Open to any</option>
            </select>
          </Field>
          <div className="stack" style={{ gap: '0.7rem' }}>
            {(['shared_interests', 'semantic', 'communication', 'lifestyle'] as const).map((key) => (
              <div key={key} className="stack" style={{ gap: '0.2rem' }}>
                <div className="row-between small"><span style={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}</span><span style={{ fontWeight: 600 }}>{Math.round((Number(weights[key]) / total) * 100)}% normalised</span></div>
                <input className="range" type="range" min={0} max={100} value={weights[key]} onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })} />
              </div>
            ))}
            <p className="tiny muted">Raw total {total}%. The engine normalises whatever you set, so the relative emphasis is what matters.</p>
          </div>
          <div className="row">
            <Button onClick={saveWeights} loading={busy}>Save weights</Button>
            <Button variant="ghost" onClick={async () => {
              try { const result: any = await api.resetPersonalisation(); await refresh(); toast.show(`Personalisation reset (${result.feedback_removed} feedback rows removed).`) }
              catch (error: any) { toast.show(error.message, 'error') }
            }}>Reset personalisation</Button>
          </div>
        </Card>
      ) : null}

      {tab === 'privacy' ? (
        <div className="stack-lg">
          <Card className="stack">
            <h3>Visibility</h3>
            <label className="checkline"><input type="checkbox" checked={form.discoverable} onChange={(e) => setForm({ ...form, discoverable: e.target.checked })} /><span>Let other members discover my profile</span></label>
            <label className="checkline"><input type="checkbox" checked={form.show_age} onChange={(e) => setForm({ ...form, show_age: e.target.checked })} /><span>Show my age to other members</span></label>
            <label className="checkline"><input type="checkbox" checked={form.show_city} onChange={(e) => setForm({ ...form, show_city: e.target.checked })} /><span>Show my city</span></label>
            <Button onClick={saveProfile} loading={busy} style={{ alignSelf: 'flex-start' }}>Save visibility</Button>
          </Card>

          <Card className="stack">
            <h3>Blocked profiles ({blocked.length})</h3>
            {blocked.length ? blocked.map((person) => (
              <div key={person.account_id} className="row-between">
                <span className="small">{person.display_name}</span>
                <Button size="sm" variant="ghost" onClick={async () => {
                  try { await api.unblock(person.account_id); const collections: any = await api.collections(); setBlocked(collections.blocked); toast.show('Unblocked.') }
                  catch (error: any) { toast.show(error.message, 'error') }
                }}>Unblock</Button>
              </div>
            )) : <p className="small muted">Nobody blocked. A block immediately removes both directions from discovery.</p>}
          </Card>

          <Card className="stack">
            <h3>Account</h3>
            <p className="small muted">Deleting removes your profile content, interests, answers, sessions, likes, saves and feedback. Block records are kept, without personal data, so a block keeps protecting the other member.</p>
            <div className="row">
              <Button variant="ghost" onClick={async () => { await signOut() }}>Sign out</Button>
              <Button variant="danger" onClick={() => setConfirmDelete(true)}>Delete account</Button>
            </div>
          </Card>
        </div>
      ) : null}

      {confirmDelete ? (
        <Modal title="Delete your account" onClose={() => setConfirmDelete(false)}>
          <div className="stack">
            <p className="small muted">This cannot be undone. Confirm your password to continue.</p>
            <Field label="Password"><input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <Button variant="ghost" onClick={() => setConfirmDelete(false)}>Cancel</Button>
              <Button variant="danger" onClick={async () => {
                try { await api.deleteAccount({ password }); toast.show('Account deleted.'); await signOut() }
                catch (error: any) { toast.show(error.message, 'error') }
              }}>Delete permanently</Button>
            </div>
          </div>
        </Modal>
      ) : null}
      {toast.node}
    </div>
  )
}
