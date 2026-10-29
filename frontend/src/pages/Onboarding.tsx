import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Field, Steps, Tag } from '../components/ui'
import { api } from '../lib/api'
import { useSession, useToast } from '../lib/session'
import type { Question } from '../lib/types'

const CONNECTIONS = [
  ['dating', 'Dating'], ['friendship', 'Friendship'], ['activity_partner', 'Activity partner'], ['any', 'Open to any'],
]

export default function Onboarding() {
  const { bundle, refresh, setBundle } = useSession()
  const navigate = useNavigate()
  const toast = useToast()
  const [step, setStep] = useState(1)
  const [status, setStatus] = useState<any>(null)
  const [catalog, setCatalog] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [profile, setProfile] = useState({ display_name: '', birth_date: '', city: '', bio: '', connection_type: 'dating' })
  const [interests, setInterests] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const [answers, setAnswers] = useState<Record<string, any>>({})
  const [prefs, setPrefs] = useState({ min_age: 21, max_age: 45, connection_type: 'dating', weights: { shared_interests: 35, semantic: 25, communication: 20, lifestyle: 20 } })
  const [discoverable, setDiscoverable] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const [onboarding, catalogue] = await Promise.all([api.onboarding(), api.catalog()])
        setStatus(onboarding)
        setCatalog(catalogue)
        const b = onboarding.bundle
        setProfile({
          display_name: b.profile.display_name ?? '',
          birth_date: b.profile.birth_date ?? '',
          city: b.profile.city ?? '',
          bio: b.profile.bio ?? '',
          connection_type: b.profile.connection_type ?? 'dating',
        })
        setInterests(b.interests ?? [])
        setAnswers(b.answers ?? {})
        setPrefs({
          min_age: b.preferences.min_age ?? 21,
          max_age: b.preferences.max_age ?? 45,
          connection_type: b.preferences.connection_type ?? 'dating',
          weights: {
            shared_interests: Math.round((b.preferences.weights?.shared_interests ?? 0.35) * 100),
            semantic: Math.round((b.preferences.weights?.semantic ?? 0.25) * 100),
            communication: Math.round((b.preferences.weights?.communication ?? 0.20) * 100),
            lifestyle: Math.round((b.preferences.weights?.lifestyle ?? 0.20) * 100),
          },
        })
        setDiscoverable(b.profile.discoverable ?? true)
        setStep(Math.min(5, Math.max(1, onboarding.next_step ?? 1)))
      } catch (err: any) { setError(err.message) }
    })()
  }, [])

  const questions: Question[] = status?.questions ?? []

  function toggleInterest(name: string) {
    setInterests((current) => current.includes(name) ? current.filter((item) => item !== name) : current.length >= 20 ? current : [...current, name])
  }

  async function saveAndAdvance() {
    setBusy(true); setError(null)
    try {
      if (step === 1) {
        await api.saveProfileStep(profile)
        setStep(2)
      } else if (step === 2) {
        await api.saveInterests(interests)
        setStep(3)
      } else if (step === 3) {
        await api.saveAnswers(answers)
        setStep(4)
      } else if (step === 4) {
        await api.savePreferences({ ...prefs, weights: prefs.weights })
        setStep(5)
      } else {
        await api.completeOnboarding({ discoverable })
        await refresh()
        navigate('/app', { replace: true })
        return
      }
      const next = await api.onboarding()
      setStatus(next)
      const b = next.bundle
      if (b) setBundle((current) => current ? { ...current, ...b } : current)
      toast.show('Saved.')
    } catch (err: any) {
      setError(err.message)
    } finally { setBusy(false) }
  }

  const preview = useMemo(() => ({
    initials: (profile.display_name || '?').split(' ').slice(0, 2).map((p) => p[0]).join('').toUpperCase(),
    age: profile.birth_date ? Math.floor((Date.now() - new Date(profile.birth_date).getTime()) / 31557600000) : null,
  }), [profile])

  if (!bundle) return null

  return (
    <div className="container" style={{ maxWidth: 760, paddingBlock: '2.5rem' }}>
      <div className="stack-lg">
        <div className="stack" style={{ gap: '0.6rem' }}>
          <span className="eyebrow">Step {step} of 5</span>
          <Steps total={5} current={step} />
          <h2>
            {step === 1 && 'The basics'}
            {step === 2 && 'What you enjoy'}
            {step === 3 && 'How you connect'}
            {step === 4 && 'What matters most'}
            {step === 5 && 'Visibility and consent'}
          </h2>
          <p className="muted small">Everything except your name and birth date is optional. You can change all of it later in Settings.</p>
        </div>

        <Card className="stack-lg">
          {step === 1 ? (
            <div className="stack">
              <Field label="Display name">
                <input className="input" value={profile.display_name} onChange={(e) => setProfile({ ...profile, display_name: e.target.value })} />
              </Field>
              <div className="grid grid-2" style={{ gap: '0.75rem' }}>
                <Field label="Birth date" hint="Used only to calculate your age. AffinityAI is 18+.">
                  <input className="input" type="date" value={profile.birth_date ?? ''} onChange={(e) => setProfile({ ...profile, birth_date: e.target.value })} />
                </Field>
                <Field label="City (optional)" hint="A broad city only — never your address or GPS.">
                  <input className="input" value={profile.city} onChange={(e) => setProfile({ ...profile, city: e.target.value })} placeholder="Pune" />
                </Field>
              </div>
              <Field label="Short biography" hint="What you would actually want someone to know. The engine reads this for semantic similarity.">
                <textarea className="textarea" value={profile.bio} onChange={(e) => setProfile({ ...profile, bio: e.target.value })} placeholder="I spend most weekends on a trail with a camera, then cook something ambitious on Sunday." />
              </Field>
              <Field label="What are you looking for?">
                <select className="select" value={profile.connection_type} onChange={(e) => setProfile({ ...profile, connection_type: e.target.value })}>
                  {CONNECTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </Field>
            </div>
          ) : null}

          {step === 2 ? (
            <div className="stack">
              <div className="row-between">
                <span className="small" style={{ fontWeight: 600 }}>Choose up to 20</span>
                <span className="tiny muted">{interests.length} selected</span>
              </div>
              {(catalog?.categories ?? []).map((category: any) => (
                <div key={category.name} className="stack" style={{ gap: '0.4rem' }}>
                  <span className="tiny muted" style={{ textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>{category.name}</span>
                  <div className="row wrap" style={{ gap: '0.4rem' }}>
                    {category.interests.map((interest: any) => (
                      <button key={interest.name} type="button" className="chip" data-selected={interests.includes(interest.name)} onClick={() => toggleInterest(interest.name)}>
                        {interest.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <div className="row" style={{ gap: '0.5rem' }}>
                <input className="input" placeholder="Add your own interest" value={custom} onChange={(e) => setCustom(e.target.value)} />
                <Button variant="ghost" size="sm" type="button" onClick={() => {
                  const name = custom.trim().toLowerCase()
                  if (name && !interests.includes(name) && interests.length < 20) setInterests([...interests, name])
                  setCustom('')
                }}>Add</Button>
              </div>
              {interests.length ? (
                <div className="row wrap" style={{ gap: '0.35rem' }}>
                  {interests.map((interest) => <Tag key={interest}>{interest}</Tag>)}
                </div>
              ) : null}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="stack-lg">
              {questions.map((question) => (
                <div key={question.key} className="stack" style={{ gap: '0.45rem' }}>
                  <span className="label">{question.prompt}</span>
                  {question.kind === 'ordinal' ? (
                    <div className="stack" style={{ gap: '0.25rem' }}>
                      <input className="range" type="range" min={1} max={5} step={1} value={Number(answers[question.key] ?? 3)} onChange={(e) => setAnswers({ ...answers, [question.key]: Number(e.target.value) })} />
                      <div className="row-between tiny muted">
                        <span>{question.scale_labels?.['1'] ?? '1'}</span>
                        <span style={{ color: 'var(--plum)', fontWeight: 600 }}>{question.options.find((o) => Number(o.value) === Number(answers[question.key] ?? 3))?.label}</span>
                        <span>{question.scale_labels?.['5'] ?? '5'}</span>
                      </div>
                    </div>
                  ) : null}
                  {question.kind === 'categorical' ? (
                    <div className="row wrap" style={{ gap: '0.4rem' }}>
                      {question.options.map((option) => (
                        <button key={option.value} type="button" className="chip" data-selected={answers[question.key] === option.value}
                          onClick={() => setAnswers({ ...answers, [question.key]: answers[question.key] === option.value ? undefined : option.value })}>
                          {option.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                  {question.kind === 'multiselect' ? (
                    <div className="row wrap" style={{ gap: '0.4rem' }}>
                      {question.options.map((option) => {
                        const picked: string[] = answers[question.key] ?? []
                        const selected = picked.includes(option.value)
                        return (
                          <button key={option.value} type="button" className="chip" data-selected={selected}
                            onClick={() => setAnswers({ ...answers, [question.key]: selected ? picked.filter((v) => v !== option.value) : [...picked, option.value].slice(0, question.max_selected ?? 3) })}>
                            {option.label}
                          </button>
                        )
                      })}
                    </div>
                  ) : null}
                </div>
              ))}
              <p className="tiny muted">Skip anything you like — unanswered questions are treated as unknown, never as disagreement.</p>
            </div>
          ) : null}

          {step === 4 ? (
            <div className="stack-lg">
              <div className="grid grid-2" style={{ gap: '0.75rem' }}>
                <Field label="Minimum age"><input className="input" type="number" min={18} max={100} value={prefs.min_age} onChange={(e) => setPrefs({ ...prefs, min_age: Number(e.target.value) })} /></Field>
                <Field label="Maximum age"><input className="input" type="number" min={18} max={100} value={prefs.max_age} onChange={(e) => setPrefs({ ...prefs, max_age: Number(e.target.value) })} /></Field>
              </div>
              <Field label="Looking for">
                <select className="select" value={prefs.connection_type} onChange={(e) => setPrefs({ ...prefs, connection_type: e.target.value })}>
                  {CONNECTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </Field>
              <div className="stack" style={{ gap: '0.6rem' }}>
                <span className="label">How much each dimension counts</span>
                {([
                  ['shared_interests', 'Shared interests'],
                  ['semantic', 'Interest & bio similarity'],
                  ['communication', 'Communication style'],
                  ['lifestyle', 'Lifestyle rhythm'],
                ] as const).map(([key, label]) => (
                  <div key={key} className="stack" style={{ gap: '0.2rem' }}>
                    <div className="row-between"><span className="small">{label}</span><span className="small" style={{ fontWeight: 600 }}>{prefs.weights[key]}%</span></div>
                    <input className="range" type="range" min={0} max={100} value={prefs.weights[key]}
                      onChange={(e) => setPrefs({ ...prefs, weights: { ...prefs.weights, [key]: Number(e.target.value) } })} />
                  </div>
                ))}
                <p className="tiny muted">
                  These sliders are relative: the engine normalises them so they always total 100%.
                  Current total {Object.values(prefs.weights).reduce((a, b) => a + Number(b), 0)}%.
                </p>
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="stack-lg">
              <div className="grid grid-2" style={{ alignItems: 'start' }}>
                <Card className="card-flat">
                  <div className="row" style={{ alignItems: 'flex-start' }}>
                    <div className="avatar lg">{preview.initials}</div>
                    <div className="stack" style={{ gap: '0.3rem' }}>
                      <span style={{ fontWeight: 600 }}>{profile.display_name || 'Your name'}{preview.age ? `, ${preview.age}` : ''}</span>
                      <span className="small muted">{profile.city || 'City hidden'}</span>
                      <p className="small">{profile.bio || 'Your biography will appear here.'}</p>
                    </div>
                  </div>
                  <div className="row wrap" style={{ gap: '0.3rem', marginTop: '0.75rem' }}>
                    {interests.slice(0, 8).map((interest) => <Tag key={interest} shared>{interest}</Tag>)}
                  </div>
                </Card>
                <div className="stack" style={{ gap: '0.7rem' }}>
                  <label className="checkline">
                    <input type="checkbox" checked={discoverable} onChange={(e) => setDiscoverable(e.target.checked)} />
                    <span>Let other members discover my profile. You can change this at any time.</span>
                  </label>
                  <div className="panel">
                    <span className="tiny muted" style={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Visible to others</span>
                    <p className="small" style={{ marginTop: '0.3rem' }}>Display name, age and city (if enabled), biography, interests.</p>
                    <span className="tiny muted" style={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em' }}>Never visible</span>
                    <p className="small" style={{ marginTop: '0.3rem' }}>Email, exact location, your individual questionnaire answers, who you liked, your reports.</p>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {error ? <p className="error-text">{error}</p> : null}

          <div className="row-between">
            <Button variant="ghost" type="button" disabled={step === 1 || busy} onClick={() => setStep(Math.max(1, step - 1))}>Back</Button>
            <div className="row">
              {step < 5 ? <Button variant="ghost" type="button" onClick={() => setStep(step + 1)}>Skip for now</Button> : null}
              <Button type="button" loading={busy} onClick={saveAndAdvance}>
                {step === 5 ? 'Finish and explore' : 'Save and continue'}
              </Button>
            </div>
          </div>
        </Card>
        {toast.node}
      </div>
    </div>
  )
}
