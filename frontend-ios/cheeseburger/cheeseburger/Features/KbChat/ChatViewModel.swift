//
//  ChatViewModel.swift
//  cheeseburger
//

import Foundation
import Combine

final class ChatViewModel: ObservableObject {
    var kbId: Int = 0
    @Published var messages: [ChatMessageItem] = []
    @Published var inputText = ""
    @Published var isLoading = false
    @Published var conversations: [ConversationOut] = []
    @Published var selectedConversationId: Int?

    private let client = APIClient.shared

    func loadConversations() async {
        do {
            conversations = try await client.listConversations(kbId: kbId)
        } catch _ {
            conversations = []
        }
    }

    /// 切换并加载指定会话
    func selectConversation(id: Int) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let msgs = try await client.getMessages(kbId: kbId, conversationId: id)
            await MainActor.run {
                selectedConversationId = id
                messages = msgs.map { ChatMessageItem(
                    id: $0.id,
                    role: $0.role,
                    content: $0.content,
                    toolCalls: $0.tool_calls
                ) }
            }
        } catch _ {
            await MainActor.run { messages = [] }
        }
    }

    /// 新对话：清空消息并可选创建新会话
    func createNewChat() async {
        let conv = try? await client.createConversation(kbId: kbId, title: nil)
        await MainActor.run {
            selectedConversationId = conv?.id
            messages = []
        }
        await loadConversations()
    }

    /// 删除会话；若为当前会话则清空消息
    func deleteConversation(id: Int) async {
        try? await client.deleteConversation(kbId: kbId, conversationId: id)
        await MainActor.run {
            if selectedConversationId == id {
                selectedConversationId = nil
                messages = []
            }
        }
        await loadConversations()
    }

    func sendMessage(content: String) {
        let userMsg = ChatMessageItem(
            id: "u-\(Date.now.timeIntervalSince1970)",
            role: "user",
            content: content
        )
        messages.append(userMsg)
        inputText = ""
        isLoading = true

        Task {
            let history = messages.map { ["role": $0.role, "content": $0.content] }
            do {
                let res = try await client.chat(kbId: kbId, messages: history)
                let assistantMsg = ChatMessageItem(
                    id: "a-\(Date.now.timeIntervalSince1970)",
                    role: "assistant",
                    content: res.message.content,
                    toolCalls: res.tool_calls,
                    citationChunks: res.citation_chunks
                )
                await MainActor.run {
                    messages.append(assistantMsg)
                    isLoading = false
                }
                if let convId = selectedConversationId {
                    let payload = ChatMessagePayload(role: "user", content: content)
                    var toolCalls: [[String: Any]]? = res.tool_calls?.map { t in
                        var d: [String: Any] = [:]
                        if let n = t.name { d["name"] = n }
                        if let a = t.arguments { d["arguments"] = a }
                        return d
                    }
                    let assistantPayload = ChatMessagePayloadWithTools(
                        role: "assistant",
                        content: res.message.content,
                        tool_calls: toolCalls
                    )
                    try? await client.appendMessages(kbId: kbId, conversationId: convId, userMsg: payload, assistantMsg: assistantPayload)
                } else {
                    let conv = try? await client.createConversation(kbId: kbId, title: nil)
                    await MainActor.run { selectedConversationId = conv?.id }
                    if let convId = conv?.id {
                        let payload = ChatMessagePayload(role: "user", content: content)
                        var toolCalls: [[String: Any]]? = res.tool_calls?.map { t in
                            var d: [String: Any] = [:]
                            if let n = t.name { d["name"] = n }
                            if let a = t.arguments { d["arguments"] = a }
                            return d
                        }
                        let assistantPayload = ChatMessagePayloadWithTools(
                            role: "assistant",
                            content: res.message.content,
                            tool_calls: toolCalls
                        )
                        try? await client.appendMessages(kbId: kbId, conversationId: convId, userMsg: payload, assistantMsg: assistantPayload)
                    }
                }
            } catch let err {
                await MainActor.run {
                    messages.append(ChatMessageItem(
                        id: "a-\(Date.now.timeIntervalSince1970)",
                        role: "assistant",
                        content: (err as? APIError).flatMap { if case .httpStatus(_, let m) = $0 { return m } else { return nil } } ?? L10n.Common.errorGeneric
                    ))
                    isLoading = false
                }
            }
        }
    }
}
