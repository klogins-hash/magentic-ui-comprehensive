# Magentic Voice iOS App

Native iOS application for voice-first interaction with Magentic-UI.

## Features

- **Real-time Voice**: Continuous audio capture and playback
- **WebSocket Communication**: Direct connection to voice backend
- **SwiftUI Interface**: Modern, responsive iOS interface
- **Background Processing**: Maintains connection while app is active

## Requirements

- iOS 15.0+
- Xcode 14.0+
- Swift 5.7+

## Setup

1. **Open Project**:
   ```bash
   cd ios-app
   open MagenticVoice.xcodeproj
   ```

2. **Configure Backend URL**:
   - Edit `MagenticVoiceApp.swift`
   - Update `BACKEND_URL` to match your voice backend

3. **Build and Run**:
   - Select target device/simulator
   - Press Cmd+R to build and run

## Architecture

```text
SwiftUI Views <-> WebSocket Manager <-> Voice Backend
     |                    |                   |
Audio Capture      Connection Mgmt      Voice Processing
```

## Key Components

- **`MagenticVoiceApp.swift`**: Main app entry point
- **`ContentView.swift`**: Primary UI interface
- **`WebSocketManager.swift`**: Backend communication
- **`AudioManager.swift`**: Audio capture/playback

## Configuration

Update backend connection in `MagenticVoiceApp.swift`:

```swift
let backendURL = "ws://localhost:8765/ws"  // Development
// let backendURL = "wss://your-domain.com/ws"  // Production
```

## Development

- **Debug Mode**: Enable verbose logging in Debug configuration
- **Simulator**: Audio capture requires physical device for full testing
- **Network**: Ensure voice backend is running and accessible

## Troubleshooting

- **Connection Issues**: Verify backend URL and network connectivity
- **Audio Problems**: Check microphone permissions in Settings
- **Build Errors**: Ensure Xcode and iOS deployment target compatibility
