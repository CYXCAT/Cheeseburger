//
//  KbChatView.swift
//  cheeseburger
//

import SwiftUI

struct KbChatView: View {
    let kb: KnowledgeBase
    @EnvironmentObject var auth: AuthService
    @Environment(\.dismiss) private var dismiss
    @StateObject private var chat = ChatViewModel()
    @State private var sidebarOpen = false

    var body: some View {
        ZStack(alignment: .leading) {
            mainContent
            ChatSidebarView(
                isPresented: sidebarOpen,
                onDismiss: { sidebarOpen = false },
                conversations: chat.conversations,
                selectedConversationId: chat.selectedConversationId,
                userName: auth.user?.username ?? "",
                onNewChat: {
                    Task { await chat.createNewChat() }
                },
                onSelectConversation: { id in
                    Task { await chat.selectConversation(id: id) }
                },
                onDeleteConversation: { id in
                    Task { await chat.deleteConversation(id: id) }
                },
                onSettings: {},
                onLogout: { auth.logout() }
            )
        }
        .background(AppTheme.bg)
        .navigationBarBackButtonHidden(true)
        .toolbar(.hidden, for: .navigationBar)
        .task {
            chat.kbId = kb.id
            await chat.loadConversations()
        }
    }

    private var mainContent: some View {
        VStack(spacing: 0) {
            header
            Divider().background(AppTheme.border)
            chatContent
        }
        .background(AppTheme.bg)
    }

    private var header: some View {
        HStack(spacing: 12) {
            Button {
                sidebarOpen = true
            } label: {
                Image(systemName: "line.3.horizontal")
                    .font(.body.weight(.medium))
                    .foregroundColor(AppTheme.accentStrong)
            }
            Button {
                dismiss()
            } label: {
                Image(systemName: "chevron.left")
                    .font(.body.weight(.medium))
                    .foregroundColor(AppTheme.accentStrong)
            }
            Text(kb.name)
                .font(.headline)
                .foregroundColor(AppTheme.text)
                .lineLimit(1)
            Spacer()
            NavigationLink(value: KbDetailRoute.manage(kb)) {
                Text(L10n.Nav.manage)
                    .font(.subheadline)
                    .foregroundColor(AppTheme.accentStrong)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(AppTheme.surface)
    }

    @ViewBuilder
    private var chatContent: some View {
        if let _ = chat.selectedConversationId {
            messagesList
        } else {
            messagesList
        }
    }

    private var messagesList: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(chat.messages) { msg in
                            ChatBubbleView(message: msg)
                                .id(msg.id)
                        }
                        if chat.isLoading {
                            HStack {
                                ProgressView()
                                Text(L10n.Chat.thinking)
                                    .font(.subheadline)
                                    .foregroundColor(AppTheme.textMuted)
                            }
                            .padding(12)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding(16)
                }
                .onChange(of: chat.messages.count) { _, _ in
                    if let last = chat.messages.last {
                        withAnimation(.easeOut(duration: 0.2)) {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
            }

            Divider().background(AppTheme.border)
            chatInputBar
        }
    }

    private var chatInputBar: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField(L10n.Chat.placeholder, text: $chat.inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .lineLimit(1...5)
                .background(AppTheme.surface)
                .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusMd).stroke(AppTheme.border, lineWidth: 1))
                .cornerRadius(AppTheme.radiusMd)

            Button {
                sendMessage()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundColor(chat.inputText.trimmingCharacters(in: .whitespaces).isEmpty ? AppTheme.textMuted : AppTheme.accentStrong)
            }
            .disabled(chat.inputText.trimmingCharacters(in: .whitespaces).isEmpty || chat.isLoading)
        }
        .padding(12)
        .background(AppTheme.surface)
    }

    private func sendMessage() {
        let text = chat.inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        chat.sendMessage(content: text)
    }
}

struct ChatBubbleView: View {
    let message: ChatMessageItem

    var body: some View {
        HStack(alignment: .top, spacing: 0) {
            if message.role == "user" { Spacer(minLength: 48) }
            VStack(alignment: message.role == "user" ? .trailing : .leading, spacing: 6) {
                if message.role == "assistant", let tools = message.toolCalls, !tools.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(L10n.Chat.toolCallsLabel)
                            .font(.caption)
                            .foregroundColor(AppTheme.textMuted)
                        ForEach(Array(tools.enumerated()), id: \.offset) { _, tc in
                            HStack(alignment: .top, spacing: 4) {
                                Text(tc.name ?? "—")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                if let args = tc.arguments, !args.isEmpty {
                                    Text(args)
                                        .font(.caption2)
                                        .foregroundColor(AppTheme.textMuted)
                                        .lineLimit(2)
                                }
                            }
                        }
                    }
                    .padding(8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(AppTheme.surface)
                    .cornerRadius(AppTheme.radiusSm)
                }
                Text(message.content)
                    .font(.body)
                    .foregroundColor(AppTheme.text)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: message.role == "user" ? .trailing : .leading)
            }
            .padding(12)
            .background(message.role == "user" ? AppTheme.accent : AppTheme.surface)
            .cornerRadius(AppTheme.radiusMd)
            .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusMd).stroke(AppTheme.border, lineWidth: message.role == "assistant" ? 1 : 0))
            if message.role == "assistant" { Spacer(minLength: 48) }
        }
    }
}
