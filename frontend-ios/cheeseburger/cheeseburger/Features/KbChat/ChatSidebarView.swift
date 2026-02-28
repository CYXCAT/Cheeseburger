//
//  ChatSidebarView.swift
//  cheeseburger
//
//  ChatGPT 风格侧边栏：历史记录 + 用户信息，点击空白收起
//

import SwiftUI

struct ChatSidebarView: View {
    var isPresented: Bool
    var onDismiss: () -> Void
    var conversations: [ConversationOut]
    var selectedConversationId: Int?
    var userName: String
    var onNewChat: () -> Void
    var onSelectConversation: (Int) -> Void
    var onDeleteConversation: (Int) -> Void
    var onSettings: () -> Void
    var onLogout: () -> Void

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    private var sidebarWidth: CGFloat {
        horizontalSizeClass == .regular ? 320 : 280
    }

    var body: some View {
        ZStack(alignment: .leading) {
            if isPresented {
                Color.black.opacity(0.35)
                    .ignoresSafeArea()
                    .onTapGesture(perform: onDismiss)
                    .accessibilityLabel("关闭侧边栏")

                HStack(spacing: 0) {
                    sidebarContent
                        .frame(width: sidebarWidth, alignment: .leading)
                        .background(AppTheme.surface)
                    Spacer(minLength: 0)
                }
                .background(Color.clear)
            }
        }
        .animation(.easeInOut(duration: 0.25), value: isPresented)
    }

    private var sidebarContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            newChatButton
            historySection
            Spacer(minLength: 0)
            footer
        }
        .padding(.top, 8)
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "text.bubble.fill")
                .font(.title2)
                .foregroundColor(AppTheme.accentStrong)
            Text(L10n.Nav.title)
                .font(.headline)
                .foregroundColor(AppTheme.text)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
    }

    private var newChatButton: some View {
        Button(action: {
            onDismiss()
            onNewChat()
        }) {
            HStack(spacing: 10) {
                Image(systemName: "plus.circle.fill")
                    .font(.body)
                Text(L10n.Sidebar.newChat)
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
            .foregroundColor(AppTheme.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(AppTheme.bg)
            .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
            .cornerRadius(AppTheme.radiusSm)
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 20)
        .padding(.bottom, 16)
    }

    private var historySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(L10n.Sidebar.history)
                .font(.caption)
                .foregroundColor(AppTheme.textMuted)
                .padding(.horizontal, 20)

            ScrollView {
                LazyVStack(spacing: 0) {
                    ForEach(conversations) { conv in
                        ChatSidebarRow(
                            title: conv.title ?? L10n.Sidebar.newChat,
                            isSelected: selectedConversationId == conv.id,
                            onTap: {
                                onDismiss()
                                onSelectConversation(conv.id)
                            },
                            onDelete: { onDeleteConversation(conv.id) }
                        )
                    }
                }
            }
        }
    }

    private var footer: some View {
        VStack(alignment: .leading, spacing: 12) {
            Divider().background(AppTheme.border)

            HStack(spacing: 12) {
                Circle()
                    .fill(AppTheme.accent)
                    .frame(width: 36, height: 36)
                    .overlay(
                        Text(String(userName.prefix(1)).uppercased())
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundColor(AppTheme.text)
                    )
                Text(userName)
                    .font(.subheadline)
                    .foregroundColor(AppTheme.text)
                    .lineLimit(1)
                Spacer(minLength: 0)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 8)

            HStack(spacing: 16) {
                NavigationLink(value: MainRoute.settings) {
                    HStack(spacing: 6) {
                        Image(systemName: "gearshape")
                        Text(L10n.Sidebar.settings)
                    }
                    .font(.subheadline)
                    .foregroundColor(AppTheme.accentStrong)
                }
                .simultaneousGesture(TapGesture().onEnded(onDismiss))

                Button(action: {
                    onDismiss()
                    onLogout()
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                        Text(L10n.Auth.logout)
                    }
                    .font(.subheadline)
                    .foregroundColor(AppTheme.danger)
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 20)
        }
        .background(AppTheme.surface)
    }
}

struct ChatSidebarRow: View {
    let title: String
    let isSelected: Bool
    let onTap: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 0) {
            Button(action: onTap) {
                Text(title)
                    .font(.subheadline)
                    .foregroundColor(AppTheme.text)
                    .lineLimit(1)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
            }
            .buttonStyle(.plain)
            .background(isSelected ? AppTheme.highlight : Color.clear)

            Button(action: onDelete) {
                Image(systemName: "trash")
                    .font(.caption)
                    .foregroundColor(AppTheme.textMuted)
                    .padding(12)
            }
            .buttonStyle(.plain)
        }
        .background(isSelected ? AppTheme.highlight : Color.clear)
    }
}

#Preview {
    ChatSidebarView(
        isPresented: true,
        onDismiss: {},
        conversations: [],
        selectedConversationId: nil,
        userName: "User",
        onNewChat: {},
        onSelectConversation: { _ in },
        onDeleteConversation: { _ in },
        onSettings: {},
        onLogout: {}
    )
}
