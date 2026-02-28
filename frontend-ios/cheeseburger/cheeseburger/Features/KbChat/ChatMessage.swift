//
//  ChatMessage.swift
//  cheeseburger
//

import Foundation

struct ChatMessageItem: Identifiable {
    let id: String
    let role: String // "user" | "assistant"
    let content: String
    var toolCalls: [ToolCallPayload]?
    var citationChunks: [CitationChunk]?
}
