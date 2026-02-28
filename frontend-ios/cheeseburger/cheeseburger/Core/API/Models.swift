//
//  Models.swift
//  cheeseburger
//
//  与后端 API 响应对齐 (frontend/src/api/types.ts)
//

import Foundation

// MARK: - Auth & User
struct UserOut: Codable {
    let id: Int
    let username: String
}

struct AuthResponse: Codable {
    let access_token: String
    let token_type: String
    let user: UserOut
}

// MARK: - Knowledge Base
struct KnowledgeBase: Codable, Identifiable, Hashable {
    let id: Int
    let user_id: String
    let name: String
    let description: String?
    let current_version_id: Int?
    let created_at: String

    func hash(into hasher: inout Hasher) { hasher.combine(id) }
    static func == (l: KnowledgeBase, r: KnowledgeBase) -> Bool { l.id == r.id }
}

struct KBVersion: Codable {
    let id: Int
    let kb_id: Int
    let version_number: Int
    let status: String
    let source_type: String?
    let created_at: String
}

// MARK: - Documents
struct DocumentUploadResponse: Codable {
    let kb_id: Int
    let source_id: String
    let source_type: String
    let chunks_count: Int
}

struct DocumentOut: Codable, Identifiable {
    let id: Int
    let kb_id: Int
    let source_id: String
    let source_type: String
    let chunks_count: Int
    let created_at: String
}

struct PineconeStats: Codable {
    let namespace: String
    let record_count: Int
    let note: String?
    let error: String?
}

struct SearchResult: Codable {
    let id: String?
    let score: Double?
    let chunk_text: String?
    let metadata: [String: AnyCodable]?
}

struct SearchResponse: Codable {
    let results: [SearchResult]
}

struct AnyCodable: Codable {}

// MARK: - Chat
struct ChatMessagePayload: Codable {
    let role: String
    let content: String
}

struct ChatResponse: Codable {
    let message: ChatMessagePayload
    let tool_calls: [ToolCallPayload]?
    let citation_chunks: [CitationChunk]?
}

struct ToolCallPayload: Codable {
    let name: String?
    let arguments: String?
}

struct CitationChunk: Codable {
    let chunk_text: String
    let source_id: String?
    let source_type: String?
    let metadata: [String: AnyCodable]?
}

struct ToolInfo: Codable {
    let name: String
    let description: String
}

// MARK: - Chat History
struct ConversationOut: Codable, Identifiable {
    let id: Int
    let kb_id: Int
    let title: String?
    let created_at: String
    let updated_at: String
}

struct HistoryMessageOut: Codable {
    let id: String
    let role: String
    let content: String
    let tool_calls: [ToolCallPayload]?
}

// MARK: - API Errors
struct APIErrorDetail: Codable {
    let detail: String?
}
