import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useAuth } from '../../contexts/AuthContext'
import { adminApi, billingApi } from '../../api'
import type { AdminUserRow } from '../../api'
import styles from './AdminPage.module.css'

function formatMoney(cents: number, currency: string): string {
  return `${(cents / 100).toFixed(2)} ${currency}`
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString()
}

export function AdminPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [list, setList] = useState<AdminUserRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [topupUser, setTopupUser] = useState<AdminUserRow | null>(null)
  const [topupCents, setTopupCents] = useState('')
  const [topupSubmitting, setTopupSubmitting] = useState(false)
  const [topupError, setTopupError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const data = await adminApi.listUsers()
      setList(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : t.common.errorGeneric)
      setList([])
    } finally {
      setLoading(false)
    }
  }, [t.common.errorGeneric])

  useEffect(() => {
    if (user?.is_admin) {
      load()
    } else {
      setLoading(false)
      setError('Forbidden')
    }
  }, [user?.is_admin, load])

  const handleTopup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topupUser) return
    const cents = parseInt(topupCents, 10)
    if (Number.isNaN(cents) || cents < 1) {
      setTopupError(t.admin.topupAmountCents)
      return
    }
    setTopupError(null)
    setTopupSubmitting(true)
    try {
      await billingApi.topup(topupUser.user_id, cents)
      setTopupUser(null)
      setTopupCents('')
      await load()
    } catch (err) {
      setTopupError(err instanceof Error ? err.message : t.common.errorGeneric)
    } finally {
      setTopupSubmitting(false)
    }
  }

  if (!user?.is_admin) {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <button type="button" className={styles.backBtn} onClick={() => navigate(-1)}>
            {t.common.back}
          </button>
        </header>
        <div className={styles.card}>
          <p className={styles.error}>{t.common.errorGeneric}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.backBtn} onClick={() => navigate(-1)}>
          {t.common.back}
        </button>
      </header>
      <div className={styles.card}>
        <h1 className={styles.title}>{t.admin.title}</h1>
        <div className={styles.toolbar}>
          <button type="button" className={styles.btn} onClick={() => void load()} disabled={loading}>
            {loading ? t.common.loading : t.settings.refresh}
          </button>
        </div>
        {error && <p className={styles.error}>{error}</p>}
        <h2 className={styles.title}>{t.admin.userList}</h2>
        {loading && <p className={styles.muted}>{t.common.loading}</p>}
        {!loading && (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t.admin.username}</th>
                <th>{t.admin.createdAt}</th>
                <th>{t.admin.lastLoginAt}</th>
                <th className={styles.right}>{t.admin.requestCount}</th>
                <th className={styles.right}>{t.admin.totalTokens}</th>
                <th className={styles.right}>{t.admin.balance}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {list.map((row) => (
                <tr key={row.user_id}>
                  <td className={styles.mono}>{row.username}</td>
                  <td className={styles.mono}>{formatDate(row.created_at)}</td>
                  <td className={styles.mono}>
                    {row.last_login_at ? formatDate(row.last_login_at) : t.admin.never}
                  </td>
                  <td className={`${styles.right} ${styles.mono}`}>{row.request_count}</td>
                  <td className={`${styles.right} ${styles.mono}`}>{row.total_tokens}</td>
                  <td className={`${styles.right} ${styles.mono}`}>
                    {formatMoney(row.balance_cents, row.currency)}
                  </td>
                  <td>
                    <button
                      type="button"
                      className={styles.btnPrimary}
                      onClick={() => {
                        setTopupUser(row)
                        setTopupCents('')
                        setTopupError(null)
                      }}
                    >
                      {t.admin.topup}
                    </button>
                  </td>
                </tr>
              ))}
              {!list.length && (
                <tr>
                  <td colSpan={7} className={styles.muted}>
                    {t.common.loading}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {topupUser && (
        <div className={styles.overlay} role="dialog" aria-modal="true" aria-label={t.admin.topup}>
          <div className={styles.modal}>
            <h3 className={styles.modalTitle}>
              {t.admin.topup} — {topupUser.username}
            </h3>
            <form onSubmit={handleTopup}>
              <label className={styles.label} htmlFor="admin-topup-cents">
                {t.admin.topupAmountCents}
              </label>
              <input
                id="admin-topup-cents"
                className={styles.input}
                type="number"
                min={1}
                value={topupCents}
                onChange={(e) => setTopupCents(e.target.value)}
                placeholder="1000"
                disabled={topupSubmitting}
              />
              {topupError && <p className={styles.error}>{topupError}</p>}
              <div className={styles.modalActions}>
                <button
                  type="button"
                  className={styles.btn}
                  onClick={() => {
                    setTopupUser(null)
                    setTopupError(null)
                  }}
                  disabled={topupSubmitting}
                >
                  {t.common.cancel}
                </button>
                <button type="submit" className={styles.btnPrimary} disabled={topupSubmitting}>
                  {topupSubmitting ? t.common.loading : t.admin.topupSuccess}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
