import { useState, useEffect, useCallback } from 'react'
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

/** 根据 Agent 检索返回的 citation_chunks 生成左侧预览 HTML，并对片段高亮。 */
function buildCitationDocSource(
  chunks: Array<{ chunk_text: string; source_id?: string | null; source_type?: string | null }>
): DocSource {
  if (!chunks.length) return defaultDocSource
  const style = `
    body { font-family: system-ui; padding: 1rem 1.5rem; line-height: 1.6; }
    .cite-block { padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 6px; border-left: 3px solid #e0e0e0; background: #fafafa; }
    .cite-block.highlight { background: #fff8e6; border-left-color: #d4a012; }
    .cite-meta { font-size: 0.75rem; color: #666; margin-bottom: 0.35rem; }
  `
  const body = chunks
    .map((c, i) => {
      const meta = [c.source_type, c.source_id].filter(Boolean).join(' · ') || '检索片段'
      const cls = i === 0 ? 'cite-block highlight' : 'cite-block'
      return `<div id="cite-${i}" class="${cls}"><span class="cite-meta">${escapeHtml(meta)}</span><p>${escapeHtml(c.chunk_text)}</p></div>`
    })
    .join('')
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${style}</style></head><body><h2>引用片段</h2>${body}</body></html>`
  return { type: 'web', html }
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
  const [_searchResults, setSearchResults] = useState<SearchResult[]>([])

  const messages = chat?.messages ?? []
  const setMessages = chat?.setMessages ?? (() => {})
  const loading = (chat?.loading ?? false) || sendLoading

  // 当最后一条 assistant 消息带有 citation_chunks 时，左侧展示检索片段并高亮第一段
  const lastCitationMessage = messages.slice().reverse().find((m) => m.role === 'assistant' && m.citation_chunks?.length)
  useEffect(() => {
    if (lastCitationMessage?.citation_chunks?.length) {
      setDocSource(buildCitationDocSource(lastCitationMessage.citation_chunks))
      setHighlight({ selector: '#cite-0' })
    }
  }, [lastCitationMessage?.id, lastCitationMessage?.citation_chunks?.length])

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
        citation_chunks: res.citation_chunks ?? undefined,
      }
      setMessages((prev) => [...prev, reply])
      let convId = chat.currentConversationId
      if (convId == null) convId = await chat.createNewChat(false) ?? null
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
