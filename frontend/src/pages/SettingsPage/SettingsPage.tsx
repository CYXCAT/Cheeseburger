import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { useAuth } from '../../contexts/AuthContext'
import { billingApi, usageApi, userApi } from '../../api'
import type { BillingMe, LedgerEntry, UsageEvent, UsageSummary } from '../../api'
import styles from './SettingsPage.module.css'

type TabKey = 'account' | 'usage' | 'billing'

function formatMoney(cents: number, currency: string): string {
  const value = (cents / 100).toFixed(2)
  return `${value} ${currency}`
}

export function SettingsPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()
  const [tab, setTab] = useState<TabKey>('account')

  const [username, setUsername] = useState(user?.username ?? '')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [billingMe, setBillingMe] = useState<BillingMe | null>(null)
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null)
  const [usageEvents, setUsageEvents] = useState<UsageEvent[]>([])
  const [ledger, setLedger] = useState<LedgerEntry[]>([])
  const [panelLoading, setPanelLoading] = useState(false)
  const [panelError, setPanelError] = useState<string | null>(null)

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

  const refreshPanels = async () => {
    setPanelError(null)
    setPanelLoading(true)
    try {
      const [me, summary, events, led] = await Promise.all([
        billingApi.me(),
        usageApi.summary(30),
        usageApi.events(50, 0),
        billingApi.ledger(50, 0),
      ])
      setBillingMe(me)
      setUsageSummary(summary)
      setUsageEvents(events)
      setLedger(led)
    } catch (err) {
      setPanelError(err instanceof Error ? err.message : t.common.errorGeneric)
    } finally {
      setPanelLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'usage' || tab === 'billing') {
      void refreshPanels()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  const kpis = useMemo(() => {
    if (!billingMe) return null
    return {
      balance: formatMoney(billingMe.balance_cents, billingMe.currency),
      last30dTokens: String(billingMe.last_30d_usage_tokens),
      last30dSpent: formatMoney(billingMe.last_30d_spent_cents, billingMe.currency),
      currency: billingMe.currency,
    }
  }, [billingMe])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.backBtn} onClick={() => navigate(-1)}>
          {t.common.back}
        </button>
      </header>
      <div className={styles.card}>
        <h1 className={styles.title}>{t.settings.title}</h1>
        <div className={styles.tabs} role="tablist" aria-label={t.settings.title}>
          <button type="button" className={styles.tabBtn} data-active={tab === 'account'} onClick={() => setTab('account')}>
            {t.settings.tabAccount}
          </button>
          <button type="button" className={styles.tabBtn} data-active={tab === 'usage'} onClick={() => setTab('usage')}>
            {t.settings.tabUsage}
          </button>
          <button type="button" className={styles.tabBtn} data-active={tab === 'billing'} onClick={() => setTab('billing')}>
            {t.settings.tabBilling}
          </button>
        </div>

        {tab === 'account' && (
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
        )}

        {(tab === 'usage' || tab === 'billing') && (
          <>
            <div className={styles.toolbar}>
              <button type="button" className={styles.btn} onClick={() => void refreshPanels()} disabled={panelLoading}>
                {panelLoading ? t.common.loading : t.settings.refresh}
              </button>
            </div>
            {panelError && <p className={styles.error}>{panelError}</p>}
            {!panelError && !panelLoading && !billingMe && (
              <p className={styles.muted}>{t.common.loading}</p>
            )}
            {kpis && (
              <div className={styles.kpis}>
                <div className={styles.kpiCard}>
                  <p className={styles.kpiLabel}>{t.settings.balance}</p>
                  <p className={styles.kpiValue}>{kpis.balance}</p>
                </div>
                <div className={styles.kpiCard}>
                  <p className={styles.kpiLabel}>{t.settings.currency}</p>
                  <p className={styles.kpiValue}>{kpis.currency}</p>
                </div>
                <div className={styles.kpiCard}>
                  <p className={styles.kpiLabel}>{t.settings.last30dTokens}</p>
                  <p className={styles.kpiValue}>{kpis.last30dTokens}</p>
                </div>
                <div className={styles.kpiCard}>
                  <p className={styles.kpiLabel}>{t.settings.last30dSpent}</p>
                  <p className={styles.kpiValue}>{kpis.last30dSpent}</p>
                </div>
              </div>
            )}
          </>
        )}

        {tab === 'usage' && (
          <>
            <h2 className={styles.sectionTitle}>{t.settings.usageSummaryTitle}</h2>
            {usageSummary && (
              <>
                <p className={styles.muted}>
                  {t.settings.tokens}: <span className={styles.mono}>{usageSummary.total_tokens}</span> · {t.settings.cost}:{' '}
                  <span className={styles.mono}>{formatMoney(usageSummary.total_cost_cents, billingMe?.currency ?? 'USD')}</span>
                </p>
                <div className={styles.row}>
                  <div style={{ flex: 1, minWidth: 320 }}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>{t.settings.model}</th>
                          <th className={styles.right}>{t.settings.tokens}</th>
                          <th className={styles.right}>{t.settings.cost}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usageSummary.by_model.map((m) => (
                          <tr key={m.model}>
                            <td className={styles.mono}>{m.model}</td>
                            <td className={`${styles.right} ${styles.mono}`}>{m.total_tokens}</td>
                            <td className={`${styles.right} ${styles.mono}`}>{formatMoney(m.cost_cents, billingMe?.currency ?? 'USD')}</td>
                          </tr>
                        ))}
                        {!usageSummary.by_model.length && (
                          <tr>
                            <td colSpan={3} className={styles.muted}>{t.common.loading}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div style={{ flex: 1, minWidth: 320 }}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>{t.settings.day}</th>
                          <th className={styles.right}>{t.settings.tokens}</th>
                          <th className={styles.right}>{t.settings.cost}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usageSummary.by_day.slice(-14).map((d) => (
                          <tr key={d.day}>
                            <td className={styles.mono}>{d.day}</td>
                            <td className={`${styles.right} ${styles.mono}`}>{d.total_tokens}</td>
                            <td className={`${styles.right} ${styles.mono}`}>{formatMoney(d.cost_cents, billingMe?.currency ?? 'USD')}</td>
                          </tr>
                        ))}
                        {!usageSummary.by_day.length && (
                          <tr>
                            <td colSpan={3} className={styles.muted}>{t.common.loading}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}

            <h2 className={styles.sectionTitle}>{t.settings.recentUsageEventsTitle}</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{t.settings.model}</th>
                  <th>{t.settings.type}</th>
                  <th className={styles.right}>{t.settings.tokens}</th>
                  <th className={styles.right}>{t.settings.cost}</th>
                  <th className={styles.right}>ms</th>
                  <th>{t.settings.time}</th>
                </tr>
              </thead>
              <tbody>
                {usageEvents.map((e) => (
                  <tr key={e.id}>
                    <td className={styles.mono}>{e.id}</td>
                    <td className={styles.mono}>{e.model}</td>
                    <td className={styles.mono}>{e.request_type}</td>
                    <td className={`${styles.right} ${styles.mono}`}>{e.total_tokens}</td>
                    <td className={`${styles.right} ${styles.mono}`}>{formatMoney(e.cost_cents, billingMe?.currency ?? 'USD')}</td>
                    <td className={`${styles.right} ${styles.mono}`}>{e.latency_ms}</td>
                    <td className={`${styles.small} ${styles.mono}`}>{new Date(e.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {!usageEvents.length && (
                  <tr>
                    <td colSpan={7} className={styles.muted}>{t.common.loading}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </>
        )}

        {tab === 'billing' && (
          <>
            <h2 className={styles.sectionTitle}>{t.settings.billingLedgerTitle}</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{t.settings.type}</th>
                  <th className={styles.right}>{t.settings.amount}</th>
                  <th>{t.settings.reason}</th>
                  <th>{t.settings.time}</th>
                </tr>
              </thead>
              <tbody>
                {ledger.map((e) => (
                  <tr key={e.id}>
                    <td className={styles.mono}>{e.id}</td>
                    <td className={styles.mono}>{e.type}</td>
                    <td className={`${styles.right} ${styles.mono}`}>{formatMoney(e.amount_cents, billingMe?.currency ?? 'USD')}</td>
                    <td className={styles.mono}>{e.reason}</td>
                    <td className={`${styles.small} ${styles.mono}`}>{new Date(e.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {!ledger.length && (
                  <tr>
                    <td colSpan={5} className={styles.muted}>{t.common.loading}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  )
}
