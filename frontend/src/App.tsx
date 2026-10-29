import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Shell } from './components/Shell'
import { useSession } from './lib/session'
import Landing from './pages/Landing'
import { Register, SignIn } from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Discover from './pages/Discover'
import Compatibility from './pages/Compatibility'
import Matches from './pages/Matches'
import Saved from './pages/Saved'
import Insights from './pages/Insights'
import Settings from './pages/Settings'
import Method from './pages/Method'
import Evaluation from './pages/Evaluation'

function Loading() {
  return (
    <div className="container" style={{ paddingBlock: '4rem' }}>
      <div className="stack" style={{ gap: '0.8rem' }}>
        <div className="skeleton" style={{ height: 26, width: 180 }} />
        <div className="skeleton" style={{ height: 140 }} />
        <div className="skeleton" style={{ height: 140 }} />
      </div>
      <p className="small muted" style={{ marginTop: '1rem' }}>Restoring your session…</p>
    </div>
  )
}

function Protected({ children }: { children: React.ReactNode }) {
  const { ready, signedIn, bundle } = useSession()
  const location = useLocation()
  if (!ready) return <Loading />
  if (!signedIn) return <Navigate to="/signin" replace state={{ from: location.pathname }} />
  if (bundle && !bundle.profile.onboarding_completed && location.pathname !== '/join') {
    return <Navigate to="/join" replace />
  }
  return <Shell>{children}</Shell>
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { ready, signedIn, bundle } = useSession()
  if (!ready) return <Loading />
  if (signedIn) return <Navigate to={bundle?.profile.onboarding_completed ? '/app' : '/join'} replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/discover" element={<Landing />} />
      <Route path="/how-it-works" element={<Landing />} />
      <Route path="/approach" element={<Landing />} />
      <Route path="/safety" element={<Landing />} />
      <Route path="/signin" element={<PublicOnly><SignIn /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
      <Route path="/join" element={<Onboarding />} />
      <Route path="/app" element={<Protected><Dashboard /></Protected>} />
      <Route path="/app/discover" element={<Protected><Discover /></Protected>} />
      <Route path="/app/people/:id" element={<Protected><Compatibility /></Protected>} />
      <Route path="/app/matches" element={<Protected><Matches /></Protected>} />
      <Route path="/app/saved" element={<Protected><Saved /></Protected>} />
      <Route path="/app/insights" element={<Protected><Insights /></Protected>} />
      <Route path="/app/settings" element={<Protected><Settings /></Protected>} />
      <Route path="/app/method" element={<Protected><Method /></Protected>} />
      <Route path="/app/evaluation" element={<Protected><Evaluation /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
