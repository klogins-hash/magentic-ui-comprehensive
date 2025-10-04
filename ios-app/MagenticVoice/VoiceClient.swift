import Foundation
import AVFoundation
import Starscream
import Combine

class VoiceClient: NSObject, ObservableObject {
    @Published var isConnected = false
    @Published var isProcessing = false
    @Published var lastUserMessage: String?
    
    let serverURL = "ws://localhost:8000/ws"
    
    private var socket: WebSocket?
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingURL: URL?
    private var completionHandler: ((String) -> Void)?
    
    override init() {
        super.init()
        setupAudioSession()
    }
    
    func connect() {
        guard let url = URL(string: serverURL) else {
            print("Invalid server URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.timeoutInterval = 5
        
        socket = WebSocket(request: request)
        socket?.delegate = self
        socket?.connect()
    }
    
    func disconnect() {
        socket?.disconnect()
        socket = nil
    }
    
    private func setupAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
            try audioSession.setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }
    
    func startRecording() {
        guard isConnected else {
            print("Not connected to server")
            return
        }
        
        // Setup recording URL
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        recordingURL = documentsPath.appendingPathComponent("recording.wav")
        
        // Audio recording settings
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: recordingURL!, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.record()
            
            print("Started recording")
        } catch {
            print("Failed to start recording: \(error)")
        }
    }
    
    func stopRecording(completion: @escaping (String) -> Void) {
        guard let recorder = audioRecorder, recorder.isRecording else {
            completion("No recording to process")
            return
        }
        
        completionHandler = completion
        isProcessing = true
        
        recorder.stop()
        audioRecorder = nil
        
        // Send audio to server
        sendAudioToServer()
    }
    
    private func sendAudioToServer() {
        guard let recordingURL = recordingURL,
              let audioData = try? Data(contentsOf: recordingURL) else {
            handleResponse("Failed to read audio file")
            return
        }
        
        // Convert audio to base64 for transmission
        let base64Audio = audioData.base64EncodedString()
        
        let message: [String: Any] = [
            "type": "voice",
            "content": base64Audio,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]
        
        sendMessage(message)
    }
    
    func sendTextMessage(_ text: String, completion: @escaping (String) -> Void) {
        guard isConnected else {
            completion("Not connected to server")
            return
        }
        
        completionHandler = completion
        isProcessing = true
        lastUserMessage = text
        
        let message: [String: Any] = [
            "type": "text",
            "content": text,
            "timestamp": ISO8601DateFormatter().string(from: Date())
        ]
        
        sendMessage(message)
    }
    
    private func sendMessage(_ message: [String: Any]) {
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: message)
            socket?.write(data: jsonData)
        } catch {
            print("Failed to send message: \(error)")
            handleResponse("Failed to send message")
        }
    }
    
    private func handleResponse(_ response: String) {
        DispatchQueue.main.async {
            self.isProcessing = false
            self.completionHandler?(response)
            self.completionHandler = nil
        }
    }
    
    private func playAudioResponse(_ base64Audio: String) {
        guard let audioData = Data(base64Encoded: base64Audio) else {
            print("Failed to decode audio data")
            return
        }
        
        do {
            audioPlayer = try AVAudioPlayer(data: audioData)
            audioPlayer?.delegate = self
            audioPlayer?.play()
        } catch {
            print("Failed to play audio: \(error)")
        }
    }
}

// MARK: - WebSocketDelegate
extension VoiceClient: WebSocketDelegate {
    func didReceive(event: WebSocketEvent, client: WebSocket) {
        switch event {
        case .connected(let headers):
            print("WebSocket connected: \(headers)")
            DispatchQueue.main.async {
                self.isConnected = true
            }
            
        case .disconnected(let reason, let code):
            print("WebSocket disconnected: \(reason) with code: \(code)")
            DispatchQueue.main.async {
                self.isConnected = false
                self.isProcessing = false
            }
            
        case .text(let string):
            print("Received text: \(string)")
            handleServerResponse(string)
            
        case .binary(let data):
            print("Received binary data: \(data.count) bytes")
            
        case .error(let error):
            print("WebSocket error: \(error?.localizedDescription ?? "Unknown error")")
            DispatchQueue.main.async {
                self.isConnected = false
                self.isProcessing = false
            }
            
        case .cancelled:
            print("WebSocket cancelled")
            DispatchQueue.main.async {
                self.isConnected = false
            }
            
        default:
            break
        }
    }
    
    private func handleServerResponse(_ jsonString: String) {
        guard let data = jsonString.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            handleResponse("Invalid response from server")
            return
        }
        
        let responseType = json["type"] as? String ?? "text"
        let content = json["content"] as? String ?? "No response"
        
        if responseType == "voice", let audioBase64 = json["audio"] as? String {
            // Play audio response
            playAudioResponse(audioBase64)
        }
        
        handleResponse(content)
    }
}

// MARK: - AVAudioRecorderDelegate
extension VoiceClient: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if !flag {
            handleResponse("Recording failed")
        }
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        print("Audio recorder error: \(error?.localizedDescription ?? "Unknown error")")
        handleResponse("Recording error occurred")
    }
}

// MARK: - AVAudioPlayerDelegate
extension VoiceClient: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        print("Audio playback finished successfully: \(flag)")
    }
    
    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        print("Audio player error: \(error?.localizedDescription ?? "Unknown error")")
    }
}
