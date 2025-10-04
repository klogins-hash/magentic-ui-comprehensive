import Foundation

struct ChatMessage: Identifiable, Codable {
    let id = UUID()
    let text: String
    let isUser: Bool
    let timestamp: Date
    
    init(text: String, isUser: Bool) {
        self.text = text
        self.isUser = isUser
        self.timestamp = Date()
    }
}

struct VoiceResponse: Codable {
    let type: String
    let content: String
    let timestamp: String
    let needsDelegation: Bool?
    let audio: String?
    
    enum CodingKeys: String, CodingKey {
        case type, content, timestamp, audio
        case needsDelegation = "needs_delegation"
    }
}

struct TaskStatus: Codable {
    let taskId: String
    let description: String
    let status: String
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case description, status
        case createdAt = "created_at"
    }
}

struct ServerInfo: Codable {
    let status: String
    let service: String
    let groqModels: GroqModels
    
    enum CodingKeys: String, CodingKey {
        case status, service
        case groqModels = "groq_models"
    }
}

struct GroqModels: Codable {
    let stt: String
    let llm: String
    let tts: String
}
