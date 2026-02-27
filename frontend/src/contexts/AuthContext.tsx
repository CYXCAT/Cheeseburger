import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { authApi, userApi, setAuthToken } from '../api'
import type { UserOut } from '../api'

type AuthState = {
  token: string | null
  user: UserOut | null
  loading: boolean
}

type AuthContextValue = AuthState & {
  login: (username: string, password: string) => Promise<void>
  register: (inviteToken: string, username: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem('doc_access_token'))
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const t = localStorage.getItem('doc_access_token')
    if (!t) {
      setUser(null)
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const u = await userApi.getMe()
      setUser(u)
      setTokenState(t)
    } catch {
      setAuthToken(null)
      setTokenState(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (token && !user) {
      refreshUser()
    } else if (!token) {
      setLoading(false)
    }
  }, [token, user, refreshUser])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login(username, password)
    setAuthToken(res.access_token)
    setTokenState(res.access_token)
    setUser(res.user)
  }, [])

  const register = useCallback(async (inviteToken: string, username: string, password: string) => {
    const res = await authApi.register(inviteToken, username, password)
    setAuthToken(res.access_token)
    setTokenState(res.access_token)
    setUser(res.user)
  }, [])

  const logout = useCallback(() => {
    setAuthToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  const value: AuthContextValue = {
    token,
    user,
    loading,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
