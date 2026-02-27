import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useAuth } from '../../contexts/AuthContext'
import styles from '../LoginPage/AuthPage.module.css'

export function RegisterPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { register } = useAuth()
  const [inviteToken, setInviteToken] = useState(() => searchParams.get('token') ?? '')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token')
    if (tokenFromUrl) setInviteToken(tokenFromUrl)
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = inviteToken.trim()
    const u = username.trim()
    const p = password
    const pc = passwordConfirm
    if (!token) {
      setError(t.auth.inviteTokenRequired)
      return
    }
    if (!u) {
      setError(t.auth.usernameRequired)
      return
    }
    if (!p) {
      setError(t.auth.passwordRequired)
      return
    }
    if (p.length < 6) {
      setError(t.auth.passwordMinLength)
      return
    }
    if (p !== pc) {
      setError(t.auth.passwordMismatch)
      return
    }
    setError(null)
    setLoading(true)
    try {
      await register(token, u, p)
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
        <h1 className={styles.title}>{t.auth.registerTitle}</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div>
            <label className={styles.label} htmlFor="reg-invite-token">{t.auth.inviteToken}</label>
            <input
              id="reg-invite-token"
              className={styles.input}
              type="text"
              autoComplete="off"
              value={inviteToken}
              onChange={(e) => setInviteToken(e.target.value)}
              placeholder={t.auth.inviteToken}
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="reg-username">{t.auth.username}</label>
            <input
              id="reg-username"
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
            <label className={styles.label} htmlFor="reg-password">{t.auth.password}</label>
            <input
              id="reg-password"
              className={styles.input}
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t.auth.password}
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="reg-password-confirm">{t.auth.passwordConfirm}</label>
            <input
              id="reg-password-confirm"
              className={styles.input}
              type="password"
              autoComplete="new-password"
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder={t.auth.passwordConfirm}
              disabled={loading}
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? t.common.loading : t.auth.register}
          </button>
          <p className={styles.switch}>
            {t.auth.hasAccount} <Link to="/login">{t.auth.login}</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
