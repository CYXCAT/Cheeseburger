//
//  PrimaryButton.swift
//  cheeseburger
//

import SwiftUI

struct PrimaryButton: View {
    let title: String
    let action: () -> Void
    var isLoading: Bool = false
    var isDestructive: Bool = false

    var body: some View {
        Button(action: action) {
            Group {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: AppTheme.textInverse))
                } else {
                    Text(title)
                        .fontWeight(.medium)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(isDestructive ? AppTheme.danger : AppTheme.accentStrong)
            .foregroundColor(AppTheme.textInverse)
            .cornerRadius(AppTheme.radiusSm)
        }
        .disabled(isLoading)
        .buttonStyle(.plain)
    }
}

struct SecondaryButton: View {
    let title: String
    let action: () -> Void
    var isLoading: Bool = false

    var body: some View {
        Button(action: action) {
            Group {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: AppTheme.text))
                } else {
                    Text(title)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(AppTheme.surface)
            .foregroundColor(AppTheme.text)
            .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
            .cornerRadius(AppTheme.radiusSm)
        }
        .disabled(isLoading)
        .buttonStyle(.plain)
    }
}
