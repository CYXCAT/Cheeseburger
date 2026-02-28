//
//  RegisterView.swift
//  cheeseburger
//

import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var auth: AuthService
    var switchToLogin: () -> Void = {}
    @State private var inviteToken = ""
    @State private var username = ""
    @State private var password = ""
    @State private var passwordConfirm = ""
    @State private var loading = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                Text(L10n.Auth.registerTitle)
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(AppTheme.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.bottom, 24)

                labeledField(L10n.Auth.inviteToken, text: $inviteToken, isSecure: false)
                labeledField(L10n.Auth.username, text: $username, isSecure: false)
                    .padding(.top, 16)
                labeledField(L10n.Auth.password, text: $password, isSecure: true)
                    .padding(.top, 16)
                labeledField(L10n.Auth.passwordConfirm, text: $passwordConfirm, isSecure: true)
                    .padding(.top, 16)
                    .padding(.bottom, 20)

                if let err = error {
                    Text(err)
                        .font(.footnote)
                        .foregroundColor(AppTheme.danger)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, 12)
                }

                PrimaryButton(title: L10n.Auth.register, action: submit, isLoading: loading)
                    .padding(.bottom, 20)

                HStack(spacing: 4) {
                    Text(L10n.Auth.hasAccount)
                        .foregroundColor(AppTheme.textMuted)
                    Button {
                        switchToLogin()
                    } label: {
                        Text(L10n.Auth.login)
                            .foregroundColor(AppTheme.accentStrong)
                            .fontWeight(.medium)
                    }
                }
                .font(.subheadline)
            }
            .padding(24)
            .frame(maxWidth: 500)
        }
        .scrollDismissesKeyboard(.interactively)
        .background(AppTheme.surface)
    }

    private func labeledField(_ label: String, text: Binding<String>, isSecure: Bool) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.subheadline)
                .foregroundColor(AppTheme.textMuted)
            Group {
                if isSecure {
                    SecureField(label, text: text)
                } else {
                    TextField(label, text: text)
                }
            }
            .authTextFieldStyle()
        }
    }

    private func submit() {
        let token = inviteToken.trimmingCharacters(in: .whitespaces)
        let u = username.trimmingCharacters(in: .whitespaces)
        let p = password
        if token.isEmpty {
            error = L10n.Auth.inviteTokenRequired
            return
        }
        if u.isEmpty {
            error = L10n.Auth.usernameRequired
            return
        }
        if p.isEmpty {
            error = L10n.Auth.passwordRequired
            return
        }
        if p.count < 6 {
            error = L10n.Auth.passwordMinLength
            return
        }
        if p != passwordConfirm {
            error = L10n.Auth.passwordMismatch
            return
        }
        error = nil
        loading = true
        Task {
            do {
                try await auth.register(inviteToken: token, username: u, password: p)
            } catch let e as APIError {
                switch e {
                case .httpStatus(_, let msg): error = msg ?? L10n.Common.errorGeneric
                default: error = L10n.Common.errorGeneric
                }
            } catch _ {
                error = L10n.Common.errorGeneric
            }
            loading = false
        }
    }
}

#Preview {
    NavigationStack {
        RegisterView()
            .environmentObject(AuthService())
    }
}
