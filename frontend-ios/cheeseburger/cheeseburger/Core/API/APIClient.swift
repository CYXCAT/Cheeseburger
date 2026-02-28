//
//  APIClient.swift
//  cheeseburger
//
//  与 frontend/src/api/client.ts 对齐
//

import Foundation

enum APIError: Error {
    case invalidURL
    case httpStatus(Int, String?)
    case decode(Error)
}

final class APIClient {
    static let shared = APIClient()

    private let baseURLString = "https://cheeseburger-h272.onrender.com"
    private let session: URLSession
    private let decoder = JSONDecoder()

    var authToken: String? {
        get { KeychainStorage.shared.accessToken }
        set { KeychainStorage.shared.accessToken = newValue }
    }

    init(session: URLSession = .shared) {
        self.session = session
    }

    private func url(path: String) -> URL? {
        let s = path.hasPrefix("/") ? path : "/\(path)"
        return URL(string: baseURLString + s)
    }

    private func request<T: Decodable>(
        _ path: String,
        method: String = "GET",
        bodyData: Data? = nil,
        formData: (String, Data, String)? = nil,
        skipAuth: Bool = false
    ) async throws -> T {
        guard let url = url(path: path) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method

        if !skipAuth, let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let (fieldName, data, fileName) = formData {
            let boundary = UUID().uuidString
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            request.httpBody = multipartBody(boundary: boundary, fieldName: fieldName, data: data, fileName: fileName)
        } else if let bodyData = bodyData {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = bodyData
        }

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.httpStatus(0, "Invalid response") }

        if http.statusCode == 204 {
            if T.self == EmptyResponse.self { return EmptyResponse() as! T }
        }

        if !http.ok {
            let detail = (try? decoder.decode(APIErrorDetail.self, from: data))?.detail
                ?? String(data: data, encoding: .utf8)
            if http.statusCode == 401 { authToken = nil }
            throw APIError.httpStatus(http.statusCode, detail ?? "HTTP \(http.statusCode)")
        }

        if T.self == EmptyResponse.self { return EmptyResponse() as! T }
        return try decoder.decode(T.self, from: data)
    }

    private func multipartBody(boundary: String, fieldName: String, data: Data, fileName: String) -> Data {
        var d = Data()
        d.append("--\(boundary)\r\n".data(using: .utf8)!)
        d.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        d.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
        d.append(data)
        d.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        return d
    }

    private func jsonBody(_ dict: [String: Any]) throws -> Data {
        try JSONSerialization.data(withJSONObject: dict)
    }

    // MARK: - Auth
    func register(inviteToken: String, username: String, password: String) async throws -> AuthResponse {
        let body = ["invite_token": inviteToken, "username": username, "password": password]
        return try await request("/api/auth/register", method: "POST", bodyData: try jsonBody(body), skipAuth: true)
    }

    func login(username: String, password: String) async throws -> AuthResponse {
        let body = ["username": username, "password": password]
        return try await request("/api/auth/login", method: "POST", bodyData: try jsonBody(body), skipAuth: true)
    }

    // MARK: - User
    func getMe() async throws -> UserOut {
        try await request("/api/users/me", method: "GET")
    }

    func updateMe(username: String?, password: String?) async throws -> UserOut {
        var body: [String: Any] = [:]
        if let u = username { body["username"] = u }
        if let p = password { body["password"] = p }
        return try await request("/api/users/me", method: "PATCH", bodyData: try jsonBody(body))
    }

    // MARK: - Knowledge Bases
    func listKnowledgeBases() async throws -> [KnowledgeBase] {
        try await request("/api/knowledge-bases", method: "GET")
    }

    func getKnowledgeBase(id: Int) async throws -> KnowledgeBase {
        try await request("/api/knowledge-bases/\(id)", method: "GET")
    }

    func createKnowledgeBase(name: String, description: String?) async throws -> KnowledgeBase {
        var body: [String: Any] = ["name": name]
        body["description"] = description?.isEmpty == true ? NSNull() : (description as Any)
        return try await request("/api/knowledge-bases", method: "POST", bodyData: try jsonBody(body))
    }

    func updateKnowledgeBase(id: Int, name: String?, description: String?) async throws -> KnowledgeBase {
        var body: [String: Any] = [:]
        if let n = name { body["name"] = n }
        body["description"] = description ?? NSNull()
        return try await request("/api/knowledge-bases/\(id)", method: "PATCH", bodyData: try jsonBody(body))
    }

    func deleteKnowledgeBase(id: Int) async throws {
        let _: EmptyResponse = try await request("/api/knowledge-bases/\(id)", method: "DELETE")
    }

    // MARK: - Documents
    func uploadPdf(kbId: Int, fileData: Data) async throws -> DocumentUploadResponse {
        try await request(
            "/api/knowledge-bases/\(kbId)/documents/upload-pdf",
            method: "POST",
            formData: ("file", fileData, "file.pdf")
        )
    }

    func uploadUrl(kbId: Int, urlString: String) async throws -> DocumentUploadResponse {
        let body = ["url": urlString]
        return try await request("/api/knowledge-bases/\(kbId)/documents/upload-url", method: "POST", bodyData: try jsonBody(body))
    }

    func uploadText(kbId: Int, text: String) async throws -> DocumentUploadResponse {
        let body = ["text": text]
        return try await request("/api/knowledge-bases/\(kbId)/documents/upload-text", method: "POST", bodyData: try jsonBody(body))
    }

    func listDocuments(kbId: Int) async throws -> [DocumentOut] {
        try await request("/api/knowledge-bases/\(kbId)/documents", method: "GET")
    }

    func getPineconeStats(kbId: Int) async throws -> PineconeStats {
        try await request("/api/knowledge-bases/\(kbId)/documents/pinecone-stats", method: "GET")
    }

    func deleteDocument(kbId: Int, sourceId: String) async throws {
        let escaped = sourceId.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? sourceId
        let _: EmptyResponse = try await request("/api/knowledge-bases/\(kbId)/documents/\(escaped)", method: "DELETE")
    }

    func search(kbId: Int, query: String, searchType: String = "semantic", topK: Int = 10) async throws -> SearchResponse {
        let body: [String: Any] = ["query": query, "search_type": searchType, "top_k": topK]
        return try await request("/api/knowledge-bases/\(kbId)/search", method: "POST", bodyData: try jsonBody(body))
    }

    // MARK: - Chat
    func chat(kbId: Int, messages: [[String: String]]) async throws -> ChatResponse {
        let body: [String: Any] = ["kb_id": kbId, "messages": messages]
        return try await request("/api/chat", method: "POST", bodyData: try jsonBody(body))
    }

    // MARK: - Chat History
    func listConversations(kbId: Int) async throws -> [ConversationOut] {
        try await request("/api/knowledge-bases/\(kbId)/chat/conversations", method: "GET")
    }

    func createConversation(kbId: Int, title: String?) async throws -> ConversationOut {
        let body: [String: Any] = ["title": title ?? NSNull()]
        return try await request("/api/knowledge-bases/\(kbId)/chat/conversations", method: "POST", bodyData: try jsonBody(body))
    }

    func getMessages(kbId: Int, conversationId: Int) async throws -> [HistoryMessageOut] {
        try await request("/api/knowledge-bases/\(kbId)/chat/conversations/\(conversationId)/messages", method: "GET")
    }

    func appendMessages(kbId: Int, conversationId: Int, userMsg: ChatMessagePayload, assistantMsg: ChatMessagePayloadWithTools) async throws {
        let messages: [[String: Any]] = [
            ["role": userMsg.role, "content": userMsg.content],
            [
                "role": assistantMsg.role,
                "content": assistantMsg.content,
                "tool_calls": assistantMsg.tool_calls ?? NSNull()
            ]
        ]
        let body: [String: Any] = ["messages": messages]
        let _: EmptyResponse = try await request(
            "/api/knowledge-bases/\(kbId)/chat/conversations/\(conversationId)/messages",
            method: "POST",
            bodyData: try jsonBody(body)
        )
    }

    func deleteConversation(kbId: Int, conversationId: Int) async throws {
        let _: EmptyResponse = try await request(
            "/api/knowledge-bases/\(kbId)/chat/conversations/\(conversationId)",
            method: "DELETE"
        )
    }
}

private struct EmptyResponse: Codable {}
private extension HTTPURLResponse {
    var ok: Bool { (200...299).contains(statusCode) }
}

// 用于 appendMessages 的 assistant 消息（含 tool_calls）
struct ChatMessagePayloadWithTools {
    let role: String
    let content: String
    let tool_calls: [[String: Any]]?
}
