import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useAuth } from '../../contexts/AuthContext'
import styles from './AuthPage.module.css'

export function LoginPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const u = username.trim()
    const p = password
    if (!u) {
      setError(t.auth.usernameRequired)
      return
    }
    if (!p) {
      setError(t.auth.passwordRequired)
      return
    }
    setError(null)
    setLoading(true)
    try {
      await login(u, p)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : t.common.errorGeneric)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.title}>{t.auth.loginTitle}</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div>
            <label className={styles.label} htmlFor="login-username">{t.auth.username}</label>
            <input
              id="login-username"
              className={styles.input}
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t.auth.username}
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="login-password">{t.auth.password}</label>
            <input
              id="login-password"
              className={styles.input}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t.auth.password}
              disabled={loading}
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? t.common.loading : t.auth.login}
          </button>
          <p className={styles.switch}>
            {t.auth.noAccount} <Link to="/register">{t.auth.register}</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
