//
//  SettingsView.swift
//  cheeseburger
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var auth: AuthService
    @Environment(\.dismiss) private var dismiss
    @State private var username: String = ""
    @State private var newPassword = ""
    @State private var newPasswordConfirm = ""
    @State private var loading = false
    @State private var error: String?
    @State private var success = false

    var body: some View {
        Form {
            Section {
                TextField(L10n.Settings.username, text: $username)
                    .authTextFieldStyle()
            } header: {
                Text(L10n.Settings.title)
            }

            Section {
                SecureField(L10n.Settings.newPassword, text: $newPassword)
                    .authTextFieldStyle()
                SecureField(L10n.Settings.newPasswordConfirm, text: $newPasswordConfirm)
                    .authTextFieldStyle()
            } header: {
                Text(L10n.Settings.newPassword)
            } footer: {
                if success {
                    Text(L10n.Settings.updateSuccess)
                        .foregroundColor(AppTheme.accentStrong)
                }
                if let err = error {
                    Text(err)
                        .foregroundColor(AppTheme.danger)
                }
            }

            Section {
                PrimaryButton(title: L10n.Common.save, action: submit, isLoading: loading)
            }
        }
        .scrollContentBackground(.hidden)
        .background(AppTheme.surface)
        .navigationTitle(L10n.Settings.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button(L10n.Common.back) {
                    dismiss()
                }
                .foregroundColor(AppTheme.accentStrong)
            }
        }
        .onAppear {
            username = auth.user?.username ?? ""
        }
    }

    private func submit() {
        let u = username.trimmingCharacters(in: .whitespaces)
        if u.isEmpty {
            error = L10n.Auth.usernameRequired
            return
        }
        if newPassword != newPasswordConfirm {
            error = L10n.Auth.passwordMismatch
            return
        }
        if !newPassword.isEmpty && newPassword.count < 6 {
            error = L10n.Auth.passwordMinLength
            return
        }
        error = nil
        success = false
        loading = true
        Task {
            do {
                _ = try await APIClient.shared.updateMe(username: u, password: newPassword.isEmpty ? nil : newPassword)
                await auth.refreshUser()
                await MainActor.run {
                    newPassword = ""
                    newPasswordConfirm = ""
                    success = true
                    loading = false
                }
            } catch let e as APIError {
                await MainActor.run {
                    if case .httpStatus(_, let msg) = e { error = msg ?? L10n.Common.errorGeneric } else { error = L10n.Common.errorGeneric }
                    loading = false
                }
            } catch _ {
                await MainActor.run {
                    error = L10n.Common.errorGeneric
                    loading = false
                }
            }
        }
    }
}
