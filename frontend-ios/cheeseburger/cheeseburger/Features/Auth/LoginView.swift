//
//  LoginView.swift
//  cheeseburger
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var auth: AuthService
    var switchToRegister: () -> Void = {}
    @State private var username = ""
    @State private var password = ""
    @State private var loading = false
    @State private var error: String?
    @FocusState private var focusedField: Field?

    enum Field { case username, password }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                Text(L10n.Auth.loginTitle)
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(AppTheme.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.bottom, 24)

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.Auth.username)
                        .font(.subheadline)
                        .foregroundColor(AppTheme.textMuted)
                    TextField(L10n.Auth.username, text: $username)
                        .authTextFieldStyle()
                        .focused($focusedField, equals: .username)
                        .submitLabel(.next)
                        .onSubmit { focusedField = .password }
                }
                .padding(.bottom, 16)

                VStack(alignment: .leading, spacing: 8) {
                    Text(L10n.Auth.password)
                        .font(.subheadline)
                        .foregroundColor(AppTheme.textMuted)
                    SecureField(L10n.Auth.password, text: $password)
                        .authTextFieldStyle()
                        .focused($focusedField, equals: .password)
                        .submitLabel(.go)
                        .onSubmit { submit() }
                }
                .padding(.bottom, 20)

                if let err = error {
                    Text(err)
                        .font(.footnote)
                        .foregroundColor(AppTheme.danger)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, 12)
                }

                PrimaryButton(title: L10n.Auth.login, action: submit, isLoading: loading)
                    .padding(.bottom, 20)

                HStack(spacing: 4) {
                    Text(L10n.Auth.noAccount)
                        .foregroundColor(AppTheme.textMuted)
                    Button {
                        switchToRegister()
                    } label: {
                        Text(L10n.Auth.register)
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
        .safeAreaInset(edge: .top) { Color.clear.frame(height: 0) }
    }

    private func submit() {
        let u = username.trimmingCharacters(in: .whitespaces)
        let p = password
        if u.isEmpty {
            error = L10n.Auth.usernameRequired
            return
        }
        if p.isEmpty {
            error = L10n.Auth.passwordRequired
            return
        }
        error = nil
        loading = true
        Task {
            do {
                try await auth.login(username: u, password: p)
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
        LoginView()
            .environmentObject(AuthService())
    }
}
