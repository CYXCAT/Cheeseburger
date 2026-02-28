//
//  CreateKbSheet.swift
//  cheeseburger
//

import SwiftUI

struct CreateKbSheet: View {
    var onDismiss: () -> Void
    var onSuccess: () -> Void

    @State private var name = ""
    @State private var description = ""
    @State private var loading = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField(L10n.Manage.nameLabel, text: $name)
                    TextField(L10n.Manage.descLabel, text: $description, axis: .vertical)
                        .lineLimit(3...6)
                } header: {
                    Text(L10n.Nav.createKb)
                }

                if let err = error {
                    Section {
                        Text(err)
                            .foregroundColor(AppTheme.danger)
                            .font(.footnote)
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(AppTheme.surface)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.Common.cancel) {
                        onDismiss()
                    }
                    .foregroundColor(AppTheme.accentStrong)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(L10n.Common.save) {
                        submit()
                    }
                    .fontWeight(.medium)
                    .foregroundColor(AppTheme.accentStrong)
                    .disabled(loading || name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    private func submit() {
        let n = name.trimmingCharacters(in: .whitespaces)
        if n.isEmpty {
            error = L10n.Common.nameRequired
            return
        }
        error = nil
        loading = true
        Task {
            do {
                _ = try await APIClient.shared.createKnowledgeBase(name: n, description: description.isEmpty ? nil : description)
                await MainActor.run { onSuccess() }
            } catch let e as APIError {
                await MainActor.run {
                    if case .httpStatus(_, let msg) = e {
                        error = msg ?? L10n.Common.errorGeneric
                    } else {
                        error = L10n.Common.errorGeneric
                    }
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
