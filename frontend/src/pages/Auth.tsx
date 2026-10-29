import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button, Card, Field, Wordmark } from '../components/ui'
import { useSession } from '../lib/session'
import { api } from '../lib/api'

export function SignIn() {
  const { signIn } = useSession()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError(null); setBusy(true)
    try {
      await signIn(email.trim(), password)
      navigate('/app')
    } catch (err: any) {
      setError(err.message ?? 'Could not sign in.')
    } finally { setBusy(false) }
  }

  return (
    <AuthFrame title="Welcome back" subtitle="Sign in to see who you align with, and why.">
      <form className="stack" onSubmit={submit}>
        <Field label="Email">
          <input className="input" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </Field>
        <Field label="Password">
          <input className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </Field>
        {error ? <p className="error-text">{error}</p> : null}
        <Button type="submit" loading={busy} block>Sign in</Button>
      </form>
      <p className="small muted center">
        New here? <Link to="/register" style={{ color: 'var(--violet)', fontWeight: 550 }}>Create an account</Link>
      </p>
      <DemoBox onUse={(mail, pass) => { setEmail(mail); setPassword(pass) }} />
    </AuthFrame>
  )
}

function DemoBox({ onUse }: { onUse: (email: string, password: string) => void }) {
  const [status, setStatus] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  return (
    <div className="panel stack" style={{ gap: '0.5rem' }}>
      <div className="row-between">
        <span className="small" style={{ fontWeight: 600 }}>Demo accounts</span>
        <button className="btn btn-ghost btn-sm" disabled={busy} onClick={async () => {
          setBusy(true)
          try { setStatus(await api.seedStatus()) } catch (e: any) { setStatus({ error: e.message }) } finally { setBusy(false) }
        }}>{busy ? 'Checking…' : 'Check status'}</button>
      </div>
      <p className="tiny muted">
        Six fictional members are seeded. Sign in as the demo member, or create your own account.
      </p>
      <div className="row wrap">
        <button className="btn btn-soft btn-sm" onClick={() => onUse('demo@demo.affinityai.invalid', 'DemoPass123!')}>
          Use demo member
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => onUse('aarav@demo.affinityai.invalid', 'DemoPass123!')}>
          Use Aarav (demo)
        </button>
      </div>
      {status ? (
        <span className="tiny muted">
          {status.error ? status.error : `${status.demo_accounts ?? 0} demo accounts, ${status.profiles ?? 0} profiles in this workspace.`}
        </span>
      ) : null}
    </div>
  )
}

export function Register() {
  const { signUp } = useSession()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ display_name: '', email: '', password: '', confirm: '', adult: false })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)

  function validate() {
    const next: Record<string, string> = {}
    if (form.display_name.trim().length < 2) next.display_name = 'Use at least 2 characters.'
    if (!/^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$/.test(form.email.trim())) next.email = 'Enter a valid email address.'
    if (form.password.length < 8) next.password = 'At least 8 characters.'
    if (form.password !== form.confirm) next.confirm = 'Passwords do not match.'
    if (!form.adult) next.adult = 'You must confirm you are 18 or over.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!validate()) return
    setBusy(true)
    try {
      await signUp(form.email.trim(), form.password, form.display_name.trim())
      navigate('/join', { replace: true, state: location.state })
    } catch (err: any) {
      setErrors({ form: err.message ?? 'Could not create the account.' })
    } finally { setBusy(false) }
  }

  return (
    <AuthFrame title="Create your account" subtitle="A few questions, no photos required, and you choose what is visible.">
      <form className="stack" onSubmit={submit}>
        <Field label="Display name" error={errors.display_name}>
          <input className="input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="How others will see you" />
        </Field>
        <Field label="Email" error={errors.email}>
          <input className="input" type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <div className="grid grid-2" style={{ gap: '0.75rem' }}>
          <Field label="Password" hint="At least 8 characters" error={errors.password}>
            <input className="input" type="password" autoComplete="new-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Field>
          <Field label="Confirm password" error={errors.confirm}>
            <input className="input" type="password" autoComplete="new-password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
          </Field>
        </div>
        <label className="checkline">
          <input type="checkbox" checked={form.adult} onChange={(e) => setForm({ ...form, adult: e.target.checked })} />
          <span>I confirm I am 18 or older and agree to keep my profile respectful and accurate.</span>
        </label>
        {errors.adult ? <p className="error-text">{errors.adult}</p> : null}
        {errors.form ? <p className="error-text">{errors.form}</p> : null}
        <Button type="submit" loading={busy} block>Create account</Button>
      </form>
      <p className="small muted center">
        Already have an account? <Link to="/signin" style={{ color: 'var(--violet)', fontWeight: 550 }}>Sign in</Link>
      </p>
    </AuthFrame>
  )
}

function AuthFrame({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="container" style={{ paddingBlock: '2.5rem' }}>
      <div className="row" style={{ marginBottom: '2rem' }}><Wordmark /></div>
      <div className="grid grid-2" style={{ alignItems: 'start', gap: '2.5rem' }}>
        <div className="stack" style={{ gap: '0.8rem' }}>
          <span className="eyebrow">Less swiping. More understanding.</span>
          <h2>{title}</h2>
          <p className="lede">{subtitle}</p>
          <ul className="stack small muted" style={{ paddingLeft: '1.1rem', marginTop: '0.5rem' }}>
            <li>Compatibility is arithmetic over your profile, not a black box.</li>
            <li>Questionnaire answers are private; only aggregated alignment is shown.</li>
            <li>A mutual match needs both people to say yes.</li>
          </ul>
        </div>
        <Card className="stack-lg">{children}</Card>
      </div>
    </div>
  )
}
