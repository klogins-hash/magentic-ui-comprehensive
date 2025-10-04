# Magentic Voice Backend

Pipecat-powered voice processing backend for Magentic-UI voice interactions.

## Features

- **Pipecat Integration**: Advanced voice processing pipeline
- **Groq STT/LLM/TTS**: Complete voice processing stack
- **WebSocket Server**: Real-time communication with iOS app
- **Magentic-UI Bridge**: Integration with core web automation

## Requirements

- Python 3.10+
- Pipecat framework
- Groq API access
- WebSocket support

## Setup

1. **Install Dependencies**:
   ```bash
   cd voice-backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run Server**:
   ```bash
   python main.py
   ```

## Configuration

Required environment variables in `.env`:

```bash
GROQ_API_KEY=your_groq_api_key_here
WEBSOCKET_PORT=8765
MAGENTIC_UI_URL=http://localhost:8081
```

## Architecture

```text
iOS App <--WebSocket--> Voice Backend <--HTTP--> Magentic-UI
   |                         |                      |
Audio Stream           Voice Processing      Web Automation
```

## Key Components

- **`main.py`**: WebSocket server and Pipecat pipeline
- **`voice_processor.py`**: Core voice processing logic
- **`magentic_bridge.py`**: Integration with Magentic-UI API
- **`config.py`**: Configuration management

## API Endpoints

- **WebSocket**: `ws://localhost:8765/ws` - iOS app connection
- **Health Check**: `GET /health` - Server status
- **Metrics**: `GET /metrics` - Performance metrics

## Development

```bash
# Run in development mode
python main.py --debug

# Run tests
pytest tests/

# Monitor logs
tail -f logs/voice_backend.log
```

## Voice Pipeline

1. **Audio Input**: Receive audio from iOS app
2. **STT**: Convert speech to text using Groq
3. **LLM Processing**: Process intent with language model
4. **Magentic Integration**: Execute web automation tasks
5. **TTS**: Convert response to speech
6. **Audio Output**: Stream back to iOS app

## Troubleshooting

- **Connection Issues**: Check WebSocket port and firewall settings
- **Audio Quality**: Verify Groq API key and model availability
- **Performance**: Monitor CPU/memory usage during processing
