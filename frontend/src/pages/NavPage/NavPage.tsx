import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { LangSwitch } from '../../components/LangSwitch'
import { Card, CardTitle, CardDescription } from '../../components/Card'
import { CreateKbModal } from '../../components/CreateKbModal'
import { kbApi } from '../../api'
import type { KnowledgeBase } from '../../api'
import styles from './NavPage.module.css'

export function NavPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)

  const loadKbs = () => {
    setLoading(true)
    kbApi.list().then(setKbs).catch(() => setKbs([])).finally(() => setLoading(false))
  }

  useEffect(() => { loadKbs() }, [])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <LangSwitch />
      </header>
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>{t.nav.title}</h1>
        <p className={styles.heroSubtitle}>{t.nav.subtitle}</p>
        <button
          type="button"
          className={styles.createBtn}
          onClick={() => setCreateOpen(true)}
        >
          {t.nav.createKb}
        </button>
      </div>
      <section className={styles.section} aria-label={t.nav.selectKb}>
        <h2 className={styles.sectionTitle}>{t.nav.selectKb}</h2>
        {loading && <p className={styles.muted}>{t.common.loading}</p>}
        <div className={styles.grid}>
          {!loading && kbs.map((kb) => (
            <Card key={kb.id} as="article" className={styles.kbCard}>
              <div
                className={styles.cardContent}
                onClick={() => navigate(`/kb/${kb.id}`)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    navigate(`/kb/${kb.id}`)
                  }
                }}
                tabIndex={0}
                role="button"
              >
                <CardTitle>{kb.name}</CardTitle>
                <CardDescription>{kb.description || '—'}</CardDescription>
              </div>
              <button
                type="button"
                className={styles.manageBtn}
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/kb/${kb.id}/manage`)
                }}
              >
                {t.nav.manage}
              </button>
            </Card>
          ))}
        </div>
      </section>
      {createOpen && (
        <CreateKbModal onClose={() => setCreateOpen(false)} onSuccess={loadKbs} />
      )}
    </div>
  )
}
