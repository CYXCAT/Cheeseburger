import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useI18n } from '../../i18n'
import { LangSwitch } from '../../components/LangSwitch'
import { DocumentPanel } from '../../components/DocumentPanel'
import type { DocSource, HighlightRegion } from '../../components/DocumentPanel'
import { ChatPanel } from '../../components/ChatPanel'
import type { Message } from '../../components/ChatPanel'
import { useKbChat } from '../../contexts/KbChatContext'
import { kbApi, chatApi, docsApi } from '../../api'
import type { KnowledgeBase, SearchResult } from '../../api'
import styles from './KbPage.module.css'

const defaultDocSource: DocSource = {
  type: 'web',
  html: '<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{font-family:system-ui;padding:1.5rem;line-height:1.6;} h1{color:#2c2c2c;} .page{padding:1rem 0;border-bottom:1px solid #eae6df;}</style></head><body><h1>检索与预览</h1><p>在下方输入关键词进行语义/关键词/混合检索，或直接与右侧对话（对话将自动调用知识库检索）。</p></body></html>',
}

export function KbPage() {
  const { kbId } = useParams<{ kbId: string }>()
  const navigate = useNavigate()
  const { t } = useI18n()
  const id = kbId ? parseInt(kbId, 10) : NaN
  const chat = useKbChat()
  const [kb, setKb] = useState<KnowledgeBase | null>(null)
  const [docSource, setDocSource] = useState<DocSource>(defaultDocSource)
  const [currentPage, setCurrentPage] = useState(1)
  const [highlight, setHighlight] = useState<HighlightRegion | null>(null)
  const [sendLoading, setSendLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])

  const messages = chat?.messages ?? []
  const setMessages = chat?.setMessages ?? (() => {})
  const loading = (chat?.loading ?? false) || sendLoading

  useEffect(() => {
    if (Number.isNaN(id)) return
    kbApi.get(id).then(setKb).catch(() => setKb(null))
  }, [id])

  const handleSend = useCallback(async (content: string) => {
    if (Number.isNaN(id) || !chat) return
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content,
    }
    setMessages((prev) => [...prev, userMsg])
    setSendLoading(true)
    try {
      const history: Message[] = [...messages, userMsg]
      const chatMessages = history.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
      const res = await chatApi.chat(id, chatMessages)
      const reply: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: res.message.content,
        tool_calls: res.tool_calls ?? undefined,
      }
      setMessages((prev) => [...prev, reply])
      let convId = chat.currentConversationId
      if (convId == null) convId = await chat.createNewChat() ?? null
      if (convId != null) await chat.appendToCurrent(convId, userMsg, reply)
    } catch (err) {
      const reply: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: err instanceof Error ? err.message : '请求失败',
      }
      setMessages((prev) => [...prev, reply])
    } finally {
      setSendLoading(false)
    }
  }, [id, messages, chat])

  const handleSearch = useCallback(async () => {
    const q = searchQuery.trim()
    if (!q || Number.isNaN(id)) return
    setSearchLoading(true)
    try {
      const res = await docsApi.search(id, q, 'semantic', 10)
      setSearchResults(res.results)
      const html = res.results.length
        ? `<body style="font-family:system-ui;padding:1rem;line-height:1.6"><h2>检索结果</h2>${res.results.map((r, i) => `<div class="page" id="p${i + 1}"><p><strong>${(r.score ?? 0).toFixed(2)}</strong> ${escapeHtml(r.chunk_text || '')}</p></div>`).join('')}</body>`
        : '<body style="padding:1rem"><p>无匹配结果。</p></body>'
      setDocSource({ type: 'web', html: `<!DOCTYPE html><html><head><meta charset="utf-8"></head>${html}</html>` })
    } catch {
      setSearchResults([])
      setDocSource(defaultDocSource)
    } finally {
      setSearchLoading(false)
    }
  }, [id, searchQuery])

  const handleCitationClick = useCallback((region: HighlightRegion) => {
    setHighlight(region)
    if (region.pageNumber) setCurrentPage(region.pageNumber)
  }, [])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <button type="button" className={styles.back} onClick={() => navigate('/')}>
          {t.common.back}
        </button>
        <span className={styles.title}>{kb ? kb.name : `KB ${kbId ?? '—'}`}</span>
        <LangSwitch />
      </header>

      <div className={styles.layout}>
        <div className={styles.docCol}>
          <div className={styles.searchBar}>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="检索知识库…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button type="button" className={styles.searchBtn} onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? t.common.loading : '检索'}
            </button>
          </div>
          <DocumentPanel
            source={docSource}
            highlight={highlight}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        </div>
        <div className={styles.chatCol}>
          <ChatPanel
            messages={messages}
            onSend={handleSend}
            onCitationClick={handleCitationClick}
            loading={loading}
          />
        </div>
      </div>
    </div>
  )
}

function escapeHtml(s: string): string {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}
