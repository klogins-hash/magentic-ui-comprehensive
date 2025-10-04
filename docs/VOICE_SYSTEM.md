# Voice System Architecture

This document outlines the voice-first interaction system built on top of Magentic-UI.

## Overview

The voice system extends Magentic-UI with always-on voice interaction capabilities, featuring:

- **iOS Native App**: SwiftUI-based mobile interface
- **Voice Backend**: Pipecat-powered voice processing
- **Real-time Communication**: WebSocket-based bidirectional audio streaming
- **Multi-modal Integration**: Voice + visual web interaction

## Components

### iOS App (`ios-app/`)

- Native SwiftUI application
- Real-time audio capture and playback
- WebSocket communication with voice backend
- Integration with Magentic-UI web interface

### Voice Backend (`voice-backend/`)

- Pipecat framework for voice processing
- Groq integration for STT/LLM/TTS pipeline
- WebSocket server for iOS communication
- Bridge to Magentic-UI core system

## Architecture

```text
iOS App <--WebSocket--> Voice Backend <--HTTP--> Magentic-UI Core
   |                         |                        |
   v                         v                        v
Audio I/O              Voice Processing         Web Automation
```

## Getting Started

See individual component READMEs:

- [iOS App Setup](../ios-app/README.md)
- [Voice Backend Setup](../voice-backend/README.md)

## Related Documentation

- [Multi-Agent Business Architecture](../MULTI_AGENT_BUSINESS_ARCHITECTURE.md)
- [Pipecat iOS Integration Plan](../PIPECAT_IOS_PLAN.md)
