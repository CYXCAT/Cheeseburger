/** 与后端 REST 响应对齐 */

export interface UserOut {
  id: number
  username: string
  is_admin?: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserOut
}

export interface KnowledgeBase {
  id: number
  user_id: string
  name: string
  description: string | null
  current_version_id: number | null
  created_at: string
}

export interface KBVersion {
  id: number
  kb_id: number
  version_number: number
  status: string
  source_type: string | null
  created_at: string
}

export interface DocumentUploadResponse {
  kb_id: number
  source_id: string
  source_type: string
  chunks_count: number
}

export interface DocumentOut {
  id: number
  kb_id: number
  source_id: string
  source_type: string
  chunks_count: number
  created_at: string
}

export interface PineconeStats {
  namespace: string
  record_count: number
  note?: string
  error?: string
}

export interface SearchResult {
  id: string | null
  score: number | null
  chunk_text: string | null
  metadata: Record<string, unknown> | null
}

export interface SearchResponse {
  results: SearchResult[]
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface CitationChunk {
  chunk_text: string
  source_id?: string | null
  source_type?: string | null
  metadata?: Record<string, unknown>
}

export interface ChatResponse {
  message: ChatMessage
  tool_calls: Array<{ name?: string; arguments?: string }> | null
  citation_chunks?: CitationChunk[] | null
}

export interface ToolInfo {
  name: string
  description: string
}

export interface ConversationOut {
  id: number
  kb_id: number
  title: string | null
  created_at: string
  updated_at: string
}

export interface HistoryMessageOut {
  id: string
  role: string
  content: string
  tool_calls?: Array<{ name?: string; arguments?: string }> | null
}

export interface BillingMe {
  user_id: number
  currency: string
  balance_cents: number
  last_30d_usage_tokens: number
  last_30d_spent_cents: number
}

export interface LedgerEntry {
  id: number
  type: string
  amount_cents: number
  reason: string
  ref_type?: string | null
  ref_id?: number | null
  created_at: string
}

export interface UsageDay {
  day: string
  total_tokens: number
  cost_cents: number
}

export interface UsageModel {
  model: string
  total_tokens: number
  cost_cents: number
}

export interface UsageSummary {
  from_ts: string
  to_ts: string
  total_tokens: number
  total_cost_cents: number
  by_day: UsageDay[]
  by_model: UsageModel[]
}

export interface UsageEvent {
  id: number
  kb_id?: number | null
  model: string
  request_type: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_cents: number
  latency_ms: number
  created_at: string
}

export interface AdminUserRow {
  user_id: number
  username: string
  created_at: string
  last_login_at: string | null
  request_count: number
  total_tokens: number
  balance_cents: number
  currency: string
}
