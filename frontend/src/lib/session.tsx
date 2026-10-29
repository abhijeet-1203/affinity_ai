import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, ApiError, setAuthToken, getAuthToken } from './api'
import type { ProfileBundle } from './types'

const TOKEN_KEY = 'affinityai.token'

type SessionValue = {
  ready: boolean
  bundle: ProfileBundle | null
  signedIn: boolean
  bootError: string | null
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, displayName: string) => Promise<void>
  signOut: () => Promise<void>
  refresh: () => Promise<void>
  applyBundle: (bundle: ProfileBundle) => void
  setBundle: React.Dispatch<React.SetStateAction<ProfileBundle | null>>
}

const SessionContext = createContext<SessionValue | null>(null)

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [bundle, setBundle] = useState<ProfileBundle | null>(null)
  const [ready, setReady] = useState(false)
  const [bootError, setBootError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) { setReady(true); return }
    setAuthToken(token)
    ;(async () => {
      try {
        const me = await api.me(token)
        if (!cancelled) setBundle(me as ProfileBundle)
      } catch (error) {
        // An invalid or expired session is cleared, never silently faked.
        if (!cancelled) {
          if (error instanceof ApiError && error.status === 401) {
            localStorage.removeItem(TOKEN_KEY)
            setAuthToken(null)
          } else {
            setBootError(error instanceof Error ? error.message : 'Could not restore your session.')
          }
        }
      } finally {
        if (!cancelled) setReady(true)
      }
    })()
    return () => { cancelled = true }
  }, [])

  const applyBundle = useCallback((next: ProfileBundle) => {
    if (next?.token) {
      localStorage.setItem(TOKEN_KEY, next.token)
      setAuthToken(next.token)
    }
    setBundle(next)
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await api.login({ email, password })
    applyBundle(result as ProfileBundle)
  }, [applyBundle])

  const signUp = useCallback(async (email: string, password: string, displayName: string) => {
    const result = await api.register({ email, password, display_name: displayName })
    applyBundle(result as ProfileBundle)
  }, [applyBundle])

  const signOut = useCallback(async () => {
    try { await api.logout() } catch { /* a dead session is still signed out locally */ }
    localStorage.removeItem(TOKEN_KEY)
    setAuthToken(null)
    setBundle(null)
  }, [])

  const refresh = useCallback(async () => {
    if (!getAuthToken()) return
    const me = await api.me()
    setBundle(me as ProfileBundle)
  }, [])

  const value = useMemo<SessionValue>(() => ({
    ready, bundle, signedIn: Boolean(bundle), bootError,
    signIn, signUp, signOut, refresh, applyBundle, setBundle,
  }), [ready, bundle, bootError, signIn, signUp, signOut, refresh, applyBundle])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext)
  if (!value) throw new Error('useSession must be used inside SessionProvider')
  return value
}

export function useToast() {
  const [toast, setToast] = useState<{ message: string; tone: 'ok' | 'error' } | null>(null)
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 4200)
    return () => clearTimeout(timer)
  }, [toast])
  const node = toast ? <div className={`toast ${toast.tone === 'error' ? 'error' : ''}`}>{toast.message}</div> : null
  return {
    show: (message: string, tone: 'ok' | 'error' = 'ok') => setToast({ message, tone }),
    node,
  }
}
