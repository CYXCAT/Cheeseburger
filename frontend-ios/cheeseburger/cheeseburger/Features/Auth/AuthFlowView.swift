//
//  AuthFlowView.swift
//  cheeseburger
//

import SwiftUI

enum AuthScreen {
    case login
    case register
}

struct AuthFlowView: View {
    @EnvironmentObject var auth: AuthService
    @State private var screen: AuthScreen = .login

    var body: some View {
        NavigationStack {
            Group {
                switch screen {
                case .login:
                    LoginView(switchToRegister: { screen = .register })
                case .register:
                    RegisterView(switchToLogin: { screen = .login })
                }
            }
            .background(AppTheme.surface)
        }
    }
}
