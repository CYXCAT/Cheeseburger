import React from 'react'
import { useI18n } from '../../i18n'
import type { Locale } from '../../i18n'
import styles from './LangSwitch.module.css'

export function LangSwitch() {
  const { locale, setLocale } = useI18n()
  return (
    <div className={styles.wrap} role="group" aria-label="Language">
      {(['zh', 'en'] as Locale[]).map((l) => (
        <button
          key={l}
          type="button"
          className={locale === l ? styles.active : styles.btn}
          onClick={() => setLocale(l)}
        >
          {l === 'zh' ? '中文' : 'EN'}
        </button>
      ))}
    </div>
  )
}
