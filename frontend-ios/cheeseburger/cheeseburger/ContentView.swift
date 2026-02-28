//
//  ContentView.swift
//  cheeseburger
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var auth: AuthService

    var body: some View {
        Group {
            if auth.isLoading {
                loadingView
            } else if auth.isLoggedIn {
                HomeView()
            } else {
                AuthFlowView()
            }
        }
        .animation(.easeInOut(duration: 0.2), value: auth.isLoggedIn)
    }

    private var loadingView: some View {
        VStack(spacing: 12) {
            ProgressView()
            Text(L10n.Common.loading)
                .font(.subheadline)
                .foregroundColor(AppTheme.textMuted)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppTheme.surface)
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthService())
}
