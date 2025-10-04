import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var voiceClient = VoiceClient()
    @State private var currentMode: InteractionMode = .voice
    @State private var textMessage = ""
    @State private var messages: [ChatMessage] = []
    @State private var isRecording = false
    @State private var showingSettings = false
    
    enum InteractionMode: String, CaseIterable {
        case voice = "Voice"
        case text = "Text"
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header with mode selector
                VStack {
                    HStack {
                        Text("Magentic AI")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Spacer()
                        
                        Button(action: { showingSettings = true }) {
                            Image(systemName: "gear")
                                .font(.title2)
                        }
                    }
                    .padding(.horizontal)
                    
                    // Mode Selector
                    Picker("Mode", selection: $currentMode) {
                        ForEach(InteractionMode.allCases, id: \.self) { mode in
                            Text(mode.rawValue).tag(mode)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    
                    // Connection Status
                    HStack {
                        Circle()
                            .fill(voiceClient.isConnected ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(voiceClient.isConnected ? "Connected" : "Connecting...")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
                .background(Color(.systemBackground))
                
                Divider()
                
                // Main Interface
                if currentMode == .voice {
                    VoiceInterface(
                        voiceClient: voiceClient,
                        isRecording: $isRecording,
                        messages: $messages
                    )
                } else {
                    TextInterface(
                        voiceClient: voiceClient,
                        textMessage: $textMessage,
                        messages: $messages
                    )
                }
            }
            .navigationBarHidden(true)
        }
        .onAppear {
            setupAudioSession()
            voiceClient.connect()
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(voiceClient: voiceClient)
        }
    }
    
    private func setupAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try audioSession.setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }
}

struct VoiceInterface: View {
    @ObservedObject var voiceClient: VoiceClient
    @Binding var isRecording: Bool
    @Binding var messages: [ChatMessage]
    @State private var audioLevels: [Float] = Array(repeating: 0.0, count: 20)
    @State private var animationTimer: Timer?
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // Recent Messages
            if !messages.isEmpty {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Recent")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    ForEach(messages.suffix(3)) { message in
                        HStack {
                            Image(systemName: message.isUser ? "person.circle" : "brain.head.profile")
                                .foregroundColor(message.isUser ? .blue : .green)
                            Text(message.text)
                                .font(.subheadline)
                                .lineLimit(2)
                            Spacer()
                        }
                        .padding(.horizontal)
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
            }
            
            Spacer()
            
            // Audio Visualization
            AudioVisualizationView(
                isRecording: isRecording,
                audioLevels: audioLevels
            )
            .frame(height: 100)
            .padding(.horizontal)
            
            // Voice Status Text
            Text(voiceClient.isProcessing ? "Processing..." : 
                 isRecording ? "Listening..." : "Hold to speak")
                .font(.headline)
                .foregroundColor(voiceClient.isProcessing ? .orange : 
                               isRecording ? .red : .secondary)
            
            // Push-to-Talk Button
            Button(action: {}) {
                ZStack {
                    Circle()
                        .fill(isRecording ? Color.red.opacity(0.2) : Color.blue.opacity(0.1))
                        .frame(width: 120, height: 120)
                    
                    Circle()
                        .stroke(isRecording ? Color.red : Color.blue, lineWidth: 3)
                        .frame(width: 120, height: 120)
                    
                    Image(systemName: isRecording ? "mic.fill" : "mic")
                        .font(.system(size: 40))
                        .foregroundColor(isRecording ? .red : .blue)
                }
            }
            .scaleEffect(isRecording ? 1.1 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: isRecording)
            .simultaneousGesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        if !isRecording && !voiceClient.isProcessing {
                            startRecording()
                        }
                    }
                    .onEnded { _ in
                        if isRecording {
                            stopRecording()
                        }
                    }
            )
            .disabled(voiceClient.isProcessing)
            
            Spacer()
        }
        .padding()
    }
    
    private func startRecording() {
        isRecording = true
        voiceClient.startRecording()
        
        // Start audio visualization animation
        animationTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            updateAudioLevels()
        }
    }
    
    private func stopRecording() {
        isRecording = false
        voiceClient.stopRecording { response in
            DispatchQueue.main.async {
                if let userMessage = voiceClient.lastUserMessage {
                    messages.append(ChatMessage(text: userMessage, isUser: true))
                }
                messages.append(ChatMessage(text: response, isUser: false))
            }
        }
        
        // Stop audio visualization
        animationTimer?.invalidate()
        audioLevels = Array(repeating: 0.0, count: 20)
    }
    
    private func updateAudioLevels() {
        // Simulate audio levels (in real app, get from audio recorder)
        audioLevels = audioLevels.map { _ in Float.random(in: 0...1) }
    }
}

struct TextInterface: View {
    @ObservedObject var voiceClient: VoiceClient
    @Binding var textMessage: String
    @Binding var messages: [ChatMessage]
    
    var body: some View {
        VStack(spacing: 0) {
            // Chat Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(messages) { message in
                            ChatBubbleView(message: message)
                                .id(message.id)
                        }
                        
                        if voiceClient.isProcessing {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("Thinking...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Spacer()
                            }
                            .padding(.horizontal)
                        }
                    }
                    .padding()
                }
                .onChange(of: messages.count) { _ in
                    if let lastMessage = messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            Divider()
            
            // Text Input
            HStack(spacing: 12) {
                TextField("Type your message...", text: $textMessage, axis: .vertical)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .lineLimit(1...4)
                    .onSubmit {
                        sendMessage()
                    }
                
                Button(action: sendMessage) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                        .foregroundColor(textMessage.isEmpty ? .gray : .blue)
                }
                .disabled(textMessage.isEmpty || voiceClient.isProcessing)
            }
            .padding()
        }
    }
    
    private func sendMessage() {
        guard !textMessage.isEmpty else { return }
        
        let userMessage = textMessage
        textMessage = ""
        
        // Add user message to chat
        messages.append(ChatMessage(text: userMessage, isUser: true))
        
        // Send to backend
        voiceClient.sendTextMessage(userMessage) { response in
            DispatchQueue.main.async {
                messages.append(ChatMessage(text: response, isUser: false))
            }
        }
    }
}

struct AudioVisualizationView: View {
    let isRecording: Bool
    let audioLevels: [Float]
    
    var body: some View {
        HStack(alignment: .center, spacing: 3) {
            ForEach(0..<audioLevels.count, id: \.self) { index in
                RoundedRectangle(cornerRadius: 2)
                    .fill(isRecording ? Color.red : Color.blue)
                    .frame(width: 4, height: CGFloat(audioLevels[index] * 60 + 4))
                    .opacity(isRecording ? 1.0 : 0.3)
                    .animation(.easeInOut(duration: 0.1), value: audioLevels[index])
            }
        }
    }
}

struct ChatBubbleView: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.isUser {
                Spacer()
            }
            
            VStack(alignment: message.isUser ? .trailing : .leading, spacing: 4) {
                Text(message.text)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(message.isUser ? Color.blue : Color(.systemGray5))
                    .foregroundColor(message.isUser ? .white : .primary)
                    .cornerRadius(16)
                
                Text(message.timestamp.formatted(date: .omitted, time: .shortened))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            if !message.isUser {
                Spacer()
            }
        }
    }
}

struct SettingsView: View {
    @ObservedObject var voiceClient: VoiceClient
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section("Connection") {
                    HStack {
                        Text("Status")
                        Spacer()
                        Text(voiceClient.isConnected ? "Connected" : "Disconnected")
                            .foregroundColor(voiceClient.isConnected ? .green : .red)
                    }
                    
                    HStack {
                        Text("Server URL")
                        Spacer()
                        Text(voiceClient.serverURL)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("Voice Settings") {
                    Toggle("Auto-record", isOn: .constant(false))
                        .disabled(true)
                    
                    HStack {
                        Text("Voice Model")
                        Spacer()
                        Text("Groq Whisper")
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("AI Settings") {
                    HStack {
                        Text("LLM Model")
                        Spacer()
                        Text("Groq LLaMA 3.3")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("TTS Voice")
                        Spacer()
                        Text("Fritz-PlayAI")
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("AutoGen Team") {
                    Button("Check Team Status") {
                        // TODO: Check AutoGen team status
                    }
                    
                    Button("View Active Tasks") {
                        // TODO: Show active tasks
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
