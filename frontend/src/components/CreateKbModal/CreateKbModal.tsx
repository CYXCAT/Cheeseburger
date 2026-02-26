import React, { useState } from 'react'
import { useI18n } from '../../i18n'
import { kbApi } from '../../api'
import styles from './CreateKbModal.module.css'

interface CreateKbModalProps {
  onClose: () => void
  onSuccess: () => void
}

export function CreateKbModal({ onClose, onSuccess }: CreateKbModalProps) {
  const { t } = useI18n()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      setError(t.common.nameRequired)
      return
    }
    setError(null)
    setLoading(true)
    try {
      await kbApi.create(trimmed, description.trim() || null)
      onSuccess()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : t.common.errorGeneric)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="create-kb-title">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 id="create-kb-title" className={styles.title}>{t.nav.createKb}</h2>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div>
            <label className={styles.label} htmlFor="kb-name">{t.manage.nameLabel}</label>
            <input
              id="kb-name"
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t.manage.nameLabel}
              autoFocus
              disabled={loading}
            />
          </div>
          <div>
            <label className={styles.label} htmlFor="kb-desc">{t.manage.descLabel}</label>
            <textarea
              id="kb-desc"
              className={styles.textarea}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t.manage.descLabel}
              disabled={loading}
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          <div className={styles.actions}>
            <button type="button" className={styles.btn} onClick={onClose} disabled={loading}>
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
