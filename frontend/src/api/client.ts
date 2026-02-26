import type {
  KnowledgeBase,
  KBVersion,
  DocumentUploadResponse,
  DocumentOut,
  PineconeStats,
  SearchResponse,
  ChatMessage,
  ChatResponse,
  ToolInfo,
  ConversationOut,
  HistoryMessageOut,
} from './types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || ''

function getUserId(): string {
  return localStorage.getItem('doc_user_id') || 'anonymous'
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: object
  formData?: FormData
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, formData, ...rest } = options
  const headers = new Headers(rest.headers as HeadersInit)
  headers.set('X-User-Id', getUserId())
  if (!formData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const init: RequestInit = {
    ...rest,
    headers,
  }
  if (formData) {
    init.body = formData
    headers.delete('Content-Type')
  } else if (body) {
    init.body = JSON.stringify(body)
  }
  const res = await fetch(`${BASE_URL}${path}`, init)
  if (res.status === 204) return undefined as T
  const text = await res.text()
  if (!res.ok) {
    let detail = text
    try {
      const j = JSON.parse(text)
      detail = (j as { detail?: string }).detail ?? text
    } catch {
      //
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }
  if (!text) return undefined as T
  return JSON.parse(text) as T
}

/** 知识库 */
export const kbApi = {
  list: () => request<KnowledgeBase[]>('/api/knowledge-bases', { method: 'GET' }),
  get: (id: number) => request<KnowledgeBase>(`/api/knowledge-bases/${id}`, { method: 'GET' }),
  create: (name: string, description?: string | null) =>
    request<KnowledgeBase>('/api/knowledge-bases', { method: 'POST', body: { name, description } }),
  update: (id: number, data: { name?: string; description?: string | null }) =>
    request<KnowledgeBase>(`/api/knowledge-bases/${id}`, { method: 'PATCH', body: data }),
  delete: (id: number) =>
    request<void>(`/api/knowledge-bases/${id}`, { method: 'DELETE' }),
  versions: (id: number) =>
    request<KBVersion[]>(`/api/knowledge-bases/${id}/versions`, { method: 'GET' }),
}

/** 文档上传与检索 */
export const docsApi = {
  uploadPdf: (kbId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<DocumentUploadResponse>(
      `/api/knowledge-bases/${kbId}/documents/upload-pdf`,
      { method: 'POST', formData: form }
    )
  },
  uploadUrl: (kbId: number, url: string) => {
    const form = new FormData()
    form.append('url', url.trim())
    return request<DocumentUploadResponse>(
      `/api/knowledge-bases/${kbId}/documents/upload-url`,
      { method: 'POST', formData: form }
    )
  },
  uploadText: (kbId: number, text: string) => {
    const form = new FormData()
    form.append('text', text)
    return request<DocumentUploadResponse>(
      `/api/knowledge-bases/${kbId}/documents/upload-text`,
      { method: 'POST', formData: form }
    )
  },
  listDocuments: (kbId: number) =>
    request<DocumentOut[]>(`/api/knowledge-bases/${kbId}/documents`, { method: 'GET' }),
  getPineconeStats: (kbId: number) =>
    request<PineconeStats>(`/api/knowledge-bases/${kbId}/documents/pinecone-stats`, { method: 'GET' }),
  deleteDocument: (kbId: number, sourceId: string) =>
    request<void>(`/api/knowledge-bases/${kbId}/documents/${encodeURIComponent(sourceId)}`, { method: 'DELETE' }),
  search: (kbId: number, query: string, searchType: 'semantic' | 'keyword' | 'hybrid' = 'semantic', topK = 10) =>
    request<SearchResponse>(`/api/knowledge-bases/${kbId}/search`, {
      method: 'POST',
      body: { query, search_type: searchType, top_k: topK },
    }),
}

/** 对话与工具 */
export const chatApi = {
  chat: (kbId: number, messages: ChatMessage[]) =>
    request<ChatResponse>('/api/chat', { method: 'POST', body: { kb_id: kbId, messages } }),
  tools: () => request<{ tools: ToolInfo[] }>('/api/chat/tools', { method: 'GET' }),
}

/** 对话历史（按知识库） */
export const chatHistoryApi = {
  listConversations: (kbId: number) =>
    request<ConversationOut[]>(`/api/knowledge-bases/${kbId}/chat/conversations`, { method: 'GET' }),
  createConversation: (kbId: number, title?: string | null) =>
    request<ConversationOut>(`/api/knowledge-bases/${kbId}/chat/conversations`, {
      method: 'POST',
      body: { title: title ?? null },
    }),
  getMessages: (kbId: number, conversationId: number) =>
    request<HistoryMessageOut[]>(
      `/api/knowledge-bases/${kbId}/chat/conversations/${conversationId}/messages`,
      { method: 'GET' }
    ),
  appendMessages: (
    kbId: number,
    conversationId: number,
    messages: Array<{ role: string; content: string; tool_calls?: Array<{ name?: string; arguments?: string }> | null }>
  ) =>
    request<{ ok: boolean }>(
      `/api/knowledge-bases/${kbId}/chat/conversations/${conversationId}/messages`,
      { method: 'POST', body: { messages } }
    ),
  deleteConversation: (kbId: number, conversationId: number) =>
    request<{ ok: boolean }>(
      `/api/knowledge-bases/${kbId}/chat/conversations/${conversationId}`,
      { method: 'DELETE' }
    ),
}
