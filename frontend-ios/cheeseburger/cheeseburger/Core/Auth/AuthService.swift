//
//  AuthService.swift
//  cheeseburger
//

import Foundation
import Combine

final class AuthService: ObservableObject {
    @Published private(set) var user: UserOut?
    @Published private(set) var isLoading = true
    @Published var errorMessage: String?

    private let client = APIClient.shared

    var isLoggedIn: Bool { user != nil }

    init() {
        Task { await refreshUser() }
    }

    func refreshUser() async {
        guard client.authToken != nil else {
            await MainActor.run {
                user = nil
                isLoading = false
            }
            return
        }
        await MainActor.run { isLoading = true }
        do {
            let u = try await client.getMe()
            await MainActor.run {
                user = u
                isLoading = false
            }
        } catch {
            client.authToken = nil
            await MainActor.run {
                user = nil
                isLoading = false
            }
        }
    }

    func login(username: String, password: String) async throws {
        errorMessage = nil
        let res = try await client.login(username: username.trimmingCharacters(in: .whitespaces), password: password)
        client.authToken = res.access_token
        await MainActor.run { user = res.user }
    }

    func register(inviteToken: String, username: String, password: String) async throws {
        errorMessage = nil
        let res = try await client.register(
            inviteToken: inviteToken.trimmingCharacters(in: .whitespaces),
            username: username.trimmingCharacters(in: .whitespaces),
            password: password
        )
        client.authToken = res.access_token
        await MainActor.run { user = res.user }
    }

    func logout() {
        client.authToken = nil
        user = nil
    }
}
