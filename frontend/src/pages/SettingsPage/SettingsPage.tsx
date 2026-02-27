import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useAuth } from '../../contexts/AuthContext'
import { userApi } from '../../api'
import styles from './SettingsPage.module.css'

export function SettingsPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()
  const [username, setUsername] = useState(user?.username ?? '')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const u = username.trim()
    if (!u) {
      setError(t.auth.usernameRequired)
      return
    }
    if (newPassword !== newPasswordConfirm) {
      setError(t.auth.passwordMismatch)
      return
    }
    if (newPassword && newPassword.length < 6) {
      setError(t.auth.passwordMinLength)
      return
    }
    setError(null)
    setSuccess(false)
    setLoading(true)
    try {
      const data: { username?: string; password?: string } = { username: u }
      if (newPassword) data.password = newPassword
      await userApi.updateMe(data)
      await refreshUser()
      setNewPassword('')
      setNewPasswordConfirm('')
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : t.common.errorGeneric)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.backBtn} onClick={() => navigate(-1)}>
          {t.common.back}
        </button>
      </header>
      <div className={styles.card}>
        <h1 className={styles.title}>{t.settings.title}</h1>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div>
            <label className={styles.label} htmlFor="settings-username">{t.settings.username}</label>
            <input
              id="settings-username"
              className={styles.input}
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t.settings.username}
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="settings-new-password">{t.settings.newPassword}</label>
            <input
              id="settings-new-password"
              className={styles.input}
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder={t.settings.newPassword}
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="settings-new-password-confirm">{t.settings.newPasswordConfirm}</label>
            <input
              id="settings-new-password-confirm"
              className={styles.input}
              type="password"
              autoComplete="new-password"
              value={newPasswordConfirm}
              onChange={(e) => setNewPasswordConfirm(e.target.value)}
              placeholder={t.settings.newPasswordConfirm}
              disabled={loading}
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          {success && <p className={styles.success}>{t.settings.updateSuccess}</p>}
          <div className={styles.actions}>
            <button type="button" className={styles.btn} onClick={() => navigate(-1)} disabled={loading}>
              {t.common.cancel}
            </button>
            <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={loading}>
              {loading ? t.common.loading : t.common.save}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
