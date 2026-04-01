import React, { useState, useRef, useEffect } from 'react'
import { useI18n } from '../../i18n'
import type { ExecutionStepTrace } from '../../api/types'
import type { HighlightRegion } from '../DocumentPanel'
import styles from './ChatPanel.module.css'

export interface Citation {
  id: string
  text: string
  /** 用于跳转定位到文档 */
  region: HighlightRegion
  sourceLabel?: string
}

export interface ToolCallDisplay {
  name?: string
  arguments?: string
}

export interface CodeResultDisplay {
  code?: string
  language?: string
  exit_code?: number
  result?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  tool_calls?: ToolCallDisplay[] | null
  citation_chunks?: Array<{ chunk_text: string; source_id?: string | null; source_type?: string | null; metadata?: Record<string, unknown> }> | null
  intent?: 'kb' | 'code' | 'html' | 'multi'
  code_result?: CodeResultDisplay | null
  html_content?: string | null
  plan_summary?: string | null
  execution_trace?: ExecutionStepTrace[] | null
}

interface ChatPanelProps {
  messages: Message[]
  onSend: (content: string) => void
  /** 点击引用时跳转到文档对应位置 */
  onCitationClick?: (region: HighlightRegion) => void
  loading?: boolean
}

export function ChatPanel({
  messages,
  onSend,
  onCitationClick,
  loading = false,
}: ChatPanelProps) {
  const { t } = useI18n()
  const [input, setInput] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed) return
    onSend(trimmed)
    setInput('')
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.messages} ref={listRef}>
        {messages.length === 0 && (
          <div className={styles.placeholder}>{t.chat.placeholder}</div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={styles.message}
            data-role={msg.role}
          >
            <div className={styles.bubble}>
              {msg.role === 'assistant' && (msg.plan_summary || (msg.execution_trace && msg.execution_trace.length > 0)) && (
                <details className={styles.orchestration}>
                  <summary className={styles.orchestrationSummary}>{t.chat.executionTrace}</summary>
                  {msg.plan_summary ? (
                    <p className={styles.planSummaryText}>
                      <span className={styles.traceMeta}>{t.chat.planSummary}: </span>
                      {msg.plan_summary}
                    </p>
                  ) : null}
                  {msg.execution_trace && msg.execution_trace.length > 0 ? (
                    <ul className={styles.traceList}>
                      {msg.execution_trace.map((tr, ti) => (
                        <li key={`${tr.step_id}-${ti}`} className={styles.traceStep} data-status={tr.status}>
                          <span className={styles.traceMeta}>
                            {t.chat.stepKind} {tr.kind} · #{tr.step_id}
                          </span>
                          <span className={styles.traceStatus}> · {tr.status}</span>
                          {tr.summary ? <div>{tr.summary}</div> : null}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </details>
              )}
              {msg.role === 'assistant' && msg.tool_calls && msg.tool_calls.length > 0 && (
                <div className={styles.toolCalls}>
                  <span className={styles.toolCallsLabel}>{t.chat.toolCallsLabel}</span>
                  {msg.tool_calls.map((tc, i) => {
                    let argsPreview = ''
                    try {
                      const args = typeof tc.arguments === 'string' ? JSON.parse(tc.arguments) : tc.arguments
                      if (args && typeof args.query === 'string') argsPreview = args.query
                    } catch {
                      argsPreview = typeof tc.arguments === 'string' ? tc.arguments.slice(0, 80) : ''
                    }
                    return (
                      <div key={i} className={styles.toolCallItem}>
                        <span className={styles.toolCallName}>{tc.name ?? '—'}</span>
                        {argsPreview && <span className={styles.toolCallArgs}>查询: {argsPreview}</span>}
                      </div>
                    )
                  })}
                </div>
              )}
              <div className={styles.content}>{msg.content}</div>
              {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                <div className={styles.citations}>
                  <span className={styles.citationsLabel}>{t.chat.source}</span>
                  {msg.citations.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      className={styles.citation}
                      onClick={() => onCitationClick?.(c.region)}
                    >
                      {c.sourceLabel ?? c.text}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className={styles.message} data-role="assistant">
            <div className={styles.bubble}>
              <span className={styles.thinking}>{t.chat.thinking}</span>
            </div>
          </div>
        )}
      </div>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder={t.chat.placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          aria-label={t.chat.placeholder}
        />
        <button type="submit" className={styles.send} aria-label={t.chat.send}>
          {t.chat.send}
        </button>
      </form>
    </div>
  )
}
