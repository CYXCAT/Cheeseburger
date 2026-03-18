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
  AuthResponse,
  UserOut,
  AdminUserRow,
  BillingMe,
  LedgerEntry,
  UsageSummary,
  UsageEvent,
} from './types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || ''

const AUTH_TOKEN_KEY = 'doc_access_token'

function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export function setAuthToken(token: string | null): void {
  if (token == null) localStorage.removeItem(AUTH_TOKEN_KEY)
  else localStorage.setItem(AUTH_TOKEN_KEY, token)
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: object
  formData?: FormData
  /** 为 true 时不带 Authorization（用于登录/注册） */
  skipAuth?: boolean
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, formData, skipAuth, ...rest } = options
  const headers = new Headers(rest.headers as HeadersInit)
  const token = getAuthToken()
  if (!skipAuth && token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
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
    if (res.status === 401) setAuthToken(null)
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

/** 认证 */
export const authApi = {
  register: (inviteToken: string, username: string, password: string) =>
    request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: { invite_token: inviteToken, username, password },
      skipAuth: true,
    }),
  login: (username: string, password: string) =>
    request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: { username, password },
      skipAuth: true,
    }),
}

/** 当前用户 */
export const userApi = {
  getMe: () => request<UserOut>('/api/users/me', { method: 'GET' }),
  updateMe: (data: { username?: string; password?: string }) =>
    request<UserOut>('/api/users/me', { method: 'PATCH', body: data }),
}

/** Billing（预付费钱包） */
export const billingApi = {
  me: () => request<BillingMe>('/api/billing/me', { method: 'GET' }),
  ledger: (limit = 50, offset = 0) =>
    request<LedgerEntry[]>(`/api/billing/ledger?limit=${limit}&offset=${offset}`, { method: 'GET' }),
  /** 管理员为指定用户充值 */
  topup: (userId: number, amountCents: number, reason = 'topup_manual') =>
    request<{ ok: boolean; user_id: number; new_balance_cents: number }>('/api/billing/topup', {
      method: 'POST',
      body: { user_id: userId, amount_cents: amountCents, reason },
    }),
}

/** 管理员 */
export const adminApi = {
  listUsers: () => request<AdminUserRow[]>('/api/admin/users', { method: 'GET' }),
}

/** Usage（用量统计） */
export const usageApi = {
  summary: (days = 30) => request<UsageSummary>(`/api/usage/summary?days=${days}`, { method: 'GET' }),
  events: (limit = 50, offset = 0) =>
    request<UsageEvent[]>(`/api/usage/events?limit=${limit}&offset=${offset}`, { method: 'GET' }),
}
