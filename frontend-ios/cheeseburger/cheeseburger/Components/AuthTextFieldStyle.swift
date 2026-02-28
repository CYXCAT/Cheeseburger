//
//  AuthTextFieldStyle.swift
//  cheeseburger
//

import SwiftUI

struct AuthTextFieldStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .textFieldStyle(.plain)
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(AppTheme.surface)
            .foregroundColor(AppTheme.text)
            .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
            .cornerRadius(AppTheme.radiusSm)
            .autocapitalization(.none)
            .disableAutocorrection(true)
    }
}

extension View {
    func authTextFieldStyle() -> some View {
        modifier(AuthTextFieldStyle())
    }
}
