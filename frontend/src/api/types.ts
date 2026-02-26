/** 与后端 REST 响应对齐 */

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
