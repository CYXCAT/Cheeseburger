//
//  KbManageView.swift
//  cheeseburger
//

import SwiftUI
import UniformTypeIdentifiers

struct KbManageView: View {
    let kb: KnowledgeBase
    @Environment(\.dismiss) private var dismiss
    @State private var documents: [DocumentOut] = []
    @State private var docsLoading = false
    @State private var pineconeCount: Int?
    @State private var pdfData: Data?
    @State private var urlInput = ""
    @State private var textInput = ""
    @State private var uploading = false
    @State private var error: String?
    @State private var showFileImporter = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                if let err = error {
                    Text(err)
                        .font(.footnote)
                        .foregroundColor(AppTheme.danger)
                        .padding(.horizontal)
                }

                section(L10n.Manage.uploadPdf) {
                    Button {
                        showFileImporter = true
                    } label: {
                        HStack {
                            Image(systemName: "doc.fill")
                            Text(pdfData == nil ? L10n.Manage.uploadPdf : "PDF 已选择")
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(AppTheme.surface)
                        .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
                        .cornerRadius(AppTheme.radiusSm)
                        .foregroundColor(AppTheme.text)
                    }
                    .disabled(uploading)
                    if pdfData != nil {
                        HStack(spacing: 12) {
                            SecondaryButton(title: L10n.Common.cancel, action: { pdfData = nil }, isLoading: false)
                            PrimaryButton(title: L10n.Manage.confirmUpload, action: uploadPdf, isLoading: uploading)
                        }
                    }
                }

                section(L10n.Manage.uploadUrl) {
                    HStack(spacing: 10) {
                        TextField(L10n.Manage.urlPlaceholder, text: $urlInput)
                            .authTextFieldStyle()
                        PrimaryButton(title: L10n.Manage.confirmUpload, action: uploadUrl, isLoading: uploading)
                            .frame(width: 120)
                    }
                }

                section(L10n.Manage.uploadText) {
                    TextEditor(text: $textInput)
                        .frame(minHeight: 80)
                        .padding(10)
                        .background(AppTheme.surface)
                        .overlay(RoundedRectangle(cornerRadius: AppTheme.radiusSm).stroke(AppTheme.border, lineWidth: 1))
                        .cornerRadius(AppTheme.radiusSm)
                    if !textInput.trimmingCharacters(in: .whitespaces).isEmpty {
                        PrimaryButton(title: L10n.Manage.confirmUpload, action: uploadText, isLoading: uploading)
                    }
                }

                section(L10n.Manage.uploaded) {
                    if docsLoading {
                        HStack {
                            ProgressView()
                            Text(L10n.Common.loading)
                                .foregroundColor(AppTheme.textMuted)
                        }
                    } else if documents.isEmpty {
                        Text(pineconeCount ?? 0 > 0
                             ? "Pinecone 中已有 \(pineconeCount!) 条向量记录。新上传的文档将在此列出。"
                             : "暂无文档，上传 PDF / 录入网址 / 上传纯文本后将在此列出。")
                        .font(.subheadline)
                        .foregroundColor(AppTheme.textMuted)
                    } else {
                        LazyVStack(alignment: .leading, spacing: 8) {
                            ForEach(documents) { doc in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(doc.source_id)
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                        Text("\(doc.source_type) · \(doc.chunks_count) 段")
                                            .font(.caption)
                                            .foregroundColor(AppTheme.textMuted)
                                    }
                                    Spacer()
                                    Button(role: .destructive) {
                                        deleteDoc(doc.source_id)
                                    } label: {
                                        Text(L10n.Manage.deleteDoc)
                                            .font(.subheadline)
                                    }
                                }
                                .padding(12)
                                .background(AppTheme.surface)
                                .cornerRadius(AppTheme.radiusSm)
                            }
                        }
                    }
                }
            }
            .padding(20)
        }
        .background(AppTheme.surface)
        .navigationTitle(L10n.Manage.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button(L10n.Common.back) {
                    dismiss()
                }
                .foregroundColor(AppTheme.accentStrong)
            }
        }
        .fileImporter(
            isPresented: $showFileImporter,
            allowedContentTypes: [.pdf],
            allowsMultipleSelection: false
        ) { result in
            switch result {
            case .success(let urls):
                guard let url = urls.first, url.startAccessingSecurityScopedResource() else { return }
                defer { url.stopAccessingSecurityScopedResource() }
                pdfData = try? Data(contentsOf: url)
            case .failure:
                pdfData = nil
            }
        }
        .task {
            await loadDocs()
        }
    }

    private func section<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
                .foregroundColor(AppTheme.text)
            content()
        }
    }

    private func loadDocs() async {
        docsLoading = true
        defer { docsLoading = false }
        do {
            documents = try await APIClient.shared.listDocuments(kbId: kb.id)
            let stats = try? await APIClient.shared.getPineconeStats(kbId: kb.id)
            pineconeCount = stats?.record_count
        } catch _ {
            documents = []
        }
    }

    private func uploadPdf() {
        guard let data = pdfData else { return }
        error = nil
        uploading = true
        Task {
            do {
                _ = try await APIClient.shared.uploadPdf(kbId: kb.id, fileData: data)
                await MainActor.run {
                    pdfData = nil
                    uploading = false
                }
                await loadDocs()
            } catch let e as APIError {
                await MainActor.run {
                    if case .httpStatus(_, let msg) = e { error = msg } else { error = L10n.Common.errorGeneric }
                    uploading = false
                }
            } catch _ {
                await MainActor.run {
                    error = L10n.Common.errorGeneric
                    uploading = false
                }
            }
        }
    }

    private func uploadUrl() {
        let url = urlInput.trimmingCharacters(in: .whitespaces)
        guard !url.isEmpty else { return }
        error = nil
        uploading = true
        Task {
            do {
                _ = try await APIClient.shared.uploadUrl(kbId: kb.id, urlString: url)
                await MainActor.run {
                    urlInput = ""
                    uploading = false
                }
                await loadDocs()
            } catch let e as APIError {
                await MainActor.run {
                    if case .httpStatus(_, let msg) = e { error = msg } else { error = L10n.Common.errorGeneric }
                    uploading = false
                }
            } catch _ {
                await MainActor.run {
                    error = L10n.Common.errorGeneric
                    uploading = false
                }
            }
        }
    }

    private func uploadText() {
        let text = textInput.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }
        error = nil
        uploading = true
        Task {
            do {
                _ = try await APIClient.shared.uploadText(kbId: kb.id, text: text)
                await MainActor.run {
                    textInput = ""
                    uploading = false
                }
                await loadDocs()
            } catch let e as APIError {
                await MainActor.run {
                    if case .httpStatus(_, let msg) = e { error = msg } else { error = L10n.Common.errorGeneric }
                    uploading = false
                }
            } catch _ {
                await MainActor.run {
                    error = L10n.Common.errorGeneric
                    uploading = false
                }
            }
        }
    }

    private func deleteDoc(_ sourceId: String) {
        error = nil
        Task {
            do {
                try await APIClient.shared.deleteDocument(kbId: kb.id, sourceId: sourceId)
                await loadDocs()
            } catch _ {
                await MainActor.run { error = "删除失败" }
            }
        }
    }
}
