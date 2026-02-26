import React, { createContext, useContext, useState, useCallback } from 'react'
import type { Locale, I18nDict } from './types'
import { zh } from './zh'
import { en } from './en'

const dicts: Record<Locale, I18nDict> = { zh, en }

type I18nContextValue = {
  locale: Locale
  setLocale: (l: Locale) => void
  t: I18nDict
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('zh')
  const setLocale = useCallback((l: Locale) => setLocaleState(l), [])
  const t = dicts[locale]
  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used within I18nProvider')
  return ctx
}
