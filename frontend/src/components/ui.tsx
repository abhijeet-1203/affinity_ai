import React from 'react'
import { Link } from 'react-router-dom'

export function Button({
  children, variant = 'primary', size, block, loading, as: As, ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost' | 'soft' | 'danger'
  size?: 'sm'
  block?: boolean
  loading?: boolean
  as?: any
}) {
  const className = ['btn', `btn-${variant}`, size === 'sm' ? 'btn-sm' : '', block ? 'btn-block' : '', rest.className ?? '']
    .filter(Boolean).join(' ')
  const Component: any = As ?? 'button'
  return (
    <Component {...rest} className={className} disabled={rest.disabled || loading}>
      {loading ? <span className="tiny">Working…</span> : children}
    </Component>
  )
}

export function Card({ children, className = '', ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`card ${className}`} {...rest}>{children}</div>
}

export function Field({ label, hint, error, children }: { label: string; hint?: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="field">
      <span className="label">{label}</span>
      {children}
      {hint && !error ? <span className="hint">{hint}</span> : null}
      {error ? <span className="error-text">{error}</span> : null}
    </label>
  )
}

export function Badge({ children, tone = 'default', dot }: { children: React.ReactNode; tone?: 'default' | 'outline' | 'success' | 'warn' | 'danger'; dot?: boolean }) {
  return <span className={`badge ${tone === 'default' ? '' : `badge-${tone}`} ${dot ? 'badge-dot' : ''}`}>{children}</span>
}

export function ScoreRing({ value, size }: { value: number; size?: 'lg' }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className={`score-ring ${size === 'lg' ? 'lg' : ''}`} style={{ ['--pct' as any]: pct }}>
      <span>{pct}%</span>
    </div>
  )
}

export function DimensionBar({ label, percent, note, missing }: { label: string; percent: number | null; note?: string; missing?: boolean }) {
  return (
    <div className="stack" style={{ gap: '0.3rem' }}>
      <div className="row-between">
        <span className="small" style={{ fontWeight: 550 }}>{label}</span>
        <span className="small" style={{ color: missing ? 'var(--muted)' : 'var(--plum)', fontWeight: 600 }}>
          {missing ? 'no data' : `${percent}%`}
        </span>
      </div>
      <div className={`bar ${missing ? 'bar-muted' : ''}`}>
        <i style={{ width: `${missing ? 100 : percent ?? 0}%` }} />
      </div>
      {note ? <span className="tiny muted">{note}</span> : null}
    </div>
  )
}

export function Avatar({ name, src, size }: { name: string; src?: string | null; size?: 'lg' }) {
  const initials = (name || '?').split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase()
  return (
    <div className={`avatar ${size === 'lg' ? 'lg' : ''}`}>
      {src ? <img src={src} alt="" onError={(event) => { (event.target as HTMLImageElement).style.display = 'none' }} /> : initials}
    </div>
  )
}

export function EmptyState({ title, children, action }: { title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      {children ? <p className="muted small" style={{ maxWidth: '52ch', margin: '0 auto 1rem' }}>{children}</p> : null}
      {action}
    </div>
  )
}

export function Skeleton({ height = 96 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} />
}

export function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="row-between" style={{ marginBottom: '0.9rem' }}>
          <h3>{title}</h3>
          <button className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close">Close</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Steps({ total, current }: { total: number; current: number }) {
  return (
    <div className="steps" aria-label={`Step ${current} of ${total}`}>
      {Array.from({ length: total }, (_, index) => (
        <span key={index} className={`step-dot ${index < current ? 'done' : ''}`} />
      ))}
    </div>
  )
}

export function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="panel stack" style={{ gap: '0.15rem' }}>
      <span className="tiny muted" style={{ textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>{label}</span>
      <span style={{ fontSize: '1.5rem', fontWeight: 650, color: 'var(--plum)' }}>{value}</span>
      {hint ? <span className="tiny muted">{hint}</span> : null}
    </div>
  )
}

export function Wordmark({ to = '/' }: { to?: string }) {
  return (
    <Link to={to} className="wordmark">
      <span className="mark">A</span>
      Affinity<span style={{ color: 'var(--violet)' }}>AI</span>
    </Link>
  )
}

export function Tag({ children, shared }: { children: React.ReactNode; shared?: boolean }) {
  return <span className={`tag ${shared ? 'shared' : ''}`}>{children}</span>
}
