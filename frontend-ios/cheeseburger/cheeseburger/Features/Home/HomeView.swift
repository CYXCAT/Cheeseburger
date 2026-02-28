//
//  HomeView.swift
//  cheeseburger
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var auth: AuthService
    @State private var kbs: [KnowledgeBase] = []
    @State private var loading = true
    @State private var showCreateSheet = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text(L10n.Nav.subtitle)
                        .font(.subheadline)
                        .foregroundColor(AppTheme.textMuted)
                        .padding(.horizontal)

                    Button {
                        showCreateSheet = true
                    } label: {
                        Text(L10n.Nav.createKb)
                            .fontWeight(.medium)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(AppTheme.accentStrong)
                            .foregroundColor(AppTheme.textInverse)
                            .cornerRadius(AppTheme.radiusSm)
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 8)

                    Text(L10n.Nav.selectKb)
                        .font(.headline)
                        .foregroundColor(AppTheme.text)
                        .padding(.horizontal)

                    if loading {
                        HStack {
                            ProgressView()
                            Text(L10n.Common.loading)
                                .foregroundColor(AppTheme.textMuted)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 32)
                    } else if kbs.isEmpty {
                        Text(L10n.Common.loading)
                            .foregroundColor(AppTheme.textMuted)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 32)
                    } else {
                        LazyVStack(spacing: 12) {
                            ForEach(kbs) { kb in
                                NavigationLink(value: KbDetailRoute.chat(kb)) {
                                    KbCard(kb: kb)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 20)
            }
            .background(AppTheme.surface)
            .navigationTitle(L10n.Nav.title)
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    NavigationLink(value: MainRoute.settings) {
                        Image(systemName: "gearshape")
                            .foregroundColor(AppTheme.text)
                    }
                    Menu {
                        Text(auth.user?.username ?? "")
                        Button(role: .destructive, action: logout) {
                            Text(L10n.Auth.logout)
                        }
                    } label: {
                        Image(systemName: "person.circle")
                            .foregroundColor(AppTheme.text)
                    }
                }
            }
            .navigationDestination(for: KnowledgeBase.self) { kb in
                KbChatView(kb: kb)
            }
            .navigationDestination(for: KbDetailRoute.self) { route in
                switch route {
                case .chat(let kb): KbChatView(kb: kb)
                case .manage(let kb): KbManageView(kb: kb)
                }
            }
            .navigationDestination(for: MainRoute.self) { route in
                switch route {
                case .settings: SettingsView()
                }
            }
            .sheet(isPresented: $showCreateSheet) {
                CreateKbSheet(onDismiss: {
                    showCreateSheet = false
                    loadKbs()
                }, onSuccess: {
                    showCreateSheet = false
                    loadKbs()
                })
            }
            .task { loadKbs() }
            .refreshable { await loadKbsAsync() }
        }
    }

    private func loadKbs() {
        Task { await loadKbsAsync() }
    }

    private func loadKbsAsync() async {
        loading = true
        defer { loading = false }
        do {
            kbs = try await APIClient.shared.listKnowledgeBases()
        } catch {
            kbs = []
        }
    }

    private func logout() {
        auth.logout()
    }
}

struct KbCard: View {
    let kb: KnowledgeBase

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(kb.name)
                    .font(.headline)
                    .foregroundColor(AppTheme.text)
                Text(kb.description ?? "—")
                    .font(.subheadline)
                    .foregroundColor(AppTheme.textMuted)
                    .lineLimit(2)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(AppTheme.textMuted)
        }
        .padding(16)
        .background(AppTheme.bg)
        .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
        .cornerRadius(AppTheme.radiusSm)
    }
}

enum MainRoute: Hashable {
    case settings
}

enum KbDetailRoute: Hashable {
    case chat(KnowledgeBase)
    case manage(KnowledgeBase)
}

#Preview {
    HomeView()
        .environmentObject(AuthService())
}
