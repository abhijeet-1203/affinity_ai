import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Compass, LayoutDashboard, Heart, Bookmark, BarChart3, Settings, FlaskConical, Info, LogOut } from 'lucide-react'
import { useSession } from '../lib/session'
import { Wordmark } from './ui'

const NAV = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/app/discover', label: 'Discover', icon: Compass },
  { to: '/app/matches', label: 'Matches', icon: Heart },
  { to: '/app/saved', label: 'Saved', icon: Bookmark },
  { to: '/app/insights', label: 'Insights', icon: BarChart3 },
  { to: '/app/settings', label: 'Settings', icon: Settings },
  { to: '/app/evaluation', label: 'Engine evidence', icon: FlaskConical },
  { to: '/app/method', label: 'How it works', icon: Info },
]

export function Shell({ children }: { children: React.ReactNode }) {
  const { bundle, signOut } = useSession()
  const navigate = useNavigate()

  return (
    <div className="shell">
      <aside className="sidebar">
        <Wordmark to="/app" />
        <nav className="stack" style={{ gap: '0.15rem' }}>
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="stack" style={{ marginTop: 'auto', gap: '0.5rem' }}>
          {bundle ? (
            <div className="panel stack" style={{ gap: '0.2rem', padding: '0.7rem 0.8rem' }}>
              <span className="small" style={{ fontWeight: 600 }}>{bundle.profile.display_name}</span>
              <span className="tiny muted">{bundle.account.email}</span>
              {bundle.account.is_demo ? <span className="badge badge-warn tiny">Demo account</span> : null}
            </div>
          ) : null}
          <button className="side-link" onClick={async () => { await signOut(); navigate('/') }}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      <main className="main">{children}</main>

      <nav className="mobile-nav">
        {NAV.slice(0, 5).map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon size={19} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
